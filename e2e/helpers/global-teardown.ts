import { deleteAllE2EUsers } from "./db";

export default async function globalTeardown() {
  await deleteAllE2EUsers();
}
