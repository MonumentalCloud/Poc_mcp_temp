---
name: daily_fortune_no_profile
description: '사주정보를 입력하지 않은 사용자가 오늘의 운세를 물을 때 사용합니다. 사주정보 입력 유도 후 운세 안내에 적합합니다. 예: "오늘의 운세 알려줘"'
metadata:
  domain: casual
  sector: non_finance
  case_type: normal
  target: 생활 컨텐츠
  seq: '254'
  dataset_id: NF_CASUAL_254
  required_tools:
  - saju_profile_inquiry
  - saju_profile_register
  - fortune_inquiry
  hooks: scripts/hook.py
  version: 1.0.0
---

# 오늘의 운세 질의

사주정보 기반 운세(오늘의 운세/사랑운/띠별/타로/토정비결/재물운/궁합)를 조회해 안내한다.

## Instructions
1. 사용자 질의에서 운세 유형과 필요한 정보(생년월일시/띠/상대방 정보)를 파악합니다.
2. 사주정보가 필요한 유형이면 등록된 사주정보를 확인하고, 미입력 시 입력을 요청합니다.
3. `saju_profile_inquiry` 툴을 호출해 사용자가 등록한 사주정보(생년월일시) 존재 여부와 내용을 조회합니다.
4. 실행 내용(대상/금액/기간)을 사용자에게 요약해 보여주고 진행 여부를 확인받습니다. 확인 없이 실행하지 않습니다.
5. 사용자가 동의하면 `saju_profile_register` 툴을 호출해 사주정보(생년월일시)를 등록/수정합니다.
6. `fortune_inquiry` 툴을 호출해 오늘의 운세/사랑운/띠별/타로/토정비결/재물운/궁합을 조회합니다.
7. 운세 요약 정보를 안내하고, 세부내용 확인 가능한 화면 이동 배너를 제공합니다.
8. 아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.

> 훅: 이 스킬은 훅 스크립트를 번들합니다(아래 'Hook' 섹션 = `scripts/hook.py` 동일 소스). 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 응답 가이드
- 입력한 사주정보에 맞는 오늘의 운세 요약정보 제공

## 예외 처리
- 사주정보가 비정상(미래 일자 등)인 경우: 정보를 재확인한 뒤 안내합니다.
- 운세는 재미로 보는 참고 정보임을 밝히고, 금융 의사결정과 연결하지 않습니다.
- 실행 대상·금액·기간이 모호한 경우: 임의로 추정해 실행하지 않고 반드시 사용자에게 확인합니다.
- 실행 실패 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 실행 위험). 실패 사실과 사유를 안내하고 재시도 여부를 묻습니다.
- 본인인증·약관 동의가 필요한 경우: 필요한 절차를 안내하고 완료 후 진행합니다.

## 유저향 최종 안내 문구
안내: "오늘의 {유형} 알려드릴게요. {운세 요약}"
정보 요청: "운세를 보려면 생년월일(시) 정보가 필요해요. 알려주시겠어요?"

## Hook (scripts/hook.py)
이 스킬의 훅 스크립트 전문. MCP 서버의 `run_skill_hook(skill, stage, ...)` 툴이 이 코드를 실행한다 — 에이전트는 코드를 직접 실행하지 말고 툴을 호출한다.

```python
# -*- coding: utf-8 -*-
"""Hook script for skill `daily_fortune_no_profile` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = 'daily_fortune_no_profile'
CASE_TYPE = 'normal'
FLOW = 'query'
REQUIRED_TOOLS = ['saju_profile_inquiry', 'saju_profile_register', 'fortune_inquiry']
ACTION_TOOLS = ['saju_profile_register']    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = ['안내: "오늘의 {유형} 알려드릴게요. {운세 요약}"', '정보 요청: "운세를 보려면 생년월일(시) 정보가 필요해요. 알려주시겠어요?"']

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
