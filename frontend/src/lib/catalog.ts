import { api } from "./api";

export type CatalogItemTier = {
  id: string;
  min_qty: number;
  unit_price: number;
};

export type CatalogItem = {
  id: string;
  name: string;
  unit: string;
  tiers: CatalogItemTier[];
};

export type CatalogItemInput = {
  name: string;
  unit: string;
  tiers: { min_qty: number; unit_price: number }[];
};

export const catalogApi = {
  list: () => api.get<CatalogItem[]>("/api/v1/catalog/items"),
  create: (item: CatalogItemInput) => api.post<CatalogItem>("/api/v1/catalog/items", item),
  update: (id: string, item: CatalogItemInput) =>
    api.put<CatalogItem>(`/api/v1/catalog/items/${id}`, item),
  remove: (id: string) => api.delete<void>(`/api/v1/catalog/items/${id}`),
};
