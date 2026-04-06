import React, { useState } from "react";
import { eachDayOfInterval, format, parseISO } from "date-fns";
import { useDieselData } from "../../hooks/useEnergyData";
import { KPICard } from "../common/KPICard";
import { DataTable } from "../common/DataTable";
import { ExportButton } from "../common/ExportButton";
import { StackedBarChart } from "../charts/StackedBarChart";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { exportAPI } from "../../api/endpoints";
import {
  asNumber,
  formatDisplayDate,
  getRecentDateRange,
} from "../../utils/recentData";
import { Droplet, AlertCircle } from "lucide-react";
import { getTabDisplayRange } from "../../config/tabDisplayRange";

export const DieselTab = () => {
  const [isExporting, setIsExporting] = useState(false);
  const dieselDisplayDays = getTabDisplayRange("diesel", 30);
  const {
    startDate: dieselDisplayStartDate,
    endDate: dieselDisplayEndDate,
  } = getRecentDateRange(dieselDisplayDays);

  const {
    data: dieselData,
    isLoading: dataLoading,
    error: dataError,
  } = useDieselData(dieselDisplayStartDate, dieselDisplayEndDate);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await exportAPI.exportDiesel(
        dieselDisplayStartDate,
        dieselDisplayEndDate,
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Diesel_Report_${new Date().toISOString().split("T")[0]}.xlsx`,
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
    return <LoadingSpinner message="Loading diesel data..." />;
  }

  if (dataError) {
    return (
      <div className="text-center py-12">
        <AlertCircle
          className="mx-auto text-(--danger-600) mb-3"
          size={32}
        />
        <p className="text-(--danger-600) text-lg">Error loading data</p>
      </div>
    );
  }

  const rawRows = Array.isArray(dieselData?.data) ? dieselData.data : [];

  const dieselValue = (row) =>
    asNumber(row, [
      "Fuel Consumed (Litres)",
      "Diesel consumed",
      "diesel_consumed",
      "DG Units Consumed (KWh)",
      "Diesel KWh",
    ]);

  const rowsByDate = rawRows.reduce((acc, row) => {
    const dateKey = String(row?.Date || "").slice(0, 10);
    if (!dateKey) return acc;

    const existing = acc[dateKey];
    if (!existing) {
      acc[dateKey] = row;
      return acc;
    }

    const existingTs = new Date(
      `${existing?.Date || ""}T${existing?.Time || "00:00:00"}`,
    ).getTime();
    const currentTs = new Date(
      `${row?.Date || ""}T${row?.Time || "00:00:00"}`,
    ).getTime();

    if (currentTs > existingTs) {
      acc[dateKey] = row;
    }

    return acc;
  }, {});

  let expectedDates = [];
  try {
    expectedDates = eachDayOfInterval({
      start: parseISO(dieselDisplayStartDate),
      end: parseISO(dieselDisplayEndDate),
    }).map((d) => format(d, "yyyy-MM-dd"));
  } catch {
    expectedDates = [];
  }

  const displayDates = expectedDates.slice(-dieselDisplayDays);
  const filledRowsAsc = displayDates.map((date) => {
    const row = rowsByDate[date] || {};
    const fuel = dieselValue(row);
    return {
      ...row,
      Date: date,
      Time: row?.Time || "09:00:00",
      "Fuel Consumed (Litres)": Number.isFinite(fuel) ? fuel : 0,
      "Total Cost (INR)": Number(((Number.isFinite(fuel) ? fuel : 0) * 100).toFixed(2)),
    };
  });

  const sortedRowsDesc = [...filledRowsAsc].sort((a, b) =>
    String(b.Date).localeCompare(String(a.Date)),
  );

  const latestDieselRecord = sortedRowsDesc[0] || null;
  const kpiRow = latestDieselRecord;
  const effectiveDate = kpiRow?.Date || kpiRow?.Timestamp;
  const latestDieselFuelConsumed = dieselValue(kpiRow);

  const groupedByDate = filledRowsAsc.reduce((acc, item) => {
    const key = item?.Date || "Unknown";
    const value = dieselValue(item);
    acc[key] = Math.max(acc[key] || 0, value);
    return acc;
  }, {});

  const chartData = Object.keys(groupedByDate)
    .sort()
    .map((date) => ({
      Date: date,
      "Diesel Fuel Consumed": groupedByDate[date],
    }));

  const totalDieselLast30Days = chartData.reduce(
    (sum, item) => sum + Number(item["Diesel Fuel Consumed"] || 0),
    0,
  );

  const tableRows = sortedRowsDesc.map((row) => {
    const fuel = dieselValue(row);
    return {
      ...row,
      "Fuel Consumed (Litres)": fuel,
      "Total Cost (INR)": Number((fuel * 100).toFixed(2)),
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-800">
          <Droplet className="text-slate-400" size={18} />
          Key Metrics for Today
        </h2>
        <p className="mb-4 text-xs text-slate-400">
          Date: {formatDisplayDate(effectiveDate)}
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 max-w-5xl">
          <KPICard
            title="Diesel Consumed Today"
            value={latestDieselFuelConsumed}
            unit="Litres"
            color="yellow"
            icon={Droplet}
          />
          <KPICard
            title="Diesel Consumed (Last 30 Days)"
            value={totalDieselLast30Days}
            unit="Litres"
            color="red"
            icon={Droplet}
          />
        </div>
      </div>

      <StackedBarChart
        data={chartData}
        title="Diesel Fuel Consumed (Last 30 Days)"
        dataKeys={["Diesel Fuel Consumed"]}
        colors={["#b68656"]}
      />

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-semibold text-slate-800">
            Detailed Diesel Data (Last 30 Days)
          </h2>
          <ExportButton
            onClick={handleExport}
            isLoading={isExporting}
            label="Export Excel"
          />
        </div>
        <DataTable
          data={tableRows}
          columns={[
            "Date",
            "Time",
            "Fuel Consumed (Litres)",
            "Total Cost (INR)",
          ]}
          centered
        />
      </div>
    </div>
  );
};
