import ky from "ky";
import { z } from "zod";

const API_BASE_URL = "http://127.0.0.1:8000";
export const BACKEND_CLI_TIMEOUT_MS = 120_000;
export const API_REQUEST_TIMEOUT_MS = BACKEND_CLI_TIMEOUT_MS + 60_000;
const api = ky.create({ timeout: API_REQUEST_TIMEOUT_MS });

const QualityCheckSchema = z.object({
  name: z.string(),
  status: z.string(),
  detail: z.string(),
});

const CandidateSchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  body: z.string(),
  recommended_channel: z.string(),
  reference_summary: z.string(),
});

const GenerateResponseSchema = z.object({
  draft_id: z.number(),
  candidates: z.array(CandidateSchema),
  search_summary: z.array(z.string()),
  quality_checks: z.array(QualityCheckSchema),
  cli_log_id: z.number(),
});

const ReviseResponseSchema = z.object({
  draft_id: z.number(),
  revised_body: z.string(),
  change_summary: z.string(),
  quality_checks: z.array(QualityCheckSchema),
  cli_log_id: z.number(),
});

const ApproveResponseSchema = z.object({
  draft_id: z.number(),
  status: z.literal("ready_to_publish"),
  saved_path: z.string(),
});

export type Candidate = z.infer<typeof CandidateSchema>;
export type QualityCheck = z.infer<typeof QualityCheckSchema>;
export type GenerateResponse = z.infer<typeof GenerateResponseSchema>;
export type ReviseResponse = z.infer<typeof ReviseResponseSchema>;
export type ApproveResponse = z.infer<typeof ApproveResponseSchema>;

export type GeneratePayload = {
  readonly topic: string;
  readonly keywords: readonly string[];
  readonly channel: string;
  readonly provider: "codex" | "claude" | "gemini";
};

export type RevisePayload = {
  readonly draft_id: number;
  readonly candidate_id: string;
  readonly tone: string;
  readonly revision_request: string;
};

export async function generateContent(payload: GeneratePayload): Promise<GenerateResponse> {
  const response = await api.post(`${API_BASE_URL}/generate`, { json: payload }).json();
  return GenerateResponseSchema.parse(response);
}

export async function reviseContent(payload: RevisePayload): Promise<ReviseResponse> {
  const response = await api.post(`${API_BASE_URL}/revise`, { json: payload }).json();
  return ReviseResponseSchema.parse(response);
}

export async function approveDraft(draftId: number): Promise<ApproveResponse> {
  const response = await api
    .post(`${API_BASE_URL}/approve`, { json: { draft_id: draftId, output_format: "markdown" } })
    .json();
  return ApproveResponseSchema.parse(response);
}
