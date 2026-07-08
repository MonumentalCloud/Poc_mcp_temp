# -*- coding: utf-8 -*-
"""Build the skill VDB from skills/*/SKILL.md.

Usage:
  # 로컬 JSON 인덱스 (기본: 문자 n-gram TF-IDF — 키/네트워크 불필요)
  python scripts/build_vdb.py

  # 로컬 JSON 인덱스 + Qwen 원격 임베딩
  QWEN_API_KEY=... python scripts/build_vdb.py --embedder qwen_api

  # Weaviate 컬렉션 적재 + Qwen 원격 임베딩 (운영 구성)
  QWEN_API_KEY=... WEAVIATE_URL=... WEAVIATE_API_KEY=... \
      python scripts/build_vdb.py --backend weaviate
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.skill_vdb import SkillVDB, make_embedder  # noqa: E402

SANITY_QUERIES = [
    ("나 지금 켈리 몇 개 있어?", "kelly_balance_inquiry"),
    ("탭탭o 이용내역 알려줘", "card_usage_inquiry"),
    ("오늘 환율 어때?", "fx_rate_inquiry"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["local", "weaviate"], default="local")
    ap.add_argument("--embedder", choices=["char_ngram_tfidf", "qwen_api"], default=None,
                    help="기본: local은 char_ngram_tfidf, weaviate는 qwen_api")
    args = ap.parse_args()

    if args.backend == "weaviate":
        from server.weaviate_vdb import WeaviateVDB
        vdb = WeaviateVDB(make_embedder(args.embedder or "qwen_api"))
        n = vdb.ingest(ROOT / "skills")
        print(f"ingested {n} skills -> weaviate collection '{vdb.collection}' @ {vdb.url}")
    else:
        vdb = SkillVDB.build(ROOT / "skills", make_embedder(args.embedder or "char_ngram_tfidf"))
        out = ROOT / "vdb" / "skills_vdb.json"
        vdb.save(out)
        print(f"indexed {len(vdb.entries)} skills -> {out} (embedder={vdb.embedder.kind})")

    for query, expect in SANITY_QUERIES:
        top = vdb.search(query, top_k=1)
        got = top[0]["name"] if top else None
        mark = "OK" if got == expect else f"!! expected {expect}"
        score = top[0]["score"] if top else None
        print(f"  [{mark}] '{query}' -> {got} ({score})")


if __name__ == "__main__":
    main()
