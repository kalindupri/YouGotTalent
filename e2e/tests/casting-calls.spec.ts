import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  postCastingCall,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("recruiter posts a multi-role casting call and it appears on the public listing", async ({ page }) => {
  const recruiterEmail = uniqueEmail("cc_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "CC Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "CC Studios" });

  // Multi-role posting is a Premium feature — a free-tier recruiter never sees the
  // "+ Add another role" control, only an upgrade prompt.
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();

  const title = `Multi-role shoot ${Date.now()}`;
  await postCastingCall(page, {
    title,
    description: "Seeking multiple roles for a branded content shoot.",
    category: "modeling",
    roles: [{ title: "Models", criteria: "Female, 18+" }, { title: "Actors", criteria: "Lead, 18+" }],
  });

  await page.goto("/casting-calls");
  const card = page.locator("div.relative.overflow-hidden", { hasText: title });
  await expect(card.getByText("Models")).toBeVisible();
  await expect(card.getByText("Actors")).toBeVisible();

  await page.getByRole("link", { name: title }).click();
  await expect(page.getByRole("heading", { name: "Roles in this project" })).toBeVisible();
  await expect(page.getByText("Female, 18+")).toBeVisible();
});

test("talent applies to a specific role and the recruiter board tags it correctly", async ({ page }) => {
  const recruiterEmail = uniqueEmail("apply_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Apply Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Apply Studios" });

  // Multi-role posting is a Premium feature.
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();

  const title = `Casting for two roles ${Date.now()}`;
  await postCastingCall(page, {
    title,
    description: "Two roles, apply to whichever fits.",
    category: "acting",
    roles: [{ title: "Lead" }, { title: "Supporting" }],
  });

  const manageLink = sectionByHeading(page, "Your talent hunts").getByRole("link", { name: "Manage" }).first();
  const callUrl = await manageLink.getAttribute("href");
  expect(callUrl).toBeTruthy();

  await page.getByRole("button", { name: "Log out" }).click();

  const talentEmail = uniqueEmail("apply_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Apply Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Apply Talent", category: "acting" });

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();

  await page.getByLabel("Role").selectOption({ label: "Supporting" });
  await page.getByLabel("Message to the recruiter (optional)").fill("I would love the supporting role.");
  await page.locator("#apply-section").getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();

  await page.getByRole("button", { name: "Log out" }).click();
  await login(page, recruiterEmail);
  await page.goto(callUrl!);
  await expect(page.getByText("Applied for: Supporting")).toBeVisible();
});

test("open casting call description supports view more / view less", async ({ page }) => {
  const recruiterEmail = uniqueEmail("longdesc_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Long Desc Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Long Desc Studios" });

  const longDescription = "Lorem ipsum dolor sit amet consectetur adipiscing elit. ".repeat(6);
  const title = `Long description job ${Date.now()}`;
  await postCastingCall(page, { title, description: longDescription, category: "acting" });

  await page.goto("/casting-calls");
  const card = page.locator("div.relative.overflow-hidden", { hasText: title });
  await card.getByRole("button", { name: "view more" }).click();
  await expect(card.getByRole("button", { name: "view less" })).toBeVisible();
});
