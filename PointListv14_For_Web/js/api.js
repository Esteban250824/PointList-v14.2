/**
 * js/api.js - Conector HTTP API y Almacenamiento Local (Offline Fallback)
 */

const ApiModule = (() => {
  const API_BASE_URL = window.location.origin.includes("http") ? window.location.origin : "http://localhost:5000";

  const request = async (endpoint, method = "GET", data = null) => {
    try {
      const options = {
        method,
        headers: {
          "Content-Type": "application/json"
        }
      };
      if (data) options.body = JSON.stringify(data);

      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      return await response.json();
    } catch (err) {
      console.warn(`[ApiModule] Fallback a LocalStorage para ${endpoint}:`, err);
      return null;
    }
  };

  return {
    login: (email, password) => request("/api/auth/login", "POST", { email, password }),
    register: (userData) => request("/api/auth/register", "POST", userData),
    getNotes: () => request("/api/notes", "GET"),
    saveNote: (note) => request("/api/notes", "POST", note),
    getEvents: () => request("/api/calendar", "GET"),
    saveEvent: (event) => request("/api/calendar", "POST", event),
    askChatbot: (pregunta) => request("/api/chatbot/ask", "POST", { pregunta })
  };
})();
