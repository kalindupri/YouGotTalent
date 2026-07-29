def test_view_count_increments_on_view_endpoint(client, recruiter_headers, casting_call):
    resp = client.post(f"/api/v1/casting-calls/{casting_call['id']}/view")
    assert resp.status_code == 204
    resp = client.post(f"/api/v1/casting-calls/{casting_call['id']}/view")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/casting-calls/{casting_call['id']}")
    assert resp.json()["view_count"] == 2


def test_view_unknown_casting_call_404(client):
    resp = client.post("/api/v1/casting-calls/00000000-0000-0000-0000-000000000000/view")
    assert resp.status_code == 404


def test_recruiter_analytics_reflects_views_and_application_breakdown(
    client, recruiter_headers, recruiter_profile, casting_call, talent_headers, talent_profile
):
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/view")
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/view")
    client.post(f"/api/v1/casting-calls/{casting_call['id']}/view")

    role_id = casting_call["roles"][0]["id"]
    application = client.post(
        f"/api/v1/casting-calls/{casting_call['id']}/applications",
        json={"role_id": role_id},
        headers=talent_headers,
    ).json()
    client.patch(
        f"/api/v1/applications/{application['id']}", json={"status": "shortlisted"}, headers=recruiter_headers
    )

    resp = client.get("/api/v1/recruiters/me/analytics", headers=recruiter_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_views"] == 3
    assert body["total_applications"] == 1
    assert body["response_rate"] == 100.0

    call_stats = next(c for c in body["casting_calls"] if c["id"] == casting_call["id"])
    assert call_stats["view_count"] == 3
    assert call_stats["application_count"] == 1
    assert call_stats["shortlisted_count"] == 1
    assert call_stats["pending_count"] == 0


def test_analytics_requires_recruiter_role(client, talent_headers):
    resp = client.get("/api/v1/recruiters/me/analytics", headers=talent_headers)
    assert resp.status_code == 403
