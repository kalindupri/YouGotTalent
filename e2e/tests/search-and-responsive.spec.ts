import { test, expect } from "@playwright/test";
import { createTalentProfile, logout, registerAndVerify } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

const API_BASE = "http://localhost:8000/api/v1";

test.describe("talent search — filter combinations", () => {
  test("category and city filters combine with AND semantics", async ({ page }) => {
    const matchEmail = uniqueEmail("search_match");
    await registerAndVerify(page, { email: matchEmail, fullName: "Search Match", role: "talent" });
    await createTalentProfile(page, { displayName: "Search Match Kandy", category: "photography", city: "Kandy" });
    await logout(page);

    const wrongCityEmail = uniqueEmail("search_wrongcity");
    await registerAndVerify(page, { email: wrongCityEmail, fullName: "Search WrongCity", role: "talent" });
    await createTalentProfile(page, { displayName: "Search WrongCity Colombo", category: "photography", city: "Colombo" });
    await logout(page);

    const wrongCategoryEmail = uniqueEmail("search_wrongcat");
    await registerAndVerify(page, { email: wrongCategoryEmail, fullName: "Search WrongCat", role: "talent" });
    await createTalentProfile(page, { displayName: "Search WrongCat Kandy", category: "modeling", city: "Kandy" });
    await logout(page);

    await page.goto("/talents");
    const categorySelect = page.getByRole("combobox").first();
    await categorySelect.selectOption("photography");
    await page.getByPlaceholder("Filter by city").fill("Kandy");

    await expect(page.getByText("Search Match Kandy")).toBeVisible();
    await expect(page.getByText("Search WrongCity Colombo")).not.toBeVisible();
    await expect(page.getByText("Search WrongCat Kandy")).not.toBeVisible();
  });

  test("a filter combination matching nothing shows the empty state, not an error", async ({ page }) => {
    await page.goto("/talents");
    await page.getByPlaceholder("Filter by city").fill(`NoSuchCity${Date.now()}`);
    await expect(page.getByText("No talent profiles match your search yet.")).toBeVisible();
  });

  test("multi-select instrument filter matches ANY selected instrument (OR), not all", async ({ page, request }) => {
    async function registerVerifyAndGetToken(label: string) {
      const email = uniqueEmail(label);
      const password = "TestPass123!";
      await request.post(`${API_BASE}/auth/register`, {
        data: { email, password, full_name: "Instrument Talent", role: "talent", consent_given: true },
      });
      const { getVerificationCode } = await import("../helpers/db");
      const code = await getVerificationCode(email);
      const verifyResp = await request.post(`${API_BASE}/auth/verify-email`, { data: { email, code } });
      return ((await verifyResp.json()) as { access_token: string }).access_token;
    }

    const guitarToken = await registerVerifyAndGetToken("instr_guitar");
    await request.post(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${guitarToken}` },
      data: { display_name: `Guitar Player ${Date.now()}`, category: "music" },
    });
    await request.patch(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${guitarToken}` },
      data: { instruments: ["guitar"] },
    });
    const guitarProfile = await (
      await request.get(`${API_BASE}/talents/me`, { headers: { Authorization: `Bearer ${guitarToken}` } })
    ).json();

    const drumsToken = await registerVerifyAndGetToken("instr_drums");
    await request.post(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${drumsToken}` },
      data: { display_name: `Drums Player ${Date.now()}`, category: "music" },
    });
    await request.patch(`${API_BASE}/talents/me`, {
      headers: { Authorization: `Bearer ${drumsToken}` },
      data: { instruments: ["drums"] },
    });
    const drumsProfile = await (
      await request.get(`${API_BASE}/talents/me`, { headers: { Authorization: `Bearer ${drumsToken}` } })
    ).json();

    // Selecting guitar+drums together should return both players (union), not their
    // intersection — confirms the backend's array-overlap ("&&") OR semantics from the UI.
    // Playwright's `params` option comma-joins array values, but FastAPI's `Query(list[str])`
    // needs the key repeated instead — build the query string by hand to get that.
    const bothResp = await request.get(`${API_BASE}/talents?instruments=guitar&instruments=drums`);
    const bothIds = (await bothResp.json()).map((t: { id: string }) => t.id);
    expect(bothIds).toContain(guitarProfile.id);
    expect(bothIds).toContain(drumsProfile.id);

    const guitarOnlyResp = await request.get(`${API_BASE}/talents?instruments=guitar`);
    const guitarOnlyIds = (await guitarOnlyResp.json()).map((t: { id: string }) => t.id);
    expect(guitarOnlyIds).toContain(guitarProfile.id);
    expect(guitarOnlyIds).not.toContain(drumsProfile.id);
  });
});

test.describe("responsive", () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test("homepage and talent browse stay usable at mobile width", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /every skill/i })).toBeVisible();
    const bodyOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(bodyOverflow).toBe(false);

    await page.goto("/talents");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const talentsOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(talentsOverflow).toBe(false);
  });
});
