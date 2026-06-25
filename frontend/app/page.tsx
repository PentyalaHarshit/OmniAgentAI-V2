"use client";

import {
  Bot,
  FileUp,
  MessageSquarePlus,
  PanelRightClose,
  PanelRightOpen,
  RotateCcw,
  Send,
  Sparkles,
  Trash2
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  AskResponse,
  ChatMessage,
  UploadedFile,
  askAgent,
  getHistory,
  listFiles,
  resetSession,
  uploadFile
} from "../lib/api";

type Conversation = {
  id: string;
  title: string;
  updatedAt: number;
};

function createSessionId() {
  return `sess_${Math.random().toString(36).slice(2, 10)}`;
}

function loadConversations(): Conversation[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem("omni_next_conversations") || "[]");
  } catch {
    return [];
  }
}

const starterMessages: ChatMessage[] = [
  {
    role: "assistant",
    content:
      "Hi. Ask OmniAgentAI about coding, healthcare, research, bookings, finance, shopping, uploaded files, or general knowledge."
  }
];

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>(starterMessages);
  const [query, setQuery] = useState("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [fileId, setFileId] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [lastResult, setLastResult] = useState<AskResponse | null>(null);
  const [sourcesOpen, setSourcesOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const active = localStorage.getItem("omni_next_active_session") || createSessionId();
    const saved = loadConversations();
    setSessionId(active);
    setConversations(saved.length ? saved : [{ id: active, title: "New chat", updatedAt: Date.now() }]);
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    localStorage.setItem("omni_next_active_session", sessionId);
    localStorage.setItem("omni_next_conversations", JSON.stringify(conversations.slice(0, 30)));
  }, [conversations, sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    void refreshFiles();
    void loadHistory(sessionId);
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  const selectedFile = useMemo(
    () => files.find((file) => file.file_id === fileId),
    [fileId, files]
  );

  async function refreshFiles() {
    try {
      const result = await listFiles();
      setFiles(result.files || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load files");
    }
  }

  async function loadHistory(id: string) {
    try {
      const result = await getHistory(id);
      setMessages(result.messages?.length ? result.messages : starterMessages);
    } catch {
      setMessages(starterMessages);
    }
  }

  function upsertConversation(id: string, title?: string) {
    setConversations((current) => {
      const existing = current.find((item) => item.id === id);
      const nextTitle = title || existing?.title || "New chat";
      const item = { id, title: nextTitle, updatedAt: Date.now() };
      return [item, ...current.filter((conversation) => conversation.id !== id)].slice(0, 30);
    });
  }

  function newChat() {
    const id = createSessionId();
    setSessionId(id);
    setMessages(starterMessages);
    setLastResult(null);
    setQuery("");
    setFileId("");
    upsertConversation(id, "New chat");
  }

  async function clearChat() {
    if (!sessionId) return;
    await resetSession(sessionId);
    setMessages(starterMessages);
    setLastResult(null);
    setConversations((current) =>
      current.map((item) => (item.id === sessionId ? { ...item, title: "New chat" } : item))
    );
  }

  async function handleUpload(file: File | null) {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      const result = await uploadFile(file);
      await refreshFiles();
      setFileId(result.file_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = query.trim();
    if (!text || busy) return;

    setBusy(true);
    setError("");
    setQuery("");
    setMessages((current) => [...current, { role: "user", content: text }]);
    upsertConversation(sessionId, text.slice(0, 44) + (text.length > 44 ? "..." : ""));

    try {
      const result = await askAgent(text, sessionId, fileId);
      setLastResult(result);
      setMessages(result.messages?.length ? result.messages : [
        { role: "user", content: text },
        { role: "assistant", content: result.final_answer }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setMessages((current) => [
        ...current,
        { role: "assistant", content: "I could not reach the OmniAgentAI backend." }
      ]);
    } finally {
      setBusy(false);
    }
  }

  const route = lastResult?.agent_result?.router?.route || "-";
  const agent = lastResult?.agent_result?.agent || lastResult?.agent_result?.router?.selected_leaf_agent || "Waiting";
  const thoughts = lastResult?.agent_result?.thoughts || [];

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark"><Sparkles size={18} /></div>
          <div>
            <h1>OmniAgentAI</h1>
            <p>V2 agent workspace</p>
          </div>
        </div>

        <button className="primaryAction" onClick={newChat}>
          <MessageSquarePlus size={16} />
          New chat
        </button>

        <section className="panelBlock">
          <div className="sectionHeader">
            <span>Chats</span>
            <button className="iconButton" title="Clear current chat" onClick={clearChat}>
              <Trash2 size={15} />
            </button>
          </div>
          <div className="conversationList">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                className={conversation.id === sessionId ? "conversation active" : "conversation"}
                onClick={() => setSessionId(conversation.id)}
              >
                {conversation.title}
              </button>
            ))}
          </div>
        </section>

        <section className="panelBlock">
          <div className="sectionHeader">
            <span>Files</span>
            <button className="iconButton" title="Refresh files" onClick={refreshFiles}>
              <RotateCcw size={14} />
            </button>
          </div>
          <label className="uploadBox">
            <FileUp size={17} />
            <span>{uploading ? "Uploading..." : "Upload TXT, PDF, DOCX"}</span>
            <input
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={(event) => void handleUpload(event.target.files?.[0] || null)}
            />
          </label>
          <select value={fileId} onChange={(event) => setFileId(event.target.value)}>
            <option value="">No file selected</option>
            {files.map((file) => (
              <option key={file.file_id} value={file.file_id}>
                {file.filename}
              </option>
            ))}
          </select>
          {selectedFile && (
            <p className="fileMeta">
              {selectedFile.storage_provider || "local"} · {selectedFile.text_chars} chars
            </p>
          )}
        </section>
      </aside>

      <section className="chatColumn">
        <header className="topbar">
          <div>
            <p className="eyebrow">Recursive ToT + ReAct</p>
            <h2>{agent}</h2>
          </div>
          <button className="ghostButton" onClick={() => setSourcesOpen((open) => !open)}>
            {sourcesOpen ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
            Trace
          </button>
        </header>

        <div className="messages">
          {messages.map((message, index) => (
            <article key={`${message.role}-${index}`} className={`message ${message.role}`}>
              <div className="avatar">{message.role === "assistant" ? <Bot size={16} /> : "You"}</div>
              <div className="bubble">
                <pre>{message.content}</pre>
              </div>
            </article>
          ))}
          {busy && (
            <article className="message assistant">
              <div className="avatar"><Bot size={16} /></div>
              <div className="bubble pending">Thinking through agents, tools, and verification...</div>
            </article>
          )}
          <div ref={bottomRef} />
        </div>

        <form className="composer" onSubmit={submit}>
          {selectedFile && <div className="attachedFile">{selectedFile.filename}</div>}
          {error && <div className="error">{error}</div>}
          <div className="composerRow">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Message OmniAgentAI..."
              rows={1}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit(event);
                }
              }}
            />
            <button className="sendButton" disabled={busy || !query.trim()} type="submit">
              <Send size={17} />
            </button>
          </div>
        </form>
      </section>

      <aside className={sourcesOpen ? "tracePanel open" : "tracePanel"}>
        <div className="traceCard">
          <h3>Run State</h3>
          <dl>
            <div><dt>Route</dt><dd>{route}</dd></div>
            <div><dt>Agent</dt><dd>{agent}</dd></div>
            <div><dt>File</dt><dd>{lastResult?.file_context_used ? "Used" : "None"}</dd></div>
            <div><dt>Score</dt><dd>{lastResult?.llm_tree?.best_score ?? "-"}</dd></div>
          </dl>
        </div>

        <div className="traceCard grow">
          <h3>Agent Thoughts</h3>
          {thoughts.length ? (
            <ol className="thoughtList">
              {thoughts.slice(0, 40).map((thought, index) => (
                <li key={`${thought}-${index}`}>{thought}</li>
              ))}
            </ol>
          ) : (
            <p className="muted">No trace yet.</p>
          )}
        </div>
      </aside>
    </main>
  );
}
