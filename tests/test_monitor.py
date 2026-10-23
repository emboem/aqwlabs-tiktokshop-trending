"""Monitor: tambah wajib konfirmasi & tidak pernah diulang; data demo dibuang. FastMoss di-stub."""
import asyncio

from app import monitor
from app.fastmoss.client import FMResult


class Stub:
    def __init__(self, data):
        self.data, self.calls = data, []

    async def get(self, path, params, **kw):
        self.calls.append(("GET", path, params, kw))
        return FMResult(status="ok", data=self.data)

    async def post(self, path, params, body, **kw):
        self.calls.append(("POST", path, body, kw))
        return FMResult(status="ok", data=self.data)


def run(stub, coro_fn):
    old = monitor.client
    monitor.client = stub
    try:
        return asyncio.run(coro_fn())
    finally:
        monitor.client = old


def test_add_requires_confirm_and_no_retry():
    s = Stub({"is_success": 1})
    res = run(s, lambda: monitor.add({"video_id": "123", "hours": 48}, "ID"))
    assert res["status"] == "error" and s.calls == []
    res = run(s, lambda: monitor.add({"video_id": "123", "hours": 48, "confirm": True, "notify_play_count": "1000"}, "ID"))
    assert res["status"] == "ok"
    _, path, body, kw = s.calls[0]
    assert path == "/api/monitor/add" and kw["retries"] == 1
    assert body == {"type": "1", "duration": 172800, "notify_video_count": "", "notify_digg_count": "",
                    "notify_play_count": "1000", "obj_id": "123"}


def test_add_rejects_bad_duration_and_reports_quota():
    s = Stub({"is_success": 0, "status": 2})
    assert run(s, lambda: monitor.add({"video_id": "1", "hours": 5, "confirm": True}, "ID"))["status"] == "error"
    res = run(s, lambda: monitor.add({"video_id": "1", "hours": 24, "confirm": True}, "ID"))
    assert res["status"] == "error" and "Kuota" in res["message"]


def test_history_drops_demo():
    s = Stub({"is_demo": "1", "total": 2, "list": [{"id": 1}]})
    res = run(s, lambda: monitor.history({}, "ID"))
    assert res["rows"] == [] and res["status"] == "ok"
