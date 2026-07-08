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
import os
import re
import unicodedata
from pathlib import Path

import httpx
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


class QwenAPIEmbedder(Embedder):
    """OpenAI-호환 원격 임베딩 API (Qwen3-Embedding 계열).

    기본값은 SiliconFlow(Qwen/Qwen3-Embedding-0.6B, 무료 티어)이며
    DashScope compatible-mode(text-embedding-v4) 등 동일 프로토콜 API로 교체 가능.
    환경변수: QWEN_API_KEY(필수), QWEN_API_BASE, QWEN_EMBEDDING_MODEL
    """

    kind = "qwen_api"

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None):
        self.base_url = (base_url or os.getenv("QWEN_API_BASE", "https://api.siliconflow.cn/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("QWEN_API_KEY", "")
        self.model = model or os.getenv("QWEN_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")

    def fit(self, corpus: list[str]) -> None:  # 원격 모델 — 학습 불필요
        pass

    def _request(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            raise RuntimeError("QWEN_API_KEY is not set — required for qwen_api embedder")
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]

    @staticmethod
    def _l2(vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed(self, text: str) -> list[float]:
        return self._l2(self._request([text])[0])

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            out.extend(self._l2(v) for v in self._request(texts[i : i + batch_size]))
        return out

    def state(self) -> dict:
        return {"base_url": self.base_url, "model": self.model}  # api_key는 저장하지 않음

    @classmethod
    def from_state(cls, state: dict) -> "QwenAPIEmbedder":
        return cls(base_url=state["base_url"], model=state["model"])


EMBEDDERS = {
    CharNgramTfidfEmbedder.kind: CharNgramTfidfEmbedder,
    QwenAPIEmbedder.kind: QwenAPIEmbedder,
}


def make_embedder(kind: str | None = None) -> Embedder:
    kind = kind or os.getenv("EMBEDDER", CharNgramTfidfEmbedder.kind)
    if kind not in EMBEDDERS:
        raise ValueError(f"unknown embedder: {kind} ({'/'.join(EMBEDDERS)})")
    return EMBEDDERS[kind]()


def cosine(a, b) -> float:
    """sparse dict 또는 dense list 벡터의 코사인 유사도 (벡터는 L2 정규화 가정)."""
    if isinstance(a, dict):
        if len(b) < len(a):
            a, b = b, a
        return sum(w * b[g] for g, w in a.items() if g in b)
    return sum(x * y for x, y in zip(a, b))


# ── corpus helpers ─────────────────────────────────────────────────
def collect_entries(skills_dir: Path) -> list[dict]:
    """skills/*/SKILL.md 를 파싱해 VDB 엔트리 목록으로 변환 (backend 공용)."""
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
            "hooks": meta.get("hooks"),
            "version": meta.get("version"),
            "payload": body,  # 임베딩하지 않음 — 적중 시 반환
        })
    return entries


def embed_entries(entries: list[dict], embedder: Embedder) -> tuple[list[str], list]:
    """임베딩 대상은 name + description 뿐 (트리거의 전부)."""
    corpus = [f'{e["name"]} {e["description"]}' for e in entries]
    embedder.fit(corpus)
    if hasattr(embedder, "embed_batch"):
        vectors = embedder.embed_batch(corpus)
    else:
        vectors = [embedder.embed(doc) for doc in corpus]
    return corpus, vectors


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
        entries = collect_entries(skills_dir)
        corpus, vectors = embed_entries(entries, embedder)
        for e, vec in zip(entries, vectors):
            e["vector"] = vec
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
