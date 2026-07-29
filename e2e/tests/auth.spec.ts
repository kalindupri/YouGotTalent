import { test, expect } from "@playwright/test";
import { getVerificationCode, uniqueEmail } from "../helpers/db";
import { PASSWORD, login, logout, registerAndVerify } from "../helpers/actions";

test("talent registration requires consent checkbox", async ({ page }) => {
  const email = uniqueEmail("noconsent");
  await page.goto("/register");
  await page.getByLabel("Full name").fill("No Consent");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("You must consent to data processing")).toBeVisible();
});

test("wrong verification code is rejected and can be retried", async ({ page }) => {
  const email = uniqueEmail("wrongcode");
  await page.goto("/register");
  await page.getByRole("button", { name: "talent", exact: true }).click();
  await page.getByLabel("Full name").fill("Wrong Code");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Check your email")).toBeVisible();

  await page.getByLabel("Verification code").fill("000000");
  await page.getByRole("button", { name: "Verify email" }).click();
  await expect(page.getByText(/could not verify|invalid/i)).toBeVisible();

  const code = await getVerificationCode(email);
  await page.getByLabel("Verification code").fill(code);
  await page.getByRole("button", { name: "Verify email" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
});

test("resend code issues a new usable code", async ({ page }) => {
  const email = uniqueEmail("resend");
  await page.goto("/register");
  await page.getByRole("button", { name: "talent", exact: true }).click();
  await page.getByLabel("Full name").fill("Resend Test");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Check your email")).toBeVisible();

  await page.getByRole("button", { name: "Resend code" }).click();
  await expect(page.getByText("Code resent")).toBeVisible();

  const code = await getVerificationCode(email);
  await page.getByLabel("Verification code").fill(code);
  await page.getByRole("button", { name: "Verify email" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
});

test("login is blocked before verification and offers an in-place verify step", async ({ page }) => {
  const email = uniqueEmail("loginblocked");
  await page.goto("/register");
  await page.getByRole("button", { name: "talent", exact: true }).click();
  await page.getByLabel("Full name").fill("Login Blocked");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Check your email")).toBeVisible();

  // Abandon the verify step and try logging in directly instead.
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(PASSWORD);
  await page.getByRole("button", { name: "Log in", exact: true }).click();

  await expect(page.getByText("Verify your email")).toBeVisible();
  const code = await getVerificationCode(email);
  await page.getByLabel("Verification code").fill(code);
  await page.getByRole("button", { name: "Verify email" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
});

test("login with wrong password shows an error", async ({ page }) => {
  const email = uniqueEmail("wrongpass");
  await registerAndVerify(page, { email, fullName: "Wrong Pass", role: "talent" });
  await logout(page);

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("definitely-not-it");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByText(/incorrect email or password/i)).toBeVisible();
});

test("verified user can log out and log back in", async ({ page }) => {
  const email = uniqueEmail("relogin");
  await registerAndVerify(page, { email, fullName: "Relogin User", role: "talent" });
  await logout(page);
  await expect(page).toHaveURL(/\/$|\/login/);

  await login(page, email);
  await expect(page).toHaveURL(/\/dashboard/);
});
