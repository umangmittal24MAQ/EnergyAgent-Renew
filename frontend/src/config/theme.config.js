/**
 * Theme Configuration
 * Centralized theme settings and defaults
 */

export const THEME_MODES = {
  LIGHT: "light",
  DARK: "dark",
};

export const THEME_COLORS = {
  light: {
    background: "#f8fafc",
    foreground: "#020617",
    card: "#ffffff",
    text: "#1e293b",
    textMuted: "#64748b",
    border: "#e2e8f0",
    primary: "#0ea5e9",
    secondary: "#8b5cf6",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
  },
  dark: {
    background: "#0f172a",
    foreground: "#f1f5f9",
    card: "#1e293b",
    text: "#f1f5f9",
    textMuted: "#94a3b8",
    border: "#334155",
    primary: "#0ea5e9",
    secondary: "#8b5cf6",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
  },
};

export const themeConfig = {
  defaultTheme: THEME_MODES.LIGHT,
  supportedThemes: Object.values(THEME_MODES),
  colors: THEME_COLORS,
};

export default themeConfig;
