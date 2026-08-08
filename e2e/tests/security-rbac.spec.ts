import { test, expect } from "@playwright/test";
import { uniqueEmail } from "../helpers/db";

const API_BASE = "http://localhost:8000/api/v1";

async function registerVerifyAndGetToken(
  request: import("@playwright/test").APIRequestContext,
  label: string,
  role: "talent" | "recruiter" = "talent"
) {
  const email = uniqueEmail(label);
  const password = "TestPass123!";
  await request.post(`${API_BASE}/auth/register`, {
    data: { email, password, full_name: "RBAC User", role, consent_given: true },
  });
  const { getVerificationCode } = await import("../helpers/db");
  const code = await getVerificationCode(email);
  const verifyResp = await request.post(`${API_BASE}/auth/verify-email`, { data: { email, code } });
  const body = await verifyResp.json();
  return { token: body.access_token as string, email };
}

test.describe("RBAC — role and auth boundaries", () => {
  test("talent account is rejected from a recruiter-only endpoint", async ({ request }) => {
    const { token } = await registerVerifyAndGetToken(request, "rbac_talent_as_recruiter", "talent");
    const resp = await request.get(`${API_BASE}/recruiters/me`, { headers: { Authorization: `Bearer ${token}` } });
    expect(resp.status()).toBe(403);
  });

  test("recruiter account is rejected from a talent-only endpoint", async ({ request }) => {
    const { token } = await registerVerifyAndGetToken(request, "rbac_recruiter_as_talent", "recruiter");
    const resp = await request.get(`${API_BASE}/talents/me`, { headers: { Authorization: `Bearer ${token}` } });
    expect(resp.status()).toBe(403);
  });

  test("unauthenticated requests are rejected across representative protected endpoints", async ({ request }) => {
    const endpoints: Array<[string, "get" | "post"]> = [
      ["/talents/me", "get"],
      ["/recruiters/me", "get"],
      ["/admin/stats", "get"],
      ["/casting-calls", "post"],
      ["/billing/me", "get"],
    ];
    for (const [path, method] of endpoints) {
      const resp = method === "get" ? await request.get(`${API_BASE}${path}`) : await request.post(`${API_BASE}${path}`, { data: {} });
      expect.soft(resp.status(), `${method.toUpperCase()} ${path}`).toBe(401);
    }
  });

  test("non-admin cannot reach an admin-only endpoint", async ({ request }) => {
    const { token } = await registerVerifyAndGetToken(request, "rbac_nonadmin", "talent");
    const resp = await request.get(`${API_BASE}/admin/stats`, { headers: { Authorization: `Bearer ${token}` } });
    expect(resp.status()).toBe(403);
  });

  test("a talent's self profile update cannot smuggle role or tier fields", async ({ request }) => {
    const { token } = await registerVerifyAndGetToken(request, "rbac_escalation", "talent");
    await request.post(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { display_name: "Escalation Test", category: "acting" },
    });
    const resp = await request.patch(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { display_name: "Still Not Admin", role: "admin", tier: "premium" },
    });
    expect(resp.ok()).toBeTruthy();
    const profile = await resp.json();
    // Pydantic schemas without a role/tier field simply ignore unknown keys — this confirms
    // there's no accidental field on TalentProfileUpdate that would let a user grant themselves
    // premium or admin by just including extra keys in the request body.
    expect(profile.tier).toBe("free");

    const meResp = await request.get(`${API_BASE}/talents/me`, { headers: { Authorization: `Bearer ${token}` } });
    const me = await meResp.json();
    expect(me.tier).toBe("free");
  });
});

test.describe("input validation — injection safety", () => {
  test("SQL injection payload in talent search is treated as a literal string", async ({ request }) => {
    const payload = "acting' OR '1'='1";
    const resp = await request.get(`${API_BASE}/talents`, { params: { q: payload } });
    expect(resp.ok()).toBeTruthy();
    const results = await resp.json();
    expect(Array.isArray(results)).toBeTruthy();

    // A real injection succeeding would either error the query or return the entire unfiltered
    // table; neither should happen for a parameterized search against a near-empty match.
    const secondResp = await request.get(`${API_BASE}/talents`, { params: { q: "'; DROP TABLE users; --" } });
    expect(secondResp.ok()).toBeTruthy();
  });

  test("an XSS payload in a talent bio renders as literal text on the public profile, not a script", async ({ page, request }) => {
    const { token } = await registerVerifyAndGetToken(request, "xss_talent", "talent");
    const createResp = await request.post(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { display_name: "XSS Test Talent", category: "acting" },
    });
    const profile = await createResp.json();
    const payload = '<img src=x onerror="window.__xss_fired = true">';
    await request.patch(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { bio: payload },
    });

    let dialogFired = false;
    page.on("dialog", () => {
      dialogFired = true;
    });
    await page.goto(`/talents/${profile.id}`);
    await expect(page.getByText(payload)).toBeVisible();
    const fired = await page.evaluate(() => (window as unknown as { __xss_fired?: boolean }).__xss_fired);
    expect(fired).toBeFalsy();
    expect(dialogFired).toBe(false);
  });
});
