import React, { useMemo, useState, useEffect } from "react";
import { useTabStore } from "../../store/tabStore";
import { useThemeStore } from "../../store/themeStore";
import {
  BellRing,
  Clock3,
  Fuel,
  Grid2X2,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  RefreshCw,
  SlidersHorizontal,
  Sun,
  SunMedium,
  Zap,
} from "lucide-react";

export const TAB_ITEMS = [
  {
    id: "overview",
    label: "Overview",
    icon: Grid2X2,
    description: "Executive operations board",
  },
  {
    id: "grid",
    label: "Grid Supply",
    icon: Zap,
    description: "Supply and tariff intelligence",
  },
  {
    id: "solar",
    label: "Solar Panel",
    icon: Sun,
    description: "Generation and inverter health",
  },
  {
    id: "diesel",
    label: "Diesel Generator",
    icon: Fuel,
    description: "Fuel and runtime performance",
  },
  {
    id: "scheduler",
    label: "Scheduler",
    icon: Clock3,
    description: "Mail automation operations",
  },
  {
    id: "filters",
    label: "Filters",
    icon: SlidersHorizontal,
    description: "Date and reporting controls",
  },
];

export function MainLayout({ children, lastRefresh, onRefresh }) {
  const { activeTab, setActiveTab } = useTabStore();
  const { theme, toggleTheme } = useThemeStore();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const activeTabItem = useMemo(
    () => TAB_ITEMS.find((item) => item.id === activeTab) || TAB_ITEMS[0],
    [activeTab],
  );

  return (
    <div className="enterprise-shell bg-slate-50">
      <aside
        className={`enterprise-sidebar ${isSidebarCollapsed ? "collapsed" : ""}`}
      >
        <div className="sidebar-header">
          <div className="logo-section">
            <div className="logo-circle">
              <SunMedium size={20} />
            </div>
            {!isSidebarCollapsed && (
              <h1 className="logo-text">Energy Dashboard</h1>
            )}
          </div>
        </div>

        <nav className="sidebar-nav">
          {TAB_ITEMS.map(({ id, label, icon: Icon, description }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`nav-item ${activeTab === id ? "active" : ""}`}
              title={isSidebarCollapsed ? description : ""}
            >
              <Icon size={20} />
              {!isSidebarCollapsed && label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="collapse-btn"
            title={isSidebarCollapsed ? "Expand" : "Collapse"}
          >
            {isSidebarCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>
      </aside>

      <main className="enterprise-main">
        <header className="enterprise-header">
          <div className="header-title">
            <h2>{activeTabItem.label}</h2>
            <p className="text-sm text-slate-600">{activeTabItem.description}</p>
          </div>

          <div className="header-controls">
            <button
              onClick={onRefresh}
              className="control-btn-primary"
              title="Refresh data"
            >
              <RefreshCw size={18} />
              {lastRefresh && (
                <span className="text-xs text-slate-500">
                  Last: {lastRefresh.toLocaleTimeString()}
                </span>
              )}
            </button>

            <button
              onClick={toggleTheme}
              className="control-btn"
              title="Toggle theme"
            >
              {theme === "light" ? <Moon size={18} /> : <Sun size={18} />}
            </button>

            <button className="control-btn" title="Notifications">
              <BellRing size={18} />
            </button>
          </div>
        </header>

        <div className="enterprise-content">
          {children}
        </div>
      </main>
    </div>
  );
}
