import os
import re
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel


class GenOSVectorMeta(BaseModel):
    class Config:
        extra = "allow"

    # ── GenOS 표준 필드 ──
    text: str | None = None            # 임베딩/검색 대상 = frontmatter.description
    n_char: int | None = None
    n_word: int | None = None
    n_line: int | None = None
    i_page: int | None = None
    e_page: int | None = None
    i_chunk_on_page: int | None = None
    n_chunk_of_page: int | None = None
    i_chunk_on_doc: int | None = None
    n_chunk_of_doc: int | None = None
    n_page: int | None = None
    reg_date: str | None = None

    # ── frontmatter.metadata.* flatten 필드 (필터 대상) ──
    skill_name: str | None = None      # 레지스트리 키이자 스킬 식별자 (frontmatter.name)
    body: str | None = None            # 비임베딩 payload — SKILL.md 본문 markdown 원문

    domain: str | None = None                   # 필터: card/life/fire/securities/monimo/…
    required_tools: list[str] | None = None     # 필터: monimo mcp tools
    version: str | None = None


# ─── frontmatter 파서 (자체 구현) ──────────────────────────────────────────
# 파일 맨 앞의 `---`~`---` 첫 블록만 frontmatter 로 인식.
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(?P<meta>.*?)\r?\n---[ \t]*\r?\n?(?P<body>.*)\Z",
    re.DOTALL,
)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """SKILL.md 원문에서 YAML frontmatter 와 body 를 분리한다.

    파일 맨 앞이 `---` 로 열리고 다음 `---` 로 닫히는 블록만 frontmatter 로
    인식한다. frontmatter 가 없으면 `({}, 원문)` 반환.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    metadata = yaml.safe_load(m.group("meta")) or {}
    if not isinstance(metadata, dict):
        raise ValueError(
            f"frontmatter 최상위가 dict 가 아닙니다: {type(metadata).__name__}"
        )
    return metadata, m.group("body")


# ─── SKILL.md 전용 로더 ────────────────────────────────────────────────────
class SkillMarkdownLoader:
    """SKILL.md 를 읽어 (metadata, body) 로 분리해 반환.

    langchain 로더를 쓰지 않는 이유:
      - Unstructured 계열은 markdown 구조를 평문화해 헤더/리스트/코드블록을
        뭉갠다. SKILL.md 는 body 의 markdown 구조 자체가 에이전트에게 전달되는
        지시문이므로 원문 보존이 필수.
      - langchain 로더는 YAML frontmatter 를 인식하지 못한다.
      - 무거운 의존성(unstructured, nltk, lxml 등) 대비 여기서 얻는 이득이 없음.
    """

    SUPPORTED_EXT = (".md", ".markdown")

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> dict:
        ext = os.path.splitext(self.file_path)[-1].lower()
        if ext not in self.SUPPORTED_EXT:
            raise ValueError(
                f"지원하지 않는 확장자입니다: {ext} (SKILL.md만 처리)"
            )

        raw = Path(self.file_path).read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw)
        return {"metadata": metadata, "body": body}


# ─── DocumentProcessor ─────────────────────────────────────────────────────
class DocumentProcessor:
    """모니모 planner skill VDB ingestion (GenOS 단일 파일 preprocessor).

    SKILL.md 1개 = vector 1개 (스킬 표준 가이드 §9).
      - text : frontmatter.description → 임베딩 대상 (preload 대체)
      - body : `---`~`---` 이후 markdown 원문 → 비임베딩 payload
      - meta : domain / required_tools / version 등 나머지 frontmatter 커스텀 키
    """

    REQUIRED_FIELDS = ("name", "description", "metadata")

    def get_loader(self, file_path: str) -> SkillMarkdownLoader:
        return SkillMarkdownLoader(file_path)

    def load_documents(self, file_path: str, **kwargs: dict) -> dict:
        document = self.get_loader(file_path).load()

        fm = document["metadata"]  # frontmatter 전체
        missing = [k for k in self.REQUIRED_FIELDS if k not in fm]
        if missing:
            raise ValueError(
                f"{file_path}: frontmatter 필수 필드 누락 -> {missing}"
            )

        # name / description 는 비어있지 않은 문자열
        for k in ("name", "description"):
            v = fm.get(k)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(
                    f"{file_path}: frontmatter.{k} 는 비어있지 않은 문자열이어야 함 (받은 값={v!r})"
                )

        # metadata 는 dict — 필터 대상 속성들이 top-level 로 flatten 될 대상
        if not isinstance(fm["metadata"], dict):
            raise ValueError(
                f"{file_path}: frontmatter.metadata 는 dict 여야 함 "
                f"(받은 타입={type(fm['metadata']).__name__})"
            )

        body = document["body"].strip()
        if not body:
            raise ValueError(f"{file_path}: body(본문)가 비어 있습니다.")

        return {"frontmatter": fm, "body": body}

    def compose_vectors(self, file_path: str, document: dict, **kwargs: dict) -> list[dict]:
        fm = document["frontmatter"]
        body = document["body"]

        skill_name = fm["name"].strip()
        description = fm["description"].strip()
        # metadata 하위 키를 top-level 로 flatten (Equal/ContainsAny 필터 인덱싱 대상)
        metadata_flat = dict(fm["metadata"])

        # skill 표준 예약어와 metadata.* 키 충돌 방지
        reserved = {"text", "n_char", "n_word", "n_line", "reg_date", "skill_name", "body"}
        conflicts = reserved & metadata_flat.keys()
        if conflicts:
            raise ValueError(
                f"{file_path}: frontmatter.metadata 에 예약 키가 포함됨 -> {sorted(conflicts)}"
            )

        global_metadata = dict(
            reg_date=datetime.now().isoformat(timespec="seconds") + "Z",
        )

        # SKILL.md 1개 = 벡터 1개. 청킹 없음.
        # n_char/n_word/n_line 은 임베딩 대상(text=description) 기준.
        vectors = []
        vectors.append(GenOSVectorMeta.model_validate({
            "text": description,
            "n_char": len(description),
            "n_word": len(description.split()),
            "n_line": len(description.splitlines()),
            "skill_name": skill_name,
            "body": body,
            # ── 첨부 프로세서 호환 필드 ──
            "i_page": 1,
            "e_page": 1,
            "i_chunk_on_page": 0,
            "n_chunk_of_page": 1,
            "i_chunk_on_doc": 0,
            "n_chunk_of_doc": 1,
            "n_page": 1,
            **metadata_flat,   # domain / required_tools / version 등을 top-level property 로 flatten
            **global_metadata,
        }))
        return vectors

    async def __call__(self, request, file_path: str, **kwargs: dict) -> list[dict]:
        document: dict = self.load_documents(file_path, **kwargs)
        # await assert_cancelled(request)

        vectors: list[dict] = self.compose_vectors(file_path, document, **kwargs)
        return vectors
