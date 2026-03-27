import React, { useState } from "react";
import {
  useInverterStatusData,
  useLast7DaysData,
  useSmbStatusData,
  useSolarData,
} from "../../hooks/useEnergyData";
import { KPICard } from "../common/KPICard";
import { DataTable } from "../common/DataTable";
import { ExportButton } from "../common/ExportButton";
import { StackedBarChart } from "../charts/StackedBarChart";
import { AreaChartComponent } from "../charts/AreaChart";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { exportAPI } from "../../api/endpoints";
import {
  asNumber,
  formatDisplayDate,
  getLatestRow,
  getRecentRows,
  getRowsForDate,
} from "../../utils/recentData";
import { useDateStore } from "../../store/dateStore";
import {
  Sun,
  DollarSign,
  Zap,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

const InverterStatus = ({ name, status }) => {
  const normalized = String(status || "").toUpperCase();
  const isOnline = ["ONLINE", "ON", "ACTIVE", "RUNNING", "HEALTHY", "OK"].includes(normalized);
  return (
    <div
      className={`p-4 rounded-xl border transition-all ${
        isOnline
          ? "bg-[#edf5f2] border-[#c0d8d0] hover:border-[#99bcae]"
          : "bg-[#f8eff1] border-[#debec4] hover:border-[#c99fa8]"
      }`}
    >
      <div className="flex items-center gap-3">
        <div
          className={`w-2 h-6 rounded-full ${isOnline ? "bg-gradient-to-b from-[#6fa791] to-[#437c65]" : "bg-gradient-to-b from-[#c17a86] to-[#9f5060]"}`}
        ></div>
        <div>
          <p className="font-semibold text-sm text-[var(--text-primary)]">
            {name}
          </p>
          <p
            className={`text-xs font-medium mt-1 ${isOnline ? "text-[#346f5a]" : "text-[#924857]"}`}
          >
            {isOnline ? `✓ ${normalized || "ONLINE"}` : `✗ ${normalized || "FAULT"}`}
          </p>
        </div>
      </div>
    </div>
  );
};

const toDateKey = (row = {}) => {
  const directDate = row?.Date || row?.date;
  if (directDate) return String(directDate).slice(0, 10);

  const ts = row?.Timestamp || row?.timestamp;
  if (!ts) return "";

  const parsed = new Date(ts);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toISOString().slice(0, 10);
};

const toTimeValue = (row = {}) => {
  const dateKey = toDateKey(row);
  const timeText = row?.Time || row?.time || "00:00:00";
  if (!dateKey) return Number.NEGATIVE_INFINITY;
  const parsed = new Date(`${dateKey}T${timeText}`);
  const value = parsed.getTime();
  return Number.isNaN(value) ? Number.NEGATIVE_INFINITY : value;
};

const collapseToAccumulatedDailyRows = (rows = []) => {
  const byDate = new Map();

  rows.forEach((row) => {
    const dateKey = toDateKey(row);
    if (!dateKey) return;

    const generation = asNumber(row, [
      "Solar Units Generated (KWh)",
      "Solar KWh",
      "Day_Generation_kWh",
      "Total Generation (kWh)",
    ]);
    const ts = toTimeValue(row);

    const existing = byDate.get(dateKey);
    if (!existing) {
      byDate.set(dateKey, {
        ...row,
        Date: dateKey,
        "Solar Units Generated (KWh)": generation,
        _gen: generation,
        _ts: ts,
      });
      return;
    }

    const shouldReplace = generation > existing._gen || (generation === existing._gen && ts >= existing._ts);
    if (shouldReplace) {
      byDate.set(dateKey, {
        ...row,
        Date: dateKey,
        "Solar Units Generated (KWh)": generation,
        _gen: generation,
        _ts: ts,
      });
    }
  });

  return Array.from(byDate.values())
    .sort((a, b) => String(a.Date).localeCompare(String(b.Date)))
    .map(({ _gen, _ts, ...cleanRow }) => cleanRow);
};

export const SolarTab = () => {
  const [isExporting, setIsExporting] = useState(false);
  const { startDate, endDate } = useDateStore();
  const {
    data: solarData,
    isLoading: dataLoading,
    error: dataError,
  } = useSolarData(startDate, endDate);
  const { data: last7DaysData } = useLast7DaysData(startDate, endDate);
  const { data: smbStatusData } = useSmbStatusData();
  const { data: inverterStatusData } = useInverterStatusData();

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await exportAPI.exportSolar(startDate, endDate);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Solar_Report_${new Date().toISOString().split("T")[0]}.xlsx`,
      );
      document.body.appendChild(link);
      link.click();
      link.parentElement.removeChild(link);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Failed to export file");
    } finally {
      setIsExporting(false);
    }
  };

  if (dataLoading) {
    return <LoadingSpinner message="Loading solar data..." />;
  }

  if (dataError) {
    return (
      <div className="text-center py-12">
        <AlertCircle
          className="mx-auto text-[var(--danger-600)] mb-3"
          size={32}
        />
        <p className="text-[var(--danger-600)] text-lg">Error loading data</p>
      </div>
    );
  }

  const recentSolarRows = getRecentRows(solarData?.data || [], 7);
  const readableLast7Rows = collapseToAccumulatedDailyRows(
    getRecentRows(last7DaysData?.data || [], 7),
  );
  const latestSolarRecord = getLatestRow(recentSolarRows);
  const effectiveDate = latestSolarRecord?.Date || latestSolarRecord?.Timestamp;
  const todaySolarRows = getRowsForDate(recentSolarRows, effectiveDate);
  const latestSolarRow = getLatestRow(todaySolarRows);
  const latestSmbRow = getLatestRow(smbStatusData?.data || []);
  const inverterRows = Array.isArray(inverterStatusData?.data) ? inverterStatusData.data : [];
  const latestSolarEnergyGenerated = asNumber(latestSolarRow, [
    "Generation (Wh)",
    "Total Generation (Wh)",
    "Solar Units Generated (KWh)",
    "Solar KWh",
    "Day_Generation_kWh",
    "Total Generation (kWh)",
  ]);
  const latestEstimatedSavings = asNumber(latestSolarRow, [
    "Energy Saving (INR)",
    "Energy Saving in INR",
  ]);
  const smbStatuses = ["SMB1", "SMB2", "SMB3", "SMB4", "SMB5"].map((smb) => ({
    name: smb,
    status: (latestSmbRow?.[`${smb} Status`] || "UNKNOWN").toString(),
  }));

  const inverterStatuses = inverterRows.map((row) => ({
    name: row?.name || "INV",
    status: (row?.status || "UNKNOWN").toString(),
  }));

  const latestInverterFaultCount = inverterStatuses.filter((inv) => {
    const normalized = String(inv.status || "").toUpperCase();
    return !["ONLINE", "ON", "ACTIVE", "RUNNING", "HEALTHY", "OK"].includes(normalized);
  }).length;

  const smbChartData =
    recentSolarRows?.map((item) => ({
      Date: item.Date,
      "Solar Energy Generated (kWh)":
        asNumber(item, [
          "Solar Units Generated (KWh)",
          "Solar KWh",
          "Day_Generation_kWh",
        ]),
      "SMB1 Energy Generated (kWh)": asNumber(item, ["SMB1 (KWh)", "SMB1 (kW)"]),
      "SMB2 Energy Generated (kWh)": asNumber(item, ["SMB2 (KWh)", "SMB2 (kW)"]),
      "SMB3 Energy Generated (kWh)": asNumber(item, ["SMB3 (KWh)", "SMB3 (kW)"]),
      "SMB4 Energy Generated (kWh)": asNumber(item, ["SMB4 (KWh)", "SMB4 (kW)"]),
      "SMB5 Energy Generated (kWh)": asNumber(item, ["SMB5 (KWh)", "SMB5 (kW)"]),
    })) || [];

  const weeklyTrendData =
    readableLast7Rows?.map((item) => ({
      Date: item?.Date,
      "Solar Energy Generated (KWh)":
        asNumber(item, ["Generation (Wh)", "Total Generation (Wh)"]) ||
        asNumber(item, ["Total Generation (kWh)"]) * 1000,
    })) || [];

  const readableSolarTableRows = readableLast7Rows.map((item) => ({
    Date: item?.Date,
    Day: item?.Day,
    "Total Generation (KWh)":
      asNumber(item, ["Generation (Wh)", "Total Generation (Wh)"]) ||
      asNumber(item, ["Total Generation (kWh)"]) * 1000,
  }));

  return (
    <div className="space-y-10">
      <div>
        <h2 className="text-2xl font-bold section-title mb-4">
          Key Metrics for Today
        </h2>
        <p className="text-sm text-[var(--text-muted)] mb-5">
          Date: {formatDisplayDate(effectiveDate)}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard
            title="Solar Energy Generated"
            value={latestSolarEnergyGenerated}
            unit="Wh"
            color="yellow"
            icon={Sun}
          />
          <KPICard
            title="Estimated Energy Cost Savings"
            value={latestEstimatedSavings}
            unit="INR"
            color="green"
            icon={DollarSign}
          />
          <KPICard
            title="Inverter Fault Count"
            value={latestInverterFaultCount}
            unit="Count"
            color={latestInverterFaultCount > 0 ? "red" : "green"}
            icon={latestInverterFaultCount > 0 ? AlertCircle : CheckCircle2}
          />
        </div>
      </div>

      <div className="surface-card rounded-2xl p-8">
        <h2 className="text-2xl font-bold section-title mb-5 flex items-center gap-2">
          <Zap className="text-[var(--accent-500)]" size={28} />
          SMB Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-5">
          {smbStatuses.map((inverter, idx) => (
            <InverterStatus
              key={idx}
              name={inverter.name}
              status={inverter.status}
            />
          ))}
        </div>
      </div>

      <div className="surface-card rounded-2xl p-8">
        <h2 className="text-2xl font-bold section-title mb-5 flex items-center gap-2">
          <Zap className="text-[var(--accent-500)]" size={28} />
          Inverter Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-5">
          {(inverterStatuses.length ? inverterStatuses : [
            { name: "INV_1", status: "UNKNOWN" },
            { name: "INV_2", status: "UNKNOWN" },
            { name: "INV_3", status: "UNKNOWN" },
            { name: "INV_4", status: "UNKNOWN" },
            { name: "INV_5", status: "UNKNOWN" },
          ]).map((inverter, idx) => (
            <InverterStatus
              key={idx}
              name={inverter.name}
              status={inverter.status}
            />
          ))}
        </div>
      </div>

      <div className="w-full">
        <AreaChartComponent
          data={weeklyTrendData}
          title="Solar Energy Generation Trend (Last 7 Days)"
          dataKeys={["Solar Energy Generated (KWh)"]}
          colors={["#8f7a58"]}
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold section-title">
            Detailed Solar Data (Last 7 Days)
          </h2>
          <ExportButton
            onClick={handleExport}
            isLoading={isExporting}
            label="Export Excel"
          />
        </div>
        <DataTable
          data={readableSolarTableRows}
          columns={[
            "Date",
            "Day",
            "Total Generation (KWh)",
          ]}
          centered
        />
      </div>
    </div>
  );
};
