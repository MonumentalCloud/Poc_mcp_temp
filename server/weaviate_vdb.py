# -*- coding: utf-8 -*-
"""Weaviate-backed skill VDB.

- 벡터는 외부 임베더(QwenAPIEmbedder 등)가 생성 (bring-your-own-vector,
  vectorizer: none) — Weaviate는 저장·nearVector 검색만 담당한다.
- REST(/v1/schema, /v1/batch/objects) + GraphQL(nearVector)만 사용하므로
  weaviate-client/gRPC 의존성이 없다. Weaviate Cloud(WCD)와 self-hosted 모두 동작.

환경변수:
  WEAVIATE_URL         예: https://xxxx.weaviate.cloud (필수)
  WEAVIATE_API_KEY     WCD API key (self-hosted 무인증이면 생략 가능)
  WEAVIATE_COLLECTION  기본 MonimoSkill
"""
from __future__ import annotations

import json
import os
import uuid

import httpx

from .skill_vdb import Embedder, collect_entries, embed_entries

_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # uuid5용 고정 네임스페이스

TEXT_PROPS = ["name", "description", "domain", "category", "target", "case_type",
              "seq", "dataset_id", "hooks", "version", "payload"]
ARRAY_PROPS = ["required_tools"]
RETURN_FIELDS = "name description domain category case_type required_tools"


class WeaviateVDB:
    def __init__(self, embedder: Embedder, url: str | None = None,
                 api_key: str | None = None, collection: str | None = None):
        self.embedder = embedder
        self.url = (url or os.environ["WEAVIATE_URL"]).rstrip("/")
        self.api_key = api_key or os.getenv("WEAVIATE_API_KEY", "")
        self.collection = collection or os.getenv("WEAVIATE_COLLECTION", "MonimoSkill")

    # -- http helpers ---------------------------------------------------
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _get(self, path: str) -> httpx.Response:
        return httpx.get(f"{self.url}{path}", headers=self._headers(), timeout=30)

    def _post(self, path: str, body: dict) -> httpx.Response:
        r = httpx.post(f"{self.url}{path}", headers=self._headers(), json=body, timeout=60)
        r.raise_for_status()
        return r

    # -- schema / ingest ------------------------------------------------
    def ensure_schema(self, recreate: bool = False) -> None:
        exists = self._get(f"/v1/schema/{self.collection}").status_code == 200
        if exists and recreate:
            httpx.delete(f"{self.url}/v1/schema/{self.collection}", headers=self._headers(), timeout=30)
            exists = False
        if exists:
            return
        props = [{"name": p, "dataType": ["text"],
                  "indexSearchable": p in ("name", "description"),
                  "indexFilterable": True} for p in TEXT_PROPS]
        props += [{"name": p, "dataType": ["text[]"], "indexFilterable": True} for p in ARRAY_PROPS]
        self._post("/v1/schema", {
            "class": self.collection,
            "vectorizer": "none",                      # 벡터는 외부(Qwen API)에서 주입
            "vectorIndexConfig": {"distance": "cosine"},
            "properties": props,
        })

    def ingest(self, skills_dir, recreate: bool = True) -> int:
        """skills/*/SKILL.md 를 임베딩해 Weaviate 컬렉션에 업서트한다."""
        entries = collect_entries(skills_dir)
        _, vectors = embed_entries(entries, self.embedder)
        self.ensure_schema(recreate=recreate)
        objects = []
        for e, vec in zip(entries, vectors):
            props = {k: e.get(k) for k in TEXT_PROPS + ARRAY_PROPS}
            objects.append({
                "class": self.collection,
                "id": str(uuid.uuid5(_NAMESPACE, e["name"])),  # name 기준 결정적 ID → 재실행 시 덮어씀
                "properties": props,
                "vector": vec,
            })
        for i in range(0, len(objects), 50):
            self._post("/v1/batch/objects", {"objects": objects[i : i + 50]})
        return len(objects)

    # -- query ----------------------------------------------------------
    def _graphql(self, query: str) -> dict:
        r = self._post("/v1/graphql", {"query": query})
        data = r.json()
        if data.get("errors"):
            raise RuntimeError(f"weaviate graphql error: {data['errors']}")
        return data["data"]["Get"].get(self.collection) or []

    @staticmethod
    def _where(domain=None, category=None, case_type=None, required_tool=None) -> str:
        operands = []
        for field, value in (("domain", domain), ("category", category), ("case_type", case_type)):
            if value:
                operands.append(f'{{path: ["{field}"], operator: Equal, valueText: {json.dumps(value)}}}')
        if required_tool:
            operands.append(f'{{path: ["required_tools"], operator: ContainsAny, valueText: [{json.dumps(required_tool)}]}}')
        if not operands:
            return ""
        if len(operands) == 1:
            return f", where: {operands[0]}"
        return f', where: {{operator: And, operands: [{", ".join(operands)}]}}'

    def search(self, query: str, top_k: int = 5, domain: str | None = None,
               category: str | None = None, case_type: str | None = None,
               required_tool: str | None = None) -> list[dict]:
        vec = self.embedder.embed(query)
        gql = (
            f'{{ Get {{ {self.collection}('
            f'nearVector: {{vector: {json.dumps(vec)}}}, limit: {int(top_k)}'
            f'{self._where(domain, category, case_type, required_tool)}'
            f') {{ {RETURN_FIELDS} _additional {{ certainty }} }} }} }}'
        )
        out = []
        for item in self._graphql(gql):
            certainty = (item.get("_additional") or {}).get("certainty")
            out.append({
                "name": item["name"], "description": item["description"],
                "score": round(certainty, 4) if certainty is not None else None,
                "domain": item.get("domain"), "category": item.get("category"),
                "case_type": item.get("case_type"),
                "required_tools": item.get("required_tools") or [],
            })
        return out

    def get(self, name: str) -> dict | None:
        fields = " ".join(TEXT_PROPS + ARRAY_PROPS)
        gql = (
            f'{{ Get {{ {self.collection}('
            f'where: {{path: ["name"], operator: Equal, valueText: {json.dumps(name)}}}, limit: 1'
            f') {{ {fields} }} }} }}'
        )
        items = self._graphql(gql)
        if not items:
            return None
        item = items[0]
        item["required_tools"] = item.get("required_tools") or []
        return item

    @property
    def entries(self) -> list[dict]:
        """list_skills용 전체 목록 (payload 제외)."""
        fields = "name description domain category case_type"
        gql = f'{{ Get {{ {self.collection}(limit: 1000) {{ {fields} }} }} }}'
        return self._graphql(gql)
