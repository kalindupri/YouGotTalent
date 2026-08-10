import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  logout,
  openDashboardSection,
  postCastingCall,
  registerAndVerify,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("recruiter can message an applicant and send a contract offer from the board; both signing accepts the application", async ({ page }) => {
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

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();
  await logout(page);

  await login(page, recruiterEmail, recruiterPassword);
  await openDashboardSection(page, "Talent hunts");
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

  // Send offer opens a popup with a rich-text contract editor pre-filled with a branded
  // template — no date/time is required.
  await page.getByRole("button", { name: "Send offer" }).click();
  await expect(page.getByText("Draft contract offer for Board Talent")).toBeVisible();
  await expect(page.locator('[contenteditable="true"]')).toContainText("Parties");
  await page.getByRole("button", { name: "Send offer", exact: true }).click();
  await expect(page.getByText("Offer sent — awaiting response")).toBeVisible();
  await logout(page);

  // Talent accepts the booking, then views the branded agreement and signs it.
  await login(page, talentEmail, talentPassword);
  await openDashboardSection(page, "Bookings");
  await expect(page.getByText("Contract offer")).toBeVisible();
  await page.getByRole("button", { name: "Accept" }).click();
  await page.getByRole("button", { name: "View & sign agreement" }).click();
  await expect(page.getByText("Talent Engagement Agreement")).toBeVisible();
  await page.getByLabel("Type your full name to sign").fill("Board Talent");
  await page.getByRole("button", { name: "Sign agreement", exact: true }).click();
  await expect(page.getByText(/signed/i).first()).toBeVisible();
  await logout(page);

  // Recruiter signs too — application should now be Accepted.
  await login(page, recruiterEmail, recruiterPassword);
  await page.goto("/dashboard");
  await openDashboardSection(page, "Bookings");
  await page.getByRole("button", { name: "View & sign agreement" }).click();
  await page.getByLabel("Type your full name to sign").fill("Board Recruiter");
  await page.getByRole("button", { name: "Sign agreement", exact: true }).click();

  await openDashboardSection(page, "Talent hunts");
  await page.getByRole("link", { name: "Manage" }).click();
  await expect(page.getByText("Accepted · 1")).toBeVisible();
});
