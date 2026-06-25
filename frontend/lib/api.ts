export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
};

export type UploadedFile = {
  file_id: string;
  filename: string;
  size_bytes: number;
  text_chars: number;
  exists: boolean;
  storage_provider?: string;
  storage_uri?: string;
};

export type AskResponse = {
  query: string;
  session_id: string;
  file_id: string;
  file_context_used: boolean;
  final_answer: string;
  messages: ChatMessage[];
  llm_tree?: {
    best_model?: string;
    best_score?: number;
    scores?: Array<Record<string, unknown>>;
  };
  agent_result?: {
    agent?: string;
    router?: {
      route?: string;
      selected_leaf_agent?: string;
    };
    thoughts?: string[];
  };
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function askAgent(query: string, sessionId: string, fileId: string) {
  return request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({ query, session_id: sessionId, file_id: fileId })
  });
}

export function listFiles() {
  return request<{ files: UploadedFile[] }>("/files");
}

export function getHistory(sessionId: string) {
  return request<{ messages: ChatMessage[] }>(`/history/${sessionId}`);
}

export function resetSession(sessionId: string) {
  return request<{ message: string }>("/reset", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId })
  });
}

export function uploadFile(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<UploadedFile & { message: string }>("/upload", {
    method: "POST",
    body: form
  });
}
