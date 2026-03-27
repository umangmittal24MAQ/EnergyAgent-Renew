import React, { useEffect, useMemo, useState } from "react";
import { useTabStore } from "./store/tabStore";
import { useThemeStore } from "./store/themeStore";
import { useUnifiedData } from "./hooks/useEnergyData";
import { OverviewTab } from "./components/tabs/OverviewTab";
import { GridTab } from "./components/tabs/GridTab";
import { SolarTab } from "./components/tabs/SolarTab";
import { DieselTab } from "./components/tabs/DieselTab";
import { SchedulerTab } from "./components/tabs/SchedulerTab";
import { FiltersTab } from "./components/tabs/FiltersTab";
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

const TAB_ITEMS = [
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

function App() {
  const { activeTab, setActiveTab } = useTabStore();
  const { theme, toggleTheme } = useThemeStore();
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { data: liveData } = useUnifiedData();

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const activeTabItem = useMemo(
    () => TAB_ITEMS.find((item) => item.id === activeTab) || TAB_ITEMS[0],
    [activeTab],
  );

  useEffect(() => {
    if (Array.isArray(liveData?.data)) {
      setLastRefresh(new Date());
    }
  }, [liveData?.total_records]);

  const renderTabContent = () => {
    if (activeTab === "overview") return <OverviewTab />;
    if (activeTab === "grid") return <GridTab />;
    if (activeTab === "solar") return <SolarTab />;
    if (activeTab === "diesel") return <DieselTab />;
    if (activeTab === "scheduler") return <SchedulerTab />;
    if (activeTab === "filters") return <FiltersTab />;
    return <OverviewTab />;
  };

  return (
    <div className="enterprise-shell bg-slate-50">
      <aside
        className={`enterprise-sidebar ${isSidebarCollapsed ? "collapsed" : ""}`}
      >
        <div className="sidebar-top">
          <div className="brand-lockup">
            <div className="brand-mark">
              <Zap className="text-white" size={22} strokeWidth={2.6} />
            </div>
            <div>
              <h1 className="text-lg font-semibold app-title">
                Energy Command
              </h1>
              <p className="text-xs app-subtitle">
                Enterprise Operations Center
              </p>
            </div>
          </div>
          <button
            type="button"
            className="theme-toggle-btn hidden lg:inline-flex"
            onClick={() => setIsSidebarCollapsed((state) => !state)}
            title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={
              isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"
            }
          >
            {isSidebarCollapsed ? (
              <PanelLeftOpen size={16} />
            ) : (
              <PanelLeftClose size={16} />
            )}
          </button>
        </div>

        <nav className="nav-rail">
          {TAB_ITEMS.map((tab) => {
            const IconComponent = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                type="button"
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                }}
                className={`nav-rail-btn ${isActive ? "nav-rail-btn-active" : ""}`}
              >
                <IconComponent size={18} />
                <span>{tab.label}</span>
                {!isSidebarCollapsed && (
                  <small className="nav-rail-meta">{tab.description}</small>
                )}
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="workspace">
        <header className="workspace-header">
          <div className="workspace-header-left">
            <div>
              <h2 className="text-[28px] font-semibold leading-tight tracking-tight text-slate-800">
                {activeTabItem.label}
              </h2>
              <p className="mt-0.5 text-[13px] text-slate-400">
                {activeTabItem.description}
              </p>
            </div>
          </div>
          <section className="fade-in-up inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
            <p className="text-xs text-slate-400">Last refresh</p>
            <p className="text-xs font-medium text-slate-600">
              {lastRefresh.toLocaleString("en-IN")}
            </p>
          </section>
        </header>

        <main className="workspace-main">
          <section className="dashboard-panel fade-in-up">
            {renderTabContent()}
          </section>
        </main>

        <footer className="footer-shell px-5 py-4 md:px-8">
          <p className="text-sm text-(--text-muted)">
            Energy Command Dashboard | Enterprise Edition | React + FastAPI
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
