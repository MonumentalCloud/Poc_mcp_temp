"""Extract the golden dataset rows from the source Excel sheet '2) DATA'.

Usage:
    python scripts/extract_dataset.py <xlsx_path> [output_json]

Produces data/dataset.json — one record per data row. Separator rows
("(필요 시 case 추가)") and empty rows are dropped.
"""
import json
import sys
from pathlib import Path

import openpyxl

COLUMNS = [
    "datasetID", "seq", "domain", "category", "target", "path",
    "intent", "subagent", "type", "case", "utterance", "guide", "api",
]


def extract(xlsx_path: str) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb["2) DATA"]
    rows = []
    for r in ws.iter_rows(min_row=7, values_only=True):
        # skip separators / blank filler rows (no 순번 and no 의도)
        if not r[1] and not r[6]:
            continue
        if r[0] and "필요 시" in str(r[0]):
            continue
        rows.append(dict(zip(COLUMNS, r[: len(COLUMNS)])))
    return rows


if __name__ == "__main__":
    xlsx = sys.argv[1]
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "data/dataset.json")
    data = extract(xlsx)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"extracted {len(data)} rows -> {out}")
