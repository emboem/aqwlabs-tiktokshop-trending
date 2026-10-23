"""Parameter waktu Tren Pasar mengikuti aturan tiap tab FastMoss."""
from app.catalog import default_period_value
from app.market import PAGE_BY_KEY, market_params


def mp(page, **q):
    return market_params(PAGE_BY_KEY[page], q, "ID")


def test_pulse_daily_default_sends_nothing_extra():
    assert mp("pulse") == {"region": "ID"}
    assert mp("pulse", date_type="1", date_value="2026-10-01")["date_value"] == "2026-10-01"


def test_pulse_week_month_fill_default_value():
    p = mp("pulse", date_type="2")
    assert p["date_type"] == "2" and p["date_value"] == default_period_value(2)


def test_category_28_days_and_month():
    assert mp("category") == {"region": "ID"}
    p = mp("category", date_type="3", date_value="2026-09", pcid="14")
    assert p == {"region": "ID", "pcid": "14", "date_type": 3, "date_value": "2026-09"}


def test_strategy_never_sends_date_type():
    assert mp("strategy") == {"region": "ID", "date_value": ""}
    p = mp("strategy", date_type="3")
    assert "date_type" not in p and p["date_value"] == default_period_value(3)


def test_old_page_keeps_daily_default():
    assert mp("category-daily") == {"region": "ID"}
    assert mp("category-daily", date_type="2")["date_type"] == "2"
