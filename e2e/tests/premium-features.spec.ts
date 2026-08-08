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

async function upgradeToPremium(page: import("@playwright/test").Page) {
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
}

test.describe("premium — work library", () => {
  test("free-tier talent sees an upgrade prompt instead of the library form", async ({ page }) => {
    const email = uniqueEmail("library_free");
    await registerAndVerify(page, { email, fullName: "Library Free", role: "talent" });
    await createTalentProfile(page, { displayName: "Library Free", category: "singing" });

    const section = sectionByHeading(page, "Track library");
    await expect(section.getByText(/is a Premium feature/)).toBeVisible();
    await expect(section.getByRole("button", { name: /Add to track library/ })).not.toBeVisible();
  });

  test("premium talent adds a track via link and deletes it", async ({ page }) => {
    const email = uniqueEmail("library_premium");
    await registerAndVerify(page, { email, fullName: "Library Premium", role: "talent" });
    await createTalentProfile(page, { displayName: "Library Premium", category: "singing" });
    await upgradeToPremium(page);

    const section = sectionByHeading(page, "Track library");
    await section.getByRole("button", { name: "Paste a link" }).click();
    await section.getByLabel("Title").fill("Original demo track");
    await section.getByLabel("URL").fill("https://soundcloud.com/example/demo-track");
    await section.getByRole("button", { name: "Add to track library" }).click();
    await expect(section.getByText("Original demo track")).toBeVisible();

    page.once("dialog", (d) => d.accept());
    await section.getByRole("button", { name: "Delete" }).click();
    await expect(section.getByText("Original demo track")).not.toBeVisible();
  });
});

test.describe("premium — talent CRM (pipeline lists)", () => {
  test("free-tier recruiter sees an upgrade prompt instead of the list builder", async ({ page }) => {
    const email = uniqueEmail("crm_free");
    await registerAndVerify(page, { email, fullName: "CRM Free", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "CRM Free Studios" });

    const section = sectionByHeading(page, "Talent lists");
    await expect(section.getByText(/are a Premium feature/)).toBeVisible();
  });

  test("premium recruiter creates a list, adds a saved talent to it, then removes and deletes", async ({ page }) => {
    const talentEmail = uniqueEmail("crm_target_talent");
    await registerAndVerify(page, { email: talentEmail, fullName: "CRM Target Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "CRM Target Talent", category: "acting" });
    await logout(page);

    const recruiterEmail = uniqueEmail("crm_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "CRM Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "CRM Studios" });
    await upgradeToPremium(page);

    // Save the talent first — only saved talent can be added to a pipeline list.
    await page.goto("/talents");
    await page.getByRole("link", { name: "CRM Target Talent" }).click();
    await page.getByRole("button", { name: "Save talent" }).click();
    await page.goto("/dashboard");

    const listsSection = sectionByHeading(page, "Talent lists");
    const listName = `Pipeline ${Date.now()}`;
    await listsSection.getByPlaceholder(/Monsoon Diaries/).fill(listName);
    await listsSection.getByRole("button", { name: "+ New list" }).click();
    await expect(listsSection.getByText(listName)).toBeVisible();

    const savedSection = sectionByHeading(page, "Saved talent");
    const savedCard = savedSection.locator("div", { hasText: "CRM Target Talent" }).first();
    await savedCard.locator("select").selectOption({ label: listName });

    const listCard = listsSection.locator("div", { hasText: listName }).first();
    await expect(listCard.getByText("CRM Target Talent")).toBeVisible();

    await listCard.getByRole("button", { name: "Remove" }).click();
    await expect(listCard.getByText("CRM Target Talent")).not.toBeVisible();

    await listCard.getByRole("button", { name: "Delete list" }).click();
    await expect(listsSection.getByText(listName)).not.toBeVisible();
  });
});

test.describe("premium — early access & AI match score", () => {
  test("premium recruiter sees a same-category talent under New talent this week", async ({ page }) => {
    const recruiterEmail = uniqueEmail("newarrivals_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "New Arrivals Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "New Arrivals Studios" });
    await upgradeToPremium(page);
    await postCastingCall(page, {
      title: `Early access post ${Date.now()}`,
      description: "Sourcing dancers.",
      category: "dancing",
    });
    await logout(page);

    const talentEmail = uniqueEmail("newarrivals_talent");
    await registerAndVerify(page, { email: talentEmail, fullName: "Fresh Dancer", role: "talent" });
    await createTalentProfile(page, { displayName: "Fresh Dancer", category: "dancing" });
    await logout(page);

    await login(page, recruiterEmail);
    await expect(sectionByHeading(page, "New talent this week").getByText("Fresh Dancer")).toBeVisible();
  });

  test("applicant board shows an AI match score percentage", async ({ page }) => {
    const recruiterEmail = uniqueEmail("aiscore_recruiter");
    await registerAndVerify(page, { email: recruiterEmail, fullName: "AI Score Recruiter", role: "recruiter" });
    await createRecruiterProfile(page, { companyName: "AI Score Studios" });
    // match_score is only computed server-side for Premium recruiters (list_applications_for_
    // casting_call passes score=recruiter.tier=="premium") — free tier always gets null.
    await upgradeToPremium(page);
    const title = `AI scoring role ${Date.now()}`;
    // match_score is only computed when the role has criteria text to compare the applicant
    // against — omitting it (as most other tests do, since they don't need a score) leaves it
    // null and the badge never renders.
    await postCastingCall(page, {
      title,
      description: "Looking for a strong fit.",
      category: "acting",
      roles: [{ title, criteria: "Lead, drama, 5+ years experience" }],
    });
    const manageLink = sectionByHeading(page, "Your talent hunts").getByRole("link", { name: "Manage" }).first();
    const manageUrl = await manageLink.getAttribute("href");
    await logout(page);

    const talentEmail = uniqueEmail("aiscore_talent");
    await registerAndVerify(page, { email: talentEmail, fullName: "AI Score Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "AI Score Talent", category: "acting" });
    await page.goto("/casting-calls");
    await page.getByRole("link", { name: title }).click();
    await page.locator("#apply-section").getByRole("button", { name: "Apply", exact: true }).click();
    await expect(page.getByText("Application submitted.")).toBeVisible();
    await logout(page);

    await login(page, recruiterEmail);
    await page.goto(manageUrl!);
    await expect(page.getByText(/\d+% match/)).toBeVisible();
  });
});
