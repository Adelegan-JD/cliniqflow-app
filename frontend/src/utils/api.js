import { getToken } from "./uitils";
import { supabase } from "./supabaseClient";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Cache session info to avoid repeated calls to getSession()
let cachedSession = null;
let cachedRole = null;
let sessionCacheTime = 0;
const SESSION_CACHE_TTL = 30000; // Cache for 30 seconds

// Listen for auth state changes and update cache
if (typeof window !== "undefined") {
  supabase.auth.onAuthStateChange((event, session) => {
    cachedSession = session;
    sessionCacheTime = Date.now();
    if (session?.user) {
      cachedRole =
        session.user.user_metadata?.role || session.user.app_metadata?.role;
    } else {
      cachedRole = null;
    }
  });
}

const buildAuthHeaders = async () => {
  const token = await getToken();
  if (!token) {
    throw new Error("Not authenticated. Please sign in again.");
  }

  const headers = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };

  // Use cached role if fresh, otherwise refresh from session
  // This reduces lock contention by batching getSession() calls
  let role = cachedRole;
  if (!role || Date.now() - sessionCacheTime > SESSION_CACHE_TTL) {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (session?.user) {
        role =
          session.user.user_metadata?.role || session.user.app_metadata?.role;
        cachedRole = role;
        sessionCacheTime = Date.now();
      }
    } catch (e) {
      console.debug("Could not extract role from Supabase session:", e);
    }
  }

  if (role) {
    headers["X-Debug-Role"] = role;
  }

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
};

export { api };
