import { test, expect } from "@playwright/test";
import { createTalentProfile, login, logout, registerAndVerify, sectionByHeading } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

async function psql(sql: string): Promise<string> {
  const { execFile } = await import("node:child_process");
  const { promisify } = await import("node:util");
  const path = await import("node:path");
  const execFileAsync = promisify(execFile);
  const repoRoot = path.resolve(__dirname, "..", "..");
  const { stdout } = await execFileAsync("docker", ["compose", "exec", "-T", "db", "psql", "-U", "ygt", "-d", "ygt", "-t", "-A", "-c", sql], {
    cwd: repoRoot,
  });
  return stdout.trim();
}

// Direct DB read for the grandfathered price — the dashboard only shows a subscriber's price
// once billing status leaves "trialing", so asserting the stored price_lkr is the reliable way
// to check grandfathering without waiting out a 90-day trial.
async function getSubscriptionPriceLkr(email: string): Promise<number> {
  const sql = `SELECT s.price_lkr FROM subscriptions s JOIN talent_profiles t ON s.talent_profile_id = t.id JOIN users u ON t.user_id = u.id WHERE u.email = '${email.replace(/'/g, "''")}'`;
  return Number(await psql(sql));
}

// The Cancel/Reactivate flow only renders for status "active"/"past_due" — a freshly started
// trial is "trialing" and has no cancel button at all (by design: nothing has been charged
// yet). Reaching "active" for real means waiting out a 90-day trial, so this simulates what
// trial-expiry reconciliation would eventually do, directly in the DB.
async function forceSubscriptionActive(email: string): Promise<void> {
  // Postgres enum columns store the Python enum member's .name (uppercase), not .value —
  // see the app guide's enum-storage convention.
  const sql = `UPDATE subscriptions SET status = 'ACTIVE', trial_end = NULL, current_period_end = now() + interval '30 days' FROM talent_profiles t, users u WHERE subscriptions.talent_profile_id = t.id AND t.user_id = u.id AND u.email = '${email.replace(/'/g, "''")}'`;
  await psql(sql);
}

test.describe("billing — subscription lifecycle (mock gateway)", () => {
  test("starting a free trial activates Premium and shows the trial end date", async ({ page }) => {
    const email = uniqueEmail("billing_trial");
    await registerAndVerify(page, { email, fullName: "Billing Trial", role: "talent" });
    await createTalentProfile(page, { displayName: "Billing Trial", category: "acting" });

    const membership = sectionByHeading(page, "Membership");
    await membership.getByRole("button", { name: "Start free trial" }).click();
    await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
    await expect(membership.getByText(/Free trial — ends/)).toBeVisible();
  });

  test("cancel flow shows the one-time retention offer, decline it, and schedule cancellation", async ({ page }) => {
    const email = uniqueEmail("billing_cancel");
    await registerAndVerify(page, { email, fullName: "Billing Cancel", role: "talent" });
    await createTalentProfile(page, { displayName: "Billing Cancel", category: "acting" });

    const membership = sectionByHeading(page, "Membership");
    await membership.getByRole("button", { name: "Start free trial" }).click();
    await expect(membership.getByText(/Free trial — ends/)).toBeVisible();

    // Cancel/Reactivate only render once billing status leaves "trialing" — simulate what
    // trial-expiry reconciliation would eventually do rather than waiting out 90 days.
    await forceSubscriptionActive(email);
    await page.reload();
    await expect(membership.getByText(/Renews/)).toBeVisible();

    await membership.getByRole("button", { name: "Cancel subscription" }).click();
    await expect(page.getByRole("heading", { name: "Wait — before you go" })).toBeVisible();
    await page.getByRole("button", { name: "No thanks, cancel" }).click();

    await expect(page.getByRole("heading", { name: "Sorry to see you go" })).toBeVisible();
    await page.getByLabel("Reason").selectOption("not_using_enough");
    await page.getByRole("button", { name: "Confirm cancellation" }).click();

    await expect(page.getByRole("heading", { name: "Cancellation scheduled" })).toBeVisible();
    await page.getByRole("button", { name: "Got it" }).click();
    await expect(membership.getByRole("button", { name: "Reactivate" })).toBeVisible();
  });

  test("accepting the retention offer applies a discount instead of canceling", async ({ page }) => {
    const email = uniqueEmail("billing_retention");
    await registerAndVerify(page, { email, fullName: "Billing Retention", role: "talent" });
    await createTalentProfile(page, { displayName: "Billing Retention", category: "acting" });

    const membership = sectionByHeading(page, "Membership");
    await membership.getByRole("button", { name: "Start free trial" }).click();
    await forceSubscriptionActive(email);
    await page.reload();
    await expect(membership.getByText(/Renews/)).toBeVisible();

    await membership.getByRole("button", { name: "Cancel subscription" }).click();
    await expect(page.getByRole("heading", { name: "Wait — before you go" })).toBeVisible();

    await page.getByRole("button", { name: /Claim \d+% off/ }).click();
    await expect(page.getByRole("heading", { name: "Discount applied!" })).toBeVisible();
    await page.getByRole("button", { name: "Got it" }).click();

    // Still an active subscriber — not scheduled for cancellation.
    await expect(membership.getByRole("button", { name: "Cancel subscription" })).toBeVisible();
    await expect(membership.getByRole("button", { name: "Reactivate" })).not.toBeVisible();
  });

  test("reactivating a canceled-at-period-end subscription restores normal billing", async ({ page }) => {
    const email = uniqueEmail("billing_reactivate");
    await registerAndVerify(page, { email, fullName: "Billing Reactivate", role: "talent" });
    await createTalentProfile(page, { displayName: "Billing Reactivate", category: "acting" });

    const membership = sectionByHeading(page, "Membership");
    await membership.getByRole("button", { name: "Start free trial" }).click();
    await forceSubscriptionActive(email);
    await page.reload();
    await expect(membership.getByText(/Renews/)).toBeVisible();

    await membership.getByRole("button", { name: "Cancel subscription" }).click();
    await page.getByRole("button", { name: "No thanks, cancel" }).click();
    await page.getByRole("button", { name: "Confirm cancellation" }).click();
    await page.getByRole("button", { name: "Got it" }).click();
    await expect(membership.getByRole("button", { name: "Reactivate" })).toBeVisible();

    await membership.getByRole("button", { name: "Reactivate" }).click();
    await expect(membership.getByRole("button", { name: "Cancel subscription" })).toBeVisible();
    await expect(membership.getByRole("button", { name: "Reactivate" })).not.toBeVisible();
  });
});

test.describe("billing — pricing & grandfathering", () => {
  test("public pricing page reflects the current live price", async ({ page }) => {
    await page.goto("/pricing");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    // Sanity check the page actually renders numeric LKR prices, not placeholders.
    await expect(page.getByText(/LKR [\d,]+/).first()).toBeVisible();
  });

  test("an existing subscriber keeps their signed-up price after admin raises it", async ({ page }) => {
    const email = uniqueEmail("billing_grandfather");
    await registerAndVerify(page, { email, fullName: "Grandfather Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Grandfather Talent", category: "acting" });
    await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
    await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();

    const priceBeforeChange = await getSubscriptionPriceLkr(email);
    expect(priceBeforeChange).toBeGreaterThan(0);
    await logout(page);

    const adminEmail = uniqueEmail("billing_grandfather_admin");
    const { createAdminAccount } = await import("../helpers/db");
    await createAdminAccount(adminEmail, "AdminPass123!", "Pricing Admin");
    await login(page, adminEmail, "AdminPass123!");
    await page.goto("/admin/pricing");

    // "div" alone matches every ancestor wrapper too — scope to the tightly-classed plan-card
    // div so the filter lands on the one card, not every containing element up the tree.
    const talentPlanCard = page.locator("div.rounded-xl").filter({ hasText: "Talent Premium" });
    const newPrice = priceBeforeChange + 500;
    await talentPlanCard.getByLabel("New monthly price (LKR)").fill(String(newPrice));
    await talentPlanCard.getByRole("button", { name: "Update price" }).click();
    await expect(talentPlanCard.getByText(new RegExp(`Currently LKR ${newPrice.toLocaleString()}/mo`))).toBeVisible();

    const priceAfterChange = await getSubscriptionPriceLkr(email);
    expect(priceAfterChange).toBe(priceBeforeChange);
    expect(priceAfterChange).not.toBe(newPrice);
  });
});
