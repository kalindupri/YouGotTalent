import { test, expect } from "@playwright/test";

test("help chat widget answers a quick question and falls back on nonsense", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Open help chat" }).click();
  await expect(page.getByText("Help & support")).toBeVisible();

  await page.getByRole("button", { name: "How do I apply to a casting call?" }).click();
  await expect(page.getByText(/click apply/i)).toBeVisible();

  const input = page.getByPlaceholder("Ask a question…");
  await input.fill("asdkjhasdkjh nonsense gibberish");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText(/couldn't find an answer/i)).toBeVisible();

  await page.getByRole("button", { name: "Minimize help chat" }).click();
  await expect(page.getByText("Help & support")).not.toBeVisible();
});
