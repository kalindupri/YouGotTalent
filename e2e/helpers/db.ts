import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

const execFileAsync = promisify(execFile);

// A native Postgres service on this Windows host also listens on 5432, shadowing Docker's
// published port for TCP connections from outside the container. Routing through
// `docker compose exec` instead sidesteps that conflict entirely and reuses the same path
// already proven reliable all session for talking to the dev database.
const REPO_ROOT = path.resolve(__dirname, "..", "..");

export const E2E_EMAIL_PREFIX = "e2e_";

export function uniqueEmail(label: string): string {
  return `${E2E_EMAIL_PREFIX}${label}_${Date.now()}_${Math.floor(Math.random() * 10000)}@example.com`;
}

function sqlLiteral(value: string): string {
  return value.replace(/'/g, "''");
}

async function psql(sql: string): Promise<string> {
  const { stdout } = await execFileAsync(
    "docker",
    ["compose", "exec", "-T", "db", "psql", "-U", "ygt", "-d", "ygt", "-t", "-A", "-c", sql],
    { cwd: REPO_ROOT }
  );
  return stdout.trim();
}

export async function getVerificationCode(email: string): Promise<string> {
  const code = await psql(`SELECT verification_code FROM users WHERE email = '${sqlLiteral(email)}'`);
  if (!code) {
    throw new Error(`No verification code found for ${email}`);
  }
  return code;
}

export async function deleteAllE2EUsers(): Promise<void> {
  await psql(`DELETE FROM users WHERE email LIKE '${E2E_EMAIL_PREFIX}%'`);
}

export async function createAdminAccount(email: string, password: string, fullName: string): Promise<void> {
  // Admin accounts are deliberately never creatable through the public API/UI — this is the
  // one and only path, mirroring exactly how a real operator would provision one.
  await execFileAsync(
    "docker",
    ["compose", "exec", "-T", "backend", "python", "scripts/create_admin.py", email, password, fullName],
    { cwd: REPO_ROOT }
  );
}
