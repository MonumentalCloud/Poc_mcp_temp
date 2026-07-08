---
name: calc_card_installment
description: '사용자가 카드 할부 시 월 납부액 계산을 원할 때 사용합니다. 무이자 여부 확인 후 월 예상 납부액 제공에 적합합니다. 예: "100만원 12개월 할부면 얼마야?"'
metadata:
  domain: financial_info
  sector: finance
  case_type: normal
  target: 금융계산기
  seq: 068
  dataset_id: F_FIN_068
  required_tools:
  - financial_calculator
  hooks: scripts/hook.py
  version: 1.0.0
---

# 카드 할부 계산

금융계산기로 사용자가 원하는 값을 계산해 안내한다.

## Instructions
1. 사용자 질의에서 계산 유형과 입력값(금액/기간/금리 등)을 파악하고, 필수 입력값이 빠졌으면 확인합니다.
2. `financial_calculator` 툴을 호출해 대출상환/적금/DSR/할부/연금/환율/세금/투자수익/목표저축 계산을 수행합니다.
3. 계산 결과를 전제 조건(금리/기간/방식)과 함께 안내합니다.
4. 단순 예상치이며 실제 값과 다를 수 있음을 밝힙니다.
5. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 사용 툴 명세
호출은 MCP `invoke_tool(tool_name, arguments)` 게이트웨이를 사용한다. 모든 툴의 응답은 `{code, message, data}` envelope이며 `code == "0000"`이 성공이다. `Optional` 파라미터는 생략 가능.
- `financial_calculator(calc_type: str, params: dict)` — 대출상환/적금/DSR/할부/연금/환율/세금/투자수익/목표저축 계산을 수행합니다

## 응답 가이드
- 무이자 여부 확인 필요 안내
- 월 예상 납부액 제공

## 예외 처리
- 필수 입력값이 없는 경우: 임의 값으로 계산하지 않고 필요한 값을 안내하며 되묻습니다.
- 조회 대상을 특정하지 못한 경우: 후보를 제시하거나 사용자에게 직접 확인합니다.
- 조회 결과가 없는 경우: 해당 내역이 없다는 사실을 안내하고 마칩니다.
- 응답에 사용자가 요청한 필드가 없는 경우: 제공 불가 사실을 알리고, 안내 가능한 다른 항목을 제안합니다.
- API 오류 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 조회로 이어질 수 있으므로). 조회 미완료를 알리고 재시도 여부를 묻습니다.

## 유저향 최종 안내 문구
계산 성공: "{조건} 기준으로 {결과}예요. 실제 값은 조건에 따라 달라질 수 있어요."
입력값 부족: "계산하려면 {필요 항목}이 필요해요. 알려주시면 바로 계산해 드릴게요."

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `calc_card_installment` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'calc_card_installment'
CASE_TYPE = 'normal'
FLOW = 'query'
REQUIRED_TOOLS = ['financial_calculator']
ACTION_TOOLS = []    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['계산 성공: "{조건} 기준으로 {결과}예요. 실제 값은 조건에 따라 달라질 수 있어요."', '입력값 부족: "계산하려면 {필요 항목}이 필요해요. 알려주시면 바로 계산해 드릴게요."']

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
