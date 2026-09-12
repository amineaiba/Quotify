import { api } from "./api";

export type Sender = "client" | "agent" | "staff";
export type ConversationStatus = "attention" | "held" | "auto_sent";
export type ConversationFilter = "all" | "needs_attention" | "auto_sent";

export type Client = { name: string | null; phone_number: string };

export type LastMessage = { content: string; sender: Sender; created_at: string };

export type ConversationSummary = {
  id: string;
  channel: "whatsapp";
  client: Client;
  last_message: LastMessage | null;
  status: ConversationStatus;
  total: number | null;
};

export type Message = { id: string; sender: Sender; content: string; created_at: string };

export type PriceLine = {
  item_id: string;
  name: string;
  unit: string;
  quantity: number;
  unit_price: number;
  applied_min_qty: number;
  total: number;
};

export type QuoteSummary = {
  status: "pending" | "approved" | "rejected" | "auto_sent";
  lines: PriceLine[];
  subtotal: number;
};

export type ConversationDetail = {
  id: string;
  channel: "whatsapp";
  client: Client;
  messages: Message[];
  latest_quote: QuoteSummary | null;
};

export const conversationsApi = {
  list: (filter: ConversationFilter) =>
    api.get<ConversationSummary[]>(
      filter === "all" ? "/api/v1/conversations" : `/api/v1/conversations?status=${filter}`,
    ),
  get: (id: string) => api.get<ConversationDetail>(`/api/v1/conversations/${id}`),
};
