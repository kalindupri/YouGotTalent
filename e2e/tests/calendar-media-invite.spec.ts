import { test, expect } from "@playwright/test";
import path from "node:path";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  logout,
  openDashboardSection,
  postCastingCall,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

async function upgradeToPremium(page: import("@playwright/test").Page) {
  await openDashboardSection(page, "Membership");
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
}

const SAMPLE_VIDEO = path.resolve(__dirname, "..", "fixtures", "sample.mp4");

test.describe("calendar", () => {
  test("talent adds a self-managed calendar entry for today and deletes it", async ({ page }) => {
    const email = uniqueEmail("calendar_talent");
    await registerAndVerify(page, { email, fullName: "Calendar Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Calendar Talent", category: "acting" });

    await openDashboardSection(page, "Bookings");
    const calendar = sectionByHeading(page, "Work calendar");
    const today = new Date().getDate();
    await calendar.getByRole("button", { name: String(today), exact: true }).click();

    const entryTitle = `Wedding shoot ${Date.now()}`;
    // exact:true — the "Show this title to talent hunters…" checkbox label also contains
    // the word "title" and would otherwise ambiguously match too.
    await calendar.getByLabel("Title", { exact: true }).fill(entryTitle);
    await calendar.getByRole("button", { name: "Add entry" }).click();

    // Appears twice — once truncated in the grid cell, once in the entries list below.
    await expect(calendar.getByText(entryTitle).first()).toBeVisible();
    await calendar.getByRole("button", { name: "Remove" }).click();
    await expect(calendar.getByText(entryTitle)).toHaveCount(0);
  });
});

test.describe("media — video quota", () => {
  test("free-tier talent blocked from a 2nd video (FREE_TIER_VIDEO_LIMIT=1)", async ({ page }) => {
    const email = uniqueEmail("video_quota_talent");
    await registerAndVerify(page, { email, fullName: "Video Quota Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Video Quota Talent", category: "acting" });

    await openDashboardSection(page, "Portfolio");
    const section = sectionByHeading(page, "Add an audition");
    await section.getByRole("button", { name: "Video", exact: true }).click();
    await section.locator('input[type="file"]').setInputFiles(SAMPLE_VIDEO);
    await section.getByRole("button", { name: "Add audition" }).click();
    await expect(section.getByText("1/1 audition video")).toBeVisible();

    // Selecting "Video" a second time should now show the limit reached instead of an active form.
    await section.getByRole("button", { name: "Video", exact: true }).click();
    await expect(section.getByRole("button", { name: "Video limit reached" })).toBeVisible();
    await expect(section.getByRole("button", { name: "Video limit reached" })).toBeDisabled();
  });

  test("a non-media file disguised with a video extension is rejected", async ({ page }) => {
    const email = uniqueEmail("bad_upload_talent");
    await registerAndVerify(page, { email, fullName: "Bad Upload Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Bad Upload Talent", category: "acting" });

    await openDashboardSection(page, "Portfolio");
    const section = sectionByHeading(page, "Add an audition");
    await section.getByRole("button", { name: "Video", exact: true }).click();
    await section.locator('input[type="file"]').setInputFiles({
      name: "fake-video.mp4",
      mimeType: "video/mp4",
      buffer: Buffer.from("this is plainly not a real video file"),
    });
    await section.getByRole("button", { name: "Add audition" }).click();
    await expect(section.getByText(/valid video\/audio file/)).toBeVisible();
  });
});

test.describe("invitations — bulk invite", () => {
  test("free-tier recruiter is blocked from inviting more than one talent at once", async ({ page }) => {
    const talentAEmail = uniqueEmail("bulk_free_talentA");
    await registerAndVerify(page, { email: talentAEmail, fullName: "Bulk Free Talent A", role: "talent" });
    await createTalentProfile(page, { displayName: "Bulk Free Talent A", category: "acting" });
    await logout(page);
    const talentBEmail = uniqueEmail("bulk_free_talentB");
    await registerAndVerify(page, { email: talentBEmail, fullName: "Bulk Free Talent B", role: "talent" });
    await createTalentProfile(page, { displayName: "Bulk Free Talent B", category: "acting" });
    await logout(page);

    const recruiterEmail = uniqueEmail("bulk_free_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "Bulk Free Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "Bulk Free Studios" });
    await postCastingCall(page, { title: `Bulk free role ${Date.now()}`, description: "x", category: "acting" });

    await page.goto("/talents");
    const cardA = page.locator("div.relative", { hasText: "Bulk Free Talent A" }).first();
    const cardB = page.locator("div.relative", { hasText: "Bulk Free Talent B" }).first();
    await cardA.locator('input[type="checkbox"]').check();
    await cardB.locator('input[type="checkbox"]').check();
    await expect(page.getByText("2 talent selected")).toBeVisible();

    // Scoped to the sticky bulk-action bar — the page also has an unrelated saved-search filter
    // combobox elsewhere, making an unscoped getByRole("combobox") ambiguous.
    const bulkBar = page.locator("div").filter({ hasText: "talent selected" }).last();
    await bulkBar.getByRole("combobox").selectOption({ index: 1 });
    await bulkBar.getByRole("button", { name: "Send invitations" }).click();
    await expect(page.getByText(/Premium feature/)).toBeVisible();
  });

  test("premium recruiter bulk-invites, skipping an already-invited talent without failing the batch", async ({ page }) => {
    const talentAEmail = uniqueEmail("bulk_premium_talentA");
    await registerAndVerify(page, { email: talentAEmail, fullName: "Bulk Premium Talent A", role: "talent" });
    await createTalentProfile(page, { displayName: "Bulk Premium Talent A", category: "acting" });
    await page.getByRole("link", { name: "View public page" }).click();
    await expect(page).toHaveURL(/\/talents\//);
    const talentAUrl = page.url();
    await logout(page);
    const talentBEmail = uniqueEmail("bulk_premium_talentB");
    await registerAndVerify(page, { email: talentBEmail, fullName: "Bulk Premium Talent B", role: "talent" });
    await createTalentProfile(page, { displayName: "Bulk Premium Talent B", category: "acting" });
    await logout(page);

    const recruiterEmail = uniqueEmail("bulk_premium_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "Bulk Premium Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "Bulk Premium Studios" });
    await upgradeToPremium(page);
    await postCastingCall(page, { title: `Bulk premium role ${Date.now()}`, description: "x", category: "acting" });

    // Directly invite Talent A first, so the bulk batch below has one duplicate to skip.
    await page.goto(talentAUrl);
    await page.getByRole("button", { name: "Invite to a role" }).click();
    await page.getByRole("button", { name: "Send invite" }).click();
    await expect(page.getByText(/Invitation sent/)).toBeVisible();

    await page.goto("/talents");
    const cardA = page.locator("div.relative", { hasText: "Bulk Premium Talent A" }).first();
    const cardB = page.locator("div.relative", { hasText: "Bulk Premium Talent B" }).first();
    await cardA.locator('input[type="checkbox"]').check();
    await cardB.locator('input[type="checkbox"]').check();
    const bulkBar = page.locator("div").filter({ hasText: "talent selected" }).last();
    await bulkBar.getByRole("combobox").selectOption({ index: 1 });
    await bulkBar.getByRole("button", { name: "Send invitations" }).click();

    await expect(page.getByText("Invited 1 talent. 1 already invited or unavailable.")).toBeVisible();
  });
});
