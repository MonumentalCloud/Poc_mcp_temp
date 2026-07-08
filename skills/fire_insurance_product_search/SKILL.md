---
name: fire_insurance_product_search
description: '사용자가 삼성화재의 특정 보험상품이나 키워드(예: AI 보험)로 상품을 찾을 때 사용합니다. 예: "삼성화재에 AI 보험이 있다는데 뭐야?"'
metadata:
  domain: product_info
  sector: finance
  case_type: normal
  target: 상품(보험)
  seq: '025'
  dataset_id: F_INFO_025
  required_tools:
  - product_search
  - product_detail
  hooks: scripts/hook.py
  version: 1.0.0
---

# 화재보험상품 탐색

모니모 내 가입 가능한 상품을 탐색하고 핵심 정보를 요약 안내한다.

## Instructions
1. 사용자 질의에서 상품 유형(보험/연금/대출/카드)과 회사·키워드 조건을 파악합니다.
2. `product_search` 툴을 호출해 상품 유형(보험/연금/대출/카드/투자)과 회사·키워드 조건으로 모니모 내 가입 가능한 상품 목록을 조회합니다.
3. `product_detail` 툴을 호출해 상품 코드로 특정 상품의 상세 정보(보장내용/혜택/금리 등)를 조회합니다.
4. 조회 결과에서 사용자가 묻는 항목(보장내용/혜택/금리 등)을 추출해 요약합니다.
5. 상세내용 확인 가능한 화면 이동 배너를 함께 제공합니다.
6. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 사용 툴 명세
호출은 MCP `invoke_tool(tool_name, arguments)` 게이트웨이를 사용한다. 모든 툴의 응답은 `{code, message, data}` envelope이며 `code == "0000"`이 성공이다. `Optional` 파라미터는 생략 가능.
- `product_search(product_type: str, company: Optional[str] = None, keyword: Optional[str] = None)` — 상품 유형(보험/연금/대출/카드/투자)과 회사·키워드 조건으로 모니모 내 가입 가능한 상품 목록을 조회합니다
- `product_detail(product_code: str)` — 상품 코드로 특정 상품의 상세 정보(보장내용/혜택/금리 등)를 조회합니다

## 응답 가이드
- 키워드 기준으로 삼성화재에서 판매하는 보험 요약안내
- 이 경우 [AI암호보장보험] 안내 가능

## 예외 처리
- 조건에 맞는 상품이 없는 경우: 없는 사실을 안내하고 유사 조건 상품을 제안합니다.
- 가입 권유·단정적 추천은 하지 않습니다(불완전판매 방지). 정보 제공과 화면 안내까지만 수행합니다.
- 조회 대상을 특정하지 못한 경우: 후보를 제시하거나 사용자에게 직접 확인합니다.
- 조회 결과가 없는 경우: 해당 내역이 없다는 사실을 안내하고 마칩니다.
- 응답에 사용자가 요청한 필드가 없는 경우: 제공 불가 사실을 알리고, 안내 가능한 다른 항목을 제안합니다.
- API 오류 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 조회로 이어질 수 있으므로). 조회 미완료를 알리고 재시도 여부를 묻습니다.

## 유저향 최종 안내 문구
조회 성공: "{상품명}의 주요 내용을 안내드릴게요. {요약}. 자세한 내용은 아래 배너에서 확인하세요."
결과 없음: "조건에 맞는 상품을 찾지 못했어요. {대안 조건}으로 다시 찾아볼까요?"

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `fire_insurance_product_search` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'fire_insurance_product_search'
CASE_TYPE = 'normal'
FLOW = 'query'
REQUIRED_TOOLS = ['product_search', 'product_detail']
ACTION_TOOLS = []    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['조회 성공: "{상품명}의 주요 내용을 안내드릴게요. {요약}. 자세한 내용은 아래 배너에서 확인하세요."', '결과 없음: "조건에 맞는 상품을 찾지 못했어요. {대안 조건}으로 다시 찾아볼까요?"']

_MONTH_PARAMS = ("year_month",)


def _norm_month(value):
    """'26년 3월'/'2026-03'/'202603' → 'YYYY-MM' 정규화."""
    if not value or not isinstance(value, str):
        return value
    s = "".join(c for c in value if c.isdigit())
    if len(s) == 6:
        return s[:4] + "-" + s[4:]
    if len(s) == 4:
        return "20" + s[:2] + "-" + s[2:]
    if len(s) == 3:
        return "20" + s[:2] + "-0" + s[2]
    return value


def on_skill_load(context=None):
    directives = ["SKILL.md body의 Instructions를 순서대로 따르세요."]
    if FLOW == "guardrail":
        directives = [
            "이 스킬은 가드레일입니다. 어떤 툴도 호출하지 말고 제한 안내 문구로만 응답하세요.",
            "시스템 내부 정보를 노출하지 마세요.",
        ]
    elif FLOW == "fallback":
        directives.append("요청을 직접 수행할 수 없음을 안내하고 대안을 제시하세요.")
    if ACTION_TOOLS:
        directives.append("실행형 툴(" + ", ".join(ACTION_TOOLS) + ")은 사용자 확인 후에만 호출하세요.")
    return {"skill": SKILL_NAME, "case_type": CASE_TYPE, "directives": directives}


def before_tool(tool_name, args=None, context=None):
    args = dict(args or {})
    context = context or {}
    warnings = []

    if FLOW == "guardrail":
        return {"allowed": False, "reason": "가드레일 스킬은 툴을 호출하지 않습니다.", "args": args}
    if tool_name not in REQUIRED_TOOLS:
        warnings.append(f"'{tool_name}'은(는) 이 스킬의 required_tools에 없는 툴입니다.")
    if tool_name in ACTION_TOOLS and not context.get("confirmed"):
        return {"allowed": False,
                 "reason": "실행형 툴입니다. 사용자에게 실행 내용을 확인받은 뒤 context.confirmed=true로 다시 호출하세요.",
                 "args": args}
    for key in _MONTH_PARAMS:
        if key in args:
            args[key] = _norm_month(args[key])
    return {"allowed": True, "args": args, "warnings": warnings}


def after_tool(tool_name, result=None, context=None):
    result = result or {}
    code = result.get("code")
    ok = code == "0000"
    out = {"ok": ok, "code": code, "retry": False}
    if not ok:
        out["directive"] = ("자동으로 재시도하지 마세요"
                            + ("(중복 실행 위험). " if tool_name in ACTION_TOOLS else "(중복 조회 방지). ")
                            + "실패 사실과 사유를 안내하고 재시도 여부를 사용자에게 물어보세요.")
        out["error_message"] = result.get("message")
    elif result.get("message") not in (None, "success"):
        out["note"] = result.get("message")  # empty / not_found / region_not_set 등 소프트 시그널
    return out


def finalize(results=None, context=None):
    return {"skill": SKILL_NAME,
             "phrase_templates": PHRASES,
             "directive": "상황에 맞는 템플릿을 골라 {placeholder}를 실제 값으로 채워 응답하세요."}
```
