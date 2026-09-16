import { api } from "./api";
import type { Client, PriceLine } from "./conversations";

export type QuoteStatus = "pending" | "approved" | "rejected" | "auto_sent";
export type HoldReason = "low_confidence" | "rate_limited";

export type QuoteListItem = {
  id: string;
  conversation_id: string;
  client: Client;
  draft_message: string;
  confidence: number | null;
  status: QuoteStatus;
  hold_reason: HoldReason | null;
  lines: PriceLine[];
  subtotal: number | null;
  created_at: string;
};

export type QuoteActionResult = {
  id: string;
  status: QuoteStatus;
  final_message: string | null;
  reviewed_at: string;
};

export const quotesApi = {
  list: (status?: QuoteStatus) =>
    api.get<QuoteListItem[]>(status ? `/api/v1/quotes?status=${status}` : "/api/v1/quotes"),
  approve: (id: string, message: string) =>
    api.post<QuoteActionResult>(`/api/v1/quotes/${id}/approve`, { message }),
  reject: (id: string) => api.post<QuoteActionResult>(`/api/v1/quotes/${id}/reject`),
};
