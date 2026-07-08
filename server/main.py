# -*- coding: utf-8 -*-
"""Monimo PoC MCP server (FastMCP).

- 81 mock domain tools (tool_catalog / mock_tools)
- Skill VDB tools: search_skills(1단계: name+description) / load_skill(2단계: body payload)

Run:
    python -m server.main                 # stdio transport
    fastmcp run server/main.py:mcp        # or via fastmcp CLI
"""
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .mock_tools import register_mock_tools
from .skill_vdb import SkillVDB

ROOT = Path(__file__).resolve().parent.parent
VDB_PATH = ROOT / "vdb" / "skills_vdb.json"

INSTRUCTIONS = """\
모니모 AI Agent PoC MCP 서버입니다.

사용 순서 (progressive disclosure):
1. 사용자 발화가 들어오면 먼저 `search_skills`로 스킬 VDB를 검색합니다.
   (name+description만 반환 — 트리거 판단용)
2. 적합한 스킬이 있으면 `load_skill`로 body(Instructions/예외 처리/안내 문구)를
   로드해 그대로 따릅니다.
3. body가 지시하는 required_tools(이 서버의 목업 도메인 툴)를 순서대로 호출합니다.

도메인 툴은 전부 목업이며 고정 픽스처(기준일 2026-07-08)를 반환합니다.
실행형 툴(즉시결제/출금/교환 등)은 반드시 사용자 확인 후 호출하세요.
"""

mcp = FastMCP("monimo-poc-mcp", instructions=INSTRUCTIONS)
register_mock_tools(mcp)

_vdb: SkillVDB | None = None


def _get_vdb() -> SkillVDB:
    global _vdb
    if _vdb is None:
        if not VDB_PATH.exists():
            raise RuntimeError("vdb/skills_vdb.json not found — run `python scripts/build_vdb.py` first")
        _vdb = SkillVDB.load(VDB_PATH)
    return _vdb


@mcp.tool
def search_skills(query: str, top_k: int = 5, domain: Optional[str] = None,
                  category: Optional[str] = None, case_type: Optional[str] = None,
                  required_tool: Optional[str] = None) -> dict:
    """사용자 발화로 스킬 VDB를 시맨틱 검색합니다 (1단계 — name/description/score만 반환).
    filters: domain(finance|non_finance), category(search|event|product_info|financial_info|
    monimo|samsung_financial|life|fire|card|securities|casual|unsupported),
    case_type(normal|error|multiturn|fallback), required_tool(툴명)."""
    results = _get_vdb().search(query, top_k=top_k, domain=domain, category=category,
                                case_type=case_type, required_tool=required_tool)
    return {"query": query, "count": len(results), "results": results}


@mcp.tool
def load_skill(name: str) -> dict:
    """스킬 이름으로 SKILL.md body(payload)를 로드합니다 (2단계 — 트리거 확정 후 호출).
    반환된 instructions(body)를 실행 매뉴얼로 그대로 따르세요."""
    entry = _get_vdb().get(name)
    if not entry:
        return {"error": f"skill not found: {name}"}
    body = entry.pop("payload")
    return {**entry, "instructions": body}


@mcp.tool
def list_skills(domain: Optional[str] = None, category: Optional[str] = None) -> dict:
    """등록된 스킬 목록(name/description/category)을 조회합니다. 디버깅/탐색용."""
    entries = _get_vdb().entries
    out = [
        {"name": e["name"], "description": e["description"], "domain": e["domain"],
         "category": e["category"], "case_type": e["case_type"]}
        for e in entries
        if (not domain or e["domain"] == domain) and (not category or e["category"] == category)
    ]
    return {"count": len(out), "skills": out}


if __name__ == "__main__":
    mcp.run()
