import { test, expect } from "@playwright/test";
import {
  createRecruiterProfile,
  createTalentProfile,
  login,
  logout,
  openDashboardSection,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

function formatDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// 0=Monday .. 6=Sunday, matching AvailabilityWindow.day_of_week
function nextWeekdayDate(targetDow: number): string {
  const now = new Date();
  const currentDow = (now.getDay() + 6) % 7;
  const daysAhead = ((targetDow - currentDow + 7) % 7) || 7;
  const target = new Date(now);
  target.setDate(now.getDate() + daysAhead);
  return formatDateLocal(target);
}

test("talent sets availability, recruiter books a slot, talent accepts, and agreement gets marked signed", async ({ page }) => {
  const talentEmail = uniqueEmail("booking_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Booking Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Booking Talent", category: "acting" });

  await openDashboardSection(page, "Bookings");
  const availability = sectionByHeading(page, "Availability");
  await availability.getByLabel("Day").selectOption("0");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("17:00");
  await availability.getByRole("button", { name: "Add window" }).click();
  await expect(availability.locator("li", { hasText: "Monday" })).toBeVisible();

  await openDashboardSection(page, "Profile");
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("booking_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Booking Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Booking Studios" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Request a booking" }).click();
  await expect(page.getByText("Monday: 9:00 AM")).toBeVisible();

  const monday = nextWeekdayDate(0);
  await page.getByLabel("Date").fill(monday);
  await page.getByLabel("Start").fill("10:00");
  await page.getByLabel("End").fill("11:00");
  await page.getByRole("button", { name: "Send request" }).click();
  await expect(page.getByText("Request sent")).toBeVisible();

  await logout(page);
  await login(page, recruiterEmail);
  await openDashboardSection(page, "Bookings");
  const recruiterBookings = sectionByHeading(page, "My booking requests");
  await expect(recruiterBookings.getByText("Booking Talent")).toBeVisible();
  await expect(recruiterBookings.getByText(/10:00/)).toBeVisible();
  await expect(recruiterBookings.getByText(/11:00/)).toBeVisible();
  await expect(recruiterBookings.getByText("pending")).toBeVisible();

  await logout(page);
  await login(page, talentEmail);
  await openDashboardSection(page, "Bookings");
  const talentBookings = sectionByHeading(page, "Booking requests");
  await expect(talentBookings.getByText("Booking Studios")).toBeVisible();
  await talentBookings.getByRole("button", { name: "Accept" }).click();
  await expect(talentBookings.getByText("accepted")).toBeVisible();

  // In-app e-signature: each party types their full legal name and submits — there is no
  // separate "mark as signed" toggle. "Agreement signed by both parties" only appears once
  // both sides have done this; after just one party, the UI shows "You signed as ...".
  await talentBookings.getByLabel("Type your full name to sign").fill("Booking Talent");
  await talentBookings.getByRole("button", { name: "Sign agreement" }).click();
  await expect(talentBookings.getByText("You signed as Booking Talent")).toBeVisible();

  await logout(page);
  await login(page, recruiterEmail);
  await openDashboardSection(page, "Bookings");
  const recruiterBookings2 = sectionByHeading(page, "My booking requests");
  await recruiterBookings2.getByLabel("Type your full name to sign").fill("Booking Studios");
  await recruiterBookings2.getByRole("button", { name: "Sign agreement" }).click();
  await expect(recruiterBookings2.getByText("Agreement signed by both parties")).toBeVisible();
});

test("booking request outside availability is rejected", async ({ page }) => {
  const talentEmail = uniqueEmail("booking_outside_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Outside Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Outside Talent", category: "acting" });

  await openDashboardSection(page, "Bookings");
  const availability = sectionByHeading(page, "Availability");
  await availability.getByLabel("Day").selectOption("0");
  await availability.getByLabel("Start time").fill("09:00");
  await availability.getByLabel("End time").fill("17:00");
  await availability.getByRole("button", { name: "Add window" }).click();
  await expect(availability.locator("li", { hasText: "Monday" })).toBeVisible();

  await openDashboardSection(page, "Profile");
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("booking_outside_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Outside Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Outside Studios" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Request a booking" }).click();

  const monday = nextWeekdayDate(0);
  await page.getByLabel("Date").fill(monday);
  await page.getByLabel("Start").fill("20:00");
  await page.getByLabel("End").fill("21:00");
  await page.getByRole("button", { name: "Send request" }).click();
  await expect(page.getByText("outside this talent's availability")).toBeVisible();
});
