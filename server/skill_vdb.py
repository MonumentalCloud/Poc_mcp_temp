# -*- coding: utf-8 -*-
"""Skill VDB — 표준 스킬 런타임의 'name+description preload + 매칭'을
벡터 검색으로 대체하는 저장소 (skillstandardguide.md §9).

- 임베딩 대상: frontmatter의 name + description (트리거 신호)
- payload   : SKILL.md body (적중 시 반환, 임베딩하지 않음)
- 필터 필드 : domain / category / case_type / required_tools

기본 임베더는 문자 n-gram TF-IDF (외부 모델/네트워크 불필요, 한국어에
토크나이저 없이 동작). `Embedder` 인터페이스를 구현해 문장 임베딩 모델로
교체할 수 있다.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path

import yaml


# ── SKILL.md parsing ───────────────────────────────────────────────
def parse_skill_md(text: str) -> tuple[dict, str]:
    """frontmatter(dict)와 body(str)로 분리한다."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("invalid SKILL.md: frontmatter block not found")
    return yaml.safe_load(m.group(1)), m.group(2).strip()


# ── Embedder ───────────────────────────────────────────────────────
class Embedder:
    """교체 가능한 임베딩 인터페이스. embed()는 sparse dict {feature: weight}."""

    kind = "base"

    def fit(self, corpus: list[str]) -> None: ...

    def embed(self, text: str) -> dict[str, float]:
        raise NotImplementedError

    def state(self) -> dict:
        return {}

    @classmethod
    def from_state(cls, state: dict) -> "Embedder":
        raise NotImplementedError


class CharNgramTfidfEmbedder(Embedder):
    """문자 2~3-gram TF-IDF. 한국어/영문 혼합 짧은 텍스트 매칭용 기본 임베더."""

    kind = "char_ngram_tfidf"

    def __init__(self, ngram_range: tuple[int, int] = (2, 3)):
        self.ngram_range = ngram_range
        self.idf: dict[str, float] = {}
        self.n_docs = 0

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFKC", text).lower()
        return re.sub(r"\s+", " ", text).strip()

    def _ngrams(self, text: str) -> list[str]:
        t = self._normalize(text)
        lo, hi = self.ngram_range
        out = []
        for n in range(lo, hi + 1):
            out.extend(t[i : i + n] for i in range(len(t) - n + 1))
        return out

    def fit(self, corpus: list[str]) -> None:
        self.n_docs = len(corpus)
        df: dict[str, int] = {}
        for doc in corpus:
            for g in set(self._ngrams(doc)):
                df[g] = df.get(g, 0) + 1
        self.idf = {g: math.log((1 + self.n_docs) / (1 + c)) + 1.0 for g, c in df.items()}

    def embed(self, text: str) -> dict[str, float]:
        tf: dict[str, int] = {}
        for g in self._ngrams(text):
            tf[g] = tf.get(g, 0) + 1
        default_idf = math.log(1 + self.n_docs) + 1.0  # 미등록 n-gram
        vec = {g: (1 + math.log(c)) * self.idf.get(g, default_idf) for g, c in tf.items()}
        norm = math.sqrt(sum(w * w for w in vec.values())) or 1.0
        return {g: w / norm for g, w in vec.items()}

    def state(self) -> dict:
        return {"ngram_range": list(self.ngram_range), "idf": self.idf, "n_docs": self.n_docs}

    @classmethod
    def from_state(cls, state: dict) -> "CharNgramTfidfEmbedder":
        emb = cls(tuple(state["ngram_range"]))
        emb.idf = state["idf"]
        emb.n_docs = state["n_docs"]
        return emb


EMBEDDERS = {CharNgramTfidfEmbedder.kind: CharNgramTfidfEmbedder}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(b) < len(a):
        a, b = b, a
    return sum(w * b[g] for g, w in a.items() if g in b)


# ── VDB ────────────────────────────────────────────────────────────
class SkillVDB:
    def __init__(self, embedder: Embedder, entries: list[dict]):
        self.embedder = embedder
        self.entries = entries
        self.by_name = {e["name"]: e for e in entries}

    # -- build / persist ------------------------------------------------
    @classmethod
    def build(cls, skills_dir: Path, embedder: Embedder | None = None) -> "SkillVDB":
        embedder = embedder or CharNgramTfidfEmbedder()
        entries = []
        for md in sorted(skills_dir.glob("*/SKILL.md")):
            meta, body = parse_skill_md(md.read_text(encoding="utf-8"))
            entries.append({
                "name": meta["name"],
                "description": meta["description"],
                "domain": meta.get("domain"),
                "category": meta.get("category"),
                "target": meta.get("target"),
                "case_type": meta.get("case_type"),
                "seq": meta.get("seq"),
                "dataset_id": meta.get("dataset_id"),
                "required_tools": meta.get("required_tools", []),
                "version": meta.get("version"),
                "payload": body,  # 임베딩하지 않음 — 적중 시 반환
            })
        # 임베딩 대상은 name + description 뿐 (트리거의 전부)
        corpus = [f'{e["name"]} {e["description"]}' for e in entries]
        embedder.fit(corpus)
        for e, doc in zip(entries, corpus):
            e["vector"] = embedder.embed(doc)
        return cls(embedder, entries)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "embedder": {"kind": self.embedder.kind, "state": self.embedder.state()},
            "skills": self.entries,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "SkillVDB":
        raw = json.loads(path.read_text(encoding="utf-8"))
        emb_cls = EMBEDDERS[raw["embedder"]["kind"]]
        return cls(emb_cls.from_state(raw["embedder"]["state"]), raw["skills"])

    # -- query ----------------------------------------------------------
    def search(self, query: str, top_k: int = 5, domain: str | None = None,
               category: str | None = None, case_type: str | None = None,
               required_tool: str | None = None) -> list[dict]:
        qv = self.embedder.embed(query)
        scored = []
        for e in self.entries:
            if domain and e["domain"] != domain:
                continue
            if category and e["category"] != category:
                continue
            if case_type and e["case_type"] != case_type:
                continue
            if required_tool and required_tool not in e["required_tools"]:
                continue
            scored.append((cosine(qv, e["vector"]), e))
        scored.sort(key=lambda x: -x[0])
        return [
            {"name": e["name"], "description": e["description"], "score": round(s, 4),
             "domain": e["domain"], "category": e["category"], "case_type": e["case_type"],
             "required_tools": e["required_tools"]}
            for s, e in scored[:top_k]
        ]

    def get(self, name: str) -> dict | None:
        e = self.by_name.get(name)
        if not e:
            return None
        return {k: v for k, v in e.items() if k != "vector"}
