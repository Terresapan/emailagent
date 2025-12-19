/**
 * API client for Content Agent backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Digest {
  id: number;
  date: string;
  briefing: string | null;
  linkedin_content: string | null;
  newsletter_summaries: string | null;
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
 */
export async function fetchLatestDigest(): Promise<Digest | null> {
  const response = await fetch(`${API_URL}/api/digest/latest`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch digest: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

/**
 * Fetch digest history with pagination.
 */
export async function fetchDigestHistory(
  limit = 10,
  offset = 0
): Promise<Digest[]> {
  const response = await fetch(
    `${API_URL}/api/digest/history?limit=${limit}&offset=${offset}`,
    { cache: "no-store" }
  );

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
