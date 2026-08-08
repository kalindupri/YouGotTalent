import { test, expect } from "@playwright/test";
import { createTalentProfile, registerAndVerify, sectionByHeading } from "../helpers/actions";
import { uniqueEmail } from "../helpers/db";

test.describe("talent dashboard", () => {
  test.beforeEach(async ({ page }) => {
    const email = uniqueEmail("dash_talent");
    await registerAndVerify(page, { email, fullName: "Dash Talent", role: "talent" });
    await createTalentProfile(page, { displayName: "Dash Talent", category: "singing" });
  });

  test("edit profile bio and city", async ({ page }) => {
    // ProfileSummary is the first card on the page, so its "Edit" button is the first match.
    await page.getByRole("button", { name: "Edit", exact: true }).first().click();
    await page.getByLabel("Bio").fill("Playback vocalist from Kandy.");
    await page.getByLabel("City").fill("Kandy");
    await page.getByRole("button", { name: "Save", exact: true }).click();

    await expect(page.getByText("Playback vocalist from Kandy.")).toBeVisible();
    await expect(page.getByText("Kandy")).toBeVisible();
  });

  test("toggle job alert notification preference", async ({ page }) => {
    const section = sectionByHeading(page, "Notifications");
    const checkbox = section.getByRole("checkbox");
    await expect(checkbox).toBeChecked();
    await checkbox.click();
    await expect(checkbox).not.toBeChecked();

    await page.reload();
    await expect(sectionByHeading(page, "Notifications").getByRole("checkbox")).not.toBeChecked();
  });

  test("add an intro video and see it embedded on the public profile", async ({ page }) => {
    const section = sectionByHeading(page, "Intro video");
    await section.getByRole("button", { name: "Add" }).click();
    // The form now offers "Upload a file" / "Paste a link" first (upload is the default) —
    // the URL field only renders after choosing "Paste a link".
    await section.getByRole("button", { name: "Paste a link" }).click();
    await page.getByLabel("Video URL").fill("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
    await page.getByRole("button", { name: "Save intro video" }).click();
    await expect(section.getByRole("button", { name: "Edit" })).toBeVisible();

    await page.getByRole("link", { name: "View public page" }).click();
    await expect(page.locator("iframe")).toHaveAttribute("src", /youtube\.com\/embed\/dQw4w9WgXcQ/);
  });

  test("add and delete a credit", async ({ page }) => {
    const section = sectionByHeading(page, "Credits & experience");
    await section.getByRole("button", { name: "+ Add credit" }).click();
    await page.getByLabel("Project title").fill("Teledrama pilot script");
    await page.getByLabel("Your role").fill("Lead vocalist");
    await section.getByRole("button", { name: "Add credit" }).click();

    await expect(page.getByText("Teledrama pilot script")).toBeVisible();

    await page.getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("Teledrama pilot script")).not.toBeVisible();
    await expect(page.getByText("No credits added yet.")).toBeVisible();
  });

  test("add media respects the free-tier portfolio limit", async ({ page }) => {
    const section = sectionByHeading(page, "Add an audition");
    for (let i = 0; i < 3; i++) {
      await section.getByLabel("URL").fill(`https://example.com/photo-${i}.jpg`);
      await section.getByRole("button", { name: "Photo", exact: true }).click();
      await section.getByRole("button", { name: "Add audition" }).click();
      await expect(section.getByLabel("URL")).toHaveValue("");
    }

    await section.getByLabel("URL").fill("https://example.com/photo-4th.jpg");
    await section.getByRole("button", { name: "Add audition" }).click();
    // Scoped to this section — the page now also has unrelated Premium upsell copy elsewhere
    // (profile views, work library), so an unscoped /premium/i match is ambiguous.
    await expect(section.getByText(/premium/i)).toBeVisible();
  });

  test("public profile reflects display name and category", async ({ page }) => {
    await page.getByRole("link", { name: "View public page" }).click();
    await expect(page.getByRole("heading", { name: "Dash Talent" })).toBeVisible();
    await expect(page.getByText("Singing", { exact: true })).toBeVisible();
  });
});
