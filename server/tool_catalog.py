# -*- coding: utf-8 -*-
"""Mock MCP tool catalog for the Monimo PoC server.

Single source of truth for tool names and their one-line Korean purpose.
- generate_skills.py uses `purpose` to render tool-orchestration steps in SKILL.md
- server/mock_tools.py uses `purpose` as the MCP tool description
"""

TOOL_CATALOG: dict[str, str] = {
    # ── 검색/안내 (RAG성) ──────────────────────────────────────────
    "menu_search": "모니모 앱 메뉴를 검색해 위치·이동 경로·딥링크·해당 메뉴에서 가능한 업무를 조회합니다",
    "faq_search": "모니모/관계사 FAQ와 이용 가이드를 검색해 관련 문서를 조회합니다",
    "glossary_search": "금융 용어 사전에서 용어의 정의·활용 예시를 조회합니다",

    # ── 상품 정보 ──────────────────────────────────────────────────
    "product_search": "상품 유형(보험/연금/대출/카드/투자)과 회사·키워드 조건으로 모니모 내 가입 가능한 상품 목록을 조회합니다",
    "product_detail": "상품 코드로 특정 상품의 상세 정보(보장내용/혜택/금리 등)를 조회합니다",
    "product_compare": "복수 상품의 특징을 비교표 형태로 조회합니다",
    "product_recommend": "사용자 조건·선호(혜택, 목적 등)에 맞는 상품 후보를 조회합니다",
    "insurance_premium_estimate": "보험상품의 연령대·성별 기준 예상 보험료를 조회합니다",
    "financial_calculator": "대출상환/적금/DSR/할부/연금/환율/세금/투자수익/목표저축 계산을 수행합니다",

    # ── 이벤트 ─────────────────────────────────────────────────────
    "event_list_inquiry": "진행 중인 이벤트 목록을 회사·키워드 필터로 조회합니다",
    "event_detail_inquiry": "특정 이벤트의 세부 내용(기간/혜택/발표일/응모방법)을 조회합니다",
    "event_participation_inquiry": "특정 이벤트에 대한 사용자의 참여/응모 여부를 조회합니다",

    # ── 자산/소비 (마이데이터) ─────────────────────────────────────
    "asset_summary_inquiry": "마이데이터 기반 통합자산 요약을 조회합니다",
    "spending_summary_inquiry": "기준월/주차의 총 소비금액과 결제수단별·일별 내역, 전월 대비 증감을 조회합니다",
    "spending_by_card_inquiry": "기준월의 카드별 소비금액 합계를 조회합니다",
    "spending_category_inquiry": "기준월/주차의 업종(카테고리)별 소비금액과 순위를 조회합니다",
    "payment_history_inquiry": "특정 일자/기간의 결제이력(명세서 단위)을 조회합니다",
    "budget_inquiry": "사용자가 설정한 한 달 예산과 현재 소비 대비 현황을 조회합니다",
    "budget_update": "사용자의 한 달 예산 금액을 변경합니다 (실행형)",

    # ── 마이통장 ───────────────────────────────────────────────────
    "account_list_inquiry": "사용자가 보유한 마이통장 상품(KB파킹통장/삼성증권 CMA 등) 목록을 조회합니다",
    "account_balance_inquiry": "마이통장 잔액을 조회합니다",
    "account_transaction_inquiry": "특정 일자/기간의 통장 거래내역을 조회합니다",
    "account_interest_inquiry": "현재 잔액 또는 지정 금액 기준 예상 이자와 적용 이자율(챌린지 우대 포함)을 조회합니다",
    "account_interest_receive": "마이통장의 매일 이자받기를 실행합니다 (실행형)",

    # ── 젤리/챌린지 ────────────────────────────────────────────────
    "jelly_balance_inquiry": "현재 보유한 젤리 개수(일반/스페셜)를 조회합니다",
    "jelly_level_inquiry": "젤리 적립 레벨·회원등급과 모니머니 전환 비율을 조회합니다",
    "jelly_exchange_request": "보유 젤리를 모니머니로 교환합니다 (실행형)",
    "jelly_history_inquiry": "기준월의 젤리 적립/사용 내역을 조회합니다",
    "jelly_investment_inquiry": "누계 젤리 투자금액과 투자 현황을 조회합니다",
    "challenge_list_inquiry": "참여 중이거나 신청 가능한 젤리 챌린지 목록과 신청 가능 기간을 조회합니다",
    "challenge_status_inquiry": "참여 중인 특정 챌린지의 달성 현황(달성일수 등)을 조회합니다",

    # ── 관심소식/컨텐츠 ────────────────────────────────────────────
    "content_list_inquiry": "인기소식 또는 관심분야별 컨텐츠 목록을 조회합니다",
    "content_detail_inquiry": "특정 컨텐츠의 본문 내용을 조회합니다",
    "interest_topic_inquiry": "사용자가 설정한 관심분야 목록을 조회합니다",
    "interest_topic_update": "관심분야를 추가/삭제합니다 (실행형)",
    "daily_news_inquiry": "오늘의 소식(뉴스레터/마감브리핑)을 조회합니다",
    "weather_inquiry": "설정 지역 또는 지정 지역의 날씨·기온·대기수준·산책지수를 조회합니다",

    # ── 모니머니 ───────────────────────────────────────────────────
    "monimoney_balance_inquiry": "현재 보유한 모니머니 잔액을 조회합니다",
    "monimoney_history_inquiry": "기준월의 모니머니 입출금/적립/차감 내역과 건별 사유를 조회합니다",
    "monimoney_info_inquiry": "모니머니 출금한도·유효기간 등 관리 정보를 조회합니다",
    "monimoney_withdraw": "모니머니를 지정 계좌로 출금(이체)합니다 (실행형)",
    "monimoney_restriction_inquiry": "모니머니 출금 불가 사유를 조회합니다",

    # ── 리워드 게임/미션 ───────────────────────────────────────────
    "walking_steps_inquiry": "오늘/특정일 걸음수를 조회합니다",
    "walking_mission_inquiry": "기준월의 걷기 미션 달성 횟수와 보상 젤리 내역을 조회합니다",
    "bingo_status_inquiry": "빙고게임 참여 현황(달성/미달성 미션, 스티커, 전월 결과)을 조회합니다",
    "bingo_start": "빙고게임 참여를 시작합니다 (실행형, 동의 필요)",
    "bingo_mission_inquiry": "빙고 미션별 달성 기준·방법을 조회합니다",
    "monischool_status_inquiry": "이번 달 모니스쿨 교시별 참여 이력(참여/정답 여부)을 조회합니다",
    "monischool_quiz_inquiry": "현재 응시 가능한 모니스쿨 문제를 조회합니다",
    "monischool_hint_inquiry": "특정 교시 문제의 힌트를 조회합니다",
    "monischool_answer_submit": "모니스쿨 문제의 답안을 제출합니다 (실행형)",
    "referral_code_inquiry": "사용자의 친구초대 코드·링크를 조회합니다",
    "referral_status_inquiry": "친구초대 성공 인원 등 진행 현황을 조회합니다",
    "monthly_mission_status_inquiry": "이달의 미션 참여 현황(달성 여부/개수)을 조회합니다",
    "monthly_mission_list_inquiry": "참여 가능한 이달의 미션 목록을 조회합니다",
    "monthly_mission_participate": "특정 이달의 미션 수행을 시작합니다 (실행형)",

    # ── 송금 ───────────────────────────────────────────────────────
    "transfer_account_inquiry": "최근 송금 이력·즐겨찾기 기반 송금 가능 계좌 목록을 조회합니다",
    "transfer_history_inquiry": "특정 기간의 송금내역(전체/보낸/받은)을 조회합니다",

    # ── 삼성금융 4사 ───────────────────────────────────────────────
    "insurance_claim_status_inquiry": "보험금 청구내역과 진행현황을 기간·상품 조건으로 조회합니다",
    "insurance_claim_submit": "보험금 청구 프로세스를 시작합니다 (실행형, 관계사 화면 이동)",
    "insurance_contract_inquiry": "사용자가 보유한 보험 계약 목록을 조회합니다",
    "contract_withdrawal_request": "신계약 청약철회를 진행합니다 (실행형)",
    "insurance_loan_inquiry": "보험계약대출 등 대출 내역·잔액·금리·이자 상환일을 조회합니다",
    "branch_search": "지역 기준으로 지점/플라자 위치·업무시간·전화번호·주차정보를 조회합니다",
    "receipt_issue_request": "해지/만기 영수증 발급을 신청합니다 (실행형, 자동차보험 불가)",
    "virtual_account_inquiry": "보험료 납부용 가상계좌번호를 조회합니다",
    "temp_driver_inquiry": "임시운전자 특약 가입 내역을 조회합니다",
    "temp_driver_apply": "임시운전자 특약을 지정 기간으로 가입합니다 (실행형)",

    # ── 카드 ───────────────────────────────────────────────────────
    "card_list_inquiry": "사용자가 보유한 삼성카드 목록을 조회합니다",
    "card_usage_inquiry": "특정 카드의 이용내역(기본 최근 2주)을 조회합니다",
    "card_billing_inquiry": "이번 결제일 기준 결제예정금액을 조회합니다",
    "card_immediate_payment": "카드 이용대금을 금액 기준 또는 건별로 즉시결제합니다 (실행형, 삼성카드만)",
    "other_card_usage_inquiry": "마이데이터 소비내역 기반 타사 카드 이용금액을 조회합니다",

    # ── 증권 ───────────────────────────────────────────────────────
    "market_index_inquiry": "국내/해외 주요지수와 환율의 현재가·등락을 조회합니다",
    "stock_item_inquiry": "특정 종목의 시세·회사정보·관련 뉴스를 조회합니다",
    "stock_ranking_inquiry": "인기/거래량/거래대금/업종별 종목 순위를 조회합니다",
    "pb_consult_request": "S.Lounge 전문PB 상담 대상 여부 확인 및 상담을 신청합니다 (실행형)",
    "pension_education_apply": "퇴직연금(DC/IRP) 가입자교육을 신청합니다 (실행형)",

    # ── 운세/일상 ──────────────────────────────────────────────────
    "saju_profile_inquiry": "사용자가 등록한 사주정보(생년월일시) 존재 여부와 내용을 조회합니다",
    "saju_profile_register": "사주정보(생년월일시)를 등록/수정합니다 (실행형)",
    "fortune_inquiry": "오늘의 운세/사랑운/띠별/타로/토정비결/재물운/궁합을 조회합니다",
}
