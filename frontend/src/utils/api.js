import { getToken } from "./uitils";

// Use relative URLs so Vite proxies to backend (avoids CORS)
const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = {
  post: async function (endpoint, payload) {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${await getToken()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const text = await response.text();
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
      throw new Error(msg);
    }
    return data;
  },
  get: async function (endpoint) {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${await getToken()}`,
        "Content-Type": "application/json",
      },
    });
    const text = await response.text();
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
      throw new Error(msg);
    }
    return data;
  },
};

export { api };
