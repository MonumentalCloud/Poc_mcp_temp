# -*- coding: utf-8 -*-
"""Generate one SKILL.md per golden-dataset row (skills/<name>/SKILL.md).

Format follows the skill standard guide:
  - frontmatter: name/description (표준 인식 필드) + domain/category/required_tools 등
    커스텀 색인 필드 (VDB 필터/라우팅용)
  - body: Instructions(툴 오케스트레이션) / 응답 가이드 / 예외 처리 / 유저향 최종 안내 문구

Usage: python scripts/generate_skills.py
"""
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from skill_map import SKILL_MAP           # noqa: E402
from server.tool_catalog import TOOL_CATALOG  # noqa: E402

CATEGORY_SLUG = {
    "검색": "search", "이벤트": "event", "상품 정보": "product_info",
    "금융 정보": "financial_info", "모니모": "monimo", "삼성금융": "samsung_financial",
    "생명": "life", "화재": "fire", "카드": "card", "증권": "securities",
    "일상": "casual", "미지원 질문": "unsupported",
}
DOMAIN_SLUG = {"금융": "finance", "비금융": "non_finance"}
CASE_TYPE_SLUG = {"정상": "normal", "에러": "error", "멀티턴": "multiturn", "Fallback": "fallback"}

# 실행형 툴 — 호출 전 사용자 확인 단계를 삽입한다
ACTION_TOOLS = {t for t, d in TOOL_CATALOG.items() if "(실행형" in d}

COMMON_EXCEPTIONS = [
    "조회 대상을 특정하지 못한 경우: 후보를 제시하거나 사용자에게 직접 확인합니다.",
    "조회 결과가 없는 경우: 해당 내역이 없다는 사실을 안내하고 마칩니다.",
    "응답에 사용자가 요청한 필드가 없는 경우: 제공 불가 사실을 알리고, 안내 가능한 다른 항목을 제안합니다.",
    "API 오류 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 조회로 이어질 수 있으므로). 조회 미완료를 알리고 재시도 여부를 묻습니다.",
]
ACTION_EXCEPTIONS = [
    "실행 대상·금액·기간이 모호한 경우: 임의로 추정해 실행하지 않고 반드시 사용자에게 확인합니다.",
    "실행 실패 또는 응답 지연: 자동으로 재시도하지 않습니다(중복 실행 위험). 실패 사실과 사유를 안내하고 재시도 여부를 묻습니다.",
    "본인인증·약관 동의가 필요한 경우: 필요한 절차를 안내하고 완료 후 진행합니다.",
]

GENERIC_PHRASES = [
    '조회 성공: "{요청 항목} 결과를 알려드릴게요. {핵심 결과 요약}"',
    '결과 없음: "조회된 내역이 없어 안내드릴 정보가 없습니다."',
    '오류: "조회가 정상적으로 완료되지 않았습니다. 다시 시도하시겠어요?"',
]

# group -> dict(overview, parse, extra_steps, exceptions, phrases, flow)
GROUPS = {
    "menu": dict(
        overview="모니모 앱 내 메뉴 위치와 이동 경로를 찾아 단계별로 안내한다.",
        parse="사용자 질의에서 찾으려는 기능·메뉴 키워드를 파악합니다.",
        extra_steps=[
            "조회된 경로를 단계별로 안내하고, 해당 메뉴에서 가능한 업무를 함께 설명합니다.",
            "응답에 딥링크가 포함된 경우 바로가기 배너/버튼으로 제공합니다.",
        ],
        exceptions=["검색 결과가 여러 메뉴에 걸치는 경우: 후보 메뉴를 제시하고 의도를 확인합니다."],
        phrases=[
            '안내 성공: "{메뉴명}은(는) {경로}에서 확인하실 수 있어요. 아래 바로가기로 이동해 보세요."',
            '결과 없음: "말씀하신 기능을 찾지 못했어요. 어떤 작업을 하려고 하시는지 조금 더 알려주시겠어요?"',
        ],
    ),
    "menu_clarify": dict(
        overview="모호한 검색어의 의도를 먼저 좁힌 뒤 해당 메뉴 경로를 안내한다.",
        parse="사용자 질의가 어떤 항목(예: 갤러/모니머니/카드포인트)을 가리키는지 후보를 정리합니다.",
        pre_steps=["후보 항목 확인 질문을 먼저 수행해 의도를 좁힙니다."],
        extra_steps=[
            "확인된 의도에 맞는 대표 서비스 메뉴와 이동 경로를 안내합니다.",
            "딥링크가 있으면 바로가기 배너로 제공합니다.",
        ],
        phrases=[
            '의도 확인: "어떤 포인트를 말씀하시는 걸까요? (갤러/모니머니/카드포인트)"',
            '안내 성공: "{항목}은(는) {경로}에서 사용하실 수 있어요."',
        ],
    ),
    "faq": dict(
        overview="FAQ·이용 가이드 문서를 검색해 질의에 답한다.",
        parse="사용자 질의에서 검색할 주제·키워드를 파악합니다.",
        extra_steps=["검색된 문서에서 질의에 해당하는 내용을 추출해 요약 안내하고, 관련 화면 이동 배너가 있으면 함께 제공합니다."],
        exceptions=["문서 근거가 없는 내용은 답하지 않습니다(잘못된 안내 방지). 확인 가능한 채널을 대신 안내합니다."],
        phrases=[
            '안내 성공: "{질의 주제}에 대해 안내드릴게요. {요약 내용}"',
            '근거 없음: "정확한 안내를 위해 고객센터 확인이 필요한 내용이에요. 고객센터로 연결해 드릴까요?"',
        ],
    ),
    "glossary": dict(
        overview="금융 용어의 정의와 활용 예시를 쉽게 설명한다.",
        parse="사용자 질의에서 설명할 용어를 파악합니다.",
        extra_steps=["정의 → 왜 중요한지/어디에 쓰이는지 → 생활 예시 순서로 쉽게 풀어 설명합니다. 비교 질문이면 차이점을 표 없이 간결히 대비합니다."],
        exceptions=["용어가 사전에 없는 경우: 일반적인 정의를 제공하되 모니모 서비스 기준 정보가 아님을 밝힙니다."],
        phrases=['설명: "{용어}은(는) {한 줄 정의}예요. 예를 들어 {활용 예시}."'],
    ),
    "product": dict(
        overview="모니모 내 가입 가능한 상품을 탐색하고 핵심 정보를 요약 안내한다.",
        parse="사용자 질의에서 상품 유형(보험/연금/대출/카드)과 회사·키워드 조건을 파악합니다.",
        extra_steps=[
            "조회 결과에서 사용자가 묻는 항목(보장내용/혜택/금리 등)을 추출해 요약합니다.",
            "상세내용 확인 가능한 화면 이동 배너를 함께 제공합니다.",
        ],
        exceptions=[
            "조건에 맞는 상품이 없는 경우: 없는 사실을 안내하고 유사 조건 상품을 제안합니다.",
            "가입 권유·단정적 추천은 하지 않습니다(불완전판매 방지). 정보 제공과 화면 안내까지만 수행합니다.",
        ],
        phrases=[
            '조회 성공: "{상품명}의 주요 내용을 안내드릴게요. {요약}. 자세한 내용은 아래 배너에서 확인하세요."',
            '결과 없음: "조건에 맞는 상품을 찾지 못했어요. {대안 조건}으로 다시 찾아볼까요?"',
        ],
    ),
    "product_recommend": dict(
        overview="추가 질문으로 사용자 조건을 파악한 뒤 맞는 상품 후보를 안내한다.",
        parse="사용자 질의에서 이미 주어진 조건(목적·상황·선호 혜택)을 파악합니다.",
        pre_steps=["조건이 부족하면 목적·선호를 추가 질문합니다(임의 추정으로 상품을 단정하지 않습니다)."],
        extra_steps=[
            "각 후보 상품의 특징을 요약 안내하고, 상세/가입 화면 이동 배너를 제공합니다.",
        ],
        exceptions=[
            "특정 상품을 단정적으로 추천하지 않습니다(불완전판매 방지). 후보와 비교 정보를 제공하고 선택은 사용자에게 맡깁니다.",
        ],
        phrases=[
            '추가 질문: "어떤 용도로 찾고 계세요? {조건 선택지}"',
            '안내: "말씀하신 조건에는 {후보 상품들}이 있어요. 각각 {특징 요약}입니다."',
        ],
    ),
    "product_compare": dict(
        overview="복수 상품의 특징을 비교해 차이를 안내한다.",
        parse="사용자 질의에서 비교할 상품들을 특정합니다.",
        extra_steps=["카드별 특징과 차이를 비교표로 정리해 안내하되, 어느 쪽이 '더 좋다'는 단정은 하지 않고 사용 패턴별 유불리를 설명합니다."],
        exceptions=["비교 대상 중 특정되지 않는 상품이 있는 경우: 후보를 제시해 확인합니다."],
        phrases=['비교 안내: "{상품A}는 {특징A}, {상품B}는 {특징B}에 강점이 있어요. {사용 패턴}이라면 {상품}이 유리해요."'],
    ),
    "premium": dict(
        overview="보험상품의 예상 보험료를 조건 기준으로 안내한다.",
        parse="사용자 질의에서 상품과 연령대·성별 등 산출 조건을 파악합니다(없으면 확인).",
        extra_steps=[
            "예상 보험료를 산출 기준(연령/성별/만기)과 함께 안내합니다. 예: 30대 여성 월 보험료 45,440원(10년 만기 기준).",
            "연령·성별·보장범위에 따라 달라지는 단순 예상치임을 반드시 밝히고, 정확한 보험료는 상품별 조회가 필요함을 안내합니다.",
        ],
        phrases=['안내: "{상품명}의 예상 보험료는 {조건} 기준 월 {금액}원이에요. 실제 보험료는 조건에 따라 달라질 수 있어요."'],
    ),
    "calculator": dict(
        overview="금융계산기로 사용자가 원하는 값을 계산해 안내한다.",
        parse="사용자 질의에서 계산 유형과 입력값(금액/기간/금리 등)을 파악하고, 필수 입력값이 빠졌으면 확인합니다.",
        extra_steps=[
            "계산 결과를 전제 조건(금리/기간/방식)과 함께 안내합니다.",
            "단순 예상치이며 실제 값과 다를 수 있음을 밝힙니다.",
        ],
        exceptions=["필수 입력값이 없는 경우: 임의 값으로 계산하지 않고 필요한 값을 안내하며 되묻습니다."],
        phrases=[
            '계산 성공: "{조건} 기준으로 {결과}예요. 실제 값은 조건에 따라 달라질 수 있어요."',
            '입력값 부족: "계산하려면 {필요 항목}이 필요해요. 알려주시면 바로 계산해 드릴게요."',
        ],
    ),
    "event": dict(
        overview="진행 중인 이벤트를 조건에 맞게 조회해 요약 안내한다.",
        parse="사용자 질의에서 조회 조건(진행회사/키워드)을 파악합니다.",
        extra_steps=["이벤트명·기간·혜택을 요약해 리스트로 안내하고, 이벤트 화면 이동 배너를 제공합니다."],
        exceptions=["조건에 맞는 진행 중 이벤트가 없는 경우: 없음을 안내하고 전체 이벤트 화면을 제안합니다."],
        phrases=[
            '조회 성공: "지금 진행 중인 이벤트는 {n}개예요. 1. {이벤트명} ({기간}) — {혜택 요약} ..."',
            '결과 없음: "현재 조건에 맞는 진행 중인 이벤트가 없어요."',
        ],
    ),
    "event_detail": dict(
        overview="특정 이벤트의 세부 내용을 조회해 안내한다.",
        parse="사용자 질의에서 대상 이벤트(이벤트명/키워드)와 묻는 항목(발표일/혜택 등)을 파악합니다.",
        extra_steps=[
            "요약 정보와 사용자가 묻는 항목(발표일/혜택 조건 등)을 안내합니다.",
            "세부 기준은 이벤트 상세화면에서 확인하도록 배너를 제공합니다.",
        ],
        exceptions=["대상 이벤트를 특정하지 못한 경우: 키워드로 조회된 후보 리스트를 제시하고 확인합니다."],
        phrases=['안내: "{이벤트명}의 {항목}은 {값}이에요. 세부 기준은 상세화면에서 확인해 주세요."'],
    ),
    "event_participation": dict(
        overview="특정 이벤트에 대한 사용자의 참여/응모 여부를 확인해 안내한다.",
        parse="사용자 질의에서 대상 이벤트를 특정합니다.",
        extra_steps=["참여/응모 여부를 안내하고, 세부 기준은 상세화면에서 확인하도록 배너를 제공합니다."],
        phrases=[
            '참여함: "{이벤트명}에 {일자}에 응모하셨어요."',
            '참여 안 함: "{이벤트명} 응모 내역이 없어요. 지금 참여해 보시겠어요?"',
        ],
    ),
    "stock": dict(
        overview="특정 종목의 시세·회사정보를 조회해 안내한다.",
        parse="사용자 질의에서 조회 대상 종목과 묻는 항목(주가/등락/회사정보)을 파악합니다.",
        extra_steps=[
            "현재가·등락률과 함께 회사 개요, 최근 관련 뉴스가 있으면 요약 안내합니다.",
            "상세 정보 확인 페이지 이동 배너를 제공합니다.",
        ],
        exceptions=["시세는 조회 시점 기준임을 밝힙니다. 매수/매도 등 투자 판단 권유는 하지 않습니다."],
        phrases=['조회 성공: "{종목명} 현재가는 {현재가}원이며, 전일 대비 {등락금액}원 ({등락률}%) {상승/하락}했어요."'],
    ),
    "stock_ranking": dict(
        overview="인기·거래량·업종 기준 종목 순위를 조회해 안내한다.",
        parse="사용자 질의에서 순위 기준(인기/거래량/거래대금/업종)을 파악합니다.",
        extra_steps=[
            "기준별 Top 종목 리스트(국내/해외 구분)를 안내합니다.",
            "더 많은 종목을 볼 수 있는 화면 이동 배너를 제공합니다.",
        ],
        exceptions=["순위는 조회 시점 기준임을 밝힙니다. 특정 종목 매수 권유로 해석될 표현은 쓰지 않습니다."],
        phrases=['조회 성공: "{기준} 상위 종목은 1. {종목1} 2. {종목2} ... 이에요. 전체 순위는 아래 화면에서 확인하세요."'],
    ),
    "stock_unlisted": dict(
        overview="비상장 종목 질의에 대해 비상장임을 안내하고 대안을 제시한다.",
        parse="사용자 질의에서 조회 대상 회사를 파악합니다.",
        extra_steps=[
            "조회 결과가 비상장이면 해당 회사가 비상장 주식임을 안내합니다.",
            "상장된 유사/관련 종목 확인을 제안하고, 종목발굴 화면 이동 배너를 제공합니다.",
        ],
        phrases=['비상장 안내: "{회사명}은(는) 아직 상장되지 않아 주가 정보를 제공할 수 없어요. 관련 상장 종목을 찾아드릴까요?"'],
    ),
    "spending": dict(
        overview="마이데이터 소비내역을 기준월/주차·카테고리·카드별로 분석해 안내한다.",
        parse="사용자 질의에서 조회 기준(월/주차/일자)과 분석 축(총액/카테고리/카드/가맹점)을 파악합니다. 기준이 없으면 이번 달로 간주합니다.",
        extra_steps=["조회 결과에서 질의에 해당하는 값(총액/최다 카테고리/카드별 금액 등)을 추출해 안내하고, 비교 정보(전월 대비 등)가 있으면 함께 제공합니다."],
        exceptions=["소비내역이 없는 기간을 조회한 경우: 내역 없음을 안내합니다.", "마이데이터 미연결 사용자인 경우: 연결 필요를 안내하고 연결 화면 배너를 제공합니다."],
        phrases=[
            '조회 성공: "{기준}에 총 {금액}원을 쓰셨어요. {추가 분석 요약}"',
            '내역 없음: "{기준}에는 조회된 소비내역이 없어요."',
        ],
    ),
    "account": dict(
        overview="마이통장(KB파킹통장/삼성증권 CMA 등)의 잔액·거래내역·이자를 조회해 안내한다.",
        parse="사용자 질의에서 조회 항목(잔액/거래내역/예상 이자/이자율)과 기준(일자/금액)을 파악합니다.",
        extra_steps=["조회 결과에서 질의 항목을 추출해 안내합니다. 이자 안내 시 챌린지 달성에 따른 우대 조건이 있으면 함께 설명합니다."],
        exceptions=["보유 마이통장이 없는 경우: 보유 상품이 없음을 안내하고 개설 가능한 상품(KB파킹통장/CMA)을 소개합니다."],
        phrases=[
            '조회 성공: "{통장명} {항목}은 {값}이에요."',
            '미보유: "아직 마이통장이 없으시네요. KB파킹통장이나 삼성증권 CMA를 개설하면 매일 이자를 받을 수 있어요."',
        ],
    ),
    "account_action": dict(
        overview="마이통장 매일 이자받기를 실행한다.",
        parse="사용자의 이자받기 요청 대상을 파악합니다.",
        extra_steps=["실행 결과(받은 이자 금액)를 안내합니다."],
        flow="action",
        exceptions=["오늘 이미 이자받기를 완료한 경우: 완료 사실과 다음 가능 시점을 안내합니다."],
        phrases=[
            '실행 성공: "오늘 이자 {금액}원을 받았어요."',
            '기실행: "오늘은 이미 이자받기를 완료하셨어요. 내일 다시 받을 수 있어요."',
        ],
    ),
    "action_confirm": dict(
        overview="사용자 요청을 확인한 뒤 실행형 작업을 수행한다.",
        parse="사용자 질의에서 실행 대상과 조건(금액/기간/항목)을 파악합니다.",
        flow="action",
        extra_steps=["실행 결과를 안내하고, 관련 화면 이동 배너가 있으면 함께 제공합니다."],
        phrases=[
            '실행 확인: "{대상}을(를) {조건}(으)로 진행할까요?"',
            '실행 성공: "요청하신 {작업}을 완료했어요. {결과 요약}"',
            '실행 실패: "{작업}이 완료되지 않았어요({사유}). 자동으로 다시 시도하지 않았어요. 다시 진행할까요?"',
        ],
    ),
    "kelly": dict(
        overview="켈리 보유·적립·전환·챌린지 현황을 조회해 안내한다.",
        parse="사용자 질의에서 조회 항목(보유 개수/적립내역/전환 비율/챌린지 현황)과 기준(월)을 파악합니다.",
        extra_steps=["조회 결과를 일반켈리/스페셜켈리 구분 등 세부 기준과 함께 안내하고, 켈리 상점·챌린지 화면 이동 배너를 제공합니다."],
        exceptions=["챌린지 신청 가능 기간(매월 16일~말일)이 아닌 경우: 신청 가능 기간을 안내합니다."],
        phrases=[
            '조회 성공: "{mm.dd}일 기준 보유한 켈리는 총 {n}개예요. (일반켈리: {n1}개, 스페셜켈리: {n2}개)"',
            '내역 없음: "{기준}에는 켈리 적립 내역이 없어요."',
        ],
    ),
    "content": dict(
        overview="관심소식·컨텐츠를 조회해 요약 안내하거나 해당 화면으로 연결한다.",
        parse="사용자 질의에서 조회 기준(인기/관심분야/특정 분야/특정 컨텐츠)을 파악합니다.",
        extra_steps=["조회된 컨텐츠의 제목·내용을 요약 안내하고, 해당 컨텐츠/설정 화면 이동 배너를 제공합니다."],
        exceptions=["관심분야 미설정 사용자인 경우: 설정 화면을 안내합니다."],
        phrases=[
            '조회 성공: "오늘의 {기준} 소식이에요. 1. {제목1} — {요약1} ..."',
            '결과 없음: "지금 보여드릴 {기준} 컨텐츠가 없어요."',
        ],
    ),
    "monimoney": dict(
        overview="모니머니 잔액·이용내역·관리정보를 조회해 안내한다.",
        parse="사용자 질의에서 조회 항목(잔액/내역/사유/한도/유효기간)과 기준(월/건)을 파악합니다.",
        extra_steps=["조회 결과에서 질의 항목을 추출해 안내하고, 모니머니 관리/이용내역 화면 이동 배너를 제공합니다."],
        phrases=[
            '조회 성공: "현재 보유하신 모니머니는 {금액}원이에요."',
            '내역 안내: "{기준} 모니머니 {유형} 내역은 총 {금액}원({건수}건)이에요."',
        ],
    ),
    "benefit_game": dict(
        overview="리워드 게임/미션(걷기·빙고·모니스쿨·친구초대·이달의 미션)의 현황을 조회해 안내한다.",
        parse="사용자 질의에서 조회 대상 서비스와 항목(현황/달성 여부/가능 목록/힌트)을 파악합니다.",
        extra_steps=["조회 결과를 달성/미달성 구분 등 세부 기준과 함께 안내하고, 해당 서비스 화면 이동 배너를 제공합니다."],
        exceptions=["서비스 미참여 사용자인 경우: 참여 방법을 안내합니다."],
        phrases=[
            '조회 성공: "{서비스} 현황이에요. {요약}"',
            '미참여: "아직 {서비스}에 참여하지 않으셨어요. 지금 시작해 보시겠어요?"',
        ],
    ),
    "news": dict(
        overview="오늘의 소식(뉴스레터/마감브리핑)을 조회해 요약 안내한다.",
        parse="사용자 질의에서 원하는 소식 유형(주요 뉴스/마감브리핑)을 파악합니다.",
        extra_steps=["첫 문단을 기준으로 핵심 내용을 요약 안내합니다. 마감브리핑은 나스닥/S&P 등 지수별 등락률을 포함합니다. HTML 태그는 제거하고 텍스트만 사용합니다."],
        phrases=['안내: "오늘의 {유형} 요약이에요. {요약 내용}"'],
    ),
    "weather": dict(
        overview="설정 지역 기준의 날씨·산책지수를 조회해 안내한다.",
        parse="사용자가 설정해 둔 지역을 기준으로 조회합니다.",
        extra_steps=["날씨/최고·최저 기온/대기 수준/산책지수를 안내합니다. 예: \"최고 기온은 ~도이며, 최저 기온은 ~도입니다.\""],
        phrases=['안내: "{지역}의 날씨는 {날씨}예요. 최고 기온은 {max}도, 최저 기온은 {min}도입니다. 산책지수는 {지수}예요."'],
    ),
    "weather_multiturn": dict(
        overview="지역 미설정 사용자에게 지역을 확인한 뒤 날씨·산책지수를 안내한다 (멀티턴).",
        parse="사용자의 설정 지역이 있는지 확인합니다.",
        pre_steps=["설정 지역이 없으면 어느 지역 기준으로 안내할지 되묻습니다(기본 제안: 서울특별시 중구)."],
        extra_steps=["확인된 지역의 날씨/기온/대기 수준을 안내하고, 자주 쓰는 지역으로 설정할지 제안합니다."],
        phrases=[
            '지역 확인: "어느 지역의 날씨를 알려드릴까요?"',
            '안내: "{지역}의 날씨는 {날씨}입니다. 최고 기온은 {max}도, 최저 기온은 {min}도입니다."',
        ],
    ),
    "transfer": dict(
        overview="송금 가능 계좌 목록·송금내역을 조회해 안내한다.",
        parse="사용자 질의에서 송금 상대방 또는 조회 기간·방향(보낸/받은)을 파악합니다.",
        extra_steps=["조회 결과(수취인/계좌/일자/금액)를 안내하고, 송금·송금내역 화면 이동 배너를 제공합니다. 실제 송금 실행은 송금 화면에서 진행하도록 안내합니다."],
        exceptions=["동명이인 등 계좌 후보가 여럿인 경우: 후보를 제시하고 확인합니다."],
        phrases=[
            '조회 성공: "{상대방}에게 보낼 수 있는 계좌는 {은행} {계좌번호}예요. 송금 화면으로 이동할까요?"',
            '내역 안내: "{기간} 송금내역은 총 {건수}건, {금액}원이에요."',
        ],
    ),
    "claims": dict(
        overview="보험금 청구내역과 진행현황을 조회해 안내한다.",
        parse="사용자 질의에서 조회 기준(최근/특정 월/기간/상품)을 파악합니다. 기준이 없으면 가장 최근 청구 건으로 간주합니다.",
        extra_steps=[
            "청구 건별 진행현황(접수/심사/지급완료 등)을 안내합니다.",
            "상세 내용 확인 가능한 화면 이동 배너를 제공합니다.",
        ],
        exceptions=["청구내역이 없는 경우: 내역 없음을 안내하고 청구 화면을 제안합니다."],
        phrases=[
            '조회 성공: "{일자}에 청구하신 {상품명} 보험금은 현재 {진행상태} 단계예요."',
            '내역 없음: "{기준}에 청구된 보험금 내역이 없어요."',
        ],
    ),
    "claims_submit": dict(
        overview="보험금 청구 요청을 받아 청구 가능한 관계사 화면으로 연결한다.",
        parse="사용자 질의에서 청구 대상 계약(회사/상품)을 파악합니다.",
        flow="action",
        extra_steps=[
            "모니모에서 직접 청구는 지원되지 않으므로, 청구 가능한 회사(생명/화재) 화면으로 이동 배너를 제공합니다.",
        ],
        phrases=[
            '안내: "보험금 청구는 {회사} 화면에서 진행할 수 있어요. 아래 배너로 이동해 청구를 계속해 주세요."',
            '대상 없음: "청구 가능한 보험 계약을 찾지 못했어요. 어떤 보험의 보험금을 청구하시려는지 알려주시겠어요?"',
        ],
    ),
    "life_loan": dict(
        overview="보험계약대출 등 대출 내역·잔액·금리·이자 상환일을 조회해 안내한다.",
        parse="사용자 질의에서 조회 항목(대출 목록/잔액/금리/이자 상환일)을 파악합니다.",
        extra_steps=[
            "대출 건별 잔액·금리·이자 상환일을 안내합니다.",
            "대출금 상환·이자 납입 진행을 원하는지 확인하고, 원하면 해당 화면으로 이동 배너를 제공합니다.",
        ],
        phrases=[
            '조회 성공: "보유하신 대출은 {건수}건이에요. {상품명}: 잔액 {금액}원, 금리 {금리}%, 이자 상환일 매월 {일}일."',
            '내역 없음: "현재 진행 중인 대출이 없어요."',
        ],
    ),
    "branch": dict(
        overview="사용자 위치 기준으로 지점/플라자 정보를 찾아 안내한다.",
        parse="사용자가 방문하려는 위치(시/도, 시/군)와 처리하려는 업무(예: 보험금 청구)를 확인합니다.",
        extra_steps=["해당 업무 처리가 가능한 지점의 위치·업무시간·전화번호·주차정보를 안내합니다."],
        exceptions=["위치가 없으면 되묻습니다. 해당 지역에 지점이 없는 경우: 가장 가까운 인접 지역 지점을 안내합니다."],
        phrases=['안내: "{지역}에서 {업무} 처리가 가능한 지점은 {지점명}이에요. 업무시간 {시간}, 전화 {번호}, 주차 {가능 여부}."'],
    ),
    "fire": dict(
        overview="삼성화재 계약 관련 정보(가상계좌/특약 가입내역 등)를 조회해 안내한다.",
        parse="사용자 질의에서 조회 대상(가상계좌/특약 계약/가입내역)을 파악합니다.",
        extra_steps=["조회된 정보가 사용자가 찾는 건이 맞는지 확인하며 안내합니다."],
        phrases=[
            '조회 성공: "{항목} 정보를 안내드릴게요. {내용}"',
            '내역 없음: "조회된 {항목} 내역이 없어요."',
        ],
    ),
    "guarded_error": dict(
        overview="지원되지 않는 요청임을 확인하고 불가 사유를 안내한다.",
        parse="사용자 질의에서 요청 대상을 파악하고, 지원 불가 대상(예: 자동차보험 해지영수증)에 해당하는지 확인합니다.",
        extra_steps=["불가 사유를 정중히 안내하고, 처리 가능한 대체 채널(고객센터 등)이 있으면 함께 안내합니다."],
        flow="query",
        phrases=['불가 안내: "{대상}은 모니모에서 발급/처리가 불가능해요. {대체 채널 안내}"'],
    ),
    "card": dict(
        overview="보유 카드의 이용내역·결제예정금액을 조회해 안내한다.",
        parse="사용자 질의에서 대상 카드와 조회 항목(이용내역/결제예정금액)·기간을 파악합니다.",
        extra_steps=[
            "조회 결과(이용내역/결제일/결제예정금액)를 안내합니다.",
            "기본 조회 기간(최근 2주)보다 과거 내역을 원하는지 확인합니다.",
        ],
        exceptions=["대상 카드를 특정하지 못한 경우: 보유 카드 목록을 안내하고 확인합니다."],
        phrases=[
            '조회 성공: "{카드명}의 최근 2주 이용내역은 총 {건수}건, {금액}원이에요."',
            '결제금액: "이번 결제일({일자})에 출금 예정인 금액은 {금액}원이에요."',
        ],
    ),
    "card_payment": dict(
        overview="카드 이용대금 즉시결제를 확인 후 실행한다.",
        parse="사용자 질의에서 결제 방식(금액 기준/건별)과 대상(금액/이용 건)을 파악합니다. 방식이 모호하면 금액결제/건별결제 차이를 설명하고 선택받습니다.",
        flow="action",
        extra_steps=["결제 결과(결제 금액/남은 결제예정금액)를 안내합니다."],
        exceptions=["타사 카드 요청인 경우: 즉시결제는 해당 카드사에서만 가능함을 안내합니다."],
        phrases=[
            '실행 확인: "{금액}원을 지금 바로 결제할까요?"',
            '실행 성공: "{금액}원 즉시결제를 완료했어요. 남은 결제예정금액은 {잔여 금액}원이에요."',
        ],
    ),
    "fallback": dict(
        overview="직접 수행할 수 없는 요청임을 안내하고 가능한 대안을 제공한다.",
        parse="사용자 질의에서 요청 내용과 수행 불가 사유(정책/권한/데이터 범위)를 파악합니다.",
        flow="fallback",
        phrases=[
            '제한 안내: "요청하신 {작업}은 제가 직접 처리할 수 없어요. 대신 {대안}을 도와드릴까요?"',
        ],
    ),
    "index": dict(
        overview="국내/해외 주요지수와 환율의 등락을 조회해 안내한다.",
        parse="사용자 질의에서 조회 범위(국내/해외/전체/환율)를 파악합니다.",
        extra_steps=[
            "지수별 현재가와 등락률, 대표 종목 흐름을 안내합니다. 환율은 최근 일주일 등락 추이를 함께 안내합니다.",
            "세부내용 확인 가능한 화면 이동 배너를 제공합니다.",
        ],
        exceptions=["조회 시점 기준 데이터임을 밝힙니다. 시장 전망·투자 판단은 제시하지 않습니다."],
        phrases=['조회 성공: "{지수명}은 {현재가}로 전일 대비 {등락률}% {상승/하락}했어요."'],
    ),
    "securities_service": dict(
        overview="삼성증권 상담·교육 서비스 대상 여부를 확인하고 신청을 진행한다.",
        parse="사용자 질의에서 요청 서비스(PB상담/가입자교육)를 파악합니다.",
        flow="action",
        extra_steps=["대상 고객이면 진입점/이수기간을 안내하고 신청을 진행합니다."],
        exceptions=["대상 고객이 아닌 경우: 대상 조건을 안내하고 이용 가능한 대체 서비스를 제안합니다."],
        phrases=[
            '대상 확인: "{서비스} 대상 고객이세요. 바로 신청을 진행할까요?"',
            '비대상: "{서비스}는 {조건} 고객만 이용할 수 있어요."',
        ],
    ),
    "fortune": dict(
        overview="사주정보 기반 운세(오늘의 운세/사랑운/띠별/타로/토정비결/재물운/궁합)를 조회해 안내한다.",
        parse="사용자 질의에서 운세 유형과 필요한 정보(생년월일시/띠/상대방 정보)를 파악합니다.",
        pre_steps=["사주정보가 필요한 유형이면 등록된 사주정보를 확인하고, 미입력 시 입력을 요청합니다."],
        extra_steps=["운세 요약 정보를 안내하고, 세부내용 확인 가능한 화면 이동 배너를 제공합니다."],
        exceptions=[
            "사주정보가 비정상(미래 일자 등)인 경우: 정보를 재확인한 뒤 안내합니다.",
            "운세는 재미로 보는 참고 정보임을 밝히고, 금융 의사결정과 연결하지 않습니다.",
        ],
        phrases=[
            '안내: "오늘의 {유형} 알려드릴게요. {운세 요약}"',
            '정보 요청: "운세를 보려면 생년월일(시) 정보가 필요해요. 알려주시겠어요?"',
        ],
    ),
    "unsupported": dict(
        overview="정책상 지원하지 않는 질의에 대해 정중한 제한 안내로 응답한다 (가드레일).",
        flow="guardrail",
        phrases=[
            '제한 안내: "죄송하지만 요청하신 내용은 도와드릴 수 없어요. 모니모 서비스와 금융 관련 질문을 도와드릴게요."',
        ],
    ),
}

GUARDRAIL_STEPS = [
    "사용자 질의가 이 유형에 해당하는지 판단합니다. 확실하지 않으면 정상 의도로 해석할 여지를 먼저 검토합니다(과차단 방지).",
    "해당하는 경우, 요청을 수행하지 않고 정중한 제한 안내 문구로만 응답합니다.",
    "제한 사유를 장황하게 설명하거나 시스템 내부 정보를 노출하지 않습니다.",
    "모니모에서 도와줄 수 있는 대안 주제(금융/모니모 서비스)를 한 문장으로 제안합니다.",
]
FALLBACK_STEPS_TAIL = [
    "요청을 직접 수행할 수 없는 이유를 한 문장으로 정중히 안내합니다.",
    "수행 가능한 대안(관련 조회, 화면 이동, 객관적 정보 제공)을 제시합니다.",
]

UNSUPPORTED_EXCEPTIONS = [
    "정상 질의를 과도하게 차단하지 않습니다: 판단이 애매하면 의도를 되묻습니다.",
    "사용자를 비난하는 표현을 쓰지 않고 중립적으로 안내합니다.",
]

HOOK_TEMPLATE = '''# -*- coding: utf-8 -*-
"""Hook script for skill `{name}` (자동 생성).

스킬 번들 리소스(scripts/) — 에이전트 런타임 또는 MCP 서버의 `run_skill_hook`
툴이 단계별로 호출한다. 표준 stdlib만 사용하는 self-contained 스크립트.

Stages:
  on_skill_load()                — 스킬 로드 직후 지켜야 할 지시사항 반환
  before_tool(tool_name, args)   — 툴 호출 전 파라미터 검증/정규화, 실행형 가드
  after_tool(tool_name, result)  — 툴 응답 envelope 검증, 재시도 금지 판단
  finalize(results)              — 유저향 최종 안내 문구 템플릿 선택
"""

SKILL_NAME = {name!r}
CASE_TYPE = {case_type!r}
FLOW = {flow!r}
REQUIRED_TOOLS = {required_tools!r}
ACTION_TOOLS = {action_tools!r}    # 사용자 확인(confirmed=True) 없이는 호출 금지
PHRASES = {phrases!r}

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
    return {{"skill": SKILL_NAME, "case_type": CASE_TYPE, "directives": directives}}


def before_tool(tool_name, args=None, context=None):
    args = dict(args or {{}})
    context = context or {{}}
    warnings = []

    if FLOW == "guardrail":
        return {{"allowed": False, "reason": "가드레일 스킬은 툴을 호출하지 않습니다.", "args": args}}
    if tool_name not in REQUIRED_TOOLS:
        warnings.append(f"'{{tool_name}}'은(는) 이 스킬의 required_tools에 없는 툴입니다.")
    if tool_name in ACTION_TOOLS and not context.get("confirmed"):
        return {{"allowed": False,
                 "reason": "실행형 툴입니다. 사용자에게 실행 내용을 확인받은 뒤 context.confirmed=true로 다시 호출하세요.",
                 "args": args}}
    for key in _MONTH_PARAMS:
        if key in args:
            args[key] = _norm_month(args[key])
    return {{"allowed": True, "args": args, "warnings": warnings}}


def after_tool(tool_name, result=None, context=None):
    result = result or {{}}
    code = result.get("code")
    ok = code == "0000"
    out = {{"ok": ok, "code": code, "retry": False}}
    if not ok:
        out["directive"] = ("자동으로 재시도하지 마세요"
                            + ("(중복 실행 위험). " if tool_name in ACTION_TOOLS else "(중복 조회 방지). ")
                            + "실패 사실과 사유를 안내하고 재시도 여부를 사용자에게 물어보세요.")
        out["error_message"] = result.get("message")
    elif result.get("message") not in (None, "success"):
        out["note"] = result.get("message")  # empty / not_found / region_not_set 등 소프트 시그널
    return out


def finalize(results=None, context=None):
    return {{"skill": SKILL_NAME,
             "phrase_templates": PHRASES,
             "directive": "상황에 맞는 템플릿을 골라 {{placeholder}}를 실제 값으로 채워 응답하세요."}}
'''


def build_hook_py(row: dict, entry: dict) -> str:
    cfg = GROUPS[entry["group"]]
    tools = entry["tools"]
    return HOOK_TEMPLATE.format(
        name=entry["name"],
        case_type=CASE_TYPE_SLUG[row["type"]],
        flow=cfg.get("flow", "query"),
        required_tools=tools,
        action_tools=[t for t in tools if t in ACTION_TOOLS],
        phrases=cfg.get("phrases", []) or GENERIC_PHRASES,
    )


def build_steps(row: dict, cfg: dict, tools: list[str]) -> list[str]:
    flow = cfg.get("flow", "query")
    steps: list[str] = []
    if flow == "guardrail":
        return list(GUARDRAIL_STEPS)

    if cfg.get("parse"):
        steps.append(cfg["parse"])
    steps.extend(cfg.get("pre_steps", []))

    for t in tools:
        purpose = TOOL_CATALOG[t].replace(" (실행형)", "")
        if t in ACTION_TOOLS:
            steps.append("실행 내용(대상/금액/기간)을 사용자에게 요약해 보여주고 진행 여부를 확인받습니다. 확인 없이 실행하지 않습니다.")
            steps.append(f"사용자가 동의하면 `{t}` 툴을 호출해 {purpose}.")
        else:
            steps.append(f"`{t}` 툴을 호출해 {purpose}.")

    steps.extend(cfg.get("extra_steps", []))
    if flow == "fallback":
        steps.extend(FALLBACK_STEPS_TAIL)
    steps.append("아래 '응답 가이드'와 '유저향 최종 안내 문구'에 맞춰 결과를 안내합니다.")
    return steps


def clean_guide(guide: str | None) -> list[str]:
    """답변 가이드 셀에서 안내 지침 bullet만 추출 (API 경로 라인은 제외)."""
    if not guide:
        return []
    lines = []
    for raw in guide.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("/") or ":/svc" in line or line.startswith(":/"):
            continue  # 원문 명세의 API 경로 표기 — 툴 매핑(required_tools)으로 대체됨
        lines.append(line.lstrip("- ").strip())
    return lines


def build_exceptions(row: dict, cfg: dict, tools: list[str]) -> list[str]:
    flow = cfg.get("flow", "query")
    out = list(cfg.get("exceptions", []))
    if flow == "guardrail":
        out.extend(UNSUPPORTED_EXCEPTIONS)
    elif flow in ("action",) or any(t in ACTION_TOOLS for t in tools):
        out.extend(ACTION_EXCEPTIONS)
    elif flow == "fallback":
        out.append("사용자가 대안을 원하지 않는 경우: 정중히 마무리합니다.")
        out.extend(COMMON_EXCEPTIONS[-1:])
    else:
        out.extend(COMMON_EXCEPTIONS)
    return out


def build_description(row: dict, cfg_desc: str) -> str:
    desc = cfg_desc.strip()
    utt = (row.get("utterance") or "").strip()
    if utt:
        desc += f' 예: "{utt}"'
    return desc


def build_skill_md(row: dict, entry: dict) -> str:
    cfg = GROUPS[entry["group"]]
    tools = entry["tools"]
    title = (row["intent"] or entry["name"]).strip()

    fm = {
        "name": entry["name"],
        "description": build_description(row, entry["desc"]),
        "domain": DOMAIN_SLUG[row["domain"]],
        "category": CATEGORY_SLUG[row["category"]],
        "target": (row.get("target") or "").strip() or None,
        "case_type": CASE_TYPE_SLUG[row["type"]],
        "dataset_id": row.get("datasetID") or None,
        "seq": row["seq"],
        "required_tools": tools,
        "hooks": "scripts/hook.py",
        "version": "1.0.0",
    }
    fm = {k: v for k, v in fm.items() if v is not None}
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, width=100).strip()

    steps = build_steps(row, cfg, tools)
    guide_bullets = clean_guide(row.get("guide"))
    exceptions = build_exceptions(row, cfg, tools)
    phrases = cfg.get("phrases", []) or GENERIC_PHRASES

    parts = [f"---\n{fm_yaml}\n---", f"\n# {title}\n", cfg["overview"] + "\n"]
    parts.append("## Instructions")
    parts.extend(f"{i}. {s}" for i, s in enumerate(steps, 1))
    parts.append("")
    parts.append("> 훅: 이 스킬은 `scripts/hook.py`를 제공합니다. 툴 호출 전 `before_tool`(파라미터 검증·실행형 가드), "
                 "호출 후 `after_tool`(오류·재시도 판단), 응답 전 `finalize`(문구 템플릿)를 실행하세요. "
                 "MCP 서버의 `run_skill_hook` 툴로 원격 실행할 수 있습니다.")
    parts.append("")

    if guide_bullets:
        parts.append("## 응답 가이드")
        parts.extend(f"- {b}" for b in guide_bullets)
        parts.append("")

    parts.append("## 예외 처리")
    parts.extend(f"- {e}" for e in exceptions)
    parts.append("")

    parts.append("## 유저향 최종 안내 문구")
    parts.extend(phrases)
    parts.append("")
    return "\n".join(parts)


def main() -> None:
    data = json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8"))
    skills_dir = ROOT / "skills"
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
    skills_dir.mkdir(parents=True)

    for row in data:
        entry = SKILL_MAP[row["seq"]]
        unknown = [t for t in entry["tools"] if t not in TOOL_CATALOG]
        if unknown:
            raise SystemExit(f"seq {row['seq']}: unknown tools {unknown}")
        out = skills_dir / entry["name"] / "SKILL.md"
        out.parent.mkdir(parents=True)
        out.write_text(build_skill_md(row, entry), encoding="utf-8")
        hook = skills_dir / entry["name"] / "scripts" / "hook.py"
        hook.parent.mkdir(parents=True)
        hook.write_text(build_hook_py(row, entry), encoding="utf-8")

    print(f"generated {len(data)} skills (+hook.py each) -> {skills_dir}")


if __name__ == "__main__":
    main()
