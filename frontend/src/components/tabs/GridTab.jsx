import React, { useState } from "react";
import { useGridData, useLast7DaysData } from "../../hooks/useEnergyData";
import { KPICard } from "../common/KPICard";
import { DataTable } from "../common/DataTable";
import { ExportButton } from "../common/ExportButton";
import { StackedBarChart } from "../charts/StackedBarChart";
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
import { Zap, DollarSign, TrendingUp, AlertCircle } from "lucide-react";

const getRowTimestamp = (row = {}) => {
  const ts = row?.Timestamp || row?.timestamp;
  if (ts) {
    const parsed = new Date(ts).getTime();
    if (!Number.isNaN(parsed)) return parsed;
  }

  const dateText = row?.Date || row?.date;
  if (!dateText) return Number.NEGATIVE_INFINITY;
  const timeText = row?.Time || row?.time || "00:00:00";
  const parsed = new Date(`${dateText}T${timeText}`).getTime();
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed;
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

const getLastEntryPerDay = (rows = [], maxDays = 7) => {
  if (!Array.isArray(rows) || rows.length === 0) return [];

  const sortedDesc = [...rows].sort((a, b) => getRowTimestamp(b) - getRowTimestamp(a));
  const selected = new Map();

  for (const row of sortedDesc) {
    const day = toDateKey(row);
    if (!day) continue;
    if (!selected.has(day)) {
      selected.set(day, row);
    }
    if (selected.size >= maxDays) break;
  }

  return Array.from(selected.values()).sort((a, b) => getRowTimestamp(a) - getRowTimestamp(b));
};

const DEFAULT_UNIT_ENERGY_COST_INR = 7.11;

const _parseOptionalNumber = (value) => {
  if (value === undefined || value === null || value === "") return null;
  const parsed = parseFloat(String(value).replace(/,/g, "").trim());
  return Number.isNaN(parsed) ? null : parsed;
};

const buildGridComputedRow = (row = {}, solarGenerationByDate = {}) => {
  const dateKey = toDateKey(row);
  const gridEnergy = asNumber(row, [
    "Grid Units Consumed (KWh)",
    "Grid KWh",
    "Total_Import_kWh",
  ]);

  const solarEnergy = solarGenerationByDate[dateKey] || 0;

  const totalEnergy = gridEnergy + solarEnergy;

  const unitEnergyCost = DEFAULT_UNIT_ENERGY_COST_INR;

  const totalEnergyCost = totalEnergy * unitEnergyCost;
  const energyCostSavings = (totalEnergy - gridEnergy) * unitEnergyCost;

  const ambientTemp =
    _parseOptionalNumber(row?.["Ambient Temperature °C"]) ??
    _parseOptionalNumber(row?.["Ambient Temperature (°C)"]) ??
    _parseOptionalNumber(row?.["Ambient Temp (°C)"]) ??
    _parseOptionalNumber(row?.["Ambient Temp"]) ??
    _parseOptionalNumber(row?.["Ambient Temperature"]) ??
    _parseOptionalNumber(row?.["Temperature (°C)"]);

  return {
    ...row,
    "Ambient Temperature °C": ambientTemp ?? "",
    "Grid Units Consumed (KWh)": gridEnergy,
    "Solar Units Generated (KWh)": solarEnergy,
    "Total Units Consumed (KWh)": totalEnergy,
    "Total Units Consumed in INR": totalEnergyCost,
    "Energy Saving in INR": energyCostSavings,
  };
};

export const GridTab = () => {
  const [isExporting, setIsExporting] = useState(false);
  const { startDate, endDate } = useDateStore();
  const {
    data: gridData,
    isLoading: dataLoading,
    error: dataError,
  } = useGridData(startDate, endDate);
  const { data: last7DaysData } = useLast7DaysData(startDate, endDate);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await exportAPI.exportGrid(startDate, endDate);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Grid_Report_${new Date().toISOString().split("T")[0]}.xlsx`,
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
    return <LoadingSpinner message="Loading grid data..." />;
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

  const recentGridRows = getLastEntryPerDay(getRecentRows(gridData?.data || [], 7), 7);
  const recentSolarRows = getRecentRows(last7DaysData?.data || [], 7);
  const solarGenerationByDate = recentSolarRows.reduce((acc, row) => {
    const dateKey = toDateKey(row);
    if (!dateKey) return acc;
    const solarWh = asNumber(row, ["Generation (Wh)", "Total Generation (Wh)"]);
    acc[dateKey] = solarWh;
    return acc;
  }, {});

  const computedGridRows = recentGridRows.map((row) =>
    buildGridComputedRow(row, solarGenerationByDate),
  );
  const latestGridRecord = getLatestRow(computedGridRows);
  const effectiveDate = latestGridRecord?.Date || latestGridRecord?.Timestamp;
  const todayGridRows = getRowsForDate(computedGridRows, effectiveDate);
  const latestGridRow = getLatestRow(todayGridRows);

  const latestGridEnergyConsumed = asNumber(latestGridRow, [
    "Grid Units Consumed (KWh)",
    "Grid KWh",
    "Total_Import_kWh",
  ]);
  const latestTotalEnergyConsumed = asNumber(latestGridRow, [
    "Total Units Consumed (KWh)",
    "Total KWh",
    "Total_Import_kWh",
  ]);
  const latestGridEnergyCost = asNumber(latestGridRow, [
    "Total Units Consumed in INR",
    "Grid Cost (INR)",
    "Grid Cost",
    "Cost (INR)",
    "Cost",
  ]);
  const latestGridContribution = latestTotalEnergyConsumed
    ? (latestGridEnergyConsumed / latestTotalEnergyConsumed) * 100
    : 0;

  const chartData =
    computedGridRows?.map((item) => ({
      Date: item.Date,
      "Grid Energy Consumed (kWh)": asNumber(item, [
        "Grid Units Consumed (KWh)",
        "Grid KWh",
        "Total_Import_kWh",
      ]),
      "Total Energy Consumed (kWh)": asNumber(item, [
        "Total Units Consumed (KWh)",
        "Total KWh",
        "Total_Import_kWh",
      ]),
    })) || [];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold section-title mb-4">
          Key Metrics for Today
        </h2>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Date: {formatDisplayDate(effectiveDate)}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Grid Energy Consumed"
            value={latestGridEnergyConsumed}
            unit="kWh"
            color="blue"
            icon={Zap}
          />
          <KPICard
            title="Total Energy Consumed"
            value={latestTotalEnergyConsumed}
            unit="kWh"
            color="blue"
          />
          <KPICard
            title="Grid Contribution To Consumption"
            value={latestGridContribution}
            unit="%"
            color="red"
            icon={TrendingUp}
          />
          <KPICard
            title="Grid Energy Cost"
            value={latestGridEnergyCost}
            unit="INR"
            color="red"
            icon={DollarSign}
          />
        </div>
      </div>

      <StackedBarChart
        data={chartData}
        title="Grid Energy Consumption (Last 7 Days)"
        dataKeys={["Grid Energy Consumed (kWh)", "Total Energy Consumed (kWh)"]}
        colors={["#496e97", "#6e8093"]}
      />

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold section-title">
            Detailed Grid Data (Last 7 Days)
          </h2>
          <ExportButton
            onClick={handleExport}
            isLoading={isExporting}
            label="Export Excel"
          />
        </div>
        <DataTable
          data={computedGridRows}
          columns={[
            "Date",
            "Day",
            "Ambient Temperature °C",
            "Grid Units Consumed (KWh)",
            "Total Units Consumed (KWh)",
            "Total Units Consumed in INR",
            "Energy Saving in INR",
          ]}
        />
      </div>
    </div>
  );
};
