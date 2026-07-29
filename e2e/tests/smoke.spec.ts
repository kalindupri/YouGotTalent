import { test, expect } from "@playwright/test";
import { registerAndVerify, createTalentProfile, createRecruiterProfile } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("talent can register, verify, and create a profile", async ({ page }) => {
  const email = uniqueEmail("smoke_talent");
  await registerAndVerify(page, { email, fullName: "Smoke Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Smoke Talent", category: "acting" });
  await expect(page.getByText("Smoke Talent")).toBeVisible();
});

test("recruiter can register, verify, and create a profile", async ({ page }) => {
  const email = uniqueEmail("smoke_recruiter");
  await registerAndVerify(page, { email, fullName: "Smoke Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Smoke Studios" });
  await expect(page.getByText("Smoke Studios")).toBeVisible();
});
