import { test, expect } from "@playwright/test";
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
import { createAdminAccount, uniqueEmail } from "../helpers/db";

const ADMIN_PASSWORD = "AdminPass123!";

async function loginAsNewAdmin(page: import("@playwright/test").Page, label: string) {
  const email = uniqueEmail(label);
  await createAdminAccount(email, ADMIN_PASSWORD, "E2E Admin");
  await login(page, email, ADMIN_PASSWORD);
  // /dashboard auto-redirects an admin to /admin (Overview) — admin has its own route tree,
  // not a single page, so each test below navigates to the specific /admin/* section it needs.
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  return email;
}

test("admin approves a talent's verification request", async ({ page }) => {
  const talentEmail = uniqueEmail("admin_verify_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Verify Candidate", role: "talent" });
  await createTalentProfile(page, { displayName: "Verify Candidate", category: "acting" });
  // "Request verification" lives under the Membership tab, not the default Profile tab.
  await openDashboardSection(page, "Membership");
  await page.getByRole("button", { name: "Request verification" }).click();
  // "View public page" is back on the Profile tab (ProfileSummary), not Membership.
  await openDashboardSection(page, "Profile");
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  await loginAsNewAdmin(page, "admin_verify");
  await page.goto("/admin/verification");

  const queue = sectionByHeading(page, "Verification requests");
  await expect(queue.getByText("Verify Candidate")).toBeVisible();
  await queue.getByRole("button", { name: "Approve" }).click();
  await expect(queue.getByText("Verify Candidate")).not.toBeVisible();

  await page.goto(talentProfileUrl);
  await expect(page.getByText("Verified")).toBeVisible();
});

test("admin suspends and reactivates a user", async ({ page }) => {
  const talentEmail = uniqueEmail("admin_suspend_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Suspend Candidate", role: "talent" });
  await logout(page);

  await loginAsNewAdmin(page, "admin_suspend");
  await page.goto("/admin/users");

  const users = sectionByHeading(page, "Users");
  await users.getByPlaceholder("Search by name or email").fill(talentEmail);
  const row = users.locator("li", { hasText: talentEmail });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Suspend" }).click();
  await expect(row.getByText("suspended")).toBeVisible();

  await logout(page);
  await page.goto("/login");
  await page.getByLabel("Email").fill(talentEmail);
  await page.getByLabel("Password").fill("TestPass123!");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByText(/suspended/i)).toBeVisible();

  await page.goto("/login");
  const adminEmail = uniqueEmail("admin_suspend_2");
  await createAdminAccount(adminEmail, ADMIN_PASSWORD, "E2E Admin 2");
  await login(page, adminEmail, ADMIN_PASSWORD);
  await page.goto("/admin/users");
  const users2 = sectionByHeading(page, "Users");
  await users2.getByPlaceholder("Search by name or email").fill(talentEmail);
  const row2 = users2.locator("li", { hasText: talentEmail });
  await row2.getByRole("button", { name: "Reactivate" }).click();
  await expect(row2.getByText("active", { exact: true })).toBeVisible();
});

test("admin moderates a casting call", async ({ page }) => {
  const recruiterEmail = uniqueEmail("admin_mod_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Mod Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Mod Studios" });
  const title = `Moderation target ${Date.now()}`;
  await postCastingCall(page, { title, description: "x", category: "acting" });
  await logout(page);

  await loginAsNewAdmin(page, "admin_mod");
  await page.goto("/admin/casting-calls");

  const hunts = sectionByHeading(page, "Talent hunts");
  const row = hunts.locator("li", { hasText: title });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Close" }).click();
  await expect(row.getByText("closed")).toBeVisible();

  await row.getByRole("button", { name: "Reopen" }).click();
  await expect(row.getByText("open", { exact: true })).toBeVisible();
});

test("admin sees full job details including recruiter and application count", async ({ page }) => {
  const recruiterEmail = uniqueEmail("admin_detail_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Detail Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Detail Studios" });
  const title = `Detail target ${Date.now()}`;
  await postCastingCall(page, { title, description: "A very specific job description.", category: "acting" });
  await logout(page);

  const talentEmail = uniqueEmail("admin_detail_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Detail Applicant", role: "talent" });
  await createTalentProfile(page, { displayName: "Detail Applicant", category: "acting" });
  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  await page.locator("#apply-section").getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();
  await logout(page);

  await loginAsNewAdmin(page, "admin_detail");
  await page.goto("/admin/casting-calls");

  const hunts = sectionByHeading(page, "Talent hunts");
  const row = hunts.locator("li", { hasText: title });
  await expect(row.getByText("by Detail Studios")).toBeVisible();
  await expect(row.getByText("1 application")).toBeVisible();

  await row.getByRole("button", { name: "View details" }).click();
  await expect(row.getByText("A very specific job description.")).toBeVisible();
});

test("admin views a user's full account detail", async ({ page }) => {
  const talentEmail = uniqueEmail("admin_account_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Account Detail Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Account Detail Talent", category: "photography", city: "Galle" });
  await logout(page);

  await loginAsNewAdmin(page, "admin_account");
  await page.goto("/admin/users");

  const users = sectionByHeading(page, "Users");
  await users.getByPlaceholder("Search by name or email").fill(talentEmail);
  const row = users.locator("li", { hasText: talentEmail });
  await row.getByRole("button", { name: "View details" }).click();
  await expect(row.getByText("Account Detail Talent · Photography · Galle")).toBeVisible();
});

test("financial overview reflects a talent upgrading to premium", async ({ page }) => {
  const talentEmail = uniqueEmail("admin_fin_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Financial Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Financial Talent", category: "acting" });
  // "Start free trial" lives under the Membership tab, not the default Profile tab.
  await openDashboardSection(page, "Membership");
  // Button text is "Start free trial" (mock gateway activates Premium instantly, no payment) —
  // not "Upgrade to Premium", which is the plan tier's label elsewhere on the page.
  await page.getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
  await logout(page);

  await loginAsNewAdmin(page, "admin_fin");
  await page.goto("/admin/financial");

  const financial = sectionByHeading(page, "Financial overview");
  await expect(financial.getByText("Premium talents")).toBeVisible();
  const premiumTalentsTile = financial.locator("p", { hasText: "Premium talents" }).locator("..");
  await expect(premiumTalentsTile.getByText(/[1-9]\d*/)).toBeVisible();

  await financial.getByLabel("What if: price per premium talent").fill("9999");
  await expect(financial.getByText(/At these prices:/)).toBeVisible();
});
