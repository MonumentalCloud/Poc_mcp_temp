---
name: account_interest_receive
description: '사용자가 ''오늘 이자받기 해줘''처럼 매일 이자받기 실행을 요청할 때 사용합니다. KB파킹통장/삼성증권 CMA 대상 이자받기 실행에 적합합니다. 예: "오늘
  이자받기 해줘"'
metadata:
  domain: monimo
  sector: finance
  case_type: normal
  target: 마이통장
  seq: 095
  dataset_id: F_MONIMO_095
  required_tools:
  - account_list_inquiry
  - account_interest_receive
  hooks: scripts/hook.py
  version: 1.0.0
---

# 통장 이자받기 요청

마이통장 매일 이자받기를 실행한다.

## Instructions
1. 사용자의 이자받기 요청 대상을 파악합니다.
2. `account_list_inquiry` 툴을 호출해 사용자가 보유한 마이통장 상품(KB파킹통장/삼성증권 CMA 등) 목록을 조회합니다.
3. 실행 내용(대상/금액/기간)을 사용자에게 요약해 보여주고 진행 여부를 확인받습니다. 확인 없이 실행하지 않습니다.
4. 사용자가 동의하면 `account_interest_receive` 툴을 호출해 마이통장의 매일 이자받기를 실행합니다.
5. 실행 결과(받은 이자 금액)를 안내합니다.
6. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 응답 가이드
- 이자 받기가 가능한 상품은 KB국민은행 파킹통장 / 삼성증권 CMA

## 예외 처리
- 오늘 이미 이자받기를 완료한 경우: 완료 사실과 다음 가능 시점을 안내합니다.
- 실행 대상·금액·기간이 모호한 경우: 임의로 추정해 실행하지 않고 반드시 사용자에게 확인합니다.
- 실행 실패 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 실행 위험). 실패 사실과 사유를 안내하고 재시도 여부를 묻습니다.
- 본인인증·약관 동의가 필요한 경우: 필요한 절차를 안내하고 완료 후 진행합니다.

## 유저향 최종 안내 문구
실행 성공: "오늘 이자 {금액}원을 받았어요."
기실행: "오늘은 이미 이자받기를 완료하셨어요. 내일 다시 받을 수 있어요."

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `account_interest_receive` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'account_interest_receive'
CASE_TYPE = 'normal'
FLOW = 'action'
REQUIRED_TOOLS = ['account_list_inquiry', 'account_interest_receive']
ACTION_TOOLS = ['account_interest_receive']    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['실행 성공: "오늘 이자 {금액}원을 받았어요."', '기실행: "오늘은 이미 이자받기를 완료하셨어요. 내일 다시 받을 수 있어요."']

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
