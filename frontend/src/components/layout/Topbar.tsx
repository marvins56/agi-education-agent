"use client";

import { User, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { ModelSelector } from "@/components/chat/ModelSelector";

export function Topbar() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex h-14 items-center justify-between border-b border-gray-800 bg-gray-950 px-4">
      <ModelSelector />

      <div className="relative" ref={menuRef}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-gray-300 transition-colors hover:bg-gray-800"
        >
          <User className="h-4 w-4" />
          <span className="max-w-[120px] truncate">
            {user?.name || "User"}
          </span>
          <ChevronDown className="h-3 w-3" />
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-gray-700 bg-gray-800 py-1 shadow-lg">
            <div className="border-b border-gray-700 px-3 py-2">
              <p className="text-sm font-medium text-gray-200">{user?.name}</p>
              <p className="text-xs text-gray-400">{user?.email}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={() => {
                setMenuOpen(false);
                logout();
              }}
              className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700"
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
