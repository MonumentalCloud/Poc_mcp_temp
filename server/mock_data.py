# -*- coding: utf-8 -*-
"""Mock fixtures for the Monimo PoC MCP server.

정적 목업 데이터 — 모든 툴은 이 픽스처를 필터/가공해 반환한다.
날짜가 필요한 값은 서버 호출 시점 기준으로 mock_tools에서 계산한다.
"""

MENUS = [
    {"menu_id": "M001", "name": "갤러 보관함", "path": "전체메뉴 > 모니모 > 혜택 > 갤러 보관함", "tasks": ["갤러 조회", "갤러 사용"], "deeplink": "monimo://benefit/gallo"},
    {"menu_id": "M002", "name": "자산", "path": "홈 > 자산", "tasks": ["통합자산 조회", "소비 분석", "마이데이터 연결"], "deeplink": "monimo://asset/home"},
    {"menu_id": "M003", "name": "고객센터", "path": "전체보기 > 이용안내 > 고객센터", "tasks": ["FAQ 검색", "채팅상담", "전화상담"], "deeplink": "monimo://cs/home"},
    {"menu_id": "M004", "name": "간편비밀번호 변경", "path": "전체메뉴 > 설정 > 보안 > 간편비밀번호 변경", "tasks": ["간편비밀번호 변경"], "deeplink": "monimo://settings/security/pin", "note": "본인인증이 필요할 수 있음"},
    {"menu_id": "M005", "name": "이벤트", "path": "전체메뉴 > 모니모 > 혜택 > 이벤트", "tasks": ["진행중 이벤트 조회", "응모"], "deeplink": "monimo://benefit/event"},
    {"menu_id": "M006", "name": "오늘뭐먹지", "path": "홈 > 자산 > 소비 > 오늘뭐먹지", "tasks": ["랜덤 메뉴 추천"], "deeplink": "monimo://asset/food-picker"},
    {"menu_id": "M007", "name": "소비내역 설정", "path": "홈 > 자산 > 소비 > 소비금액 클릭 > 내역 포함 설정", "tasks": ["정산/이체내역/포인트머니 포함 토글"], "deeplink": "monimo://asset/spending/settings"},
    {"menu_id": "M008", "name": "카드 신청", "path": "전체메뉴 > 삼성카드 > 카드 신청", "tasks": ["카드 발급 신청", "가족카드 신청"], "deeplink": "monimo://card/apply"},
    {"menu_id": "M009", "name": "보험계약 해지", "path": "전체메뉴 > 삼성생명 > 보험 > 보험계약 관리 > 해지", "tasks": ["보험계약 해지 신청"], "deeplink": "monimo://life/contract/cancel"},
    {"menu_id": "M010", "name": "금리인하요구권 신청", "path": "전체메뉴 > 삼성생명 > 대출 > 금리인하요구권", "tasks": ["금리인하요구권 신청"], "deeplink": "monimo://life/loan/rate-cut"},
    {"menu_id": "M011", "name": "포인트 사용처", "path": "전체메뉴 > 모니모 > 혜택", "tasks": ["갤러 사용", "모니머니 사용", "카드포인트 사용"], "deeplink": "monimo://benefit/points", "note": "갤러/모니머니/카드포인트 중 확인 필요"},
]

FAQS = [
    {"faq_id": "F001", "category": "고객센터", "question": "고객센터 운영시간이 어떻게 되나요?", "answer": "채팅상담은 평일 09:00~18:00, 전화상담(1588-3114)은 평일 09:00~18:00 운영합니다. FAQ는 24시간 이용 가능합니다."},
    {"faq_id": "F002", "category": "고객센터", "question": "온라인상담과 전화상담의 차이는?", "answer": "채팅상담은 대기 없이 순차 연결되며 캡처 첨부가 가능하고, 전화상담은 복잡한 업무를 상담원과 직접 처리할 수 있습니다. 운영시간은 동일합니다."},
    {"faq_id": "F003", "category": "고객센터", "question": "삼성생명 문의는 어디로 하나요?", "answer": "관계사 업무는 각 사 고객센터로 문의하세요. 삼성생명 1588-3114, 삼성화재 1588-5114, 삼성카드 1588-8700, 삼성증권 1588-2323. 모니모 앱 문의는 모니모 고객센터를 이용하세요."},
    {"faq_id": "F004", "category": "보험금청구", "question": "보험금 청구는 어떻게 하나요?", "answer": "마이삼성 > 보험 > 보험금청구에서 관계사(생명/화재) 화면으로 이동해 청구할 수 있습니다. 진단서 등 서류를 사진으로 제출하면 접수됩니다."},
    {"faq_id": "F005", "category": "모니머니", "question": "모니머니는 어떻게 사용하나요?", "answer": "모니머니는 충전/송금/결제, 투자, 보험료 납입에 사용할 수 있는 선불전자지급수단입니다. 혜택 화면에서 적립하고 결제 시 사용할 수 있습니다."},
    {"faq_id": "F006", "category": "모니머니", "question": "모니머니 사용 시 유의사항은?", "answer": "1일 출금한도 200만원, 보유한도 200만원이며 유효기간(최종 적립일로부터 5년)이 지나면 소멸될 수 있습니다. 일부 가맹점은 결제가 제한됩니다."},
    {"faq_id": "F007", "category": "젤리", "question": "젤리 챌린지가 뭐예요?", "answer": "걷기 등 미션을 달성하면 젤리를 받는 리워드 서비스입니다. 매월 16일~말일에 다음 달 챌린지를 신청할 수 있습니다."},
    {"faq_id": "F008", "category": "빙고", "question": "빙고게임은 어떻게 하나요?", "answer": "매월 3x3 빙고판의 미션 9개를 수행해 스티커를 모으고, 한 줄 완성 시마다 젤리를 받습니다. 매월 1일 오픈되며 말일에 종료됩니다."},
    {"faq_id": "F009", "category": "모니스쿨", "question": "모니스쿨은 어떤 서비스인가요?", "answer": "매월 교시별 금융 퀴즈를 풀고 정답 시 젤리를 받는 학습형 이벤트입니다. 1~4교시 문제가 순차 오픈되며 힌트 화면이 제공됩니다."},
    {"faq_id": "F010", "category": "친구초대", "question": "친구초대 혜택이 뭐예요?", "answer": "내 초대코드로 친구가 가입하면 나와 친구 모두 모니머니를 받습니다. 초대 성공 인원에 따라 추가 보상이 지급됩니다."},
    {"faq_id": "F011", "category": "카드발급", "question": "가족카드 발급이 가능한가요?", "answer": "모니모 카드는 본인회원 기준 가족카드 발급이 가능합니다(배우자/부모/자녀). 카드 신청 화면에서 가족카드를 선택해 신청하세요."},
    {"faq_id": "F012", "category": "증권", "question": "타사 연금을 삼성증권으로 가져오려면?", "answer": "연금저축 이전 제도를 통해 타사 연금저축을 삼성증권 계좌로 이전할 수 있습니다. 전체메뉴 > 증권 > 연금 > 연금저축 이전에서 신청하면 기존 금융사 확인 후 이전이 완료됩니다."},
    {"faq_id": "F013", "category": "금리인하요구권", "question": "금리인하요구권은 누가 신청할 수 있나요?", "answer": "취업, 승진, 소득 증가 등 신용상태가 개선된 대출 고객이 신청할 수 있습니다. 보험계약대출은 대상이 아니며, 신용대출/담보대출이 대상입니다."},
]

GLOSSARY = {
    "DSR": {"definition": "총부채원리금상환비율(Debt Service Ratio). 연소득 대비 모든 대출의 연간 원리금 상환액 비율", "example": "대출 심사 시 한도 산정에 활용되며, 규제 기준(예: 40%)을 넘으면 신규 대출이 제한될 수 있어요."},
    "면책기간": {"definition": "보험 가입 후 일정 기간 보험금 지급 사유가 발생해도 보장하지 않는 기간", "example": "역선택(질병을 알고 가입) 방지를 위한 장치로, 암보험은 통상 90일입니다. 상품별로 기간이 다를 수 있어요."},
    "리볼빙": {"definition": "일부결제금액이월약정. 카드 결제금액 중 일부만 결제하고 나머지는 다음 달로 이월하는 서비스", "example": "이월 금액에는 수수료(이자)가 붙으므로 장기 사용 시 부담이 커질 수 있어요."},
    "ETF": {"definition": "상장지수펀드. 거래소에 상장되어 주식처럼 실시간 매매되는 펀드", "example": "일반 펀드는 하루 1회 기준가로 거래되지만 ETF는 장중 실시간 거래되며 통상 수수료가 낮아요."},
    "고정금리": {"definition": "대출 기간 동안 금리가 변하지 않는 방식. 변동금리는 시장금리에 따라 주기적으로 조정", "example": "금리 상승기에는 고정금리가, 하락기에는 변동금리가 유리할 수 있어요."},
    "세액공제": {"definition": "산출된 세금 자체를 깎아주는 것. 소득공제는 세금을 매기는 소득 기준을 줄여주는 것", "example": "소득공제는 과세표준 단계에서, 세액공제는 세금 산출 후 단계에서 차감돼요."},
    "마이데이터": {"definition": "여러 금융회사에 흩어진 내 금융정보를 고객 동의 기반으로 한곳에 모아 조회·활용하는 서비스", "example": "모니모 자산 화면에서 은행/카드/증권/보험 자산을 한 번에 볼 수 있어요."},
    "선불전자지급수단": {"definition": "미리 충전한 금액으로 결제·송금하는 전자적 지급수단", "example": "모니머니가 대표적이에요. 계좌에서 충전해 결제/송금에 사용해요."},
    "기준금리": {"definition": "한국은행이 결정하는 정책금리로, 시중금리의 기준", "example": "기준금리가 오르면 은행 조달비용이 올라 대출금리도 따라 오르는 흐름이 일반적이에요."},
    "APR": {"definition": "Annual Percentage Rate(연이율). 수수료 등을 포함해 연간 기준으로 환산한 총 비용 비율", "example": "카드 리볼빙/현금서비스 비용 비교 시 APR 기준으로 확인하면 정확해요."},
}

PRODUCTS = [
    {"code": "INS001", "type": "보험", "company": "삼성생명", "name": "삼성생명 암보험", "summary": "암 진단·치료·입원 보장", "coverage": ["암 진단금 최대 5,000만원", "항암치료비", "암 입원일당"], "detail_url": "monimo://product/INS001"},
    {"code": "INS002", "type": "보험", "company": "삼성화재", "name": "삼성화재 암보험", "summary": "암 진단·수술·통원 보장", "coverage": ["암 진단금 최대 3,000만원", "암 수술비", "통원치료비"], "detail_url": "monimo://product/INS002"},
    {"code": "INS003", "type": "보험", "company": "삼성생명", "name": "삼성생명 핵심건강보험", "summary": "위·간 등 주요 질병 집중 보장", "coverage": ["주요질병 진단금", "수술비", "입원일당"], "detail_url": "monimo://product/INS003"},
    {"code": "INS004", "type": "보험", "company": "삼성화재", "name": "AI암호보장보험", "summary": "AI 기반 맞춤 암호화 보장 상품", "coverage": ["디지털자산 피해 보장", "개인정보 유출 보장"], "detail_url": "monimo://product/INS004"},
    {"code": "PEN001", "type": "연금", "company": "삼성증권", "name": "삼성증권 IRP", "summary": "세액공제 연 최대 900만원 한도 개인형 퇴직연금", "features": ["세액공제", "ETF/펀드 운용 가능", "수수료 우대"], "detail_url": "monimo://product/PEN001"},
    {"code": "PEN002", "type": "연금", "company": "삼성증권", "name": "삼성증권 연금저축", "summary": "노후 대비 장기 세제혜택 상품", "features": ["세액공제 연 600만원 한도", "자유납입"], "detail_url": "monimo://product/PEN002"},
    {"code": "PEN003", "type": "연금", "company": "삼성생명", "name": "삼성생명 연금보험", "summary": "종신 수령 가능한 연금보험", "features": ["종신형/확정형 선택", "비과세 요건 충족 시 비과세"], "detail_url": "monimo://product/PEN003"},
    {"code": "LOAN001", "type": "대출", "company": "삼성생명", "name": "삼성생명 보험계약대출", "summary": "보험 해약환급금 범위 내 간편 대출", "rate": 4.5, "features": ["중도상환수수료 없음", "심사 없이 즉시 실행"], "detail_url": "monimo://product/LOAN001"},
    {"code": "LOAN002", "type": "대출", "company": "삼성카드", "name": "삼성카드 장기카드대출", "summary": "카드 회원 대상 장기 대출", "rate": 7.9, "features": ["최대 5,000만원", "모바일 신청"], "detail_url": "monimo://product/LOAN002"},
    {"code": "LOAN003", "type": "대출", "company": "삼성증권", "name": "삼성증권 주식담보대출", "summary": "보유 주식 담보 대출", "rate": 5.2, "features": ["담보 범위 내 즉시", "수시 상환"], "detail_url": "monimo://product/LOAN003"},
    {"code": "CARD001", "type": "카드", "company": "삼성카드", "name": "모니모 카드", "summary": "모니모 전용 혜택 카드", "benefits": ["배달앱 10% 할인(월 2회, 건당 2만원 이상 결제 시, 일부 가맹점 제외)", "모니머니 적립 1%", "대중교통 5% 할인"], "detail_url": "monimo://product/CARD001"},
    {"code": "CARD002", "type": "카드", "company": "삼성카드", "name": "탭탭오", "summary": "선택형 할인 카드", "benefits": ["3개 영역 선택 할인 10%", "통신비 할인"], "detail_url": "monimo://product/CARD002"},
    {"code": "CARD003", "type": "카드", "company": "삼성카드", "name": "탭탭아이스", "summary": "온라인 특화 할인 카드", "benefits": ["온라인 쇼핑 10% 할인", "스트리밍 30% 할인"], "detail_url": "monimo://product/CARD003"},
    {"code": "CARD004", "type": "카드", "company": "삼성카드", "name": "iD EV카드", "summary": "전기차 특화 카드", "benefits": ["전기차 충전 50% 할인(월 최대 2만원)", "주차/세차 할인"], "detail_url": "monimo://product/CARD004"},
]

PREMIUM_TABLE = {  # (product_code) -> age_group -> gender -> 월 보험료(원)
    "INS001": {"20대": {"남": 32100, "여": 28900}, "30대": {"남": 48200, "여": 45440}, "40대": {"남": 71300, "여": 66800}, "50대": {"남": 112000, "여": 98700}},
    "INS002": {"20대": {"남": 27400, "여": 24100}, "30대": {"남": 41800, "여": 39200}, "40대": {"남": 63500, "여": 58900}, "50대": {"남": 99800, "여": 87300}},
}

EVENTS = [
    {"event_id": "EV001", "company": "모니모", "name": "에버랜드 이용권 응모 이벤트", "period": "2026-06-15 ~ 2026-07-15", "benefit": "에버랜드 자유이용권 2매 (추첨 100명)", "announce_date": "2026-07-22", "participated": True, "participated_at": "2026-06-20"},
    {"event_id": "EV002", "company": "삼성카드", "name": "여름휴가 결제 캐시백", "period": "2026-07-01 ~ 2026-08-31", "benefit": "해외 결제 5% 캐시백 (최대 3만원)", "announce_date": None, "participated": False},
    {"event_id": "EV003", "company": "삼성카드", "name": "15만원 캐시백 이벤트", "period": "2026-06-01 ~ 2026-07-31", "benefit": "신규 발급+30만원 이용 시 15만원 캐시백", "announce_date": None, "participated": True, "participated_at": "2026-06-05"},
    {"event_id": "EV004", "company": "삼성생명", "name": "연금저축보험 첫가입 축하금", "period": "2026-07-01 ~ 2026-09-30", "benefit": "첫 가입 시 모니머니 3만원 지급", "announce_date": None, "participated": False},
    {"event_id": "EV005", "company": "모니모", "name": "젤리 챌린지 더블 적립", "period": "2026-07-01 ~ 2026-07-31", "benefit": "챌린지 달성 젤리 2배 적립", "announce_date": None, "participated": False},
]

ASSET_SUMMARY = {
    "connected": True,
    "total_asset": 128_450_000,
    "breakdown": {"예금/파킹": 23_400_000, "투자": 61_050_000, "연금": 38_000_000, "포인트/머니": 6_000_000 // 1000},
    "services": ["통합자산 조회", "소비 분석", "예산 관리", "마이통장", "송금"],
    "screen": "monimo://asset/home",
}

SPENDING = {  # year_month -> summary
    "2026-07": {"total": 1_842_300, "prev_month_diff": -215_400,
                "by_category": [{"category": "외식", "amount": 512_300}, {"category": "쇼핑", "amount": 428_000}, {"category": "교통", "amount": 231_000}, {"category": "구독/디지털", "amount": 189_000}, {"category": "기타", "amount": 482_000}],
                "by_card": [{"card": "모니모 카드", "amount": 1_012_300}, {"card": "탭탭오", "amount": 530_000}, {"card": "삼성 iD GLOBAL 카드", "amount": 300_000}],
                "food_detail": [{"category": "커피/디저트", "amount": 182_000}, {"category": "한식", "amount": 156_300}, {"category": "배달", "amount": 174_000}]},
    "2026-06": {"total": 2_057_700, "prev_month_diff": 120_000,
                "by_category": [{"category": "쇼핑", "amount": 640_000}, {"category": "외식", "amount": 498_000}, {"category": "여행", "amount": 420_000}, {"category": "교통", "amount": 210_700}, {"category": "기타", "amount": 289_000}],
                "by_card": [{"card": "모니모 카드", "amount": 1_120_000}, {"card": "탭탭오", "amount": 637_700}, {"card": "삼성 iD GLOBAL 카드", "amount": 300_000}],
                "food_detail": [{"category": "배달", "amount": 214_000}, {"category": "한식", "amount": 165_000}, {"category": "커피/디저트", "amount": 119_000}]},
    "2026-05": {"total": 1_937_700, "prev_month_diff": -80_000,
                "by_category": [{"category": "외식", "amount": 530_000}, {"category": "쇼핑", "amount": 510_000}, {"category": "의료", "amount": 300_000}, {"category": "교통", "amount": 227_700}, {"category": "기타", "amount": 370_000}],
                "by_card": [{"card": "모니모 카드", "amount": 980_000}, {"card": "탭탭오", "amount": 657_700}, {"card": "삼성 iD GLOBAL 카드", "amount": 300_000}],
                "food_detail": [{"category": "한식", "amount": 210_000}, {"category": "배달", "amount": 180_000}, {"category": "커피/디저트", "amount": 140_000}]},
    "2026-03": {"total": 1_720_000, "prev_month_diff": 60_000,
                "by_category": [{"category": "쇼핑", "amount": 520_000}, {"category": "외식", "amount": 460_000}, {"category": "교통", "amount": 240_000}, {"category": "기타", "amount": 500_000}],
                "by_card": [{"card": "삼성 iD GLOBAL 카드", "amount": 812_000}, {"card": "모니모 카드", "amount": 608_000}, {"card": "탭탭오", "amount": 300_000}],
                "food_detail": [{"category": "한식", "amount": 190_000}, {"category": "배달", "amount": 150_000}]},
    "2026-01": {"total": 2_310_000, "prev_month_diff": 410_000,
                "by_category": [{"category": "쇼핑", "amount": 780_000}, {"category": "외식", "amount": 520_000}, {"category": "여행", "amount": 450_000}, {"category": "기타", "amount": 560_000}],
                "by_card": [{"card": "모니모 카드", "amount": 1_300_000}, {"card": "탭탭오", "amount": 710_000}, {"card": "삼성 iD GLOBAL 카드", "amount": 300_000}],
                "food_detail": [{"category": "한식", "amount": 230_000}, {"category": "배달", "amount": 160_000}]},
}

WEEKLY_SPENDING = {
    "total": 412_500,
    "by_category": [{"category": "외식", "amount": 148_000}, {"category": "쇼핑", "amount": 120_500}, {"category": "교통", "amount": 54_000}, {"category": "기타", "amount": 90_000}],
    "by_day": [{"day": "월", "amount": 32_000}, {"day": "화", "amount": 18_500}, {"day": "수", "amount": 96_000}, {"day": "목", "amount": 41_000}, {"day": "금", "amount": 78_000}, {"day": "토", "amount": 112_000}, {"day": "일", "amount": 35_000}],
}

PAYMENT_HISTORY = [
    {"date": "2026-07-07", "merchant": "스타벅스 역삼점", "amount": 6_300, "method": "모니모 카드"},
    {"date": "2026-07-07", "merchant": "GS25 테헤란점", "amount": 4_800, "method": "모니모 카드"},
    {"date": "2026-07-06", "merchant": "쿠팡", "amount": 42_900, "method": "탭탭오"},
    {"date": "2026-07-06", "merchant": "배달의민족", "amount": 23_500, "method": "모니모 카드"},
    {"date": "2026-07-05", "merchant": "이마트 성수점", "amount": 87_200, "method": "탭탭오"},
]

BUDGET = {"monthly_budget": 2_000_000, "spent": 1_842_300, "remaining": 157_700, "over": False}

ACCOUNTS = [
    {"account_id": "AC001", "bank": "KB국민은행", "name": "KB 모니모 파킹통장", "balance": 5_230_000, "base_rate": 2.0, "bonus_rate": 0.5, "bonus_conditions": ["마케팅 동의(+0.2%p) 달성", "카드 자동이체(+0.3%p) 달성"], "daily_interest_available": True},
    {"account_id": "AC002", "bank": "삼성증권", "name": "삼성증권 CMA", "balance": 12_400_000, "base_rate": 3.1, "bonus_rate": 0.0, "bonus_conditions": [], "daily_interest_available": True},
]

ACCOUNT_TRANSACTIONS = [
    {"date": "2026-07-07", "account_id": "AC001", "type": "입금", "description": "급여", "amount": 3_200_000},
    {"date": "2026-07-07", "account_id": "AC001", "type": "출금", "description": "모니머니 충전", "amount": -100_000},
    {"date": "2026-07-06", "account_id": "AC002", "type": "입금", "description": "이자", "amount": 1_054},
    {"date": "2026-07-05", "account_id": "AC001", "type": "출금", "description": "카드대금 자동이체", "amount": -1_012_300},
]

JELLY = {
    "balance": {"normal": 12, "special": 2},
    "level": {"level": 3, "grade": "GOLD", "conversion_rate": "젤리 1개 = 모니머니 10원", "mission_bonus": True, "mydata_bonus": True},
    "history": {
        "2026-07": [{"date": "2026-07-05", "type": "적립", "reason": "걷기 챌린지", "kind": "일반", "count": 3}, {"date": "2026-07-03", "type": "적립", "reason": "빙고 1줄 달성", "kind": "스페셜", "count": 1}, {"date": "2026-07-01", "type": "사용", "reason": "모니머니 전환", "kind": "일반", "count": -5}],
        "2026-06": [{"date": "2026-06-28", "type": "적립", "reason": "걷기 챌린지", "kind": "일반", "count": 8}, {"date": "2026-06-15", "type": "적립", "reason": "이달의 미션", "kind": "일반", "count": 4}, {"date": "2026-06-10", "type": "적립", "reason": "모니스쿨 정답", "kind": "스페셜", "count": 2}],
    },
    "investment": {"active": True, "total_invested": 3_450, "current_value": 3_612, "started_at": "2026-03-02"},
}

CHALLENGES = {
    "participating": [{"name": "걷기 챌린지", "period": "2026-07-01 ~ 2026-07-31", "goal": "일 5,000보 20일 달성", "achieved_days": 14, "reward": "젤리 최대 30개"}],
    "available": [{"name": "8월 걷기 챌린지", "apply_period": "2026-07-16 ~ 2026-07-31", "reward": "젤리 최대 30개"}, {"name": "8월 아침기상 챌린지", "apply_period": "2026-07-16 ~ 2026-07-31", "reward": "젤리 최대 20개"}],
    "apply_window": "매월 16일~말일에 다음 달 챌린지 신청 가능",
}

CONTENTS = [
    {"content_id": "C001", "topic": "여행맛집", "title": "여름휴가 국내 바다 맛집 5곳", "views": 12_400, "body": "속초·강릉·부산 등 여름 휴가지에서 검증된 해산물 맛집 5곳을 소개합니다. 1위는 속초 A횟집으로 오전 대기가 짧습니다."},
    {"content_id": "C002", "topic": "재테크", "title": "고비맥주 ETF, 지금 담아도 될까", "views": 9_800, "body": "고배당·비만치료제·맥주 소비 관련 테마를 묶은 ETF 흐름을 정리했습니다. 최근 3개월 수익률과 편입 종목 구성을 설명합니다."},
    {"content_id": "C003", "topic": "건강", "title": "장마철 실내 운동 루틴", "views": 7_300, "body": "장마철 걷기 미션을 채우기 어려울 때 실내에서 걸음수를 채우는 루틴을 소개합니다."},
    {"content_id": "C004", "topic": "여행맛집", "title": "서울 여름 빙수 맛집 지도", "views": 6_100, "body": "서울 주요 상권별 빙수 맛집을 지도로 정리했습니다."},
]

INTEREST_TOPICS = {"selected": ["여행맛집", "재테크"], "available": ["여행맛집", "재테크", "건강", "라이프", "테크", "문화"]}

DAILY_NEWS = {
    "newsletter": {"date": "2026-07-08", "headline": "미 연준 금리 동결 시사, 국내 증시 강보합", "first_paragraph": "미 연준이 7월 FOMC에서 금리 동결을 시사하면서 위험자산 선호가 이어졌습니다. 코스피는 외국인 순매수에 힘입어 강보합으로 마감했고, 원/달러 환율은 소폭 하락했습니다."},
    "closing_brief": {"date": "2026-07-07", "summary": "나스닥 +0.8%, S&P500 +0.5% 상승 마감. 반도체 업종 강세가 지수를 견인했습니다. 코스피 +0.4%, 코스닥 +0.9%."},
}

WEATHER = {
    "default_region": None,  # 사용자가 지역을 설정하지 않은 상태를 기본 목업으로 둔다
    "regions": {
        "서울특별시 중구": {"weather": "맑음", "temp_max": 31, "temp_min": 24, "air": "보통", "walk_index": "좋음"},
        "부산광역시 해운대구": {"weather": "구름 많음", "temp_max": 29, "temp_min": 25, "air": "좋음", "walk_index": "보통"},
    },
}

MONIMONEY = {
    "balance": 152_300,
    "info": {"withdraw_limit_daily": 2_000_000, "balance_limit": 2_000_000, "expiry": "2031-07-01 (최종 적립일로부터 5년)"},
    "history": {
        "2026-07": [{"date": "2026-07-05", "type": "출금", "amount": -20_000, "reason": "모니모 KB통장 자동충전 약정에 따른 자동출금", "channel": "KB통장"}, {"date": "2026-07-03", "type": "적립", "amount": 3_200, "reason": "카드 결제 적립"}, {"date": "2026-07-01", "type": "적립", "amount": 120, "reason": "젤리 전환"}],
        "2026-04": [{"date": "2026-04-20", "type": "적립", "amount": 5_400, "reason": "이벤트 보상"}, {"date": "2026-04-12", "type": "적립", "amount": 2_100, "reason": "카드 결제 적립"}, {"date": "2026-04-02", "type": "충전", "amount": 50_000, "reason": "계좌 충전"}],
    },
    "restriction": {"restricted": True, "reason": "잔불(진행 중 결제 정산 대기) 금액 30,000원이 있어 해당 금액은 정산 완료 후 출금 가능합니다.", "available_amount": 122_300},
}

WALKING = {"today_steps": 6_842, "today_km": 4.8, "mission_goal": 5_000,
           "monthly": {"2026-07": {"achieved_days": 5, "reward_jelly": 5}, "2026-04": {"achieved_days": 17, "reward_jelly": 17}}}

BINGO = {
    "participating": True,
    "board": {"total_missions": 9, "sticker_owned": 3, "sticker_attached": 4, "missions_remaining": 2, "bonus_sticker": 1,
              "lines_done": 1, "lines_for_bingo": 3},
    "last_month": {"achieved": True, "lines": 3, "reward_jelly": 15},
    "missions": [{"mission": "걷기 5,000보 3회", "how": "걷기 서비스에서 달성"}, {"mission": "소비 리포트 확인", "how": "자산 > 소비 리포트 열람"}, {"mission": "모니스쿨 1회 응시", "how": "모니스쿨 문제 풀기"}],
    "consent_required": "개인(신용)정보 수집·이용 동의 필요",
}

MONISCHOOL = {
    "current_round": "2026년 7월 2회차",
    "status": [{"session": 1, "title": "금융 영역", "participated": True, "correct": True}, {"session": 2, "title": "소비 영역", "participated": True, "correct": False}, {"session": 3, "title": "건강 영역", "participated": False, "correct": None}, {"session": 4, "title": "상식 영역", "participated": False, "correct": None}],
    "quizzes": [{"session": 3, "title": "건강 영역", "question": "스테이크에 곁들이면 소화를 돕는 향신료는?", "hint": "톡 쏘는 검은 알갱이예요.", "hint_url": "monimo://school/hint/3"}, {"session": 4, "title": "상식 영역", "question": "한국은행이 결정하는 정책금리는?", "hint": "'기준'이 되는 금리예요.", "hint_url": "monimo://school/hint/4"}],
    "reward": "정답 시 젤리 2개",
}

REFERRAL = {"code": "MONI-JJ2026", "link": "https://monimo.com/invite/MONI-JJ2026", "invited_success": 4, "reward_per_invite": "모니머니 5,000원", "next_tier": "6명 달성 시 추가 10,000원"}

MONTHLY_MISSIONS = {
    "status": {"achieved": 3, "total": 6},
    "missions": [
        {"name": "오늘의 영어 확인하기", "achieved": False, "reward": "젤리 1개", "landing": "monimo://mission/english"},
        {"name": "출석체크 15일", "achieved": True, "reward": "젤리 3개"},
        {"name": "소비 리포트 확인", "achieved": True, "reward": "젤리 1개"},
        {"name": "친구초대 1회", "achieved": False, "reward": "모니머니 5,000원", "landing": "monimo://mission/referral"},
        {"name": "걷기 10만보", "achieved": True, "reward": "젤리 5개"},
        {"name": "금융상품 둘러보기", "achieved": False, "reward": "젤리 1개", "landing": "monimo://mission/products"},
    ],
}

TRANSFER = {
    "recent_accounts": [
        {"payee": "김민수", "bank": "KB국민은행", "account_no": "123456-01-987654", "last_sent": "2026-07-01", "favorite": True},
        {"payee": "이서연", "bank": "카카오뱅크", "account_no": "3333-01-1234567", "last_sent": "2026-06-24", "favorite": False},
        {"payee": "박지훈", "bank": "신한은행", "account_no": "110-234-567890", "last_sent": "2026-05-30", "favorite": True},
    ],
    "history": [
        {"date": "2026-07-01", "direction": "보냄", "counterparty": "김민수", "amount": 200_000},
        {"date": "2026-06-30", "direction": "받음", "counterparty": "이서연", "amount": 50_000},
        {"date": "2026-06-24", "direction": "보냄", "counterparty": "이서연", "amount": 120_000},
    ],
    "screen": "monimo://transfer/home",
}

CLAIMS = [
    {"claim_id": "CL001", "company": "삼성화재", "product": "삼성화재 실손의료비보험", "claimed_at": "2026-06-28", "amount": 184_000, "status": "심사 중", "detail_url": "monimo://claim/CL001"},
    {"claim_id": "CL002", "company": "삼성생명", "product": "삼성생명 암보험", "claimed_at": "2026-03-14", "amount": 1_200_000, "status": "지급 완료", "paid_at": "2026-03-21", "detail_url": "monimo://claim/CL002"},
    {"claim_id": "CL003", "company": "삼성화재", "product": "삼성화재 실손의료비보험", "claimed_at": "2025-11-02", "amount": 92_000, "status": "지급 완료", "paid_at": "2025-11-09", "detail_url": "monimo://claim/CL003"},
    {"claim_id": "CL004", "company": "삼성생명", "product": "삼성생명 암보험", "claimed_at": "2025-05-18", "amount": 350_000, "status": "지급 완료", "paid_at": "2025-05-26", "detail_url": "monimo://claim/CL004"},
]

CONTRACTS = [
    {"contract_id": "CT001", "company": "삼성생명", "product": "삼성생명 암보험", "signed_at": "2023-04-10", "status": "정상", "monthly_premium": 45_440},
    {"contract_id": "CT002", "company": "삼성생명", "product": "삼성생명 팩보험(미니건강)", "signed_at": "2026-06-30", "status": "정상", "monthly_premium": 9_900, "withdrawal_eligible": True, "withdrawal_deadline": "2026-07-30"},
    {"contract_id": "CT003", "company": "삼성화재", "product": "삼성화재 자동차보험", "signed_at": "2026-01-15", "status": "정상", "monthly_premium": 0, "yearly_premium": 684_000},
    {"contract_id": "CT004", "company": "삼성화재", "product": "삼성화재 여행자보험", "signed_at": "2025-12-01", "status": "해지", "cancelled_at": "2026-02-01", "receipt_available": True},
]

INSURANCE_LOANS = [
    {"loan_id": "LN001", "company": "삼성생명", "product": "보험계약대출", "balance": 5_000_000, "rate": 4.5, "interest_due_day": 15, "monthly_interest": 18_750, "repay_url": "monimo://life/loan/repay"},
]

BRANCHES = [
    {"name": "삼성생명 강남플라자", "region": "서울 강남구", "address": "서울 강남구 테헤란로 123", "hours": "평일 09:00~17:00", "phone": "02-1234-5678", "parking": "가능(2시간 무료)", "services": ["보험금 청구", "계약 변경", "대출"]},
    {"name": "삼성생명 종로플라자", "region": "서울 종로구", "address": "서울 종로구 종로 55", "hours": "평일 09:00~17:00", "phone": "02-2345-6789", "parking": "불가(인근 공영주차장)", "services": ["보험금 청구", "상담"]},
    {"name": "삼성화재 부산센터", "region": "부산 해운대구", "address": "부산 해운대구 센텀로 77", "hours": "평일 09:00~17:00", "phone": "051-345-6789", "parking": "가능", "services": ["보험금 청구", "자동차보험 상담"]},
]

VIRTUAL_ACCOUNT = {"bank": "우리은행", "account_no": "1005-703-123456", "holder": "삼성화재해상보험", "purpose": "보험료 납부 전용", "note": "계약별로 가상계좌가 다를 수 있어 상세화면 확인 권장"}

TEMP_DRIVER = {"history": [{"contract_id": "CT003", "start": "2026-05-01", "end": "2026-05-03", "status": "종료"}], "active": []}

CARDS = [
    {"card_id": "CD001", "name": "모니모 카드", "masked_no": "5570-12**-****-1234", "billing_day": 25},
    {"card_id": "CD002", "name": "탭탭오", "masked_no": "5570-34**-****-5678", "billing_day": 25},
    {"card_id": "CD003", "name": "삼성 iD GLOBAL 카드", "masked_no": "5570-56**-****-9012", "billing_day": 25},
]

CARD_USAGE = {
    "탭탭오": [
        {"date": "2026-07-06", "merchant": "쿠팡", "amount": 42_900, "status": "승인"},
        {"date": "2026-07-05", "merchant": "이마트 성수점", "amount": 87_200, "status": "승인"},
        {"date": "2026-06-28", "merchant": "넷플릭스", "amount": 17_000, "status": "승인"},
    ],
    "모니모 카드": [
        {"date": "2026-07-07", "merchant": "스타벅스 역삼점", "amount": 6_300, "status": "승인"},
        {"date": "2026-07-07", "merchant": "GS25 테헤란점", "amount": 4_800, "status": "승인"},
        {"date": "2026-07-06", "merchant": "배달의민족", "amount": 23_500, "status": "승인"},
    ],
    "삼성 iD GLOBAL 카드": [
        {"date": "2026-07-02", "merchant": "애플(해외)", "amount": 129_000, "status": "승인"},
    ],
}

CARD_BILLING = {"billing_day": 25, "billing_date": "2026-07-25", "expected_amount": 1_542_300, "immediate_payable": True}

OTHER_CARDS = {"현대카드": {"source": "자산 > 소비내역(마이데이터)", "year_month": "2026-07", "amount": 342_000, "tx_count": 12}}

MARKET_INDEX = {
    "domestic": [
        {"name": "코스피", "value": 3_412.55, "change_pct": 0.42, "advancers": 512, "decliners": 331, "leaders": ["삼성전자 +1.2%", "SK하이닉스 +2.1%"]},
        {"name": "코스닥", "value": 912.34, "change_pct": 0.91, "advancers": 780, "decliners": 542, "leaders": ["에코프로 +3.0%"]},
    ],
    "overseas": [
        {"name": "나스닥", "value": 21_540.12, "change_pct": 0.80, "leaders": ["엔비디아 +2.4%", "애플 +0.9%"]},
        {"name": "S&P500", "value": 6_412.30, "change_pct": 0.50, "leaders": ["마이크로소프트 +1.1%"]},
        {"name": "다우존스", "value": 44_120.80, "change_pct": 0.21, "leaders": []},
    ],
    "fx": {"usdkrw": 1_318.50, "change": -4.20, "change_pct": -0.32,
           "week": [{"date": "2026-07-01", "rate": 1_331.0}, {"date": "2026-07-02", "rate": 1_328.5}, {"date": "2026-07-03", "rate": 1_325.0}, {"date": "2026-07-04", "rate": 1_322.8}, {"date": "2026-07-07", "rate": 1_322.7}, {"date": "2026-07-08", "rate": 1_318.5}]},
}

STOCKS = {
    "삼성전자": {"code": "005930", "market": "KOSPI", "price": 112_300, "change": 1_300, "change_pct": 1.17, "company": "국내 최대 반도체·전자 기업", "news": ["2분기 영업이익 컨센서스 상회 전망", "HBM4 양산 일정 공개"], "detail_url": "monimo://stock/005930"},
    "SK하이닉스": {"code": "000660", "market": "KOSPI", "price": 428_500, "change": 8_800, "change_pct": 2.10, "company": "메모리 반도체 전문 기업", "news": ["HBM 수요 지속 전망"], "detail_url": "monimo://stock/000660"},
    "마켓컬리": {"code": None, "market": None, "listed": False, "company": "신선식품 새벽배송 플랫폼(컬리)", "note": "비상장 기업", "discover_url": "monimo://stock/discover"},
}

STOCK_RANKINGS = {
    "popular": {"domestic": ["삼성전자", "SK하이닉스", "에코프로", "카카오", "NAVER"], "overseas": ["엔비디아", "테슬라", "애플", "팔란티어", "마이크로소프트"]},
    "volume": [{"name": "삼성전자", "volume": "2,140만주"}, {"name": "카카오", "volume": "1,320만주"}, {"name": "에코프로", "volume": "890만주"}],
    "amount": [{"name": "SK하이닉스", "amount": "1.2조원"}, {"name": "삼성전자", "amount": "1.1조원"}],
    "sector": {"제약": ["삼성바이오로직스", "셀트리온", "유한양행", "한미약품"]},
    "more_url": "monimo://stock/ranking",
}

PB_LOUNGE = {"eligible": True, "condition": "예탁자산 3억원 이상", "entry": "전체메뉴 > 증권 > S.Lounge", "next_slot": "2026-07-10 14:00"}

PENSION_EDU = {"enrolled_plans": ["IRP"], "education": "퇴직연금 가입자 법정의무교육(연 1회)", "period": "2026-01-01 ~ 2026-12-31", "status": "미이수", "apply_url": "monimo://securities/pension-edu"}

SAJU_PROFILE = {"registered": False, "birth_date": None, "birth_time": None, "calendar_type": None}

FORTUNES = {
    "daily": "재물운이 상승하는 하루예요. 오전에 중요한 결정을 하면 좋은 결과가 따릅니다. 다만 오후에는 충동구매를 조심하세요.",
    "love": "오늘은 솔직한 대화가 관계를 깊게 만들어요. 먼저 연락해 보세요.",
    "zodiac": {"양띠": "귀인이 나타나는 날입니다. 주변의 제안에 귀 기울여 보세요.", "쥐띠": "차분히 계획을 정리하기 좋은 날입니다."},
    "tarot": {"card": "The Sun", "meaning": "성공과 긍정의 카드예요. 미뤄둔 일을 시작하기 좋은 날입니다.", "screen": "monimo://fortune/tarot"},
    "tojeong": "올해는 상반기보다 하반기에 운이 트입니다. 7~9월에 재물운이 강하니 저축 계획을 세워보세요.",
    "wealth": "예상치 못한 부수입이 생길 수 있는 흐름이에요. 다만 큰 투자는 신중히.",
    "compatibility": "서로 부족한 부분을 채워주는 좋은 궁합이에요. 금전 문제는 미리 규칙을 정하면 갈등이 없습니다.",
}

FX_RATE = 1_318.50  # USD/KRW, financial_calculator 환율 계산용
