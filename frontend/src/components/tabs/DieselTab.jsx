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
  getLatestRow,
} from "../../utils/recentData";
import { useDateStore } from "../../store/dateStore";
import { Droplet, AlertCircle } from "lucide-react";

export const DieselTab = () => {
  const [isExporting, setIsExporting] = useState(false);
  const { startDate, endDate } = useDateStore();
  const {
    data: dieselData,
    isLoading: dataLoading,
    error: dataError,
  } = useDieselData(startDate, endDate);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const response = await exportAPI.exportDiesel(startDate, endDate);
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
          className="mx-auto text-[var(--danger-600)] mb-3"
          size={32}
        />
        <p className="text-[var(--danger-600)] text-lg">Error loading data</p>
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
      start: parseISO(startDate),
      end: parseISO(endDate),
    }).map((d) => format(d, "yyyy-MM-dd"));
  } catch {
    expectedDates = [];
  }

  const sevenDayDates = expectedDates.slice(-7);
  const filledRowsAsc = sevenDayDates.map((date) => {
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

  const totalDieselLast7Days = chartData.reduce(
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
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold section-title mb-4">
          Key Metrics for Today
        </h2>
        <p className="text-sm text-[var(--text-muted)] mb-4">
          Date: {formatDisplayDate(effectiveDate)}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6 max-w-5xl">
          <KPICard
            title="Diesel Consumed Today"
            value={latestDieselFuelConsumed}
            unit="Litres"
            color="yellow"
            icon={Droplet}
          />
          <KPICard
            title="Diesel Consumed (Last 7 Days)"
            value={totalDieselLast7Days}
            unit="Litres"
            color="blue"
            icon={Droplet}
          />
        </div>
      </div>

      <StackedBarChart
        data={chartData}
        title="Diesel Fuel Consumed (Last 7 Days)"
        dataKeys={["Diesel Fuel Consumed"]}
        colors={["#9f7b52"]}
      />

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold section-title">
            Detailed Diesel Data (Last 7 Days)
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
