export type InteractionType = "Meeting" | "Call" | "Email" | "Conference" | "WhatsApp";
export type Sentiment = "positive" | "neutral" | "negative";
export type ChatRole = "assistant" | "user";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  created_at: string;
}

export interface ToolEvent {
  tool_name: string;
  status: "success" | "warning" | "error";
  summary: string;
  changed_fields: string[];
  created_at: string;
}

export interface ValidationReport {
  is_valid: boolean;
  missing_fields: string[];
  warnings: string[];
}

export interface HCPSummary {
  id: number;
  name: string;
  specialty: string;
  organization: string;
  city: string;
  territory: string;
}

export interface MaterialSummary {
  id: number;
  name: string;
  material_type: string;
}

export interface InteractionDraft {
  hcp_name: string;
  interaction_type: InteractionType;
  interaction_date: string;
  interaction_time: string;
  attendees: string[];
  topics_discussed: string;
  materials_shared: string[];
  samples_distributed: string[];
  sentiment: Sentiment;
  outcomes: string;
  follow_up_actions: string[];
  ai_suggested_follow_up: string[];
  ai_summary: string;
  source_text: string;
}

export interface SessionResponse {
  session_id: string;
  draft: InteractionDraft;
  messages: ChatMessage[];
  validation: ValidationReport;
  tool_events: ToolEvent[];
  last_saved_interaction_id: number | null;
  llm_mode: string;
  hcps: HCPSummary[];
  materials: MaterialSummary[];
}

export interface ChatResponse {
  session_id: string;
  assistant_message: ChatMessage;
  draft: InteractionDraft;
  validation: ValidationReport;
  tool_events: ToolEvent[];
  last_saved_interaction_id: number | null;
  llm_mode: string;
}

export interface InteractionRecord {
  id: number;
  hcp_name: string;
  interaction_type: string;
  interaction_date: string | null;
  sentiment: string;
  topics_discussed: string;
  ai_summary: string;
}

export interface InteractionListResponse {
  items: InteractionRecord[];
}
