# -*- coding: utf-8 -*-
"""Monimo PoC MCP server (FastMCP).

- 81 mock domain tools (tool_catalog / mock_tools)
- Skill VDB tools: search_skills(1단계) / load_skill(2단계) / list_skills
- run_skill_hook: 스킬 번들 훅(scripts/hook.py)의 원격 실행

Run (HTTP — Genos 등 외부 에이전트 연동용, 기본):
    python -m server.main                      # 0.0.0.0:$PORT(기본 8000), MCP path=/mcp
Run (stdio — 로컬 클라이언트용):
    MCP_TRANSPORT=stdio python -m server.main
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional, Union

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent

# FastMCP Cloud/CLI는 이 파일을 단독 모듈로 로드하므로(패키지 컨텍스트 없음)
# 상대 임포트 대신 절대 임포트를 쓴다.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.mock_tools import register_mock_tools  # noqa: E402
from server.skill_vdb import SkillVDB  # noqa: E402
VDB_PATH = ROOT / "vdb" / "skills_vdb.json"
SKILLS_DIR = ROOT / "skills"

INSTRUCTIONS = """\
모니모 AI Agent PoC MCP 서버입니다.

사용 순서 (progressive disclosure):
1. 사용자 발화가 들어오면 먼저 `search_skills`로 스킬 VDB를 검색합니다.
   (name+description만 반환 — 트리거 판단용)
2. 적합한 스킬이 있으면 `load_skill`로 body(Instructions/예외 처리/안내 문구)를
   로드해 그대로 따릅니다.
3. `run_skill_hook(skill, stage="before_tool", ...)`로 파라미터 검증·실행형 가드를
   거친 뒤, body가 지시하는 required_tools(이 서버의 목업 도메인 툴)를 호출합니다.
   호출 후 stage="after_tool"로 오류/재시도 판단, 응답 전 stage="finalize"로
   유저향 문구 템플릿을 받습니다.

도메인 툴은 전부 목업이며 고정 픽스처(기준일 2026-07-08)를 반환합니다.
실행형 툴(즉시결제/출금/교환 등)은 before_tool 훅이 context.confirmed=true 를
요구합니다 — 반드시 사용자 확인 후 호출하세요.
"""

mcp = FastMCP("monimo-poc-mcp", instructions=INSTRUCTIONS)
register_mock_tools(mcp)

_vdb: SkillVDB | None = None
_hook_cache: dict[str, Any] = {}


def _get_vdb() -> SkillVDB:
    global _vdb
    if _vdb is None:
        if not VDB_PATH.exists():
            raise RuntimeError("vdb/skills_vdb.json not found — run `python scripts/build_vdb.py` first")
        _vdb = SkillVDB.load(VDB_PATH)
    return _vdb


def _coerce_list(value) -> Optional[list[str]]:
    """LLM 클라이언트가 리스트 대신 'a, b' 같은 문자열을 보내는 경우 보정."""
    if value is None or isinstance(value, list):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("["):
            try:
                return [str(x) for x in json.loads(s)]
            except json.JSONDecodeError:
                pass
        return [t for t in re.split(r"[,\s]+", s) if t]
    return [str(value)]


def _coerce_dict(value) -> Optional[dict]:
    """LLM 클라이언트가 dict 대신 JSON 문자열을 보내는 경우 보정."""
    if value is None or isinstance(value, dict):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        parsed = json.loads(s)  # 실패 시 그대로 에러 — 지어내지 않는다
        if not isinstance(parsed, dict):
            raise ValueError(f"expected JSON object, got {type(parsed).__name__}")
        return parsed
    raise ValueError(f"expected dict, got {type(value).__name__}")


def _get_hook_module(skill_name: str):
    if skill_name in _hook_cache:
        return _hook_cache[skill_name]
    path = SKILLS_DIR / skill_name / "scripts" / "hook.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"skill_hook_{skill_name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _hook_cache[skill_name] = module
    return module


@mcp.tool
def search_skills(query: str, top_k: int = 5, domain: Optional[str] = None,
                  sector: Optional[str] = None, case_type: Optional[str] = None,
                  required_tool: Optional[str] = None) -> dict:
    """사용자 발화로 스킬 VDB를 시맨틱 검색합니다 (1단계 — name/description/score만 반환).
    filters: domain(search|event|product_info|financial_info|monimo|samsung_financial|
    life|fire|card|securities|casual|unsupported), sector(finance|non_finance),
    case_type(normal|error|multiturn|fallback), required_tool(툴명)."""
    results = _get_vdb().search(query, top_k=top_k, domain=domain, sector=sector,
                                case_type=case_type, required_tool=required_tool)
    return {"query": query, "count": len(results), "results": results}


@mcp.tool
def load_skill(name: str) -> dict:
    """스킬 이름으로 SKILL.md body(payload)를 로드합니다 (2단계 — 트리거 확정 후 호출).
    반환된 instructions(body)를 실행 매뉴얼로 그대로 따르고, hooks가 있으면
    run_skill_hook으로 before_tool/after_tool/finalize 단계를 실행하세요."""
    entry = _get_vdb().get(name)
    if not entry:
        return {"error": f"skill not found: {name}"}
    body = entry.pop("payload")
    return {**entry, "instructions": body,
            "hook_stages": ["on_skill_load", "before_tool", "after_tool", "finalize"] if entry.get("hooks") else []}


@mcp.tool
def list_skills(domain: Optional[str] = None, sector: Optional[str] = None) -> dict:
    """등록된 스킬 목록(name/description/domain)을 조회합니다. 디버깅/탐색용."""
    entries = _get_vdb().entries
    out = [
        {"name": e["name"], "description": e["description"], "domain": e["domain"],
         "sector": e["sector"], "case_type": e["case_type"]}
        for e in entries
        if (not domain or e["domain"] == domain) and (not sector or e["sector"] == sector)
    ]
    return {"count": len(out), "skills": out}


@mcp.tool
def run_skill_hook(skill: str, stage: str, tool_name: Optional[str] = None,
                   payload: Optional[Union[dict, str]] = None,
                   context: Optional[Union[dict, str]] = None) -> dict:
    """스킬 번들 훅(scripts/hook.py)을 원격 실행합니다.
    stage: on_skill_load | before_tool(tool_name+payload=툴 인자, context.confirmed로 실행형 승인)
           | after_tool(tool_name+payload=툴 응답) | finalize(payload=수집한 결과).
    payload/context 는 dict (JSON 문자열도 허용)."""
    module = _get_hook_module(skill)
    if module is None:
        return {"error": f"hook not found for skill: {skill}"}
    try:
        payload = _coerce_dict(payload)
        context = _coerce_dict(context)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"error": f"payload/context must be a JSON object: {exc}"}
    try:
        if stage == "on_skill_load":
            result = module.on_skill_load(context)
        elif stage == "before_tool":
            if not tool_name:
                return {"error": "before_tool stage requires tool_name"}
            result = module.before_tool(tool_name, payload, context)
        elif stage == "after_tool":
            if not tool_name:
                return {"error": "after_tool stage requires tool_name"}
            result = module.after_tool(tool_name, payload, context)
        elif stage == "finalize":
            result = module.finalize(payload, context)
        else:
            return {"error": f"unknown stage: {stage} (on_skill_load|before_tool|after_tool|finalize)"}
    except Exception as exc:  # 훅 자체 오류는 에이전트가 무시하고 진행할 수 있게 반환
        return {"error": f"hook execution failed: {exc}"}
    return {"skill": skill, "stage": stage, "result": result}


@mcp.tool
def invoke_tool(tool_name: str, arguments: Optional[Union[dict, str]] = None) -> dict:
    """도메인 목업 툴 게이트웨이 — 81개 도메인 툴을 이 하나로 호출합니다.
    tool_name: 스킬의 required_tools에 명시된 툴 이름, arguments: 해당 툴의 인자
    dict (JSON 문자열도 허용). 툴별 파라미터는 describe_tools로 확인."""
    from .mock_tools import MOCK_TOOLS
    fn = MOCK_TOOLS.get((tool_name or "").strip())
    if fn is None:
        return {"code": "T404", "message": f"unknown tool: {tool_name}", "data": None}
    try:
        args = _coerce_dict(arguments)
    except (json.JSONDecodeError, ValueError) as exc:
        return {"code": "T400", "message": f"arguments must be a JSON object: {exc}", "data": None}
    try:
        return fn(**(args or {}))
    except TypeError as exc:  # 잘못된 인자 — 시그니처 안내
        import inspect
        return {"code": "T400", "message": f"invalid arguments: {exc}",
                "data": {"signature": str(inspect.signature(fn))}}


@mcp.tool
def describe_tools(tool_names: Optional[Union[list[str], str]] = None) -> dict:
    """도메인 툴의 설명과 파라미터 명세를 조회합니다 (invoke_tool 사용 전 참조용).
    tool_names: 툴 이름 리스트 (쉼표 구분 문자열도 허용). 생략 시 전체 카탈로그."""
    import inspect
    from .mock_tools import MOCK_TOOLS
    from .tool_catalog import TOOL_CATALOG
    names = _coerce_list(tool_names) or sorted(TOOL_CATALOG)
    out = []
    for n in names:
        if n not in TOOL_CATALOG:
            out.append({"name": n, "error": "unknown tool"})
            continue
        params = []
        for p in inspect.signature(MOCK_TOOLS[n]).parameters.values():
            ann = p.annotation
            params.append({
                "name": p.name,
                "type": ann.__name__ if isinstance(ann, type) else str(ann).replace("typing.", ""),
                "required": p.default is inspect.Parameter.empty,
                "default": None if p.default is inspect.Parameter.empty else p.default,
            })
        out.append({"name": n, "description": TOOL_CATALOG[n], "parameters": params,
                    "response_envelope": '{"code": "0000"=성공, "message", "data"}'})
    return {"count": len(out), "tools": out}


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    vdb = _get_vdb()
    return JSONResponse({"status": "ok", "skills": len(vdb.entries)})


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http")
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
