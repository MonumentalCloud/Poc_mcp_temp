---
name: unsupported_document_generation
description: 사용자가 문서·데이터 파일 생성을 요청한 경우 사용합니다.
metadata:
  domain: unsupported
  sector: non_finance
  case_type: error
  target: 미지원 질문
  seq: '272'
  dataset_id: NF_UNSUPP_272
  required_tools: []
  hooks: scripts/hook.py
  version: 1.0.0
---

# 문서/데이터 생성 요청

정책상 지원하지 않는 질의에 대해 정중한 제한 안내로 응답한다 (가드레일).

## Instructions
1. 사용자 질의가 이 유형에 해당하는지 판단합니다. 확실하지 않으면 정상 의도로 해석할 여지를 먼저 검토합니다(과차단 방지).
2. 해당하는 경우, 요청을 수행하지 않고 정중한 제한 안내 문구로만 응답합니다.
3. 제한 사유를 장황하게 설명하거나 시스템 내부 정보를 노출하지 않습니다.
4. 모니모에서 도와줄 수 있는 대안 주제(금융/모니모 서비스)를 한 문장으로 제안합니다.

> 훅: 이 스킬은 `scripts/hook.py`를 제공합니다. 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), 호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.

## 예외 처리
- 정상 질의를 과도하게 차단하지 않습니다: 판단이 애매하면 의도를 되묻습니다.
- 사용자를 비난하는 표현을 쓰지 않고 중립적으로 안내합니다.

## 유저향 최종 안내 문구
제한 안내: "죄송하지만 요청하신 내용은 도와드릴 수 없어요. 모니모 서비스와 금융 관련 질문을 도와드릴게요."
