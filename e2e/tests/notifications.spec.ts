import { test, expect } from "@playwright/test";
import { createRecruiterProfile, createTalentProfile, login, logout, postCastingCall, registerAndVerify } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("recruiter sees a notification bell badge when a talent applies, and can open it", async ({ page }) => {
  const recruiterEmail = uniqueEmail("notif_recruiter");
  const recruiterPassword = "TestPass123!";
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Notif Recruiter", role: "recruiter", password: recruiterPassword });
  await createRecruiterProfile(page, { companyName: "Notif Studios" });

  const title = `Lead role ${Date.now()}`;
  await postCastingCall(page, { title, description: "Seeking a lead.", category: "acting", roles: [{ title: "Lead" }] });
  await logout(page);

  const talentEmail = uniqueEmail("notif_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Notif Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Notif Talent", category: "acting" });

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  // A single-role casting call has no role <select> — just a straight Apply button.
  await page.getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();
  await logout(page);

  await login(page, recruiterEmail, recruiterPassword);
  const bellButton = page.getByRole("button", { name: "Notifications" });
  await expect(bellButton.locator("span")).toHaveText("1");

  await bellButton.click();
  await expect(page.getByText(`New application for ${title}`)).toBeVisible();
  await page.getByText(`New application for ${title}`).click();
  await expect(page).toHaveURL(/\/dashboard\/casting-calls\//);

  // Badge clears once the notification's been opened.
  await expect(bellButton.locator("span")).toHaveCount(0);
});
