async def test_health_reports_ok_with_db_state(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] in {"ok", "unreachable"}
    assert isinstance(body["version"], str)
