/**
 * API client for Content Agent backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CategorySummary {
  industry_news: string[];
  new_tools: string[];
  insights: string[];
  core_thesis?: string;
  key_concepts?: string[];
  primary_arguments?: string[];
  evidence?: string[];
  implications?: string[];
}

export interface EmailDigest {
  email_id: string;
  sender: string;
  subject: string;
  summary: CategorySummary;
}

export interface Digest {
  id: number;
  date: string;
  digest_type: "daily" | "weekly";
  briefing: string | null;
  linkedin_content: string | null;
  newsletter_summaries: string | null;
  structured_digests: EmailDigest[] | null;
  emails_processed: string[] | null;
  created_at: string;
}

export interface Email {
  id: number;
  gmail_id: string;
  sender: string;
  subject: string;
  body: string;
  received_at: string | null;
  processed_at: string;
  digest_id: number | null;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  database: string;
}

/**
 * Fetch the latest digest from the API.
 * @param digestType - Either 'daily' or 'weekly'
 */
export async function fetchLatestDigest(digestType: "daily" | "weekly" = "daily"): Promise<Digest | null> {
  const response = await fetch(`${API_URL}/api/digest/latest?digest_type=${digestType}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch digest: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Fetch the latest daily digest.
 */
export async function fetchLatestDailyDigest(): Promise<Digest | null> {
  return fetchLatestDigest("daily");
}

/**
 * Fetch the latest weekly deep dive.
 */
export async function fetchLatestWeeklyDeepDive(): Promise<Digest | null> {
  return fetchLatestDigest("weekly");
}

/**
 * Fetch digest history with pagination.
 * @param digestType - Optional filter by 'daily' or 'weekly'
 */
export async function fetchDigestHistory(
  limit = 10,
  offset = 0,
  digestType?: "daily" | "weekly"
): Promise<Digest[]> {
  let url = `${API_URL}/api/digest/history?limit=${limit}&offset=${offset}`;
  if (digestType) {
    url += `&digest_type=${digestType}`;
  }
  
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch a specific digest by ID.
 */
export async function fetchDigestById(id: number): Promise<Digest> {
  const response = await fetch(`${API_URL}/api/digest/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch digest: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch raw emails with pagination.
 */
export async function fetchEmails(limit = 50, offset = 0): Promise<Email[]> {
  const response = await fetch(
    `${API_URL}/api/emails?limit=${limit}&offset=${offset}`,
    { cache: "no-store" }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch emails: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Check API health status.
 */
export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_URL}/api/health`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

export interface ProcessResponse {
  status: string;
  message: string;
  digest_id: number | null;
}

/**
 * Manually trigger email processing.
 * @param digestType - Either 'dailydigest' or 'weeklydeepdives'
 * @param dryRun - If true, preview only without modifying emails
 */
export async function triggerProcess(
  digestType: "dailydigest" | "weeklydeepdives" = "dailydigest",
  dryRun: boolean = false
): Promise<ProcessResponse> {
  const response = await fetch(
    `${API_URL}/api/process?digest_type=${digestType}&dry_run=${dryRun}`,
    {
      method: "POST",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to trigger process: ${response.statusText}`);
  }

  return response.json();
}
