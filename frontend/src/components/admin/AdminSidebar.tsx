"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Clapperboard,
  DollarSign,
  Flag,
  Gauge,
  LogOut,
  MessagesSquare,
  ShieldCheck,
  Tag,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/admin", label: "Overview", icon: Gauge },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/verification", label: "Verification", icon: ShieldCheck },
  { href: "/admin/casting-calls", label: "Talent hunts", icon: Clapperboard },
  { href: "/admin/community", label: "Community", icon: MessagesSquare },
  { href: "/admin/reports", label: "Reports", icon: Flag },
  { href: "/admin/subscriptions", label: "Subscriptions", icon: Wallet },
  { href: "/admin/pricing", label: "Pricing", icon: Tag },
  { href: "/admin/financial", label: "Financial", icon: DollarSign },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950 text-zinc-300">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-rose-600 text-sm font-black text-white">
          YT
        </span>
        <div>
          <p className="font-heading text-sm font-black uppercase tracking-tight text-white">YouGotTalent</p>
          <p className="text-xs text-zinc-500">Admin</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
        {NAV_ITEMS.map((item) => {
          const active = item.href === "/admin" ? pathname === "/admin" : pathname?.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                active ? "bg-rose-600 text-white" : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800 p-3">
        <p className="truncate px-3 text-xs text-zinc-500">{user?.full_name}</p>
        <Link
          href="/"
          className="mt-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4 shrink-0" /> Back to site
        </Link>
        <button
          onClick={handleLogout}
          className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-semibold text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-white"
        >
          <LogOut className="h-4 w-4 shrink-0" /> Log out
        </button>
      </div>
    </aside>
  );
}
