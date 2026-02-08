"use client";

import { useCallback, useEffect, useState } from "react";
import * as modelsApi from "@/lib/api/models";
import type { CurrentModel, ModelProvider } from "@/lib/types/api";

export function useModels() {
  const [providers, setProviders] = useState<ModelProvider[]>([]);
  const [currentModel, setCurrentModel] = useState<CurrentModel | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");

  const loadModels = useCallback(async () => {
    try {
      const [providerList, current] = await Promise.all([
        modelsApi.listModels(),
        modelsApi.getCurrentModel(),
      ]);
      setProviders(providerList);
      setCurrentModel(current);
      setSelectedProvider(current.provider);
      setSelectedModel(current.model);
    } catch {
      // Models endpoint may not be available
    }
  }, []);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const selectModel = useCallback((provider: string, model: string) => {
    setSelectedProvider(provider);
    setSelectedModel(model);
  }, []);

  return {
    providers,
    currentModel,
    selectedProvider,
    selectedModel,
    selectModel,
    loadModels,
  };
}
