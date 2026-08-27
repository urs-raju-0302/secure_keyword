import axios from "axios";
import type { AuditEvent, DocumentMeta, KeyStatus, SearchResponse, TokenPair, User } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function register(email: string, password: string): Promise<User> {
  const { data } = await api.post<User>("/auth/register", { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const { data } = await api.post<TokenPair>("/auth/login", { email, password });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}

export async function logout(): Promise<void> {
  const refresh = localStorage.getItem("refresh_token");
  try {
    if (refresh) {
      await api.post("/auth/logout", { refresh_token: refresh });
    }
  } finally {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}

export async function me(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function listDocuments(): Promise<DocumentMeta[]> {
  const { data } = await api.get<DocumentMeta[]>("/documents");
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentMeta> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<DocumentMeta>("/documents", form);
  return data;
}

export async function getDocument(id: string): Promise<DocumentMeta> {
  const { data } = await api.get<DocumentMeta>(`/documents/${id}`);
  return data;
}

export async function downloadDocument(id: string, filename: string): Promise<void> {
  const { data } = await api.get<Blob>(`/documents/${id}/download`, { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}

export async function search(keyword: string): Promise<SearchResponse> {
  const { data } = await api.post<SearchResponse>("/search", { keyword });
  return data;
}

export async function keyStatus(): Promise<KeyStatus> {
  const { data } = await api.get<KeyStatus>("/keys/status");
  return data;
}

export async function rotateSearchKey(): Promise<unknown> {
  const { data } = await api.post("/keys/rotate/search");
  return data;
}

export async function rotateMasterKey(): Promise<unknown> {
  const { data } = await api.post("/keys/rotate/master");
  return data;
}

export async function reindex(): Promise<unknown> {
  const { data } = await api.post("/keys/reindex");
  return data;
}

export async function listAudit(): Promise<AuditEvent[]> {
  const { data } = await api.get<AuditEvent[]>("/audit");
  return data;
}

export async function myAudit(): Promise<AuditEvent[]> {
  const { data } = await api.get<AuditEvent[]>("/audit/me");
  return data;
}
