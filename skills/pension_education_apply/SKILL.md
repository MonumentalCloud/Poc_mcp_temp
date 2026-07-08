---
name: pension_education_apply
description: 'DC/IRP 가입 사용자가 퇴직연금 가입자교육 신청을 원할 때 사용합니다. 법정의무교육과 이수기간 안내에 적합합니다. 예: "퇴직연금 교육 신청할래"'
metadata:
  domain: securities
  sector: finance
  case_type: normal
  target: 이벤트/교육안내
  seq: '223'
  dataset_id: F_STCK_223
  required_tools:
  - pension_education_apply
  hooks: scripts/hook.py
  version: 1.0.0
---

# 퇴직연금가입자교육 신청에 대한 질의

삼성증권 상담·교육 서비스 대상 여부를 확인하고 신청을 진행한다.

## Instructions
1. 사용자 질의에서 요청 서비스(PB상담/가입자교육)를 파악합니다.
2. 실행 내용(대상/금액/기간)을 사용자에게 요약해 보여주고 진행 여부를 확인받습니다. 확인 없이 실행하지 않습니다.
3. 사용자가 동의하면 `pension_education_apply` 툴을 호출해 퇴직연금(DC/IRP) 가입자교육을 신청합니다.
4. 대상 고객이면 진입점/이수기간을 안내하고 신청을 진행합니다.
5. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 응답 가이드
- DC 또는 IRP 가입고객 중 해당 퇴직연금제도에 가입한 경우 해당하는 법정의무교육 안내
- 해당 교육이수기간 안내

## 예외 처리
- 대상 고객이 아닌 경우: 대상 조건을 안내하고 이용 가능한 대체 서비스를 제안합니다.
- 실행 대상·금액·기간이 모호한 경우: 임의로 추정해 실행하지 않고 반드시 사용자에게 확인합니다.
- 실행 실패 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 실행 위험). 실패 사실과 사유를 안내하고 재시도 여부를 묻습니다.
- 본인인증·약관 동의가 필요한 경우: 필요한 절차를 안내하고 완료 후 진행합니다.

## 유저향 최종 안내 문구
대상 확인: "{서비스} 대상 고객이세요. 바로 신청을 진행할까요?"
비대상: "{서비스}는 {조건} 고객만 이용할 수 있어요."

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `pension_education_apply` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'pension_education_apply'
CASE_TYPE = 'normal'
FLOW = 'action'
REQUIRED_TOOLS = ['pension_education_apply']
ACTION_TOOLS = ['pension_education_apply']    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['대상 확인: "{서비스} 대상 고객이세요. 바로 신청을 진행할까요?"', '비대상: "{서비스}는 {조건} 고객만 이용할 수 있어요."']

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
