export type User = {
  id: string;
  email: string;
  role: "USER" | "ADMIN";
  is_active: boolean;
  created_at: string;
};

export type DocumentMeta = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  encryption_algorithm: string;
  dek_key_version: number;
  created_at: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type SearchResponse = {
  keyword_normalized_length: number;
  result_count: number;
  documents: DocumentMeta[];
  note: string;
};

export type KeyStatus = {
  keys: Array<{
    key_type: string;
    version: number;
    status: string;
    activated_at: string | null;
    retired_at: string | null;
  }>;
};

export type AuditEvent = {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  success: boolean;
  created_at: string;
  metadata_json: Record<string, unknown> | null;
};
