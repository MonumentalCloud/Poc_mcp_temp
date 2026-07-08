# -*- coding: utf-8 -*-
"""Build the skill VDB index from skills/*/SKILL.md.

Usage: python scripts/build_vdb.py
Produces vdb/skills_vdb.json (임베딩된 name+description + payload body).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.skill_vdb import SkillVDB  # noqa: E402


def main() -> None:
    vdb = SkillVDB.build(ROOT / "skills")
    out = ROOT / "vdb" / "skills_vdb.json"
    vdb.save(out)
    print(f"indexed {len(vdb.entries)} skills -> {out}")

    # sanity check: 대표 발화로 자기 스킬이 top-1에 오는지 몇 건 확인
    for query, expect in [
        ("나 지금 켈리 몇 개 있어?", "kelly_balance_inquiry"),
        ("탭탭o 이용내역 알려줘", "card_usage_inquiry"),
        ("오늘 환율 어때?", "fx_rate_inquiry"),
    ]:
        top = vdb.search(query, top_k=1)[0]
        mark = "OK" if top["name"] == expect else f"!! expected {expect}"
        print(f"  [{mark}] '{query}' -> {top['name']} ({top['score']})")


if __name__ == "__main__":
    main()
