import { getToken } from "./uitils";
import { supabase } from "./supabaseClient";

export const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

const buildAuthHeaders = async () => {
  const token = await getToken();
  if (!token) {
    throw new Error("Not authenticated. Please sign in again.");
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  return headers;
};

const api = {
  post: async function (endpoint, payload) {
    console.debug("[api.post] preparing request", { endpoint, payload });
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "POST",
      headers: await buildAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    console.debug("[api.post] raw response", {
      endpoint,
      status: response.status,
      ok: response.ok,
      raw: text?.slice(0, 1000),
    });
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (_) {
      throw new Error(
        response.ok
          ? "Invalid response"
          : text || `Request failed (${response.status})`,
      );
    }
    if (!response.ok) {
      const msg =
        data?.error?.message ??
        (typeof data?.detail === "string"
          ? data.detail
          : JSON.stringify(data?.detail ?? data ?? "Request failed"));
      console.error("API POST error:", response.status, endpoint, {
        data,
        raw: text?.slice(0, 300),
      });
      const err = new Error(msg);
      err.status = response.status;
      err.response = data;
      throw err;
    }
    return data;
  },
  get: async function (endpoint) {
    console.debug("[api.get] preparing request", { endpoint });
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "GET",
      headers: await buildAuthHeaders(),
    });
    const text = await response.text();
    console.debug("[api.get] raw response", {
      endpoint,
      status: response.status,
      ok: response.ok,
      raw: text?.slice(0, 1000),
    });
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (_) {
      throw new Error(
        response.ok
          ? "Invalid response"
          : text || `Request failed (${response.status})`,
      );
    }
    if (!response.ok) {
      const msg =
        data?.error?.message ??
        (typeof data?.detail === "string"
          ? data.detail
          : JSON.stringify(data?.detail ?? "Request failed"));
      const err = new Error(msg);
      err.status = response.status;
      err.response = data;
      throw err;
    }
    return data;
  },
  put: async function (endpoint, payload) {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "PUT",
      headers: await buildAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const raw = await response.text();
    let data;
    try { data = raw ? JSON.parse(raw) : {}; }
    catch (_) { throw new Error(response.ok ? "Invalid response" : raw || `Request failed (${response.status})`); }
    if (!response.ok) {
      const error = new Error(data?.error?.message ?? data?.detail ?? "Request failed");
      error.status = response.status;
      error.response = data;
      throw error;
    }
    return data;
  },
};

export { api };
