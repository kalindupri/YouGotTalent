import { test, expect } from "@playwright/test";
import {
  createTalentProfile,
  logout,
  openDashboardSection,
  registerAndVerify,
  sectionByHeading,
} from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

async function upgradeToPremium(page: import("@playwright/test").Page) {
  await openDashboardSection(page, "Membership");
  await sectionByHeading(page, "Membership").getByRole("button", { name: "Start free trial" }).click();
  await expect(page.getByText("Premium", { exact: true }).first()).toBeVisible();
}

test("free-tier talent sees the Reels upsell and no add form", async ({ page }) => {
  const email = uniqueEmail("reels_free");
  await registerAndVerify(page, { email, fullName: "Reels Free", role: "talent" });
  await createTalentProfile(page, { displayName: "Reels Free", category: "acting" });

  await openDashboardSection(page, "Portfolio");
  const section = sectionByHeading(page, "Reels");
  await expect(section.getByText(/Premium feature/)).toBeVisible();
  await expect(section.getByRole("button", { name: "Add reel" })).not.toBeVisible();
});

test("premium talent adds a reel and it appears on their public profile", async ({ page }) => {
  const email = uniqueEmail("reels_premium");
  await registerAndVerify(page, { email, fullName: "Reels Premium Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Reels Premium Talent", category: "acting" });
  await upgradeToPremium(page);

  await openDashboardSection(page, "Portfolio");
  const section = sectionByHeading(page, "Reels");
  await section.getByLabel("Reel URL").fill("https://www.tiktok.com/@reels_e2e/video/123");
  await section.getByLabel("Caption (optional)").fill("On set today");
  await section.getByRole("button", { name: "Add reel" }).click();
  await expect(section.getByText("On set today")).toBeVisible();

  await logout(page);
  await page.goto("/talents");
  await page.getByRole("link", { name: /Reels Premium Talent/ }).first().click();
  await expect(page.getByRole("heading", { name: "Reels", exact: true })).toBeVisible();
  await expect(page.getByText("On set today")).toBeVisible();
  await expect(page.getByRole("link", { name: /Watch on TikTok/ })).toBeVisible();
});

test("a real TikTok reel plays in-app on the public profile instead of just linking out", async ({ page }) => {
  const email = uniqueEmail("reels_embed");
  await registerAndVerify(page, { email, fullName: "Reels Embed Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Reels Embed Talent", category: "acting" });
  await upgradeToPremium(page);

  await openDashboardSection(page, "Portfolio");
  const section = sectionByHeading(page, "Reels");
  await section.getByLabel("Reel URL").fill("https://www.tiktok.com/@kalindu.yapa/video/7637017808911568129");
  await section.getByRole("button", { name: "Add reel" }).click();
  await expect(section.getByText("TikTok", { exact: false }).first()).toBeVisible();

  await logout(page);
  await page.goto("/talents");
  await page.getByRole("link", { name: /Reels Embed Talent/ }).first().click();
  await expect(page.locator(".tiktok-embed")).toBeVisible({ timeout: 15000 });
});

test("premium talent gets an error for an unrecognized reel URL", async ({ page }) => {
  const email = uniqueEmail("reels_invalid");
  await registerAndVerify(page, { email, fullName: "Reels Invalid", role: "talent" });
  await createTalentProfile(page, { displayName: "Reels Invalid", category: "acting" });
  await upgradeToPremium(page);

  await openDashboardSection(page, "Portfolio");
  const section = sectionByHeading(page, "Reels");
  await section.getByLabel("Reel URL").fill("https://www.google.com/search?q=hi");
  await section.getByRole("button", { name: "Add reel" }).click();
  await expect(section.getByText(/TikTok, Instagram, or Facebook/)).toBeVisible();
});
