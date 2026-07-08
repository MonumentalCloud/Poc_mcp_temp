# Monimo PoC — FastMCP Mock Server + Skill VDB

모니모 AI Agent 골든데이터셋(`2) DATA` 시트, 189행)을 기반으로 한 PoC.

- **FastMCP 서버**: 도메인 목업 툴 81개 + 스킬 VDB 검색 툴 3개
- **스킬 189개**: 데이터셋 1행 = 스킬 1개, [스킬 표준 가이드] 형식의 SKILL.md
  (frontmatter `name`/`description` + body `Instructions`/`응답 가이드`/`예외 처리`/`유저향 최종 안내 문구`)
- **스킬 VDB**: 표준 런타임의 "name+description preload + 매칭"을 벡터 검색으로 대체
  — description은 임베딩(트리거), body는 payload(적중 시 반환, 임베딩 안 함)

## 구조

```
data/dataset.json          # xlsx '2) DATA' 시트에서 추출한 189행
skills/<name>/SKILL.md     # 생성된 스킬 189개
vdb/skills_vdb.json        # 빌드된 VDB 인덱스 (임베딩 + payload)
server/
  main.py                  # FastMCP 서버 엔트리포인트
  mock_tools.py            # 목업 툴 81개 구현
  mock_data.py             # 목업 픽스처 (기준일 2026-07-08 고정)
  tool_catalog.py          # 툴 이름/설명 단일 소스
  skill_vdb.py             # VDB (파싱/임베딩/검색/저장)
scripts/
  extract_dataset.py       # xlsx -> data/dataset.json
  skill_map.py             # 행별 스킬명/설명/required_tools/템플릿 그룹 매핑
  generate_skills.py       # dataset.json -> skills/*/SKILL.md
  build_vdb.py             # skills/ -> vdb/skills_vdb.json
  eval_vdb.py              # 대표 발화 기준 검색 리콜 측정
```

## 실행

```bash
pip install -r requirements.txt

# (스킬/VDB는 커밋되어 있음 — 재생성 시)
python scripts/generate_skills.py
python scripts/build_vdb.py

# MCP 서버 (stdio)
python -m server.main
```

MCP 클라이언트 등록 예 (Claude Code):

```bash
claude mcp add monimo-poc -- python -m server.main
```

## 에이전트 사용 흐름 (progressive disclosure)

1. `search_skills(query, top_k, domain?, category?, case_type?, required_tool?)`
   — 사용자 발화로 VDB 시맨틱 검색. **name/description/score만** 반환 (1단계)
2. `load_skill(name)` — 적중 스킬의 body(payload)를 로드해 실행 매뉴얼로 사용 (2단계)
3. body의 `required_tools` 순서대로 이 서버의 목업 도메인 툴 호출 (3단계)

```text
search_skills("탭탭o 이용내역 알려줘")
  → card_usage_inquiry (score 0.59)
load_skill("card_usage_inquiry")
  → Instructions: card_list_inquiry → card_usage_inquiry → 최근 2주 내역 안내 ...
card_usage_inquiry(card_name="탭탭오")
  → {"code":"0000", "data": {...최근 2주 이용내역...}}
```

## 스킬 형식

- frontmatter: 표준 필드 `name`/`description` + 커스텀 색인 필드
  `domain`(finance/non_finance), `category`, `target`, `case_type`(normal/error/multiturn/fallback),
  `dataset_id`, `seq`, `required_tools`, `version`
- description에 트리거 정보(무엇+언제+대표 발화 예시)를 모두 담고, body에는 how-to만 둔다
- 실행형 툴(즉시결제/출금/교환 등 `(실행형)` 표기)을 쓰는 스킬은 실행 전 사용자 확인 +
  재시도 금지(중복 실행 위험) 단계가 body에 포함됨
- 미지원 질문 16행은 툴 없는 가드레일 스킬로 생성됨 (`category: unsupported`)

## VDB

기본 임베더는 **문자 2~3-gram TF-IDF** (외부 모델·네트워크 불필요, 한국어에 토크나이저
없이 동작). `server/skill_vdb.py`의 `Embedder` 인터페이스를 구현하면 문장 임베딩
모델(예: multilingual-e5, OpenAI embeddings)로 교체 가능 — 인덱스 포맷은 동일하다.

리콜 (골든 대표 발화 172건, `scripts/eval_vdb.py`):

| top-1 | top-3 | top-5 |
|------:|------:|------:|
| 98.3% | 100%  | 100%  |

## 목업 데이터 주의

모든 도메인 툴은 `server/mock_data.py`의 고정 픽스처를 반환한다 (기준일 **2026-07-08**).
실행형 툴은 상태를 바꾸지 않고 그럴듯한 실행 결과만 돌려준다.

[스킬 표준 가이드]: https://code.claude.com/docs/en/skills
