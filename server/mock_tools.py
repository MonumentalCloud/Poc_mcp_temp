# -*- coding: utf-8 -*-
"""Mock implementations for every tool in tool_catalog.TOOL_CATALOG.

모든 툴은 {"code": "0000", "message": "success", "data": ...} envelope 로
mock_data 픽스처를 필터/가공해 반환한다. 실행형 툴은 상태를 바꾸는 대신
그럴듯한 실행 결과를 돌려준다 (PoC 목적).
"""
from datetime import date, timedelta
from typing import Optional

from . import mock_data as D
from .tool_catalog import TOOL_CATALOG

TODAY = date(2026, 7, 8)  # 데이터셋 기준일 고정 (골든데이터 26년 기준)
THIS_MONTH = "2026-07"


def ok(data, message: str = "success") -> dict:
    return {"code": "0000", "message": message, "data": data}


def err(code: str, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


def _norm_month(year_month: Optional[str]) -> str:
    """'26년 3월'/'2026-03'/'202603' 스타일 입력을 'YYYY-MM'으로 정규화."""
    if not year_month:
        return THIS_MONTH
    digits = [c for c in year_month if c.isdigit()]
    s = "".join(digits)
    if len(s) == 6:      # 202603
        return f"{s[:4]}-{s[4:]}"
    if len(s) == 4:      # 2603
        return f"20{s[:2]}-{s[2:]}"
    if len(s) == 3:      # 265 (26년 5월)
        return f"20{s[:2]}-0{s[2]}"
    return year_month if "-" in year_month else THIS_MONTH


# ── 검색/안내 ──────────────────────────────────────────────────────
def menu_search(query: str) -> dict:
    q = query.strip()
    hits = [m for m in D.MENUS if any(tok in m["name"] or tok in m["path"] or any(tok in t for t in m["tasks"]) for tok in q.split())]
    return ok({"query": q, "results": hits or D.MENUS[:3], "exact_match": bool(hits)})


def faq_search(query: str, company: Optional[str] = None) -> dict:
    hits = [f for f in D.FAQS if any(tok in f["question"] + f["answer"] + f["category"] for tok in query.split())]
    return ok({"query": query, "company": company, "results": hits or D.FAQS[:3], "recommended_keywords": [f["category"] for f in (hits or D.FAQS[:3])]})


def glossary_search(term: str) -> dict:
    key = term.strip().upper() if term.isascii() else term.strip()
    for k, v in D.GLOSSARY.items():
        if k in key or key in k:
            return ok({"term": k, **v})
    return ok({"term": term, "definition": None, "note": "사전에 등재되지 않은 용어"}, message="not_found")


# ── 상품 정보 ──────────────────────────────────────────────────────
def product_search(product_type: str, company: Optional[str] = None, keyword: Optional[str] = None) -> dict:
    items = [p for p in D.PRODUCTS if product_type in p["type"]]
    if company:
        items = [p for p in items if company in p["company"]]
    if keyword:
        items = [p for p in items if keyword in p["name"] or keyword in p["summary"]] or items
    return ok({"product_type": product_type, "results": items})


def product_detail(product_code: str) -> dict:
    for p in D.PRODUCTS:
        if p["code"] == product_code or product_code in p["name"]:
            return ok(p)
    return err("P404", f"상품을 찾을 수 없습니다: {product_code}")


def product_compare(product_codes: list[str]) -> dict:
    found = [p for p in D.PRODUCTS if p["code"] in product_codes or any(c in p["name"] for c in product_codes)]
    if len(found) < 2:
        return err("P400", "비교할 상품을 2개 이상 특정해 주세요.")
    return ok({"products": found, "compare_note": "혜택 영역과 조건을 비교해 사용 패턴별 유불리를 안내하세요."})


def product_recommend(product_type: str, preference: Optional[str] = None) -> dict:
    items = [p for p in D.PRODUCTS if product_type in p["type"]]
    if preference:
        pref = [p for p in items if any(preference in b for b in p.get("benefits", []) + p.get("features", []) + [p["summary"]])]
        items = pref or items
    return ok({"product_type": product_type, "preference": preference, "candidates": items[:3],
               "note": "단정적 추천 대신 후보별 특징을 안내하세요."})


def insurance_premium_estimate(product_code: str, age_group: str, gender: str) -> dict:
    table = D.PREMIUM_TABLE.get(product_code) or D.PREMIUM_TABLE["INS001"]
    row = table.get(age_group)
    if not row:
        return err("P400", f"지원하지 않는 연령대: {age_group} (20대/30대/40대/50대)")
    g = "여" if "여" in gender else "남"
    return ok({"product_code": product_code, "age_group": age_group, "gender": g,
               "monthly_premium": row[g], "basis": "10년 만기 기준", "disclaimer": "보장범위·특약에 따라 달라지는 예상치입니다."})


def financial_calculator(calc_type: str, params: dict) -> dict:
    """calc_type: loan_repayment | savings | dsr | installment | pension | fx | income_tax | investment_return | target_saving"""
    p = params or {}
    if calc_type == "loan_repayment":
        principal, rate, months = p.get("principal", 100_000_000), p.get("annual_rate", 4.5), p.get("months", 360)
        r = rate / 100 / 12
        pay = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
        return ok({"monthly_payment": round(pay), "method": "원리금균등", "assumption": f"연 {rate}%, {months}개월",
                   "note": "원금균등 방식은 초기 납입액이 더 크고 총이자가 적습니다."})
    if calc_type == "savings":
        monthly, months, rate = p.get("monthly", 500_000), p.get("months", 24), p.get("annual_rate", 3.0)
        interest = sum(monthly * (rate / 100) * (months - i) / 12 for i in range(months))
        return ok({"total_principal": monthly * months, "interest_before_tax": round(interest),
                   "maturity_amount": round(monthly * months + interest * 0.846), "assumption": f"단리 연 {rate}%, 이자소득세 15.4% 반영"})
    if calc_type == "dsr":
        income, annual_repay = p.get("annual_income", 60_000_000), p.get("annual_repayment", 18_000_000)
        return ok({"dsr_pct": round(annual_repay / income * 100, 1), "formula": "연간 원리금 상환액 / 연소득", "regulatory_note": "규제 기준은 통상 40%입니다."})
    if calc_type == "installment":
        amount, months, rate = p.get("amount", 1_000_000), p.get("months", 12), p.get("annual_rate", 15.9)
        interest_free = p.get("interest_free", False)
        if interest_free:
            return ok({"monthly_payment": round(amount / months), "total_fee": 0, "assumption": "무이자 할부"})
        r = rate / 100 / 12
        pay = amount * r * (1 + r) ** months / ((1 + r) ** months - 1)
        return ok({"monthly_payment": round(pay), "total_fee": round(pay * months - amount), "assumption": f"수수료율 연 {rate}%"})
    if calc_type == "pension":
        monthly, years, ret = p.get("monthly", 300_000), p.get("years", 20), p.get("annual_return", 4.0)
        total = 0.0
        for _ in range(years * 12):
            total = (total + monthly) * (1 + ret / 100 / 12)
        return ok({"total_paid": monthly * 12 * years, "estimated_balance": round(total), "assumption": f"연 수익률 {ret}% 복리", "disclaimer": "수익률에 따라 달라지는 단순 예상치입니다."})
    if calc_type == "fx":
        usd = p.get("amount_usd", 100)
        return ok({"rate": D.FX_RATE, "amount_usd": usd, "amount_krw": round(usd * D.FX_RATE), "note": "매매기준율 기준. 카드 결제 환율/수수료는 다를 수 있습니다."})
    if calc_type == "income_tax":
        salary = p.get("annual_salary", 50_000_000)
        net = salary * 0.845  # 국민연금/건보/소득세 대략 반영
        return ok({"annual_salary": salary, "estimated_monthly_net": round(net / 12), "assumption": "국민연금·건강보험·소득세 개략 반영(부양가족 1인 기준)"})
    if calc_type == "investment_return":
        principal, pct = p.get("principal", 10_000_000), p.get("return_pct", 20)
        return ok({"principal": principal, "return_pct": pct, "profit": round(principal * pct / 100), "final_amount": round(principal * (1 + pct / 100))})
    if calc_type == "target_saving":
        target, years, ret = p.get("target", 30_000_000), p.get("years", 5), p.get("annual_return", 3.0)
        months, r = years * 12, ret / 100 / 12
        factor = sum((1 + r) ** (months - i) for i in range(1, months + 1))
        return ok({"target": target, "monthly_required": round(target / factor), "assumption": f"연 {ret}% 복리 가정"})
    return err("C400", f"지원하지 않는 calc_type: {calc_type}")


# ── 이벤트 ─────────────────────────────────────────────────────────
def event_list_inquiry(company: Optional[str] = None, keyword: Optional[str] = None) -> dict:
    items = D.EVENTS
    if company:
        items = [e for e in items if company in e["company"]]
    if keyword:
        items = [e for e in items if keyword in e["name"] or keyword in e["benefit"]]
    view = [{k: e[k] for k in ("event_id", "company", "name", "period", "benefit")} for e in items]
    return ok({"count": len(view), "events": view})


def event_detail_inquiry(event_id: str) -> dict:
    for e in D.EVENTS:
        if e["event_id"] == event_id or event_id in e["name"]:
            return ok({**e, "detail_url": f"monimo://event/{e['event_id']}"})
    return err("E404", f"이벤트를 찾을 수 없습니다: {event_id}")


def event_participation_inquiry(event_id: str) -> dict:
    for e in D.EVENTS:
        if e["event_id"] == event_id or event_id in e["name"]:
            return ok({"event_id": e["event_id"], "name": e["name"], "participated": e["participated"],
                       "participated_at": e.get("participated_at"), "detail_url": f"monimo://event/{e['event_id']}"})
    return err("E404", f"이벤트를 찾을 수 없습니다: {event_id}")


# ── 자산/소비 ──────────────────────────────────────────────────────
def asset_summary_inquiry() -> dict:
    return ok(D.ASSET_SUMMARY)


def spending_summary_inquiry(year_month: Optional[str] = None, period: Optional[str] = None) -> dict:
    """period='weekly' 이면 지난주 주간 소비 요약을 반환."""
    if period == "weekly":
        return ok({"period": "지난주", **D.WEEKLY_SPENDING})
    ym = _norm_month(year_month)
    s = D.SPENDING.get(ym)
    if not s:
        return ok({"year_month": ym, "total": 0, "note": "해당 월 소비내역 없음"}, message="empty")
    return ok({"year_month": ym, **s})


def spending_by_card_inquiry(year_month: Optional[str] = None, card_name: Optional[str] = None) -> dict:
    ym = _norm_month(year_month)
    s = D.SPENDING.get(ym)
    if not s:
        return ok({"year_month": ym, "by_card": []}, message="empty")
    cards = s["by_card"]
    if card_name:
        cards = [c for c in cards if card_name.replace(" ", "") in c["card"].replace(" ", "")] or cards
    return ok({"year_month": ym, "by_card": cards})


def spending_category_inquiry(year_month: Optional[str] = None, period: Optional[str] = None, category: Optional[str] = None) -> dict:
    if period == "weekly":
        return ok({"period": "지난주", "by_category": D.WEEKLY_SPENDING["by_category"]})
    ym = _norm_month(year_month)
    s = D.SPENDING.get(ym)
    if not s:
        return ok({"year_month": ym, "by_category": []}, message="empty")
    data = {"year_month": ym, "by_category": s["by_category"]}
    if category and ("식" in category or "외식" in category):
        data["food_total"] = next((c["amount"] for c in s["by_category"] if c["category"] == "외식"), 0)
        data["food_detail"] = s.get("food_detail", [])
    return ok(data)


def payment_history_inquiry(target_date: Optional[str] = None, merchant: Optional[str] = None) -> dict:
    items = D.PAYMENT_HISTORY
    if target_date:
        items = [t for t in items if t["date"] == target_date] or items
    if merchant:
        items = [t for t in items if merchant in t["merchant"]]
    return ok({"count": len(items), "total": sum(t["amount"] for t in items), "transactions": items})


def budget_inquiry() -> dict:
    b = D.BUDGET
    return ok({**b, "diff_from_budget": b["spent"] - b["monthly_budget"]})


def budget_update(new_amount: int) -> dict:
    return ok({"previous_budget": D.BUDGET["monthly_budget"], "new_budget": new_amount,
               "updated": True, "screen": "monimo://asset/budget"})


# ── 마이통장 ───────────────────────────────────────────────────────
def account_list_inquiry() -> dict:
    return ok({"accounts": [{k: a[k] for k in ("account_id", "bank", "name", "daily_interest_available")} for a in D.ACCOUNTS]})


def account_balance_inquiry(account_id: Optional[str] = None) -> dict:
    accs = [a for a in D.ACCOUNTS if not account_id or a["account_id"] == account_id or account_id in a["name"] or account_id in a["bank"]]
    return ok({"accounts": [{"name": a["name"], "bank": a["bank"], "balance": a["balance"]} for a in accs],
               "total_balance": sum(a["balance"] for a in accs)})


def account_transaction_inquiry(target_date: Optional[str] = None, account_id: Optional[str] = None) -> dict:
    items = D.ACCOUNT_TRANSACTIONS
    if target_date:
        items = [t for t in items if t["date"] == target_date]
    if account_id:
        items = [t for t in items if t["account_id"] == account_id]
    return ok({"count": len(items), "transactions": items})


def account_interest_inquiry(account_id: Optional[str] = None, simulation_amount: Optional[int] = None, simulation_months: Optional[int] = None) -> dict:
    a = next((x for x in D.ACCOUNTS if not account_id or x["account_id"] == account_id or account_id.upper() in x["name"].upper() or account_id in x["bank"]), D.ACCOUNTS[0])
    rate = a["base_rate"] + a["bonus_rate"]
    amount = simulation_amount or a["balance"]
    months = simulation_months or 1
    interest = round(amount * rate / 100 / 12 * months)
    return ok({"account": a["name"], "base_rate": a["base_rate"], "bonus_rate": a["bonus_rate"], "applied_rate": rate,
               "bonus_conditions": a["bonus_conditions"], "basis_amount": amount, "months": months,
               "expected_interest_before_tax": interest, "note": "이자소득세 15.4% 공제 전 금액"})


def account_interest_receive(account_id: Optional[str] = None) -> dict:
    a = next((x for x in D.ACCOUNTS if not account_id or x["account_id"] == account_id), D.ACCOUNTS[0])
    daily = round(a["balance"] * (a["base_rate"] + a["bonus_rate"]) / 100 / 365)
    return ok({"account": a["name"], "received_interest": daily, "received_at": str(TODAY),
               "next_available": str(TODAY + timedelta(days=1))})


# ── 젤리/챌린지 ────────────────────────────────────────────────────
def jelly_balance_inquiry() -> dict:
    b = D.JELLY["balance"]
    return ok({"as_of": str(TODAY), "total": b["normal"] + b["special"], "normal": b["normal"], "special": b["special"]})


def jelly_level_inquiry() -> dict:
    return ok(D.JELLY["level"])


def jelly_exchange_request(count: Optional[int] = None) -> dict:
    b = D.JELLY["balance"]
    n = count or (b["normal"] + b["special"])
    if n > b["normal"] + b["special"]:
        return err("K400", f"보유 젤리({b['normal'] + b['special']}개)보다 많은 수량은 교환할 수 없습니다.")
    return ok({"exchanged": n, "credited_monimoney": n * 10, "screen": "monimo://benefit/jelly-shop"})


def jelly_history_inquiry(year_month: Optional[str] = None) -> dict:
    ym = _norm_month(year_month)
    items = D.JELLY["history"].get(ym, [])
    earned = sum(i["count"] for i in items if i["count"] > 0)
    return ok({"year_month": ym, "as_of": f"{TODAY} (D-1 기준)", "earned_total": earned, "history": items})


def jelly_investment_inquiry() -> dict:
    return ok({**D.JELLY["investment"], "as_of": f"{TODAY} (D-1 기준)"})


def challenge_list_inquiry(status: str = "available") -> dict:
    c = D.CHALLENGES
    in_window = 16 <= TODAY.day <= 31
    return ok({"status": status, "challenges": c.get(status, []), "apply_window": c["apply_window"],
               "apply_open_now": in_window})


def challenge_status_inquiry(challenge_name: Optional[str] = None) -> dict:
    items = D.CHALLENGES["participating"]
    if challenge_name:
        items = [c for c in items if challenge_name.replace(" 챌린지", "") in c["name"]] or items
    return ok({"participating": items})


# ── 관심소식/컨텐츠 ────────────────────────────────────────────────
def content_list_inquiry(sort: str = "popular", topic: Optional[str] = None) -> dict:
    items = D.CONTENTS
    if topic:
        items = [c for c in items if topic in c["topic"] or topic in c["title"]]
    elif sort == "interest":
        items = [c for c in items if c["topic"] in D.INTEREST_TOPICS["selected"]]
    items = sorted(items, key=lambda c: -c["views"])
    return ok({"sort": sort, "topic": topic, "contents": [{k: c[k] for k in ("content_id", "topic", "title", "views")} for c in items]})


def content_detail_inquiry(content_id: str) -> dict:
    for c in D.CONTENTS:
        if c["content_id"] == content_id or content_id in c["title"]:
            return ok(c)
    return err("C404", f"컨텐츠를 찾을 수 없습니다: {content_id}")


def interest_topic_inquiry() -> dict:
    return ok({**D.INTEREST_TOPICS, "settings_screen": "monimo://content/interests"})


def interest_topic_update(action: str, topic: str) -> dict:
    sel = list(D.INTEREST_TOPICS["selected"])
    if action == "add" and topic not in sel:
        sel.append(topic)
    elif action == "remove" and topic in sel:
        sel.remove(topic)
    return ok({"action": action, "topic": topic, "selected": sel, "settings_screen": "monimo://content/interests"})


def daily_news_inquiry(news_type: str = "newsletter") -> dict:
    key = "closing_brief" if "brief" in news_type or "마감" in news_type else "newsletter"
    return ok({"type": key, **D.DAILY_NEWS[key]})


def weather_inquiry(region: Optional[str] = None) -> dict:
    target = region or D.WEATHER["default_region"]
    if not target:
        return ok({"region": None, "region_set": False, "note": "사용자 설정 지역 없음 — 기준 지역을 확인하세요.",
                   "suggestion": "서울특별시 중구"}, message="region_not_set")
    info = D.WEATHER["regions"].get(target) or D.WEATHER["regions"]["서울특별시 중구"]
    return ok({"region": target, "region_set": True, **info})


# ── 모니머니 ───────────────────────────────────────────────────────
def monimoney_balance_inquiry() -> dict:
    return ok({"balance": D.MONIMONEY["balance"], "as_of": str(TODAY)})


def monimoney_history_inquiry(year_month: Optional[str] = None, tx_type: Optional[str] = None) -> dict:
    ym = _norm_month(year_month)
    items = D.MONIMONEY["history"].get(ym, [])
    if tx_type:
        items = [t for t in items if t["type"] == tx_type]
    return ok({"year_month": ym, "tx_type": tx_type, "total": sum(t["amount"] for t in items), "history": items,
               "list_screen": "monimo://money/history"})


def monimoney_info_inquiry() -> dict:
    return ok(D.MONIMONEY["info"])


def monimoney_withdraw(amount: int, target_account: Optional[str] = None) -> dict:
    r = D.MONIMONEY["restriction"]
    if amount > r["available_amount"]:
        return err("M403", f"출금 가능 금액({r['available_amount']:,}원)을 초과했습니다. 사유: {r['reason']}")
    return ok({"withdrawn": amount, "target_account": target_account or "대표계좌(KB국민은행)",
               "remaining_balance": D.MONIMONEY["balance"] - amount})


def monimoney_restriction_inquiry() -> dict:
    return ok(D.MONIMONEY["restriction"])


# ── 리워드 게임/미션 ───────────────────────────────────────────────
def walking_steps_inquiry(target_date: Optional[str] = None) -> dict:
    return ok({"date": target_date or str(TODAY), "steps": D.WALKING["today_steps"], "km": D.WALKING["today_km"],
               "mission_goal": D.WALKING["mission_goal"], "goal_achieved": D.WALKING["today_steps"] >= D.WALKING["mission_goal"],
               "screen": "monimo://challenge/walk"})


def walking_mission_inquiry(year_month: Optional[str] = None) -> dict:
    ym = _norm_month(year_month)
    m = D.WALKING["monthly"].get(ym)
    if not m:
        return ok({"year_month": ym, "achieved_days": 0}, message="empty")
    return ok({"year_month": ym, **m})


def bingo_status_inquiry(year_month: Optional[str] = None) -> dict:
    ym = _norm_month(year_month)
    if ym != THIS_MONTH:
        return ok({"year_month": ym, **D.BINGO["last_month"]})
    return ok({"year_month": ym, "participating": D.BINGO["participating"], **D.BINGO["board"]})


def bingo_start() -> dict:
    return ok({"started": True, "consent": D.BINGO["consent_required"], "screen": "monimo://benefit/bingo"})


def bingo_mission_inquiry() -> dict:
    return ok({"missions": D.BINGO["missions"], "guide_screen": "혜택 > 빙고 > 빙고 조건 모두 보기"})


def monischool_status_inquiry() -> dict:
    return ok({"round": D.MONISCHOOL["current_round"], "sessions": D.MONISCHOOL["status"], "reward": D.MONISCHOOL["reward"]})


def monischool_quiz_inquiry() -> dict:
    return ok({"round": D.MONISCHOOL["current_round"], "available_quizzes": D.MONISCHOOL["quizzes"]})


def monischool_hint_inquiry(session: int) -> dict:
    for q in D.MONISCHOOL["quizzes"]:
        if q["session"] == session:
            return ok({"session": session, "hint": q["hint"], "hint_url": q["hint_url"]})
    return err("S404", f"{session}교시는 현재 응시 가능한 문제가 아닙니다.")


def monischool_answer_submit(session: int, answer: str) -> dict:
    for q in D.MONISCHOOL["quizzes"]:
        if q["session"] == session:
            correct = answer.strip() in ("후추", "기준금리")
            return ok({"session": session, "submitted": answer, "correct": correct,
                       "reward": D.MONISCHOOL["reward"] if correct else None})
    return err("S404", f"{session}교시는 현재 응시 가능한 문제가 아닙니다.")


def referral_code_inquiry() -> dict:
    return ok({"code": D.REFERRAL["code"], "link": D.REFERRAL["link"], "screen": "monimo://event/referral#my-code"})


def referral_status_inquiry() -> dict:
    return ok({k: D.REFERRAL[k] for k in ("invited_success", "reward_per_invite", "next_tier")})


def monthly_mission_status_inquiry() -> dict:
    return ok({**D.MONTHLY_MISSIONS["status"], "missions": D.MONTHLY_MISSIONS["missions"]})


def monthly_mission_list_inquiry() -> dict:
    return ok({"available": [m for m in D.MONTHLY_MISSIONS["missions"] if not m["achieved"]]})


def monthly_mission_participate(mission_name: str) -> dict:
    for m in D.MONTHLY_MISSIONS["missions"]:
        if mission_name in m["name"]:
            if m["achieved"]:
                return err("MM409", f"'{m['name']}' 미션은 이미 달성했습니다.")
            return ok({"mission": m["name"], "reward": m["reward"], "landing": m.get("landing"), "started": True})
    return err("MM404", f"미션을 찾을 수 없습니다: {mission_name}")


# ── 송금 ───────────────────────────────────────────────────────────
def transfer_account_inquiry(payee_name: Optional[str] = None) -> dict:
    items = D.TRANSFER["recent_accounts"]
    if payee_name:
        items = [a for a in items if payee_name in a["payee"]]
    return ok({"accounts": items, "transfer_screen": D.TRANSFER["screen"]})


def transfer_history_inquiry(period: Optional[str] = None, direction: Optional[str] = None) -> dict:
    items = D.TRANSFER["history"]
    if direction in ("보냄", "받음"):
        items = [t for t in items if t["direction"] == direction]
    return ok({"period": period or "최근 1개월", "count": len(items), "history": items,
               "history_screen": "monimo://transfer/history"})


# ── 삼성금융 4사 ───────────────────────────────────────────────────
def insurance_claim_status_inquiry(period: Optional[str] = None, product_keyword: Optional[str] = None) -> dict:
    items = D.CLAIMS
    if product_keyword:
        items = [c for c in items if product_keyword in c["product"]]
    if period:
        digits = "".join(ch for ch in period if ch.isdigit())
        if len(digits) >= 4:
            items = [c for c in items if c["claimed_at"].startswith(f"{digits[:4]}")] or items
        if "작년" in period:
            items = [c for c in D.CLAIMS if c["claimed_at"].startswith("2025")]
        if "3월" in period:
            items = [c for c in D.CLAIMS if c["claimed_at"][5:7] == "03"]
    return ok({"count": len(items), "claims": items, "latest": items[0] if items else None})


def insurance_claim_submit(company: str, claim_type: Optional[str] = None) -> dict:
    if company not in ("삼성생명", "삼성화재", "생명", "화재"):
        return err("CL400", "보험금 청구는 삼성생명/삼성화재 화면에서만 진행 가능합니다.")
    return ok({"supported_in_monimo": False, "redirect": f"monimo://{'life' if '생명' in company else 'fire'}/claim/submit",
               "note": "모니모에서 직접 청구는 지원되지 않아 관계사 청구 화면으로 이동합니다."})


def insurance_contract_inquiry(company: Optional[str] = None) -> dict:
    items = D.CONTRACTS
    if company:
        items = [c for c in items if company in c["company"]]
    return ok({"count": len(items), "contracts": items})


def contract_withdrawal_request(contract_id: str) -> dict:
    for c in D.CONTRACTS:
        if c["contract_id"] == contract_id or contract_id in c["product"]:
            if not c.get("withdrawal_eligible"):
                return err("CW403", f"'{c['product']}'은(는) 청약철회 가능 기간이 아니거나 대상이 아닙니다.")
            return ok({"contract": c["product"], "status": "청약철회 접수 완료", "refund_amount": c["monthly_premium"],
                       "deadline_was": c["withdrawal_deadline"]})
    return err("CW404", f"계약을 찾을 수 없습니다: {contract_id}")


def insurance_loan_inquiry() -> dict:
    return ok({"count": len(D.INSURANCE_LOANS), "loans": D.INSURANCE_LOANS})


def branch_search(region: str, service: Optional[str] = None) -> dict:
    items = [b for b in D.BRANCHES if any(tok in b["region"] for tok in region.split())]
    if service:
        items = [b for b in items if any(service in s for s in b["services"])] or items
    return ok({"region": region, "service": service, "branches": items or D.BRANCHES[:1],
               "exact_region": bool(items)})


def receipt_issue_request(contract_id: str, receipt_type: str = "해지") -> dict:
    for c in D.CONTRACTS:
        if c["contract_id"] == contract_id or contract_id in c["product"]:
            if "자동차" in c["product"]:
                return err("R403", "자동차보험은 해지영수증 발급이 불가능합니다.")
            if not c.get("receipt_available"):
                return err("R404", f"'{c['product']}'은(는) 발급 가능한 {receipt_type}영수증이 없습니다.")
            return ok({"contract": c["product"], "receipt_type": receipt_type, "issued": True, "delivery": "앱 내 문서함"})
    return err("R404", f"계약을 찾을 수 없습니다: {contract_id}")


def virtual_account_inquiry() -> dict:
    return ok(D.VIRTUAL_ACCOUNT)


def temp_driver_inquiry() -> dict:
    return ok({"active": D.TEMP_DRIVER["active"], "history": D.TEMP_DRIVER["history"],
               "has_active": bool(D.TEMP_DRIVER["active"])})


def temp_driver_apply(start_date: str, end_date: str) -> dict:
    try:
        s, e = date.fromisoformat(start_date), date.fromisoformat(end_date)
    except ValueError:
        return err("T400", "날짜 형식은 YYYY-MM-DD 입니다.")
    if e < s:
        return err("T400", "종료일이 시작일보다 빠릅니다.")
    days = (e - s).days + 1
    return ok({"contract": "삼성화재 자동차보험(CT003)", "start": start_date, "end": end_date, "days": days,
               "premium": days * 3_800, "applied": True})


# ── 카드 ───────────────────────────────────────────────────────────
def card_list_inquiry() -> dict:
    return ok({"cards": D.CARDS})


def card_usage_inquiry(card_name: Optional[str] = None, period: Optional[str] = None) -> dict:
    if card_name:
        key = next((k for k in D.CARD_USAGE if card_name.replace(" ", "").replace("o", "오").lower() in k.replace(" ", "").lower()
                    or card_name.replace(" ", "").lower() in k.replace(" ", "").lower()), None)
        if not key:
            return err("CD404", f"보유 카드 중 '{card_name}'을(를) 찾을 수 없습니다.")
        items = D.CARD_USAGE[key]
        return ok({"card": key, "period": period or "최근 2주", "count": len(items), "total": sum(t["amount"] for t in items), "usage": items})
    merged = [{"card": k, **t} for k, v in D.CARD_USAGE.items() for t in v]
    return ok({"card": None, "period": period or "최근 2주", "count": len(merged), "usage": merged})


def card_billing_inquiry() -> dict:
    return ok(D.CARD_BILLING)


def card_immediate_payment(amount: Optional[int] = None, tx_ids: Optional[list[str]] = None) -> dict:
    pay = amount or D.CARD_BILLING["expected_amount"]
    mode = "건별결제" if tx_ids else "금액결제"
    return ok({"mode": mode, "paid_amount": pay, "tx_ids": tx_ids,
               "remaining_expected": max(D.CARD_BILLING["expected_amount"] - pay, 0), "paid_at": str(TODAY)})


def other_card_usage_inquiry(company: str) -> dict:
    info = D.OTHER_CARDS.get(company)
    if not info:
        return ok({"company": company, "note": "마이데이터 소비내역에 해당 카드사 이용내역이 없습니다."}, message="empty")
    return ok({"company": company, **info, "immediate_payment_supported": False,
               "note": "타사 카드 즉시결제는 해당 카드사 앱에서만 가능합니다."})


# ── 증권 ───────────────────────────────────────────────────────────
def market_index_inquiry(scope: str = "all") -> dict:
    m = D.MARKET_INDEX
    if scope == "domestic":
        return ok({"scope": scope, "indexes": m["domestic"], "detail_url": "monimo://securities/index"})
    if scope == "overseas":
        return ok({"scope": scope, "indexes": m["overseas"], "detail_url": "monimo://securities/index"})
    if scope == "fx":
        return ok({"scope": scope, **m["fx"]})
    return ok({"scope": "all", "domestic": m["domestic"], "overseas": m["overseas"], "fx": m["fx"],
               "detail_url": "monimo://securities/index"})


def stock_item_inquiry(keyword: str) -> dict:
    for name, s in D.STOCKS.items():
        if keyword.replace(" ", "") in name.replace(" ", "") or (s.get("code") and keyword == s["code"]):
            return ok({"name": name, **s, "listed": s.get("listed", True)})
    return ok({"name": keyword, "listed": None, "note": "종목을 찾지 못했습니다. 비상장이거나 종목명이 다를 수 있습니다.",
               "discover_url": "monimo://stock/discover"}, message="not_found")


def stock_ranking_inquiry(criteria: str = "popular", sector: Optional[str] = None) -> dict:
    r = D.STOCK_RANKINGS
    if sector:
        items = r["sector"].get(sector)
        if not items:
            return ok({"criteria": "sector", "sector": sector, "stocks": []}, message="empty")
        return ok({"criteria": "sector", "sector": sector, "stocks": items, "more_url": r["more_url"]})
    if criteria in ("volume", "amount"):
        return ok({"criteria": criteria, "rankings": r[criteria], "more_url": r["more_url"]})
    return ok({"criteria": "popular", **r["popular"], "more_url": r["more_url"]})


def pb_consult_request() -> dict:
    p = D.PB_LOUNGE
    if not p["eligible"]:
        return err("PB403", f"S.Lounge 대상 고객이 아닙니다. 대상 조건: {p['condition']}")
    return ok({"eligible": True, "entry": p["entry"], "reserved_slot": p["next_slot"], "requested": True})


def pension_education_apply() -> dict:
    p = D.PENSION_EDU
    if not p["enrolled_plans"]:
        return err("PE403", "DC/IRP 가입 고객만 신청할 수 있습니다.")
    return ok({"plans": p["enrolled_plans"], "education": p["education"], "period": p["period"],
               "status": "신청 완료", "apply_url": p["apply_url"]})


# ── 운세/일상 ──────────────────────────────────────────────────────
def saju_profile_inquiry() -> dict:
    return ok(D.SAJU_PROFILE)


def saju_profile_register(birth_date: str, birth_time: Optional[str] = None, calendar_type: str = "양력") -> dict:
    try:
        bd = date.fromisoformat(birth_date)
    except ValueError:
        return err("F400", "생년월일 형식은 YYYY-MM-DD 입니다.")
    if bd > TODAY:
        return err("F422", f"생년월일({birth_date})이 미래 일자입니다. 사주정보를 다시 확인해 주세요.")
    return ok({"registered": True, "birth_date": birth_date, "birth_time": birth_time, "calendar_type": calendar_type})


def fortune_inquiry(fortune_type: str = "daily", zodiac: Optional[str] = None, birth_date: Optional[str] = None) -> dict:
    f = D.FORTUNES
    if fortune_type == "zodiac":
        z = zodiac or "양띠"
        return ok({"type": "zodiac", "zodiac": z, "fortune": f["zodiac"].get(z, f["zodiac"]["양띠"])})
    if fortune_type == "tarot":
        return ok({"type": "tarot", **f["tarot"]})
    if fortune_type in f:
        return ok({"type": fortune_type, "birth_date": birth_date, "fortune": f[fortune_type],
                   "detail_screen": "monimo://fortune/home", "disclaimer": "재미로 보는 참고 정보예요."})
    return err("F400", f"지원하지 않는 운세 유형: {fortune_type}")


# ── registry ───────────────────────────────────────────────────────
MOCK_TOOLS = {
    name: fn for name, fn in list(globals().items())
    if callable(fn) and not name.startswith("_") and name in TOOL_CATALOG
}

_missing = set(TOOL_CATALOG) - set(MOCK_TOOLS)
if _missing:
    raise RuntimeError(f"mock implementation missing for tools: {sorted(_missing)}")


def register_mock_tools(mcp) -> None:
    """Register every mock tool on a FastMCP server."""
    for name, fn in MOCK_TOOLS.items():
        mcp.tool(fn, name=name, description=TOOL_CATALOG[name])
