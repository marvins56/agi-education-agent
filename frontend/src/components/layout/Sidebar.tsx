"use client";

import {
  BookOpen,
  MessageSquare,
  BarChart3,
  UserCircle,
  ClipboardCheck,
  Route,
  LogOut,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/profile", label: "Profile", icon: UserCircle },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/assessments", label: "Assessments", icon: ClipboardCheck },
  { href: "/learning-path", label: "Learning Path", icon: Route },
  { href: "/library", label: "Library", icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-gray-800 bg-gray-950">
      <div className="flex h-14 items-center gap-2 border-b border-gray-800 px-4">
        <BookOpen className="h-6 w-6 text-blue-500" />
        <span className="text-lg font-bold text-gray-100">EduAGI</span>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-gray-800 text-blue-400"
                  : "text-gray-400 hover:bg-gray-900 hover:text-gray-200"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-800 p-3">
        <div className="mb-2 px-3 text-sm text-gray-400 truncate">
          {user?.name || user?.email}
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-400 transition-colors hover:bg-gray-900 hover:text-gray-200"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
