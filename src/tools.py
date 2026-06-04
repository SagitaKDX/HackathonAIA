"""
Tools Module — Real Data Retrieval, Analytics, and Executive Functions.

Implements the three levels of tools specified in the hackathon plan:
Level 1: get_reviews, search_reviews, get_supporting_quotes
Level 2: get_top_complaints, get_top_strengths, detect_emerging_issues, get_category_breakdown, rank_branches
Level 3: prioritize_risks, generate_weekly_summary
"""

import json
import os
import re
import collections
from datetime import datetime, timedelta

DATA_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "processed", "analyzed_reviews.json")
)


_cached_data = None
_cached_mtime = None


def load_review_data():
    """Load analyzed reviews from the JSON data file with in-memory caching."""
    global _cached_data, _cached_mtime
    if not os.path.exists(DATA_FILE):
        return []
    try:
        current_mtime = os.path.getmtime(DATA_FILE)
        if _cached_data is not None and _cached_mtime == current_mtime:
            return _cached_data
            
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        _cached_data = data
        _cached_mtime = current_mtime
        return data
    except Exception as e:
        print(f"[Tools] Error loading review data: {e}")
        return _cached_data if _cached_data is not None else []


def parse_datetime(date_str):
    """Parse ISO timestamp string timezone-safely into a naive datetime."""
    if not date_str:
        return datetime(2026, 6, 4)
    try:
        # Strip timezone suffix to compare with standard naive datetime
        # e.g., '2026-06-01T19:30:00+07:00' -> '2026-06-01T19:30:00'
        clean_str = date_str
        if "+" in clean_str:
            clean_str = clean_str.split("+")[0]
        if "Z" in clean_str:
            clean_str = clean_str.split("Z")[0]
        return datetime.fromisoformat(clean_str)
    except Exception:
        return datetime(2026, 6, 4)


def get_period_dates(period):
    """Get start/end dates for current and previous periods relative to dataset max date or baseline 2026-06-04."""
    records = load_review_data()
    if records:
        try:
            # Find the max date in the dataset to act as the baseline dynamically
            max_date_str = max(r.get("created_at") for r in records if r.get("created_at"))
            base_date = parse_datetime(max_date_str)
        except Exception:
            base_date = datetime(2026, 6, 4)
    else:
        base_date = datetime(2026, 6, 4)
        
    if period == "7d":
        days = 7
    elif period == "30d":
        days = 30
    else:
        days = 30
        
    end = datetime(base_date.year, base_date.month, base_date.day, 23, 59, 59)
    start = datetime(base_date.year, base_date.month, base_date.day) - timedelta(days=days)
    
    prev_end = start - timedelta(seconds=1)
    prev_start = start - timedelta(days=days)
    
    return start, end, prev_start, prev_end


# ──────────────────────────────────────────────────────────────────────
# LEVEL 1 — Retrieval Tools
# ──────────────────────────────────────────────────────────────────────

def get_reviews(branch_id=None, start_date=None, end_date=None, sentiment=None, category=None, subcategory=None, limit=50):
    """
    Get raw reviews filtered by branch, date range, sentiment type, and categories.
    
    Args:
        branch_id (str): Branch name or ID.
        start_date (str): ISO start date.
        end_date (str): ISO end date.
        sentiment (str): 'positive', 'negative', 'neutral', or 'all'.
        category (str): Main category (FOOD, SERVICE, etc.).
        subcategory (str): Specific subcategory.
        limit (int): Max records to return.
    """
    records = load_review_data()
    filtered = []
    
    s_date = parse_datetime(start_date) if start_date else None
    e_date = parse_datetime(end_date) if end_date else None

    for r in records:
        # Branch
        if branch_id and branch_id != "all":
            b_id_lower = str(branch_id).lower().strip()
            r_id = str(r.get("branch_id", "")).lower().strip()
            r_name = str(r.get("branch_name", "")).lower().strip()
            if r_id != b_id_lower and r_name != b_id_lower:
                def _strip_accents(s):
                    accents = {
                        "áàảãạăắằẳẵặâấầẩẫậ": "a",
                        "éèẻẽẹêếềểễệ": "e",
                        "íìỉĩị": "i",
                        "óòỏõọôốồổỗộơớờởỡợ": "o",
                        "úùủũụưứừửữự": "u",
                        "ýỳỷỹỵ": "y",
                        "đ": "d"
                    }
                    s_new = ""
                    for char in s:
                        matched = False
                        for group, replacement in accents.items():
                            if char in group:
                                s_new += replacement
                                matched = True
                                break
                        if not matched:
                            s_new += char
                    return s_new
                b_clean = _strip_accents(b_id_lower).replace("branch_", "").replace("_", "").replace(" ", "")
                r_name_clean = _strip_accents(r_name).replace("branch_", "").replace("_", "").replace(" ", "")
                r_id_clean = _strip_accents(r_id).replace("branch_", "").replace("_", "").replace(" ", "")
                if r_id_clean != b_clean and r_name_clean != b_clean:
                    continue
                
        # Date
        r_date = parse_datetime(r.get("created_at"))
        if s_date and r_date < s_date:
            continue
        if e_date and r_date > e_date:
            continue
            
        # Sentiment
        if sentiment and sentiment != "all":
            r_sent = r.get("sentiment", 0)
            if sentiment == "positive" and r_sent <= 0:
                continue
            elif sentiment == "negative" and r_sent >= 0:
                continue
            elif sentiment == "neutral" and r_sent != 0:
                continue
                
        # Category
        if category and category != "all":
            if r.get("main_category") != category:
                continue
                
        # Subcategory
        if subcategory and subcategory != "all":
            if r.get("subcategory") != subcategory:
                continue
                
        created_date = r.get("created_at", "")[:10] if r.get("created_at") else ""
        filtered.append({
            "branch": r.get("branch_name"),
            "sentiment": r.get("sentiment"),
            "category": r.get("main_category"),
            "sub": r.get("subcategory"),
            "sev": r.get("severity"),
            "evidence": r.get("evidence"),
            "date": created_date
        })
        
    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)
    return filtered[:limit]


def count_reviews(branch_id=None, start_date=None, end_date=None, period=None, sentiment=None, category=None, subcategory=None):
    """
    Đếm số lượng đánh giá khách hàng (reviews) thỏa mãn các điều kiện lọc.
    
    Args:
        branch_id (str): Tên hoặc ID chi nhánh (ví dụ: 'Times City', 'Lý Quốc Sư').
        start_date (str): Ngày bắt đầu lọc (định dạng ISO, ví dụ: '2026-05-01').
        end_date (str): Ngày kết thúc lọc (định dạng ISO, ví dụ: '2026-06-04').
        period (str): Khoảng thời gian tự động lọc ('7d' hoặc '30d') nếu không truyền start_date/end_date.
        sentiment (str): 'positive' (tích cực), 'negative' (tiêu cực), 'neutral' (trung lập), hoặc 'all'.
        category (str): Danh mục chính (FOOD, SERVICE, AMBIENCE, PRICE, OTHER, hoặc 'all').
        subcategory (str): Danh mục con cụ thể.
    """
    records = load_review_data()
    
    s_date = parse_datetime(start_date) if start_date else None
    e_date = parse_datetime(end_date) if end_date else None
        
    if not s_date and not e_date and period:
        s_date, e_date, _, _ = get_period_dates(period)
        
    count = 0
    for r in records:
        # Branch
        if branch_id and branch_id != "all":
            b_id_lower = str(branch_id).lower().strip()
            r_id = str(r.get("branch_id", "")).lower().strip()
            r_name = str(r.get("branch_name", "")).lower().strip()
            if r_id != b_id_lower and r_name != b_id_lower:
                def _strip_accents(s):
                    accents = {
                        "áàảãạăắằẳẵặâấầẩẫậ": "a",
                        "éèẻẽẹêếềểễệ": "e",
                        "íìỉĩị": "i",
                        "óòỏõọôốồổỗộơớờởỡợ": "o",
                        "úùủũụưứừửữự": "u",
                        "ýỳỷỹỵ": "y",
                        "đ": "d"
                    }
                    s_new = ""
                    for char in s:
                        matched = False
                        for group, replacement in accents.items():
                            if char in group:
                                s_new += replacement
                                matched = True
                                break
                        if not matched:
                            s_new += char
                    return s_new
                b_clean = _strip_accents(b_id_lower).replace("branch_", "").replace("_", "").replace(" ", "")
                r_name_clean = _strip_accents(r_name).replace("branch_", "").replace("_", "").replace(" ", "")
                r_id_clean = _strip_accents(r_id).replace("branch_", "").replace("_", "").replace(" ", "")
                if r_id_clean != b_clean and r_name_clean != b_clean:
                    continue
                
        # Date
        r_date = parse_datetime(r.get("created_at"))
        if s_date and r_date < s_date:
            continue
        if e_date and r_date > e_date:
            continue
            
        # Sentiment
        if sentiment and sentiment != "all":
            r_sent = r.get("sentiment", 0)
            if sentiment == "positive" and r_sent <= 0:
                continue
            elif sentiment == "negative" and r_sent >= 0:
                continue
            elif sentiment == "neutral" and r_sent != 0:
                continue
                
        # Category
        if category and category != "all":
            if r.get("main_category") != category:
                continue
                
        # Subcategory
        if subcategory and subcategory != "all":
            if r.get("subcategory") != subcategory:
                continue
                
        count += 1
        
    return {"count": count}



def search_reviews(keyword, branch_id=None, start_date=None, end_date=None, limit=50):
    """
    Search reviews by keyword matching in content or evidence text.
    
    Args:
        keyword (str): The search keyword.
        branch_id (str): Optional branch filter.
        start_date (str): Optional start date filter.
        end_date (str): Optional end date filter.
        limit (int): Max records.
    """
    if not keyword:
        return []
    records = load_review_data()
    filtered = []
    
    s_date = parse_datetime(start_date) if start_date else None
    e_date = parse_datetime(end_date) if end_date else None
    kw_lower = keyword.lower()

    for r in records:
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
        r_date = parse_datetime(r.get("created_at"))
        if s_date and r_date < s_date:
            continue
        if e_date and r_date > e_date:
            continue
            
        content = r.get("content", "") or ""
        evidence = r.get("evidence", "") or ""
        
        if kw_lower in content.lower() or kw_lower in evidence.lower():
            created_date = r.get("created_at", "")[:10] if r.get("created_at") else ""
            filtered.append({
                "branch": r.get("branch_name"),
                "evidence": r.get("evidence"),
                "sentiment": r.get("sentiment"),
                "date": created_date
            })
            
    filtered.sort(key=lambda x: x.get("date", ""), reverse=True)
    return filtered[:limit]


def get_supporting_quotes(issue_id, branch_id=None, limit=5):
    """
    Get representative evidence quotes for a specific subcategory or issue.
    
    Args:
        issue_id (str): The subcategory ID (e.g. SERVICE_WAIT_TIME) or category.
        branch_id (str): Optional branch filter.
        limit (int): Max quotes.
    """
    records = load_review_data()
    quotes = []
    
    for r in records:
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
        if r.get("subcategory") == issue_id or r.get("main_category") == issue_id:
            quotes.append({
                "review_id": r.get("review_id"),
                "branch_name": r.get("branch_name"),
                "quote": r.get("evidence") or r.get("content"),
                "confidence": r.get("confidence", 1.0)
            })
            
    quotes.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    return {
        "issue_id": issue_id,
        "quotes": quotes[:limit]
    }


# ──────────────────────────────────────────────────────────────────────
# LEVEL 2 — Analytics Tools
# ──────────────────────────────────────────────────────────────────────

def get_top_complaints(branch_id=None, period="7d", limit=5):
    """
    Get the top complaints sorted by Impact Score.
    
    Args:
        branch_id (str): Optional branch filter.
        period (str): '7d' or '30d'.
        limit (int): Max complaints.
    """
    start, end, prev_start, prev_end = get_period_dates(period)
    records = load_review_data()
    
    current_negs = []
    prev_negs = []
    
    for r in records:
        if r.get("sentiment", 0) >= 0:
            continue
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
                
        r_date = parse_datetime(r.get("created_at"))
        if start <= r_date <= end:
            current_negs.append(r)
        elif prev_start <= r_date <= prev_end:
            prev_negs.append(r)
            
    sub_groups = collections.defaultdict(list)
    for r in current_negs:
        sub_groups[r.get("subcategory")].append(r)
        
    prev_counts = collections.Counter(r.get("subcategory") for r in prev_negs)
    
    items = []
    for sub, recs in sub_groups.items():
        mentions = len(recs)
        avg_severity = sum(r.get("severity", 1) for r in recs) / mentions
        avg_confidence = sum(r.get("confidence", 1.0) for r in recs) / mentions
        impact_score = round(mentions * avg_severity * avg_confidence, 1)
        
        affected = list(set(r.get("branch_name") for r in recs if r.get("branch_name")))[:3]
        
        prev_m = prev_counts.get(sub, 0)
        if prev_m == 0:
            trend_pct = 100 if mentions > 0 else 0
        else:
            trend_pct = int(round((mentions - prev_m) / prev_m * 100))
            
        items.append({
            "subcategory": sub,
            "mentions": mentions,
            "trend_pct": trend_pct,
            "impact_score": impact_score,
            "affected_branches": affected
        })
        
    items.sort(key=lambda x: x["impact_score"], reverse=True)
    return {
        "period": period,
        "items": items[:limit]
    }


def get_top_strengths(branch_id=None, period="30d", limit=5):
    """
    Get top strengths based on positive reviews.
    
    Args:
        branch_id (str): Optional branch filter.
        period (str): '7d' or '30d'.
        limit (int): Max strengths.
    """
    start, end, prev_start, prev_end = get_period_dates(period)
    records = load_review_data()
    
    current_pos = []
    prev_pos = []
    
    for r in records:
        if r.get("sentiment", 0) <= 0:
            continue
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
                
        r_date = parse_datetime(r.get("created_at"))
        if start <= r_date <= end:
            current_pos.append(r)
        elif prev_start <= r_date <= prev_end:
            prev_pos.append(r)
            
    sub_groups = collections.defaultdict(list)
    for r in current_pos:
        sub_groups[r.get("subcategory")].append(r)
        
    prev_counts = collections.Counter(r.get("subcategory") for r in prev_pos)
    
    items = []
    for sub, recs in sub_groups.items():
        mentions = len(recs)
        avg_sentiment = sum(r.get("sentiment", 0.5) for r in recs) / mentions
        avg_confidence = sum(r.get("confidence", 1.0) for r in recs) / mentions
        strength_score = round(mentions * avg_sentiment * avg_confidence, 1)
        
        top_branches = list(set(r.get("branch_name") for r in recs if r.get("branch_name")))[:3]
        
        prev_m = prev_counts.get(sub, 0)
        if prev_m == 0:
            trend_pct = 100 if mentions > 0 else 0
        else:
            trend_pct = int(round((mentions - prev_m) / prev_m * 100))
            
        items.append({
            "subcategory": sub,
            "mentions": mentions,
            "trend_pct": trend_pct,
            "strength_score": strength_score,
            "top_branches": top_branches
        })
        
    items.sort(key=lambda x: x["strength_score"], reverse=True)
    return {
        "period": period,
        "items": items[:limit]
    }


def detect_emerging_issues(branch_id=None, period="7d", limit=5):
    """
    Detect subcategories with sharp negative increases.
    
    Emerging rules: Current negative mentions >= 5, growth >= 50% (0.5), avg severity >= 2.5
    """
    start, end, prev_start, prev_end = get_period_dates(period)
    records = load_review_data()
    
    current_negs = []
    prev_negs = []
    
    for r in records:
        if r.get("sentiment", 0) >= 0:
            continue
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
                
        r_date = parse_datetime(r.get("created_at"))
        if start <= r_date <= end:
            current_negs.append(r)
        elif prev_start <= r_date <= prev_end:
            prev_negs.append(r)
            
    sub_groups = collections.defaultdict(list)
    for r in current_negs:
        sub_groups[r.get("subcategory")].append(r)
        
    prev_counts = collections.Counter(r.get("subcategory") for r in prev_negs)
    
    emerging = []
    for sub, recs in sub_groups.items():
        curr_count = len(recs)
        prev_count = prev_counts.get(sub, 0)
        
        growth_rate = (curr_count - prev_count) / max(prev_count, 1)
        avg_severity = sum(r.get("severity", 1) for r in recs) / curr_count
        
        if curr_count >= 5 and growth_rate >= 0.5 and avg_severity >= 2.5:
            evidence = recs[0].get("evidence") or recs[0].get("content")
            
            emerging.append({
                "subcategory": sub,
                "current_mentions": curr_count,
                "previous_mentions": prev_count,
                "growth_rate_pct": round(growth_rate * 100, 1),
                "avg_severity": round(avg_severity, 1),
                "evidence": evidence
            })
            
    emerging.sort(key=lambda x: x["growth_rate_pct"], reverse=True)
    return emerging[:limit]


def get_category_breakdown(branch_id=None, period="30d"):
    """Get category distribution of aspects."""
    start, end, _, _ = get_period_dates(period)
    records = load_review_data()
    
    breakdown = collections.Counter()
    for r in records:
        if branch_id and branch_id != "all":
            if r.get("branch_id") != branch_id and r.get("branch_name") != branch_id:
                continue
                
        r_date = parse_datetime(r.get("created_at"))
        if start <= r_date <= end:
            cat = r.get("main_category", "OTHER")
            breakdown[cat] += 1
            
    return {
        "branch_id": branch_id,
        "period": period,
        "breakdown": dict(breakdown)
    }


def rank_branches(metric="risk", period="7d", limit=10):
    """
    Rank branches based on specified metric.
    
    Metrics: 'risk', 'rating', 'sentiment', 'complaint_volume', 'strength'
    """
    start, end, _, _ = get_period_dates(period)
    records = load_review_data()
    
    period_records = []
    for r in records:
        r_date = parse_datetime(r.get("created_at"))
        if start <= r_date <= end:
            period_records.append(r)
            
    branch_groups = collections.defaultdict(list)
    for r in period_records:
        if r.get("branch_name"):
            branch_groups[r.get("branch_name")].append(r)
            
    branch_stats = []
    for b_name, recs in branch_groups.items():
        total_aspects = len(recs)
        unique_reviews = len(set(r.get("review_id") for r in recs))
        
        avg_sentiment = sum(r.get("sentiment", 0.0) for r in recs) / total_aspects
        
        unique_ratings = []
        seen_reviews = set()
        for r in recs:
            r_id = r.get("review_id")
            if r_id not in seen_reviews:
                seen_reviews.add(r_id)
                unique_ratings.append(r.get("rating", 1))
        avg_rating = sum(unique_ratings) / len(unique_ratings) if unique_ratings else 1.0
        
        complaint_volume = sum(1 for r in recs if r.get("sentiment", 0) < 0)
        
        # Risk Score (negatives)
        sub_negs = collections.defaultdict(list)
        sub_pos = collections.defaultdict(list)
        for r in recs:
            if r.get("sentiment", 0) < 0:
                sub_negs[r.get("subcategory")].append(r)
            elif r.get("sentiment", 0) > 0:
                sub_pos[r.get("subcategory")].append(r)
                
        risk_score = 0.0
        for sub, neg_recs in sub_negs.items():
            mentions = len(neg_recs)
            avg_sev = sum(r.get("severity", 1) for r in neg_recs) / mentions
            avg_conf = sum(r.get("confidence", 1.0) for r in neg_recs) / mentions
            risk_score += mentions * avg_sev * avg_conf
            
        # Strength Score (positives)
        strength_score = 0.0
        for sub, pos_recs in sub_pos.items():
            mentions = len(pos_recs)
            avg_sent = sum(r.get("sentiment", 0.5) for r in pos_recs) / mentions
            avg_conf = sum(r.get("confidence", 1.0) for r in pos_recs) / mentions
            strength_score += mentions * avg_sent * avg_conf
            
        branch_stats.append({
            "branch_name": b_name,
            "total_reviews": unique_reviews,
            "avg_sentiment": round(avg_sentiment, 2),
            "avg_rating": round(avg_rating, 2),
            "complaint_volume": complaint_volume,
            "risk_score": round(risk_score, 1),
            "strength_score": round(strength_score, 1)
        })
        
    if metric == "risk":
        branch_stats.sort(key=lambda x: x["risk_score"], reverse=True)
    elif metric == "rating":
        branch_stats.sort(key=lambda x: x["avg_rating"], reverse=True)
    elif metric == "sentiment":
        branch_stats.sort(key=lambda x: x["avg_sentiment"], reverse=True)
    elif metric == "complaint_volume":
        branch_stats.sort(key=lambda x: x["complaint_volume"], reverse=True)
    elif metric == "strength":
        branch_stats.sort(key=lambda x: x["strength_score"], reverse=True)
    else:
        branch_stats.sort(key=lambda x: x["risk_score"], reverse=True)
        
    return branch_stats[:limit]

def get_operational_health_summary(branch_id=None, start_date=None, end_date=None, period=None):
    """
    Tính toán các chỉ số sức khỏe vận hành vĩ mô cho một hoặc tất cả chi nhánh.
    Trả về: Tổng số review, True Negative Rate (%), Average Severity, và số lượng sự cố khẩn cấp (Severity 4-5).
    """
    records = load_review_data()
    
    s_date = parse_datetime(start_date) if start_date else None
    e_date = parse_datetime(end_date) if end_date else None
    
    if not s_date and not e_date and period:
        s_date, e_date, _, _ = get_period_dates(period)
        
    filtered = []
    for r in records:
        # Branch
        if branch_id and branch_id != "all":
            b_id_lower = str(branch_id).lower().strip()
            r_id = str(r.get("branch_id", "")).lower().strip()
            r_name = str(r.get("branch_name", "")).lower().strip()
            if r_id != b_id_lower and r_name != b_id_lower:
                def _strip_accents(s):
                    accents = {
                        "áàảãạăắằẳẵặâấầẩẫậ": "a",
                        "éèẻẽẹêếềểễệ": "e",
                        "íìỉĩị": "i",
                        "óòỏõọôốồổỗộơớờởỡợ": "o",
                        "úùủũụưứừửữự": "u",
                        "ýỳỷỹỵ": "y",
                        "đ": "d"
                    }
                    s_new = ""
                    for char in s:
                        matched = False
                        for group, replacement in accents.items():
                            if char in group:
                                s_new += replacement
                                matched = True
                                break
                        if not matched:
                            s_new += char
                    return s_new
                b_clean = _strip_accents(b_id_lower).replace("branch_", "").replace("_", "").replace(" ", "")
                r_name_clean = _strip_accents(r_name).replace("branch_", "").replace("_", "").replace(" ", "")
                r_id_clean = _strip_accents(r_id).replace("branch_", "").replace("_", "").replace(" ", "")
                if r_id_clean != b_clean and r_name_clean != b_clean:
                    continue
                    
        # Date
        r_date = parse_datetime(r.get("created_at"))
        if s_date and r_date < s_date:
            continue
        if e_date and r_date > e_date:
            continue
            
        filtered.append(r)
        
    # Tính toán các chỉ số vĩ mô
    unique_reviews = len(set(r.get("review_id") for r in filtered if r.get("review_id")))
    total_aspects = len(filtered)
    
    # Tính True Negative Rate (%)
    # TNR = (TN / Actual Negatives) * 100
    # Actual Negatives (nhãn thực tế là tiêu cực) có rating == 0
    # TN (dự đoán đúng tiêu cực) có rating == 0 và sentiment < 0
    actual_neg_count = sum(1 for r in filtered if r.get("rating") == 0)
    if actual_neg_count > 0:
        tn_count = sum(1 for r in filtered if r.get("rating") == 0 and r.get("sentiment", 0) < 0)
        tnr_val = (tn_count / actual_neg_count) * 100
    else:
        tnr_val = 100.0  # Nếu không có review tiêu cực nào thì xem như 100%
        
    # Tính Average Severity
    severities = [r.get("severity") for r in filtered if r.get("severity") is not None]
    avg_severity = sum(severities) / len(severities) if severities else 0.0
    
    # Số lượng sự cố khẩn cấp (Severity từ 4 đến 5)
    critical_incidents = sum(1 for r in filtered if r.get("severity", 0) >= 4)
    
    return {
        "local": branch_id if branch_id else "All Branches",
        "total_reviews": unique_reviews,
        "total_aspect_records": total_aspects,
        "true_negative_rate_pct": round(tnr_val, 2),
        "average_severity": round(avg_severity, 2),
        "critical_incidents_count": critical_incidents
    }

# ──────────────────────────────────────────────────────────────────────
# LEVEL 3 — Executive Tools
# ──────────────────────────────────────────────────────────────────────

def prioritize_risks(branch_id=None, period="7d", limit=3):
    """Prioritize complaints by Impact Score, providing actionable details."""
    complaints = get_top_complaints(branch_id=branch_id, period=period, limit=limit)
    prioritized = []
    
    for idx, c in enumerate(complaints.get("items", [])):
        affected_str = ", ".join(c.get("affected_branches", []))
        desc = f"Khách hàng phàn nàn nhiều về {c.get('subcategory')} tại {affected_str or 'các chi nhánh'}."
        
        prioritized.append({
            "priority": idx + 1,
            "subcategory": c.get("subcategory"),
            "impact_score": c.get("impact_score"),
            "mentions": c.get("mentions"),
            "avg_severity": round(c.get("impact_score") / max(c.get("mentions") * 0.9, 1.0), 1),
            "description": desc
        })
        
    return {
        "period": period,
        "branch_id": branch_id,
        "prioritized_risks": prioritized
    }


def generate_weekly_summary(period="7d"):
    """Compile a unified weekly summary report."""
    complaints = get_top_complaints(period=period, limit=3)
    strengths = get_top_strengths(period=period, limit=3)
    ranked = rank_branches(metric="risk", period=period, limit=12)
    ranked_str = rank_branches(metric="strength", period=period, limit=12)
    emerging = detect_emerging_issues(period=period, limit=3)
    
    worst_branch = ranked[0] if ranked else {}
    best_branch = ranked_str[0] if ranked_str else {}
    
    actions = []
    for c in complaints.get("items", []):
        sub = c.get("subcategory")
        branches = c.get("affected_branches", [])
        branch_str = f"chi nhánh {', '.join(branches)}" if branches else "các chi nhánh bị ảnh hưởng"
        
        if "WAIT_TIME" in sub:
            actions.append(f"Tăng cường nhân sự vào giờ cao điểm tại {branch_str}.")
        elif "TEMPERATURE" in sub:
            actions.append(f"Kiểm tra và nâng cấp thiết bị giữ nhiệt thức ăn tại {branch_str}.")
        elif "FRESHNESS" in sub:
            actions.append(f"Kiểm tra nguồn cung ứng nguyên liệu tươi và quy trình bảo quản tại {branch_str}.")
        elif "CLEANLINESS" in sub:
            actions.append(f"Thực hiện tổng vệ sinh toàn bộ cửa hàng và chấn chỉnh tác phong dọn dẹp tại {branch_str}.")
        elif "STAFF_ATTITUDE" in sub:
            actions.append(f"Tổ chức đào tạo lại kỹ năng CSKH và thái độ ứng xử của nhân viên phục vụ tại {branch_str}.")
        else:
            actions.append(f"Xem xét và xử lý khắc phục vấn đề {sub} tại {branch_str}.")
            
    if not actions:
        actions.append("Tiếp tục theo dõi phản hồi của khách hàng để phát hiện các bất thường vận hành.")
        
    return {
        "period": period,
        "top_risks": complaints.get("items", []),
        "top_strengths": strengths.get("items", []),
        "worst_branch": worst_branch,
        "best_branch": best_branch,
        "emerging_issues": emerging,
        "recommended_actions": actions[:3]
    }
