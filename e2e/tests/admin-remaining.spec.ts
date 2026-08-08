import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  logout,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { createAdminAccount, uniqueEmail } from "../helpers/db";

const ADMIN_PASSWORD = "AdminPass123!";

async function loginAsNewAdmin(page: import("@playwright/test").Page, label: string) {
  const email = uniqueEmail(label);
  await createAdminAccount(email, ADMIN_PASSWORD, "E2E Admin");
  await login(page, email, ADMIN_PASSWORD);
  await expect(page).toHaveURL(/\/admin$/);
  return email;
}

test("admin deletes a reported discussion thread from the reports queue", async ({ page }) => {
  const starterEmail = uniqueEmail("modq_starter");
  await registerAndVerify(page, { email: starterEmail, fullName: "ModQ Starter", role: "talent" });
  await createTalentProfile(page, { displayName: "ModQ Starter", category: "acting" });

  await page.goto("/community/discussions/new");
  const subject = `Reportable thread ${Date.now()}`;
  await page.getByLabel("Subject").fill(subject);
  await page.getByLabel("What's on your mind?").fill("This will get reported and removed.");
  await page.getByRole("button", { name: "Post" }).click();
  await expect(page).toHaveURL(/\/community\/discussions\/(?!new)[\w-]+$/);

  const reportDescription = `Testing the moderation delete path ${Date.now()}`;
  // exact:true — the footer also has an unrelated site-wide "Report a problem" bug-report
  // link, which an unscoped substring match on "Report" would ambiguously (and here,
  // apparently non-deterministically) hit instead of the thread's own report button.
  await page.getByRole("button", { name: "Report", exact: true }).click();
  await page.getByPlaceholder("What happened?").fill(reportDescription);
  await page.getByRole("button", { name: "Submit report" }).click();
  await expect(page.getByText("Thanks — our team will review this.")).toBeVisible();
  // The confirmation stays open behind a full-screen backdrop with no explicit close button —
  // click the backdrop corner (outside the centered card, which stops click propagation) to
  // dismiss it, otherwise it keeps intercepting clicks on the rest of the page (e.g. Log out).
  await page.locator(".fixed.inset-0.z-50").click({ position: { x: 5, y: 5 } });
  await logout(page);

  await loginAsNewAdmin(page, "modq_admin");
  await page.goto("/admin/reports");
  const reports = sectionByHeading(page, "Reports");
  // The report row's own "subject" field is just the category label ("Spam", etc.) — the
  // description text (which we set to something unique) is what actually identifies this report.
  const reportRow = reports.locator("li", { hasText: reportDescription });
  await expect(reportRow).toBeVisible();
  await reportRow.getByRole("button", { name: "Delete content" }).click();
  await expect(reportRow.getByText("resolved")).toBeVisible();

  await page.goto("/community/discussions");
  await expect(page.getByText(subject)).not.toBeVisible();
});

test("admin subscriptions panel filters, shows payment history, and runs the dunning sweep", async ({ page }) => {
  const talentEmail = uniqueEmail("adminsub_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "AdminSub Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "AdminSub Talent", category: "acting" });
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
  await logout(page);

  await loginAsNewAdmin(page, "adminsub_admin");
  await page.goto("/admin/subscriptions");
  const panel = sectionByHeading(page, "Subscriptions");

  await page.locator("select").first().selectOption("trialing");
  // Scoped by the unique email, not the shared display name "AdminSub Talent" — that name
  // is reused verbatim by every run of this test and stale e2e_ rows from earlier runs in
  // the same dev DB (only cleared by this whole suite's global teardown) make an unscoped
  // match on the display name ambiguous.
  const row = panel.locator("li", { hasText: talentEmail });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "View payments" }).click();
  // Mock-gateway trial activation records no real payment.
  await expect(row.getByText("No payments recorded yet.")).toBeVisible();

  await panel.getByRole("button", { name: "Run dunning sweep" }).click();
  await expect(panel.getByText(/Checked \d+, applied \d+ transitions?\./)).toBeVisible();
});

test("admin pricing change appends a new entry to price history", async ({ page }) => {
  await loginAsNewAdmin(page, "pricing_history_admin");
  await page.goto("/admin/pricing");

  const talentCard = page.locator("div.rounded-xl").filter({ hasText: "Talent Premium" });
  const currentText = await talentCard.locator("p").nth(1).innerText();
  const currentPrice = Number(currentText.match(/LKR ([\d,]+)/)?.[1].replace(/,/g, ""));
  const newPrice = currentPrice + 111;

  await talentCard.getByLabel("New monthly price (LKR)").fill(String(newPrice));
  await talentCard.getByRole("button", { name: "Update price" }).click();
  await expect(talentCard.getByText(new RegExp(`Currently LKR ${newPrice.toLocaleString()}/mo`))).toBeVisible();

  const history = sectionByHeading(page, "Price history");
  const newestEntry = history.locator("li").first();
  await expect(newestEntry.getByText(`LKR ${newPrice.toLocaleString()}/mo`)).toBeVisible();
  await expect(newestEntry.getByText(/· by /)).toBeVisible();
});
