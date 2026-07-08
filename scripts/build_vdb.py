# -*- coding: utf-8 -*-
"""Build the local skill VDB index from skills/*/SKILL.md.

Usage: python scripts/build_vdb.py
Produces vdb/skills_vdb.json (임베딩된 name+description + payload body).

운영(GenOS VDB) 적재는 genos/skill_document_processor.py 를 GenOS ingestion
파이프라인에 등록해 동일한 SKILL.md 를 업로드한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.skill_vdb import SkillVDB  # noqa: E402

SANITY_QUERIES = [
    ("나 지금 젤리 몇 개 있어?", "jelly_balance_inquiry"),
    ("탭탭o 이용내역 알려줘", "card_usage_inquiry"),
    ("오늘 환율 어때?", "fx_rate_inquiry"),
]


def main() -> None:
    vdb = SkillVDB.build(ROOT / "skills")
    out = ROOT / "vdb" / "skills_vdb.json"
    vdb.save(out)
    print(f"indexed {len(vdb.entries)} skills -> {out}")

    for query, expect in SANITY_QUERIES:
        top = vdb.search(query, top_k=1)[0]
        mark = "OK" if top["name"] == expect else f"!! expected {expect}"
        print(f"  [{mark}] '{query}' -> {top['name']} ({top['score']})")


if __name__ == "__main__":
    main()
