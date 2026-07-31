import { chromium } from "@playwright/test";
import { mkdirSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, "..", "docs", "screenshots");
mkdirSync(OUT_DIR, { recursive: true });

const BASE_URL = "http://localhost:3001";

// Auth tokens are read from the environment rather than hardcoded — generate short-lived ones
// for whichever seed accounts you want to shoot against, e.g.:
//
//   docker exec yougottalent-backend-1 python -c "
//   from app.db.session import SessionLocal
//   from app.models.user import User
//   from app.core.security import create_access_token
//   db = SessionLocal()
//   for email in ['talent1@example.com', 'recruiter1@example.com', 'admin@yougottalent.lk']:
//       u = db.query(User).filter(User.email == email).first()
//       print(email, create_access_token(str(u.id)))
//   "
//
// then: TALENT_TOKEN=... RECRUITER_TOKEN=... ADMIN_TOKEN=... node capture-screenshots.mjs
const TOKENS = {
  talent: process.env.TALENT_TOKEN,
  recruiter: process.env.RECRUITER_TOKEN,
  admin: process.env.ADMIN_TOKEN,
};

for (const [role, token] of Object.entries(TOKENS)) {
  if (!token) {
    console.error(`Missing ${role.toUpperCase()}_TOKEN env var — see the comment above for how to generate one.`);
    process.exit(1);
  }
}

// These IDs are specific to the dev seed data this was captured against — swap them for
// whatever exists in your own database if the seed data has changed.
const TALENT_PROFILE_ID = "c54bc974-9f2f-4d6e-8e80-468fcfd6875c";
const RECRUITER_PROFILE_ID = "443165e8-731f-4c12-a938-ef41f5f7741e";
const CASTING_CALL_ID = "dc20c661-d0c8-4292-9c54-92a6f80ef4a6";
const TITLE_ID = "43d6614e-54ac-44b9-9646-2c28972104a1";
const THREAD_ID = "58594742-d2e9-47b2-9026-92f57a9a2209";

async function setAuth(page, role) {
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
  await page.evaluate((token) => localStorage.setItem("ygt_token", token), TOKENS[role]);
}

async function shot(page, url, filename) {
  await page.goto(`${BASE_URL}${url}`, { waitUntil: "networkidle" });
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(OUT_DIR, filename), fullPage: false });
  console.log("captured", filename);
}

async function main() {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // ---- Public, logged out ----
  await shot(page, "/", "01-home.png");
  await shot(page, "/talents", "02-browse-talent.png");
  await shot(page, `/talents/${TALENT_PROFILE_ID}`, "03-talent-profile.png");
  await shot(page, `/recruiters/${RECRUITER_PROFILE_ID}`, "04-recruiter-profile.png");
  await shot(page, "/casting-calls", "05-casting-calls.png");
  await shot(page, `/casting-calls/${CASTING_CALL_ID}`, "06-casting-call-detail.png");
  await shot(page, "/login", "07-login.png");
  await shot(page, "/register", "08-register.png");
  await shot(page, "/pricing", "09-pricing.png");
  await shot(page, "/community", "10-community-hub.png");
  await shot(page, "/community/titles", "11-community-titles.png");
  await shot(page, `/community/titles/${TITLE_ID}`, "12-community-title-detail.png");
  await shot(page, "/community/discussions", "13-community-discussions.png");
  await shot(page, `/community/discussions/${THREAD_ID}`, "14-community-discussion-detail.png");

  // ---- Talent, logged in ----
  await setAuth(page, "talent");
  await shot(page, "/dashboard", "15-talent-dashboard.png");
  await shot(page, "/messages", "16-messages.png");

  // ---- Recruiter, logged in ----
  await setAuth(page, "recruiter");
  await shot(page, "/dashboard", "17-recruiter-dashboard.png");
  await shot(page, `/dashboard/casting-calls/${CASTING_CALL_ID}`, "18-applicant-tracking.png");

  // ---- Admin, logged in ----
  await setAuth(page, "admin");
  await shot(page, "/admin", "19-admin-overview.png");
  await shot(page, "/admin/users", "20-admin-users.png");
  await shot(page, "/admin/verification", "21-admin-verification.png");
  await shot(page, "/admin/casting-calls", "22-admin-casting-calls.png");
  await shot(page, "/admin/community", "23-admin-community.png");
  await shot(page, "/admin/reports", "24-admin-reports.png");
  await shot(page, "/admin/subscriptions", "25-admin-subscriptions.png");
  await shot(page, "/admin/pricing", "26-admin-pricing.png");
  await shot(page, "/admin/financial", "27-admin-financial.png");

  await browser.close();
  console.log("done");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
