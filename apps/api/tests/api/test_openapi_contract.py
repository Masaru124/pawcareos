import json

from app.export_openapi import CONTRACT_PATH, build


def test_committed_openapi_matches_the_application():
    assert CONTRACT_PATH.exists(), "run `uv run python -m app.export_openapi`"
    committed = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert json.loads(build()) == committed, "run `uv run python -m app.export_openapi`"


def test_contract_covers_the_auth_and_patient_routes():
    document = json.loads(build())
    paths = document["paths"]
    assert "/api/v1/health" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/patients/{patient_id}" in paths
