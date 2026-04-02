/**
 * API Configuration
 * Centralized API endpoints and client configuration
 */

const API_BASE_URL = import.meta.env.VITE_API_URL?.trim() || "http://localhost:8000";

export const apiConfig = {
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
};

export const API_ENDPOINTS = {
  // Data endpoints
  data: {
    refresh: "/api/data/refresh",
    unified: "/api/data/live/unified",
    grid: "/api/data/live/grid",
    solar: "/api/data/live/solar",
    diesel: "/api/data/live/diesel",
    smbStatus: "/api/data/live/smb-status",
    inverterStatus: "/api/data/live/inverter-status",
    last7Days: "/api/data/live/last-7-days",
    dailySummary: "/api/data/live/daily-summary",
  },

  // KPI endpoints
  kpis: {
    overview: "/api/kpis/overview",
    grid: "/api/kpis/grid",
    solar: "/api/kpis/solar",
    diesel: "/api/kpis/diesel",
  },

  // Export endpoints
  export: {
    data: "/api/export/data",
    pdf: "/api/export/pdf",
    excel: "/api/export/excel",
  },

  // Scheduler endpoints
  scheduler: {
    getStatus: "/api/scheduler/status",
    getJobs: "/api/scheduler/jobs",
    triggerJob: "/api/scheduler/trigger",
  },
};

export default apiConfig;
