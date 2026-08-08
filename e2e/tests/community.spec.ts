import { test, expect, Page } from "@playwright/test";
import { createTalentProfile, createRecruiterProfile, login, logout, registerAndVerify } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

// Titles/discussions have no accessible name on the star-rating icons or on "Edit"/"Delete"
// buttons beyond their visible text, and delete actions go through window.confirm — every
// test that deletes something must accept that native dialog before the click resolves.
function acceptNextDialog(page: Page) {
  page.once("dialog", (d) => d.accept());
}

// "/community/titles/new" itself matches a loose /\/community\/titles\/.+/ pattern, so a
// regex used to assert "navigated to the new title's detail page" must explicitly exclude it
// — otherwise the assertion can pass while still sitting on the empty creation form.
const TITLE_DETAIL_URL = /\/community\/titles\/(?!new)[\w-]+$/;
const DISCUSSION_DETAIL_URL = /\/community\/discussions\/(?!new)[\w-]+$/;

test.describe("community — titles", () => {
  test("any logged-in role can add a title, rate it, and see the average update", async ({ page }) => {
    const talentEmail = uniqueEmail("title_talent");
    await registerAndVerify(page, { email: talentEmail, fullName: "Title Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Title Talent", category: "acting" });

    await page.goto("/community/titles/new");
    const name = `Test Film ${Date.now()}`;
    await page.getByLabel("Name").fill(name);
    await page.getByLabel("Type").selectOption("film");
    await page.getByLabel("Synopsis").fill("A film added for E2E coverage.");
    await page.getByRole("button", { name: "Add title" }).click();
    await expect(page).toHaveURL(TITLE_DETAIL_URL);
    await expect(page.getByRole("heading", { name })).toBeVisible();

    // Rate it 5 stars — the picker is 5 icon-only buttons inside the "Rate this" form.
    const rateForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Submit review" }) });
    await rateForm.locator("button").nth(4).click();
    await rateForm.locator("textarea").fill("Loved it.");
    await rateForm.getByRole("button", { name: "Submit review" }).click();
    await expect(page.getByText("Update review")).toBeVisible();
    await expect(page.getByText("Critiques (1)")).toBeVisible();

    await page.goto("/community/titles");
    await expect(page.getByText(name)).toBeVisible();
  });

  test("title appears in the catalog and is viewable by a guest with no login", async ({ page }) => {
    const recruiterEmail = uniqueEmail("title_guest_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "Title Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "Title Studios" });

    await page.goto("/community/titles/new");
    const name = `Guest Visible Film ${Date.now()}`;
    await page.getByLabel("Name").fill(name);
    await page.getByRole("button", { name: "Add title" }).click();
    await expect(page).toHaveURL(TITLE_DETAIL_URL);
    const url = page.url();
    await logout(page);

    await page.goto(url);
    await expect(page.getByRole("heading", { name })).toBeVisible();
    // Scoped to <main> — the header nav has its own "Log in" link too.
    await expect(page.locator("main").getByRole("link", { name: "Log in", exact: true })).toBeVisible();
  });

  test("owner edits and deletes their own title and review", async ({ page }) => {
    const email = uniqueEmail("title_owner");
    await registerAndVerify(page, { email, fullName: "Title Owner", role: "talent" });
    await createTalentProfile(page, { displayName: "Title Owner", category: "acting" });

    await page.goto("/community/titles/new");
    const name = `Owned Film ${Date.now()}`;
    await page.getByLabel("Name").fill(name);
    await page.getByRole("button", { name: "Add title" }).click();
    await expect(page).toHaveURL(TITLE_DETAIL_URL);

    await page.getByRole("button", { name: "Edit", exact: true }).click();
    const renamed = `${name} (edited)`;
    await page.getByLabel("Name").fill(renamed);
    await page.getByRole("button", { name: "Save changes" }).click();
    await expect(page.getByRole("heading", { name: renamed })).toBeVisible();

    const rateForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Submit review" }) });
    await rateForm.locator("button").nth(2).click();
    await rateForm.getByRole("button", { name: "Submit review" }).click();
    await expect(page.getByRole("button", { name: "Delete my review" })).toBeVisible();
    // No confirm() dialog on this one — only the title/thread delete below has one.
    await page.getByRole("button", { name: "Delete my review" }).click();
    await expect(page.getByRole("button", { name: "Submit review" })).toBeVisible();

    acceptNextDialog(page);
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(page).toHaveURL(/\/community\/titles$/);
    await expect(page.getByText(renamed)).not.toBeVisible();
  });
});

test.describe("community — discussions", () => {
  test("any logged-in role starts a thread and another role replies", async ({ page, browser }) => {
    const starterEmail = uniqueEmail("disc_starter");
    await registerAndVerify(page, { email: starterEmail, fullName: "Disc Starter", role: "talent" });
    await createTalentProfile(page, { displayName: "Disc Starter", category: "acting" });

    await page.goto("/community/discussions/new");
    const subject = `Test thread ${Date.now()}`;
    await page.getByLabel("Subject").fill(subject);
    await page.getByLabel("What's on your mind?").fill("Kicking off an E2E discussion thread.");
    await page.getByRole("button", { name: "Post" }).click();
    await expect(page).toHaveURL(DISCUSSION_DETAIL_URL);
    const threadUrl = page.url();

    const replierContext = await browser.newContext();
    const replierPage = await replierContext.newPage();
    const replierEmail = uniqueEmail("disc_replier");
    await registerAndVerify(replierPage, { email: replierEmail, fullName: "Disc Replier", role: "recruiter" });
    await createRecruiterProfile(replierPage, { companyName: "Disc Studios" });
    await replierPage.goto(threadUrl);
    await replierPage.getByPlaceholder("Add to the discussion...").fill("Great topic, replying in.");
    await replierPage.getByRole("button", { name: "Reply", exact: true }).click();
    await expect(replierPage.getByText("Great topic, replying in.")).toBeVisible();
    await replierContext.close();

    await page.reload();
    await expect(page.getByText("Great topic, replying in.")).toBeVisible();
  });

  test("thread owner edits and deletes their own thread", async ({ page }) => {
    const email = uniqueEmail("disc_owner");
    await registerAndVerify(page, { email, fullName: "Disc Owner", role: "talent" });
    await createTalentProfile(page, { displayName: "Disc Owner", category: "acting" });

    await page.goto("/community/discussions/new");
    const subject = `Owned thread ${Date.now()}`;
    await page.getByLabel("Subject").fill(subject);
    await page.getByLabel("What's on your mind?").fill("Original body.");
    await page.getByRole("button", { name: "Post" }).click();
    await expect(page).toHaveURL(DISCUSSION_DETAIL_URL);

    await page.getByRole("button", { name: "Edit", exact: true }).click();
    const renamed = `${subject} (edited)`;
    // The thread edit form's subject/body fields have no accessible label — target them
    // structurally within the form that contains the "Save changes" button.
    const editForm = page.locator("form").filter({ has: page.getByRole("button", { name: "Save changes" }) });
    await editForm.locator("input").fill(renamed);
    await editForm.getByRole("button", { name: "Save changes" }).click();
    await expect(page.getByRole("heading", { name: renamed })).toBeVisible();

    acceptNextDialog(page);
    await page.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(page).toHaveURL(/\/community\/discussions$/);
    await expect(page.getByText(renamed)).not.toBeVisible();
  });
});

test.describe("community — ownership (direct API)", () => {
  const API_BASE = "http://localhost:8000/api/v1";

  async function registerVerifyAndGetToken(request: import("@playwright/test").APIRequestContext, label: string) {
    const email = uniqueEmail(label);
    const password = "TestPass123!";
    await request.post(`${API_BASE}/auth/register`, {
      data: { email, password, full_name: "API User", role: "talent", consent_given: true },
    });
    // The UI flow reads the code from the DB via helpers/db.ts; direct-API tests reuse it too.
    const { getVerificationCode } = await import("../helpers/db");
    const code = await getVerificationCode(email);
    const verifyResp = await request.post(`${API_BASE}/auth/verify-email`, { data: { email, code } });
    const { access_token } = await verifyResp.json();
    return access_token as string;
  }

  test("cannot delete another user's title via direct API call", async ({ request }) => {
    const ownerToken = await registerVerifyAndGetToken(request, "own_title_api");
    const createResp = await request.post(`${API_BASE}/titles`, {
      headers: { Authorization: `Bearer ${ownerToken}` },
      data: { name: `API-owned title ${Date.now()}`, work_type: "film" },
    });
    expect(createResp.ok()).toBeTruthy();
    const title = await createResp.json();

    const otherToken = await registerVerifyAndGetToken(request, "other_title_api");
    const deleteResp = await request.delete(`${API_BASE}/titles/${title.id}`, {
      headers: { Authorization: `Bearer ${otherToken}` },
    });
    expect(deleteResp.status()).toBeGreaterThanOrEqual(400);
    expect(deleteResp.status()).toBeLessThan(500);

    const getResp = await request.get(`${API_BASE}/titles/${title.id}`);
    expect(getResp.ok()).toBeTruthy();
  });

  test("cannot delete another user's discussion thread via direct API call", async ({ request }) => {
    const ownerToken = await registerVerifyAndGetToken(request, "own_thread_api");
    const createResp = await request.post(`${API_BASE}/discussions`, {
      headers: { Authorization: `Bearer ${ownerToken}` },
      data: { category: "general", subject: `API-owned thread ${Date.now()}`, body: "body" },
    });
    expect(createResp.ok()).toBeTruthy();
    const thread = await createResp.json();

    const otherToken = await registerVerifyAndGetToken(request, "other_thread_api");
    const deleteResp = await request.delete(`${API_BASE}/discussions/${thread.id}`, {
      headers: { Authorization: `Bearer ${otherToken}` },
    });
    expect(deleteResp.status()).toBeGreaterThanOrEqual(400);
    expect(deleteResp.status()).toBeLessThan(500);
  });
});
