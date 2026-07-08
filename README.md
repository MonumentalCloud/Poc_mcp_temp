# Monimo PoC — FastMCP Mock Server + Skill VDB

모니모 AI Agent 골든데이터셋(`2) DATA` 시트, 189행)을 기반으로 한 PoC.
에이전트(planner)는 외부(Genos)에 있고, 이 저장소는 **HTTP MCP 서버**만 제공한다.

- **FastMCP 서버 (HTTP)**: 도메인 목업 툴 81개 + 스킬 VDB 툴 4개
  (`search_skills` / `load_skill` / `list_skills` / `run_skill_hook` — 스킬 검색 자체가 MCP 툴)
- **스킬 189개**: 데이터셋 1행 = 스킬 1개, [스킬 표준 가이드] 형식의 SKILL.md
  (frontmatter `name`/`description` + body `Instructions`/`응답 가이드`/`예외 처리`/`유저향 최종 안내 문구`)
  + 스킬별 번들 훅 스크립트 `scripts/hook.py`
- **스킬 VDB**: 표준 런타임의 "name+description preload + 매칭"을 벡터 검색으로 대체
  — description은 임베딩(트리거), body는 payload(적중 시 반환, 임베딩 안 함)

## 구조

```
data/dataset.json          # xlsx '2) DATA' 시트에서 추출한 189행
skills/<name>/
  SKILL.md                 # 생성된 스킬 189개
  scripts/hook.py          # 스킬별 훅 (before_tool/after_tool/finalize 등)
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

# HTTP MCP 서버 (기본) — 엔드포인트 http://0.0.0.0:8000/mcp, 헬스체크 /health
python -m server.main

# stdio가 필요하면
MCP_TRANSPORT=stdio python -m server.main
```

## 공개 엔드포인트 호스팅 (Genos 연동)

서버는 streamable HTTP MCP를 노출한다 — 어디에 올리든 `https://<host>/mcp`가
Genos 에이전트가 연결할 엔드포인트다. `PORT` 환경변수를 따르므로 대부분의
PaaS에 그대로 올라간다.

- **FastMCP Cloud (가장 빠름)**: [fastmcp.cloud]에서 이 GitHub 저장소를 연결하고
  entrypoint를 `server/main.py:mcp`로 지정하면 `https://<project>.fastmcp.app/mcp`
  공개 URL이 발급된다.
- **컨테이너 (Cloud Run / Render / Fly 등)**: 포함된 `Dockerfile` 사용.
  ```bash
  docker build -t monimo-poc-mcp . && docker run -p 8000:8000 monimo-poc-mcp
  # 예: Google Cloud Run
  gcloud run deploy monimo-poc-mcp --source . --allow-unauthenticated --port 8000
  ```
- **임시 데모**: 로컬 실행 후 `ngrok http 8000` 등 터널로 노출.

Genos(또는 임의 MCP 클라이언트) 연결 정보:

```json
{ "transport": "streamable-http", "url": "https://<host>/mcp" }
```

> PoC 서버에는 인증이 없다. 외부에 오래 열어둘 경우 FastMCP auth 또는
> 프록시단 토큰을 붙일 것.

## 에이전트 사용 흐름 (progressive disclosure)

스킬 검색은 그 자체가 MCP 툴이다 — Genos 에이전트는 아래 순서로 호출한다.

1. `search_skills(query, top_k, domain?, category?, case_type?, required_tool?)`
   — 사용자 발화로 VDB 시맨틱 검색. **name/description/score만** 반환 (1단계)
2. `load_skill(name)` — 적중 스킬의 body(payload)를 로드해 실행 매뉴얼로 사용 (2단계)
3. `run_skill_hook(skill, stage, ...)` — 훅 실행(아래 참조) 후, body의
   `required_tools` 순서대로 이 서버의 목업 도메인 툴 호출 (3단계)

```text
search_skills("내 켈리 전부 모니머니로 바꿔줘")
  → kelly_exchange_request (score 0.31)
load_skill("kelly_exchange_request")
  → Instructions + hooks: scripts/hook.py
run_skill_hook(skill=..., stage="before_tool", tool_name="kelly_exchange_request", payload={count:14})
  → {allowed: false, reason: "실행형 툴입니다. 사용자 확인 후 context.confirmed=true..."}
(사용자 확인 후 context={"confirmed": true}로 재호출 → allowed)
kelly_exchange_request(count=14)
  → {"code":"0000", "data": {exchanged:14, credited_monimoney:140}}
run_skill_hook(stage="after_tool") → {ok:true, retry:false}
run_skill_hook(stage="finalize")   → 유저향 문구 템플릿
```

## 스킬 훅 (scripts/hook.py)

각 스킬 폴더에 self-contained 훅 스크립트가 번들된다(frontmatter `hooks: scripts/hook.py`).
로컬 런타임은 직접 import해서, 원격 에이전트(Genos)는 `run_skill_hook` 툴로 실행한다.

| stage | 시점 | 역할 |
|---|---|---|
| `on_skill_load` | 스킬 로드 직후 | 가드레일/실행형 주의 등 지시사항 반환 |
| `before_tool` | 툴 호출 전 | required_tools 검증, `year_month` 등 파라미터 정규화, 실행형 툴은 `context.confirmed=true` 없으면 차단 |
| `after_tool` | 툴 응답 후 | envelope(code) 검증, 실패 시 재시도 금지 지시 반환 |
| `finalize` | 응답 직전 | 유저향 최종 안내 문구 템플릿 선택 |

## 스킬 형식

- frontmatter: 표준 필드 `name`/`description` + 커스텀 색인 필드
  `domain`(finance/non_finance), `category`, `target`, `case_type`(normal/error/multiturn/fallback),
  `dataset_id`, `seq`, `required_tools`, `version`
- description에 트리거 정보(무엇+언제+대표 발화 예시)를 모두 담고, body에는 how-to만 둔다
- 실행형 툴(즉시결제/출금/교환 등 `(실행형)` 표기)을 쓰는 스킬은 실행 전 사용자 확인 +
  재시도 금지(중복 실행 위험) 단계가 body에 포함됨
- 미지원 질문 16행은 툴 없는 가드레일 스킬로 생성됨 (`category: unsupported`)

## VDB

두 가지 backend를 환경변수로 선택한다 (검색 API·스킬 툴 인터페이스는 동일):

| | `VDB_BACKEND=local` (기본) | `VDB_BACKEND=weaviate` (운영 구성) |
|---|---|---|
| 저장/검색 | `vdb/skills_vdb.json` + 코사인 | Weaviate nearVector (REST/GraphQL, gRPC 클라이언트 불필요) |
| 임베딩 | 문자 2~3-gram TF-IDF (키·네트워크 불필요) | 원격 Qwen 임베딩 API (`EMBEDDER=qwen_api`) |
| 시맨틱 매칭 | 어휘(문자) 기반 — 동의어에 약함 | Qwen3-Embedding 기반 시맨틱 매칭 |

**Qwen 임베딩 API** (`server/skill_vdb.py: QwenAPIEmbedder`)는 OpenAI-호환
`/v1/embeddings`를 호출한다. 기본값은 SiliconFlow 무료 티어:

```bash
export QWEN_API_KEY=sk-...                                # 필수
export QWEN_API_BASE=https://api.siliconflow.cn/v1        # 기본값
export QWEN_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B     # 기본값
# DashScope를 쓰려면: QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
#                   QWEN_EMBEDDING_MODEL=text-embedding-v4
```

**Weaviate 적재** (한 번 실행 — 컬렉션 `MonimoSkill` 생성·업서트):

```bash
export WEAVIATE_URL=https://xxxx.weaviate.cloud
export WEAVIATE_API_KEY=...                               # self-hosted 무인증이면 생략
python scripts/build_vdb.py --backend weaviate
```

**서버를 Weaviate 모드로 실행** (fly.io면 `fly secrets set`으로 주입):

```bash
VDB_BACKEND=weaviate EMBEDDER=qwen_api \
QWEN_API_KEY=... WEAVIATE_URL=... WEAVIATE_API_KEY=... python -m server.main
```

로컬 backend의 기본 임베더는 **문자 2~3-gram TF-IDF** (한국어에 토크나이저 없이
동작). `Embedder` 인터페이스(`fit/embed/state/from_state`)를 구현하면 다른 임베딩
모델로도 교체 가능 — 인덱스 포맷은 동일하다.

리콜 (골든 대표 발화 172건, `scripts/eval_vdb.py`):

| top-1 | top-3 | top-5 |
|------:|------:|------:|
| 98.3% | 100%  | 100%  |

## 목업 데이터 주의

모든 도메인 툴은 `server/mock_data.py`의 고정 픽스처를 반환한다 (기준일 **2026-07-08**).
실행형 툴은 상태를 바꾸지 않고 그럴듯한 실행 결과만 돌려준다.

[스킬 표준 가이드]: https://code.claude.com/docs/en/skills
[fastmcp.cloud]: https://fastmcp.cloud
