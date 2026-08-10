import { test, expect } from "@playwright/test";
import { createRecruiterProfile, createTalentProfile, login, logout, postCastingCall, registerAndVerify } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("recruiter can message an applicant and send an offer from the board; both signing accepts the application", async ({ page }) => {
  const recruiterEmail = uniqueEmail("board_recruiter");
  const recruiterPassword = "TestPass123!";
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Board Recruiter", role: "recruiter", password: recruiterPassword });
  await createRecruiterProfile(page, { companyName: "Board Studios" });

  const title = `Lead role ${Date.now()}`;
  await postCastingCall(page, { title, description: "Seeking a lead.", category: "acting", roles: [{ title: "Lead" }] });
  await logout(page);

  const talentEmail = uniqueEmail("board_talent");
  const talentPassword = "TestPass123!";
  await registerAndVerify(page, { email: talentEmail, fullName: "Board Talent", role: "talent", password: talentPassword });
  await createTalentProfile(page, { displayName: "Board Talent", category: "acting" });
  // Availability must cover the offer's proposed time window.
  await page.goto("/dashboard");
  await page.getByRole("combobox", { name: "Day" }).selectOption("0");
  await page.getByRole("textbox", { name: "Start time" }).fill("09:00");
  await page.getByRole("textbox", { name: "End time" }).fill("17:00");
  await page.getByRole("button", { name: "Add window" }).click();

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();
  await logout(page);

  await login(page, recruiterEmail, recruiterPassword);
  await page.getByRole("link", { name: "Manage" }).click();
  await expect(page.getByText("Board Talent")).toBeVisible();

  // Search and sort controls are present and usable.
  await page.getByPlaceholder("Search by talent name").fill("Board");
  await expect(page.getByText("Board Talent")).toBeVisible();
  await page.getByPlaceholder("Search by talent name").fill("");

  // Message button starts a conversation and navigates to it.
  await page.getByRole("button", { name: "Message" }).click();
  await expect(page).toHaveURL(/\/messages\//);
  await page.goBack();

  // Send an offer.
  await page.getByRole("button", { name: "Send offer" }).click();
  const nextMonday = new Date();
  nextMonday.setDate(nextMonday.getDate() + ((1 + 7 - nextMonday.getDay()) % 7 || 7));
  const dateStr = nextMonday.toISOString().slice(0, 10);
  await page.locator('input[type="datetime-local"]').first().fill(`${dateStr}T10:00`);
  await page.locator('input[type="datetime-local"]').nth(1).fill(`${dateStr}T11:00`);
  await page.getByRole("button", { name: "Send offer", exact: true }).click();
  await expect(page.getByText("Offer sent — awaiting response")).toBeVisible();
  await logout(page);

  // Talent accepts the booking and signs.
  await login(page, talentEmail, talentPassword);
  await expect(page.getByText("Board Studios", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Accept" }).click();
  await page.getByLabel("Type your full name to sign").fill("Board Talent");
  await page.getByRole("button", { name: "Sign agreement" }).click();
  await expect(page.getByText(/signed/i).first()).toBeVisible();
  await logout(page);

  // Recruiter signs too — application should now be Accepted.
  await login(page, recruiterEmail, recruiterPassword);
  await page.goto("/dashboard");
  await page.getByLabel("Type your full name to sign").fill("Board Recruiter");
  await page.getByRole("button", { name: "Sign agreement" }).click();

  await page.getByRole("link", { name: "Manage" }).click();
  await expect(page.getByText("Accepted · 1")).toBeVisible();
});
