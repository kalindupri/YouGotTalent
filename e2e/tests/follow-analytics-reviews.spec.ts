import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  logout,
  postCastingCall,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("talent follows a recruiter from a casting call and sees them in Following", async ({ page }) => {
  const recruiterEmail = uniqueEmail("follow_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Follow Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Follow Studios" });
  const title = `Follow target ${Date.now()}`;
  await postCastingCall(page, { title, description: "x", category: "acting" });
  await logout(page);

  const talentEmail = uniqueEmail("follow_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Follow Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Follow Talent", category: "acting" });

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("button", { name: "Follow", exact: true }).click();
  await expect(page.getByRole("button", { name: "Following", exact: true })).toBeVisible();

  await page.goto("/dashboard");
  const following = sectionByHeading(page, "Following");
  await expect(following.getByText("Follow Studios")).toBeVisible();

  await following.getByRole("button", { name: "Unfollow" }).click();
  await expect(following.getByText("Follow Studios")).not.toBeVisible();
});

test("recruiter analytics reflect casting call views and applications", async ({ page }) => {
  const recruiterEmail = uniqueEmail("analytics_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Analytics Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Analytics Studios" });
  const title = `Analytics target ${Date.now()}`;
  await postCastingCall(page, { title, description: "x", category: "acting" });

  await expect(sectionByHeading(page, "Analytics").getByText("Total views")).toBeVisible();
  await logout(page);

  await page.goto("/casting-calls");
  await page.getByRole("link", { name: title }).click();
  await expect(page).toHaveURL(/\/casting-calls\/[0-9a-f-]+$/);
  const castingCallUrl = page.url();

  const talentEmail = uniqueEmail("analytics_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Analytics Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Analytics Talent", category: "acting" });
  await page.goto(castingCallUrl);
  await page.locator("#apply-section").getByRole("button", { name: "Apply", exact: true }).click();
  await expect(page.getByText("Application submitted.")).toBeVisible();
  await logout(page);

  await login(page, recruiterEmail);
  const analytics2 = sectionByHeading(page, "Analytics");
  await expect(analytics2.getByText("1 applications")).toBeVisible();
  await expect(analytics2.getByText("1 pending")).toBeVisible();
});

test("recruiter and talent leave reviews after an accepted booking", async ({ page }) => {
  const talentEmail = uniqueEmail("review_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Review Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Review Talent", category: "acting" });

  const availability = sectionByHeading(page, "Availability");
  await availability.getByLabel("Day").selectOption("0");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("17:00");
  await availability.getByRole("button", { name: "Add window" }).click();
  await expect(availability.locator("li", { hasText: "Monday" })).toBeVisible();

  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("review_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Review Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Review Studios" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Request a booking" }).click();

  const now = new Date();
  const currentDow = (now.getDay() + 6) % 7;
  const daysAhead = ((0 - currentDow + 7) % 7) || 7;
  const monday = new Date(now);
  monday.setDate(now.getDate() + daysAhead);
  const dateStr = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, "0")}-${String(monday.getDate()).padStart(2, "0")}`;

  await page.getByLabel("Date").fill(dateStr);
  await page.getByLabel("Start").fill("10:00");
  await page.getByLabel("End").fill("11:00");
  await page.getByRole("button", { name: "Send request" }).click();
  await expect(page.getByText("Request sent")).toBeVisible();

  await logout(page);
  await login(page, talentEmail);
  const talentBookings = sectionByHeading(page, "Booking requests");
  await talentBookings.getByRole("button", { name: "Accept" }).click();
  await expect(talentBookings.getByText("accepted")).toBeVisible();

  await talentBookings.getByRole("button", { name: "5 stars" }).click();
  await talentBookings.getByRole("button", { name: "Submit review" }).click();
  await expect(talentBookings.getByText("Thanks for your review!")).toBeVisible();

  await logout(page);
  await login(page, recruiterEmail);
  const recruiterBookings = sectionByHeading(page, "My booking requests");
  await recruiterBookings.getByRole("button", { name: "4 stars" }).click();
  await recruiterBookings.getByRole("button", { name: "Submit review" }).click();
  await expect(recruiterBookings.getByText("Thanks for your review!")).toBeVisible();

  const reviewsReceived = sectionByHeading(page, "Reviews received");
  await expect(reviewsReceived.getByText("Review Talent")).toBeVisible();

  await page.goto(talentProfileUrl);
  await expect(page.getByText("Review Studios")).toBeVisible();
});
