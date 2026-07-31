def submit_bug_report(client, headers, *, subject="Something is broken", description="The page crashed when I clicked submit."):
    return client.post(
        "/api/v1/reports",
        json={"category": "bug", "subject": subject, "description": description, "page_url": "/talents/123"},
        headers=headers,
    )


def submit_profile_report(client, headers, target_id):
    return client.post(
        "/api/v1/reports",
        json={
            "category": "fake_profile",
            "target_type": "talent_profile",
            "target_id": str(target_id),
            "subject": "This looks like a fake profile",
            "description": "The photos are stock images.",
        },
        headers=headers,
    )


def test_submit_bug_report(client, talent_headers, talent_profile):
    resp = submit_bug_report(client, talent_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["category"] == "bug"
    assert body["status"] == "open"
    assert body["target_type"] is None


def test_submit_profile_report(client, recruiter_headers, recruiter_profile, talent_profile):
    resp = submit_profile_report(client, recruiter_headers, talent_profile["id"])
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["target_type"] == "talent_profile"
    assert body["target_id"] == talent_profile["id"]


def test_submit_report_requires_auth(client):
    resp = client.post(
        "/api/v1/reports",
        json={"category": "bug", "subject": "x", "description": "y"},
    )
    assert resp.status_code == 401


def test_non_admin_cannot_list_reports(client, talent_headers, talent_profile):
    submit_bug_report(client, talent_headers)
    resp = client.get("/api/v1/admin/reports", headers=talent_headers)
    assert resp.status_code == 403


def test_admin_can_list_and_filter_reports(client, talent_headers, talent_profile, admin_headers):
    submit_bug_report(client, talent_headers, subject="Bug one")
    submit_profile_report(client, talent_headers, talent_profile["id"])

    resp = client.get("/api/v1/admin/reports", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2
    assert all("reporter_email" in r for r in resp.json())

    resp = client.get("/api/v1/admin/reports", params={"category": "bug"}, headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["category"] == "bug"


def test_admin_can_update_report_status(client, talent_headers, talent_profile, admin_headers):
    created = submit_bug_report(client, talent_headers).json()

    resp = client.patch(
        f"/api/v1/admin/reports/{created['id']}",
        json={"status": "resolved", "admin_notes": "Fixed in the next deploy."},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "resolved"
    assert body["admin_notes"] == "Fixed in the next deploy."


def test_update_nonexistent_report_404s(client, admin_headers):
    resp = client.patch(
        "/api/v1/admin/reports/00000000-0000-0000-0000-000000000000",
        json={"status": "resolved"},
        headers=admin_headers,
    )
    assert resp.status_code == 404
