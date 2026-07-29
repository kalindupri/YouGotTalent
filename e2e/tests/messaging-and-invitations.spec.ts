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

test("recruiter messages a talent and receives a reply", async ({ page }) => {
  const talentEmail = uniqueEmail("msg_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Msg Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Msg Talent", category: "singing" });
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("msg_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Msg Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Msg Studios" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Message" }).click();
  await expect(page).toHaveURL(/\/messages\//);
  await page.getByPlaceholder("Type a message…").fill("Hi, are you available next week?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Hi, are you available next week?")).toBeVisible();

  await logout(page);
  await login(page, talentEmail);
  await page.goto("/messages");
  await expect(page.getByText("1", { exact: true })).toBeVisible();
  await page.getByText("Msg Studios").click();
  await expect(page.getByText("Hi, are you available next week?")).toBeVisible();

  await page.getByPlaceholder("Type a message…").fill("Yes, I am!");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Yes, I am!")).toBeVisible();

  await logout(page);
  await login(page, recruiterEmail);
  await page.goto("/messages");
  await page.getByText("Msg Talent").click();
  await expect(page.getByText("Yes, I am!")).toBeVisible();
});

test("recruiter invites a talent to a role and the talent accepts", async ({ page }) => {
  const talentEmail = uniqueEmail("invite_talent");
  await registerAndVerify(page, { email: talentEmail, fullName: "Invite Talent", role: "talent" });
  await createTalentProfile(page, { displayName: "Invite Talent", category: "acting" });
  await page.getByRole("link", { name: "View public page" }).click();
  await expect(page).toHaveURL(/\/talents\//);
  const talentProfileUrl = page.url();
  await logout(page);

  const recruiterEmail = uniqueEmail("invite_recruiter");
  await registerAndVerify(page, { email: recruiterEmail, fullName: "Invite Recruiter", role: "recruiter" });
  await createRecruiterProfile(page, { companyName: "Invite Studios" });
  const castingTitle = `Lead role invite test ${Date.now()}`;
  await postCastingCall(page, { title: castingTitle, description: "Looking for a lead.", category: "acting" });

  await page.goto(talentProfileUrl);
  await page.getByRole("button", { name: "Invite to a role" }).click();
  await page.getByLabel("Invite to").selectOption({ label: `${castingTitle} · Acting` });
  await page.getByLabel("Message (optional)").fill("Loved your reel, would you audition?");
  await page.getByRole("button", { name: "Send invite" }).click();
  await expect(page.getByText("Invitation sent")).toBeVisible();

  await logout(page);
  await login(page, talentEmail);
  await page.goto("/dashboard");
  const invitations = sectionByHeading(page, "Invitations");
  await expect(invitations.getByText(castingTitle)).toBeVisible();
  await expect(invitations.getByText("Loved your reel, would you audition?")).toBeVisible();

  await invitations.getByRole("button", { name: "Accept" }).click();
  await expect(invitations.getByText("accepted")).toBeVisible();
});
