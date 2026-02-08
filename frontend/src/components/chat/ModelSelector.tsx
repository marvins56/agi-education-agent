"use client";

import { ChevronDown, Cpu } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useModels } from "@/hooks/useModels";

export function ModelSelector() {
  const { providers, selectedProvider, selectedModel, selectModel } =
    useModels();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const displayName = selectedModel
    ? `${selectedProvider}/${selectedModel}`
    : "Select model";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-gray-300 transition-colors hover:bg-gray-700"
      >
        <Cpu className="h-4 w-4 text-blue-400" />
        <span className="max-w-[200px] truncate">{displayName}</span>
        <ChevronDown className="h-3 w-3" />
      </button>

      {open && (
        <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-lg border border-gray-700 bg-gray-800 py-1 shadow-lg">
          {providers.length === 0 ? (
            <p className="px-3 py-2 text-sm text-gray-500">
              No models available
            </p>
          ) : (
            providers.map((provider) => (
              <div key={provider.provider}>
                <div className="px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-gray-500">
                  {provider.provider}
                  {!provider.available && " (offline)"}
                </div>
                {provider.models.map((model) => (
                  <button
                    key={`${provider.provider}-${model}`}
                    onClick={() => {
                      selectModel(provider.provider, model);
                      setOpen(false);
                    }}
                    disabled={!provider.available}
                    className={`w-full px-3 py-1.5 text-left text-sm transition-colors ${
                      selectedProvider === provider.provider &&
                      selectedModel === model
                        ? "bg-blue-600/20 text-blue-300"
                        : "text-gray-300 hover:bg-gray-700"
                    } disabled:opacity-40 disabled:cursor-not-allowed`}
                  >
                    {model}
                  </button>
                ))}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
