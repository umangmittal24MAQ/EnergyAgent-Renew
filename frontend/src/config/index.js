/**
 * Environment Configuration
 * Centralized environment and feature flags
 */

export const appConfig = {
  // Application metadata
  name: "Energy Dashboard",
  version: import.meta.env.VITE_APP_VERSION || "1.0.0",
  description: "Enterprise Energy Monitoring & Optimization Dashboard",

  // Feature flags
  features: {
    exportPDF: true,
    exportExcel: true,
    realTimeUpdates: true,
    schedulerIntegration: true,
    multiserverSupport: false,
  },

  // Default display settings
  defaults: {
    refreshInterval: 300000, // 5 minutes
    dateFormat: "YYYY-MM-DD",
    timeFormat: "HH:mm:ss",
    timezone: "Asia/Kolkata",
  },

  // Cache settings
  cache: {
    enabled: true,
    ttl: 300000, // 5 minutes
  },
};

export default appConfig;
