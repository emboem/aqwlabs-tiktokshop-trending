"""Mesin bagian detail: wildcard root, tampilan alternatif (alt), periode kustom, opsi milik detail.

Klien FastMoss diganti stub — tes tidak pernah mengirim request ke FastMoss.
"""
import asyncio
import datetime as dt

from app import details
from app.catalog import check_range
from app.details import DETAILS, fetch_option, pick, run_section
from app.fastmoss.client import FMResult


class StubClient:
    def __init__(self, data):
        self.data, self.calls = data, []

    async def row_limit(self):
        return 0

    async def get(self, path, params, region=None, referer=None, use_cache=True):
        self.calls.append((path, dict(params)))
        return FMResult(status="ok", data=self.data)


def _run(sec, query, data):
    stub = StubClient(data)
    old = details.client
    details.client = stub
    try:
        return asyncio.run(run_section(sec, {"id": "1"}, query, "ID")), stub.calls
    finally:
        details.client = old


def test_pick_wildcard_flattens_groups():
    data = {"sku_units_sold": {"Warna": {"list": [{"source": "Merah"}]}, "Ukuran": {"list": [{"source": "L"}]}}}
    rows = pick(data, "sku_units_sold.*.list")
    assert {(r["_group"], r["source"]) for r in rows} == {("Warna", "Merah"), ("Ukuran", "L")}


def test_view_control_switches_root_and_series_without_sending_param():
    sec = DETAILS["product"].by_key["channel"]
    data = {"channel_distribution": {"gmv": {"list": [1]}, "units_sold": {"list": [2]}}}
    res, calls = _run(sec, {"m": "units_sold"}, data)
    assert res["data"] == [2]
    assert res["layout"]["series"][0]["key"] == "sold_count"
    assert "m" not in calls[0][1] and calls[0][1]["d_type"] == 28


def test_dperiod_custom_range_and_validation():
    sec = DETAILS["product"].by_key["overview"]
    end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    start = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    res, calls = _run(sec, {"d_type": "custom", "start_date": start, "end_date": end}, {"overview": {}})
    p = calls[0][1]
    assert p["start_date"] == start and p["end_date"] == end and "d_type" not in p
    res, calls = _run(sec, {"d_type": "custom", "start_date": "2020-01-01", "end_date": end}, {})
    assert res["status"] == "error" and calls == []


def test_dperiod_also_fills_second_param():
    sec = DETAILS["shop"].by_key["recent"]
    _, calls = _run(sec, {"d_type": "90"}, {})
    assert calls[0][1]["d_type"] == "90" and calls[0][1]["date_type"] == "90"


def test_table_total_from_digit_string_and_pagesize():
    sec = DETAILS["product"].by_key["reviews"]
    res, calls = _run(sec, {}, {"total": "42", "review_list": [{"review_text": "ok"}]})
    assert res["total"] == 42 and res["rows"][0]["review_text"] == "ok"
    assert calls[0][1]["pagesize"] == 10


def test_fetch_option_flattens_tree_and_drops_all():
    data = {"category_info": [{"category_id": "1", "category_name": ["Semua"]},
                              {"category_id": "6", "category_name": ["Buku"],
                               "sub": [{"category_id": "61", "category_name": ["Buku", "Agama"]}]}]}
    stub = StubClient(data)
    old = details.client
    details.client = stub
    try:
        res = asyncio.run(fetch_option("shop", "9", "goodsStats", "ID"))
    finally:
        details.client = old
    cat = res["options"]["category"]
    assert cat == [{"v": "6", "l": "Buku", "sub": [{"v": "61", "l": "Buku › Agama"}]}]
    assert stub.calls[0][1] == {"id": "9", "order": "1,2"}


def test_check_range_limits():
    today = dt.date(2026, 10, 23)
    assert check_range("2026-10-01", "2026-10-22", 180, 1, "", today) == ("2026-10-01", "2026-10-22")
    for bad in (("2026-10-01", "2026-10-23"), ("2026-01-01", "2026-10-22")):
        try:
            check_range(*bad, 180, 1, "", today)
        except ValueError:
            continue
        raise AssertionError(bad)


def test_local_controls_only_in_sync_groups():
    for det in DETAILS.values():
        for s in det.sections:
            for c in s.controls:
                if c.source.startswith("@"):
                    assert c.source[1:] in det.options, (det.kind, s.key, c.source)
