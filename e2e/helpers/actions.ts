import { Page, expect } from "@playwright/test";
import { getVerificationCode } from "./db";

export const PASSWORD = "TestPass123!";

export async function registerAndVerify(
  page: Page,
  opts: { email: string; fullName: string; role: "talent" | "recruiter"; password?: string }
) {
  const password = opts.password ?? PASSWORD;

  await page.goto("/register");
  await page.getByRole("button", { name: opts.role, exact: true }).click();
  await page.getByLabel("Full name").fill(opts.fullName);
  await page.getByLabel("Email").fill(opts.email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page.getByText("Check your email")).toBeVisible();
  const code = await getVerificationCode(opts.email);
  await page.getByLabel("Verification code").fill(code);
  await page.getByRole("button", { name: "Verify email" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
}

export async function login(page: Page, email: string, password = PASSWORD) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  // Talent/recruiter land on /dashboard; admin redirects straight to /admin and never
  // touches /dashboard at all, so this has to accept either landing page.
  await expect(page).toHaveURL(/\/(dashboard|admin)/);
}

export async function logout(page: Page) {
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page.getByRole("navigation").getByRole("link", { name: "Log in" })).toBeVisible();
}

function categoryLabel(slug: string): string {
  return slug
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

// An ordinary adult. Specs that care about age (guardian consent, minimum working age) pass
// their own dateOfBirth; everything else just needs a profile that isn't a minor's.
export const ADULT_DOB = "1995-06-15";

export async function createTalentProfile(
  page: Page,
  opts: { displayName: string; category?: string; city?: string; bio?: string; dateOfBirth?: string }
) {
  await page.goto("/dashboard");
  await page.getByLabel("Display name").fill(opts.displayName);
  // Required: it decides whether guardian consent is needed and whether paid work is allowed.
  // Three dropdowns rather than a date input -- see components/DateOfBirthInput.tsx.
  const [year, month, day] = (opts.dateOfBirth ?? ADULT_DOB).split("-").map(Number);
  await page.getByLabel("Day", { exact: true }).selectOption(String(day));
  await page.getByLabel("Month", { exact: true }).selectOption(String(month));
  await page.getByLabel("Year", { exact: true }).selectOption(String(year));
  if (opts.category) {
    // Categories are a checkbox group (multi-category support), not a <select> — "acting"
    // defaults checked, so clear it before checking the requested one for a clean single-value state.
    await page.getByRole("checkbox", { name: "Acting" }).uncheck();
    await page.getByRole("checkbox", { name: categoryLabel(opts.category) }).check();
  }
  if (opts.city) {
    await page.getByLabel("City").fill(opts.city);
  }
  if (opts.bio) {
    await page.getByLabel("Bio").fill(opts.bio);
  }
  await page.getByRole("button", { name: "Create profile" }).click();
  // The dashboard's default sidebar tab is "Profile" — after creation the create-form is
  // replaced by the profile summary, which is the reliable signal here (unlike "Membership",
  // which now lives behind a different sidebar tab).
  await expect(page.getByRole("heading", { name: opts.displayName })).toBeVisible();
}

export async function postCastingCall(
  page: Page,
  opts: {
    title: string;
    description: string;
    category?: string;
    roles?: { title: string; criteria?: string }[];
  }
) {
  await page.goto("/dashboard");
  await openDashboardSection(page, "Talent hunts");
  const form = sectionByHeading(page, "Post a talent hunt");
  await form.getByLabel("Title").fill(opts.title);
  if (opts.category) {
    await form.getByLabel("Category").selectOption(opts.category);
  }
  await form.getByLabel("Description").fill(opts.description);

  const extraRoles = (opts.roles ?? []).slice(1);
  const firstRole = opts.roles?.[0];
  if (firstRole?.title) {
    await form.locator('input[placeholder^="Role title"]').first().fill(firstRole.title);
  }
  if (firstRole?.criteria) {
    await form.locator('input[placeholder^="Criteria"]').first().fill(firstRole.criteria);
  }
  for (const role of extraRoles) {
    await form.getByRole("button", { name: "+ Add another role" }).click();
    const roleInputs = form.locator('input[placeholder^="Role title"]');
    await roleInputs.last().fill(role.title);
    if (role.criteria) {
      await form.locator('input[placeholder^="Criteria"]').last().fill(role.criteria);
    }
  }

  await form.getByRole("button", { name: "Post talent hunt" }).click();
  await expect(page.getByText(opts.title).first()).toBeVisible();
}

export function sectionByHeading(page: Page, heading: string) {
  return page.locator("section").filter({ has: page.getByRole("heading", { name: heading, exact: true }) });
}

// The talent/recruiter dashboards use a sidebar that shows one panel of sections at a time —
// call this before interacting with a section that isn't under the sidebar's default tab.
export async function openDashboardSection(page: Page, navLabel: string) {
  await page.getByRole("button", { name: navLabel, exact: true }).click();
}

export async function createRecruiterProfile(page: Page, opts: { companyName: string; industry?: string }) {
  await page.goto("/dashboard");
  await page.getByLabel("Company / agency name").fill(opts.companyName);
  if (opts.industry) {
    await page.getByLabel("Industry").fill(opts.industry);
  }
  await page.getByRole("button", { name: "Create profile" }).click();
  // The dashboard's default sidebar tab is "Overview" — after creation the create-form is
  // replaced by the company header card, which is the reliable signal here ("Post a talent
  // hunt" now lives behind the "Talent hunts" sidebar tab).
  await expect(page.getByRole("heading", { name: opts.companyName })).toBeVisible();
}
