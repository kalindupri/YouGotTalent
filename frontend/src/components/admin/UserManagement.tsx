"use client";

import { useEffect, useState } from "react";
import { AdminUserDetail, User, UserRole, api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { badgeClass, btnSmall, btnSmallPrimary, formatCategory, inputClass, sectionClass } from "@/lib/ui";

export default function UserManagement() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [role, setRole] = useState<UserRole | "">("");
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    const handle = setTimeout(() => {
      api.adminListUsers({ role: role || undefined, q: q || undefined }, token).then(setUsers).catch(() => {});
    }, 250);
    return () => clearTimeout(handle);
  }, [role, q, token]);

  async function toggleActive(user: User) {
    if (!token) return;
    setBusyId(user.id);
    try {
      const updated = await api.adminSetUserActive(user.id, !user.is_active, token);
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
    } catch {
      // Most likely the "can't change your own status" guard — nothing to recover here.
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className={sectionClass}>
      <h2 className="font-heading text-xl font-bold text-zinc-900 dark:text-zinc-50">Users</h2>
      <div className="mt-4 flex flex-wrap gap-3">
        <input
          placeholder="Search by name or email"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} max-w-xs`}
        />
        <select value={role} onChange={(e) => setRole(e.target.value as UserRole | "")} className={`${inputClass} w-auto`}>
          <option value="">All roles</option>
          <option value="talent">Talent</option>
          <option value="recruiter">Recruiter</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <ul className="mt-4 flex flex-col gap-2">
        {users.map((u) => (
          <li key={u.id} className="rounded-2xl border-2 border-zinc-100 px-4 py-3 text-sm dark:border-zinc-800">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-zinc-900 dark:text-zinc-50">
                  {u.full_name} <span className="font-normal text-zinc-500">— {u.email}</span>
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <span className={badgeClass("neutral")}>{u.role}</span>
                  <span className={badgeClass(u.is_active ? "success" : "warning")}>
                    {u.is_active ? "active" : "suspended"}
                  </span>
                  {!u.email_verified && <span className={badgeClass("warning")}>unverified email</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setExpandedId((prev) => (prev === u.id ? null : u.id))} className={btnSmall}>
                  {expandedId === u.id ? "Hide details" : "View details"}
                </button>
                <button
                  disabled={busyId === u.id}
                  onClick={() => toggleActive(u)}
                  className={u.is_active ? btnSmall : btnSmallPrimary}
                >
                  {u.is_active ? "Suspend" : "Reactivate"}
                </button>
              </div>
            </div>
            {expandedId === u.id && token && <UserDetailPanel userId={u.id} token={token} />}
          </li>
        ))}
        {users.length === 0 && <p className="text-sm text-zinc-500">No users match this filter.</p>}
      </ul>
    </section>
  );
}

function UserDetailPanel({ userId, token }: { userId: string; token: string }) {
  const [detail, setDetail] = useState<AdminUserDetail | null>(null);

  useEffect(() => {
    api.adminGetUserDetail(userId, token).then(setDetail).catch(() => {});
  }, [userId, token]);

  if (!detail) {
    return <p className="mt-3 text-xs text-zinc-500">Loading account details…</p>;
  }

  return (
    <div className="mt-3 flex flex-col gap-2 border-t border-zinc-200 pt-3 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
      <p>Phone: {detail.phone ?? "—"}</p>
      <p>Joined: {new Date(detail.created_at).toLocaleDateString()}</p>
      {detail.talent_profile && (
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
          <p className="font-semibold text-zinc-700 dark:text-zinc-300">Talent profile</p>
          <p className="mt-1">
            {detail.talent_profile.display_name} · {formatCategory(detail.talent_profile.category)} ·{" "}
            {detail.talent_profile.city ?? "no city set"}
          </p>
          <p className="mt-1">
            Tier: {detail.talent_profile.tier} · {detail.talent_profile.is_verified ? "Verified" : "Not verified"}
          </p>
        </div>
      )}
      {detail.recruiter_profile && (
        <div className="rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/60">
          <p className="font-semibold text-zinc-700 dark:text-zinc-300">Recruiter profile</p>
          <p className="mt-1">
            {detail.recruiter_profile.company_name} · {detail.recruiter_profile.industry ?? "no industry set"}
          </p>
          <p className="mt-1">
            Tier: {detail.recruiter_profile.tier} · {detail.recruiter_profile.is_verified ? "Verified" : "Not verified"}
          </p>
        </div>
      )}
      {!detail.talent_profile && !detail.recruiter_profile && <p>No linked talent or recruiter profile.</p>}
    </div>
  );
}
