import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  logout,
  openDashboardSection,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("homepage loads with hero and primary navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /every skill/i })).toBeVisible();
  await expect(page.getByRole("link", { name: "Browse talent" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Talent hunts" }).first()).toBeVisible();
});

test("browse talents page filters by category", async ({ page }) => {
  const email = uniqueEmail("nav_talent");
  await registerAndVerify(page, { email, fullName: "Nav Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Nav Talent Unique", category: "photography" });
  await logout(page);

  await page.goto("/talents");
  // The category filter is a checkbox pill group (multi-category support), not a <select>.
  // The checkbox input is display:none (removed from the a11y tree) — the <label> is the
  // real clickable pill, same pattern as the existing instrument filter.
  await page.locator("label").filter({ hasText: "Photography" }).click();
  await expect(page.getByText("Nav Talent Unique")).toBeVisible();

  await page.locator("label").filter({ hasText: "Photography" }).click();
  await page.locator("label").filter({ hasText: "Modeling" }).click();
  await expect(page.getByText("Nav Talent Unique")).not.toBeVisible();
});

test("browse casting calls page loads", async ({ page }) => {
  await page.goto("/casting-calls");
  await expect(page.getByRole("heading", { name: "Talent hunts" })).toBeVisible();
});

test("recruiter can save and unsave a talent", async ({ page }) => {
  const talentEmail = uniqueEmail("save_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Save Target", role: "talent" });
  await createTalentProfile(page, { displayName: "Save Target", category: "dancing" });
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("save_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Save Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Save Studios" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Save talent" }).click();
  await expect(page.getByRole("button", { name: "Saved", exact: true })).toBeVisible();

  await page.goto("/dashboard");
  await openDashboardSection(page, "Discover talent");
  await expect(sectionByHeading(page, "Saved talent").getByText("Save Target")).toBeVisible();

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Saved", exact: true }).click();
  await expect(page.getByRole("button", { name: "Save talent" })).toBeVisible();

  await page.goto("/dashboard");
  await openDashboardSection(page, "Discover talent");
  await expect(sectionByHeading(page, "Saved talent").getByText("Save Target")).not.toBeVisible();
});
