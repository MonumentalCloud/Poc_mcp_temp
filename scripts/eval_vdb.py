# -*- coding: utf-8 -*-
"""VDB retrieval eval — 골든데이터셋의 대표 발화로 자기 스킬이 검색되는지 측정.

Usage: python scripts/eval_vdb.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from server.skill_vdb import SkillVDB  # noqa: E402
from skill_map import SKILL_MAP        # noqa: E402


def main() -> None:
    vdb = SkillVDB.load(ROOT / "vdb" / "skills_vdb.json")
    data = json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8"))

    n = top1 = top3 = top5 = 0
    misses = []
    for row in data:
        utt = (row.get("utterance") or "").strip()
        if not utt:
            continue  # 발화 없는 행(가드레일 등)은 제외
        n += 1
        expect = SKILL_MAP[row["seq"]]["name"]
        names = [r["name"] for r in vdb.search(utt, top_k=5)]
        top1 += expect == names[0]
        top3 += expect in names[:3]
        if expect in names[:5]:
            top5 += 1
        else:
            misses.append((row["seq"], utt, expect, names[:3]))

    print(f"queries={n}  top1={top1 / n:.1%}  top3={top3 / n:.1%}  top5={top5 / n:.1%}")
    for seq, utt, expect, got in misses:
        print(f"  MISS seq={seq} '{utt}' expected={expect} got={got}")


if __name__ == "__main__":
    main()
