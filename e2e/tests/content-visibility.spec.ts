import { test, expect } from "@playwright/test";
import { createTalentProfile, logout, openDashboardSection, registerAndVerify, sectionByHeading } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test("content visibility tiers are respected by guest, member, and recruiter viewers", async ({ page }) => {
  const talentEmail = uniqueEmail("vis_owner");
  await registerAndVerify(page, { email: talentEmail, fullName: "Visibility Owner", role: "talent" });
  await createTalentProfile(page, { displayName: "Visibility Owner", category: "acting" });

  await openDashboardSection(page, "Portfolio");
  const mediaSection = sectionByHeading(page, "Add an audition");
  await mediaSection.getByLabel("Title").fill("Public Photo");
  await mediaSection.getByLabel("URL").fill("https://example.com/public.jpg");
  await mediaSection.getByLabel("Who can see this").selectOption("public");
  await mediaSection.getByRole("button", { name: "Add audition" }).click();
  await expect(page.getByText("Public Photo")).toBeVisible();

  await mediaSection.getByLabel("Title").fill("Members Photo");
  await mediaSection.getByLabel("URL").fill("https://example.com/members.jpg");
  await mediaSection.getByLabel("Who can see this").selectOption("members");
  await mediaSection.getByRole("button", { name: "Add audition" }).click();
  await expect(page.getByText("Members Photo")).toBeVisible();

  await page.goto("/talents");
  await page.getByRole("link", { name: /Visibility Owner/ }).first().click();
  await page.waitForURL(/\/talents\/[0-9a-f-]+/);
  const profileUrl = page.url();

  await logout(page);
  await page.goto(profileUrl);
  await expect(page.getByAltText("Public Photo")).toBeVisible();
  await expect(page.getByAltText("Members Photo")).not.toBeVisible();

  const memberEmail = uniqueEmail("vis_member");
  await registerAndVerify(page, { email: memberEmail, fullName: "Visibility Member", role: "talent" });
  await createTalentProfile(page, { displayName: "Visibility Member", category: "singing" });
  await page.goto(profileUrl);
  await expect(page.getByAltText("Public Photo")).toBeVisible();
  await expect(page.getByAltText("Members Photo")).toBeVisible();
});
