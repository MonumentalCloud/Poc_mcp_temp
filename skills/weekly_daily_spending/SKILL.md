---
name: weekly_daily_spending
description: '사용자가 지난주 언제(어느 요일/일자) 돈을 가장 많이 썼는지 물을 때 사용합니다. 예: "내가 지난주 언제 돈을 제일 많이 썼어?"'
metadata:
  domain: monimo
  sector: finance
  case_type: normal
  target: 자산 (소비 only)
  seq: 090
  dataset_id: F_MONIMO_090
  required_tools:
  - spending_summary_inquiry
  hooks: scripts/hook.py
  version: 1.0.0
---

# 주차별 요일 기준 소비

마이데이터 소비내역을 기준월/주차·카테고리·카드별로 분석해 안내한다.

## Instructions
1. 사용자 질의에서 조회 기준(월/주차/일자)과 분석 축(총액/카테고리/카드/가맹점)을 파악합니다. 기준이 없으면 이번 달로 간주합니다.
2. `spending_summary_inquiry` 툴을 호출해 기준월/주차의 총 소비금액과 결제수단별·일별 내역, 전월 대비 증감을 조회합니다.
3. 조회 결과에서 질의에 해당하는 값(총액/최다 카테고리/카드별 금액 등)을 추출해 안내하고, 비교 정보(전월 대비 등)가 있으면 함께 제공합니다.
4. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 응답 가이드
- 지난 주간 일별소비금액이 가장 많은 일자

## 예외 처리
- 소비내역이 없는 기간을 조회한 경우: 내역 없음을 안내합니다.
- 마이데이터 미연결 사용자인 경우: 연결 필요를 안내하고 연결 화면 배너를 제공합니다.
- 조회 대상을 특정하지 못한 경우: 후보를 제시하거나 사용자에게 직접 확인합니다.
- 조회 결과가 없는 경우: 해당 내역이 없다는 사실을 안내하고 마칩니다.
- 응답에 사용자가 요청한 필드가 없는 경우: 제공 불가 사실을 알리고, 안내 가능한 다른 항목을 제안합니다.
- API 오류 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 조회로 이어질 수 있으므로). 조회 미완료를 알리고 재시도 여부를 묻습니다.

## 유저향 최종 안내 문구
조회 성공: "{기준}에 총 {금액}원을 쓰셨어요. {추가 분석 요약}"
내역 없음: "{기준}에는 조회된 소비내역이 없어요."

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `weekly_daily_spending` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'weekly_daily_spending'
CASE_TYPE = 'normal'
FLOW = 'query'
REQUIRED_TOOLS = ['spending_summary_inquiry']
ACTION_TOOLS = []    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['조회 성공: "{기준}에 총 {금액}원을 쓰셨어요. {추가 분석 요약}"', '내역 없음: "{기준}에는 조회된 소비내역이 없어요."']

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
