import React, { useState } from "react";
import {
  useDieselData,
  useGridData,
  useOverviewKPIs,
  useSolarData,
  useUnifiedData,
} from "../../hooks/useEnergyData";
import { KPICard } from "../common/KPICard";
import { DataTable } from "../common/DataTable";
import { ExportButton } from "../common/ExportButton";
import { StackedBarChart } from "../charts/StackedBarChart";
import { LineChartComponent } from "../charts/LineChart";
import { DonutChart } from "../charts/DonutChart";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { format, subDays } from "date-fns";
import {
  asNumber,
  formatDisplayDate,
  getRecentRows,
} from "../../utils/recentData";
import {
  formatDate,
  formatDateDayMonth,
  normalizeIssueText,
  safeNumeric,
  toDateKey,
} from "../../utils/reportFormatting";
import { useDateStore } from "../../store/dateStore";
import {
  Zap,
  Sun,
  Leaf,
  TrendingUp,
  ShieldCheck,
  IndianRupee,
} from "lucide-react";

const BASE_REPORT_COLUMNS = [
  "Date",
  "Day",
  "Time",
  "Ambient Temperature (°C)",
  "Grid Units Consumed (kWh)",
  "Solar Units Consumed (kWh)",
  "Total Units Consumed (kWh)",
  "Total Cost (INR)",
  "Solar Cost Savings (INR)",
  "Panels Cleaned",
  "Diesel Consumed (Litres)",
  "Water Treated through STP (kilo Litres)",
  "Water Treated through WTP (kilo Litres)",
  "Issues",
];

const INVERTER_COLUMN_KEYS = ["inv1", "inv2", "inv3", "inv4", "inv5"];

const REPORT_COLUMNS = [...BASE_REPORT_COLUMNS, ...INVERTER_COLUMN_KEYS];

const EXPORT_COLUMNS = [
  ...BASE_REPORT_COLUMNS,
  "Inverter 1 Uptime (h)",
  "Inverter 1 Downtime (h)",
  "Inverter 2 Uptime (h)",
  "Inverter 2 Downtime (h)",
  "Inverter 3 Uptime (h)",
  "Inverter 3 Downtime (h)",
  "Inverter 4 Uptime (h)",
  "Inverter 4 Downtime (h)",
  "Inverter 5 Uptime (h)",
  "Inverter 5 Downtime (h)",
];

const REPORT_COLUMN_MIN_WIDTHS = {
  Date: 110,
  Day: 100,
  Time: 80,
  "Ambient Temperature (°C)": 130,
  "Grid Units Consumed (kWh)": 140,
  "Solar Units Consumed (kWh)": 140,
  "Total Units Consumed (kWh)": 140,
  "Total Cost (INR)": 120,
  "Solar Cost Savings (INR)": 140,
  "Panels Cleaned": 110,
  "Diesel Consumed (Litres)": 130,
  "Water Treated through STP (kilo Litres)": 160,
  "Water Treated through WTP (kilo Litres)": 160,
  Issues: 220,
  inv1: 130,
  inv2: 130,
  inv3: 130,
  inv4: 130,
  inv5: 130,
};

const REPORT_COLUMN_ALIGNMENTS = {
  Date: "left",
  Day: "left",
  Time: "left",
  "Ambient Temperature (°C)": "right",
  "Grid Units Consumed (kWh)": "right",
  "Solar Units Consumed (kWh)": "right",
  "Total Units Consumed (kWh)": "right",
  "Total Cost (INR)": "right",
  "Solar Cost Savings (INR)": "right",
  "Panels Cleaned": "right",
  "Diesel Consumed (Litres)": "right",
  "Water Treated through STP (kilo Litres)": "right",
  "Water Treated through WTP (kilo Litres)": "right",
  Issues: "left",
  inv1: "center",
  inv2: "center",
  inv3: "center",
  inv4: "center",
  inv5: "center",
};

const REPORT_NUMERIC_COLUMNS = [
  "Ambient Temperature (°C)",
  "Grid Units Consumed (kWh)",
  "Solar Units Consumed (kWh)",
  "Total Units Consumed (kWh)",
  "Total Cost (INR)",
  "Solar Cost Savings (INR)",
  "Panels Cleaned",
  "Diesel Consumed (Litres)",
  "Water Treated through STP (kilo Litres)",
  "Water Treated through WTP (kilo Litres)",
];

const NUMERIC_COLUMN_DECIMALS = {
  "Grid Units Consumed (kWh)": 0,
  "Solar Units Consumed (kWh)": 0,
  "Total Units Consumed (kWh)": 0,
  "Total Cost (INR)": 2,
  "Solar Cost Savings (INR)": 2,
  "Panels Cleaned": 0,
  "Diesel Consumed (Litres)": 0,
  "Water Treated through STP (kilo Litres)": 0,
  "Water Treated through WTP (kilo Litres)": 0,
};

const formatAmbientTemperature = (value) => {
  if (value === null || value === undefined || value === "" || value === "-") {
    return "0";
  }

  const text = String(value).trim();
  if (!text) return "0";

  const numeric = Number(text.replace(/,/g, ""));
  if (!Number.isNaN(numeric)) {
    return safeNumeric(numeric, 0);
  }

  return text;
};

const parseInverterData = (rawValue) => {
  if (rawValue === "" || rawValue === null || rawValue === undefined) {
    return { uptime: null, downtime: null };
  }

  try {
    const toMetric = (value) => {
      if (typeof value === "number") return value;
      if (typeof value === "string") {
        const parsed = Number.parseFloat(value);
        return Number.isFinite(parsed) ? parsed : null;
      }
      return null;
    };

    const parsed =
      typeof rawValue === "string" ? JSON.parse(rawValue) : rawValue;
    const uptime = toMetric(parsed?.uptime ?? parsed?.Uptime);
    const downtime = toMetric(parsed?.downtime ?? parsed?.Downtime);
    if (uptime !== null || downtime !== null) {
      return { uptime, downtime };
    }
  } catch {
    // fall through to alternative formats
  }

  const text = String(rawValue).trim();
  if (!text) {
    return { uptime: null, downtime: null };
  }

  // Format: "Uptime: 24.0 hours | Downtime: 0.0 hours"
  if (text.toLowerCase().includes("uptime:")) {
    const uptimeMatch = text.match(/Uptime:\s*([\d.]+)/i);
    const downtimeMatch = text.match(/Downtime:\s*([\d.]+)/i);
    return {
      uptime: uptimeMatch ? Number.parseFloat(uptimeMatch[1]) : null,
      downtime: downtimeMatch ? Number.parseFloat(downtimeMatch[1]) : null,
    };
  }

  // Format: "100.00%" interpreted as uptime percentage of 24h for the day.
  const percentMatch = text.match(/^([\d.]+)\s*%$/);
  if (percentMatch) {
    const pct = Number.parseFloat(percentMatch[1]);
    if (Number.isFinite(pct)) {
      const uptime = Number.parseFloat(((pct / 100) * 24).toFixed(1));
      const downtime = Number.parseFloat((24 - uptime).toFixed(1));
      return { uptime, downtime };
    }
  }

  // Format: "24.0" (uptime-only)
  const numeric = Number.parseFloat(text);
  if (!Number.isNaN(numeric)) {
    return { uptime: numeric, downtime: null };
  }

  return { uptime: null, downtime: null };
};

function InverterCell({ data }) {
  if (data?.uptime === null && data?.downtime === null) {
    return <span className="text-slate-300 text-sm">—</span>;
  }

  return (
    <div className="flex flex-col gap-0.5 text-xs">
      <span className="text-emerald-600 font-medium whitespace-nowrap">
        ↑ {data?.uptime?.toFixed(1) ?? "0.0"}h
      </span>
      <span className="text-rose-500 font-medium whitespace-nowrap">
        ↓ {data?.downtime?.toFixed(1) ?? "0.0"}h
      </span>
    </div>
  );
}

const formatOverviewReportCellValue = (column, value, row) => {
  if (column === "Date") {
    return formatDate(value);
  }

  if (column === "Ambient Temperature (°C)") {
    return formatAmbientTemperature(value);
  }

  if (column === "Issues") {
    return normalizeIssueText(value);
  }

  if (Object.prototype.hasOwnProperty.call(NUMERIC_COLUMN_DECIMALS, column)) {
    return safeNumeric(value, NUMERIC_COLUMN_DECIMALS[column]);
  }

  if (INVERTER_COLUMN_KEYS.includes(column)) {
    return <InverterCell data={row?.[column]} />;
  }

  return value === undefined || value === null ? "" : String(value);
};

const getInverterExportMetric = (stats, key) => {
  if (!stats || typeof stats[key] !== "number") {
    return "—";
  }
  return Number(stats[key].toFixed(1));
};

const getExportCellValue = (column, row) => {
  if (column === "Inverter 1 Uptime (h)") {
    return getInverterExportMetric(row?.inv1, "uptime");
  }
  if (column === "Inverter 1 Downtime (h)") {
    return getInverterExportMetric(row?.inv1, "downtime");
  }
  if (column === "Inverter 2 Uptime (h)") {
    return getInverterExportMetric(row?.inv2, "uptime");
  }
  if (column === "Inverter 2 Downtime (h)") {
    return getInverterExportMetric(row?.inv2, "downtime");
  }
  if (column === "Inverter 3 Uptime (h)") {
    return getInverterExportMetric(row?.inv3, "uptime");
  }
  if (column === "Inverter 3 Downtime (h)") {
    return getInverterExportMetric(row?.inv3, "downtime");
  }
  if (column === "Inverter 4 Uptime (h)") {
    return getInverterExportMetric(row?.inv4, "uptime");
  }
  if (column === "Inverter 4 Downtime (h)") {
    return getInverterExportMetric(row?.inv4, "downtime");
  }
  if (column === "Inverter 5 Uptime (h)") {
    return getInverterExportMetric(row?.inv5, "uptime");
  }
  if (column === "Inverter 5 Downtime (h)") {
    return getInverterExportMetric(row?.inv5, "downtime");
  }
  return formatOverviewReportCellValue(column, row?.[column], row);
};

const asFiniteNumber = (value, fallback = 0) => {
  if (value === undefined || value === null || value === "") return fallback;
  const parsed = Number(String(value).replace(/,/g, "").trim());
  return Number.isFinite(parsed) ? parsed : fallback;
};

const asDisplayNumberOrText = (value) => {
  if (value === undefined || value === null || value === "") return "";
  const text = String(value).trim();
  if (!text) return "";

  const normalized = text.replace(/,/g, "");
  if (/^[-+]?\d*\.?\d+$/.test(normalized)) {
    const parsed = Number(normalized);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return text;
};

const buildOverviewTrendChartData = (rows = []) => {
  const orderedRows = [...rows].sort((a, b) =>
    String(a?.__dateKey || "").localeCompare(String(b?.__dateKey || "")),
  );

  return orderedRows.map((row) => ({
    Date: row?.Date,
    __dateKey: row?.__dateKey,
    "Grid Energy Consumed (kWh)": asFiniteNumber(
      row?.["Grid Units Consumed (kWh)"],
      0,
    ),
    "Solar Energy Generated (kWh)": asFiniteNumber(
      row?.["Solar Units Consumed (kWh)"],
      0,
    ),
    "Diesel Generator Energy Consumed (kWh)": asFiniteNumber(
      row?.["Diesel Consumed (Litres)"],
      0,
    ),
  }));
};

const parseDateKey = (value) => {
  return toDateKey(value);
};

const parseRowTimestamp = (row) => {
  const dateKey = parseDateKey(row?.Date);
  const timeText = String(row?.Time || "00:00:00").trim() || "00:00:00";
  if (!dateKey) return Number.NEGATIVE_INFINITY;
  const parsed = new Date(`${dateKey}T${timeText}`);
  const millis = parsed.getTime();
  return Number.isNaN(millis) ? Number.NEGATIVE_INFINITY : millis;
};

const normalizeOverviewReportRows = (rows = []) => {
  const normalized = (Array.isArray(rows) ? rows : [])
    .map((row) => {
      const dateKey = parseDateKey(row?.Date || row?.Timestamp);
      if (!dateKey) return null;

      const dateText = formatDate(dateKey);
      const dayText = String(row?.Day || "").trim();
      const timeText = String(row?.Time || "00:00:00").trim() || "00:00:00";

      return {
        Date: dateText,
        Day: dayText,
        Time: timeText,
        "Ambient Temperature (°C)": asDisplayNumberOrText(
          row?.["Ambient Temperature (°C)"],
        ),
        "Grid Units Consumed (kWh)": asFiniteNumber(
          row?.["Grid Units Consumed (kWh)"],
          0,
        ),
        "Solar Units Consumed (kWh)": asFiniteNumber(
          row?.["Solar Units Consumed (kWh)"],
          0,
        ),
        "Total Units Consumed (kWh)": asFiniteNumber(
          row?.["Total Units Consumed (kWh)"],
          0,
        ),
        "Total Cost (INR)": asFiniteNumber(row?.["Total Cost (INR)"], 0),
        "Solar Cost Savings (INR)": asFiniteNumber(
          row?.["Solar Cost Savings (INR)"],
          0,
        ),
        "Panels Cleaned": row?.["Panels Cleaned"] ?? 0,
        "Diesel Consumed (Litres)": asDisplayNumberOrText(
          row?.["Diesel Consumed (Litres)"],
        ),
        "Water Treated through STP (kilo Litres)":
          row?.["Water Treated through STP (kilo Litres)"] ?? 0,
        "Water Treated through WTP (kilo Litres)":
          row?.["Water Treated through WTP (kilo Litres)"] ?? 0,
        Issues: normalizeIssueText(row?.Issues),
        inv1: parseInverterData(row?.["INV_1"] ?? row?.["Inverter_1"]),
        inv2: parseInverterData(row?.["INV_2"] ?? row?.["Inverter_2"]),
        inv3: parseInverterData(row?.["INV_3"] ?? row?.["Inverter_3"]),
        inv4: parseInverterData(row?.["INV_4"] ?? row?.["Inverter_4"]),
        inv5: parseInverterData(row?.["INV_5"] ?? row?.["Inverter_5"]),
        __dateKey: dateKey,
      };
    })
    .filter(Boolean)
    .sort((a, b) => parseRowTimestamp(b) - parseRowTimestamp(a));

  const uniqueByDate = new Map();
  normalized.forEach((row) => {
    if (!uniqueByDate.has(row.__dateKey)) {
      uniqueByDate.set(row.__dateKey, row);
    }
  });

  return Array.from(uniqueByDate.values()).slice(0, 30);
};

const formatRupeeValue = (value) =>
  `₹${Math.round(asFiniteNumber(value, 0)).toLocaleString("en-IN")}`;

const escapeForHtml = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");

const buildOverviewChartData = (
  gridRows = [],
  solarRows = [],
  dieselRows = [],
) => {
  const groupedByDate = {};

  const ensureDateBucket = (date) => {
    const key = date || "Unknown";
    if (!groupedByDate[key]) {
      groupedByDate[key] = {
        Date: key,
        "Grid Energy Consumed (kWh)": 0,
        "Solar Energy Generated (kWh)": 0,
        "Diesel Generator Energy Consumed (kWh)": 0,
      };
    }
    return groupedByDate[key];
  };

  gridRows.forEach((row) => {
    const bucket = ensureDateBucket(row?.Date);
    bucket["Grid Energy Consumed (kWh)"] += asNumber(row, [
      "Grid KWh",
      "Grid Units Consumed (KWh)",
      "Total_Import_kWh",
    ]);
  });

  solarRows.forEach((row) => {
    const bucket = ensureDateBucket(row?.Date);
    bucket["Solar Energy Generated (kWh)"] += asNumber(row, [
      "Solar KWh",
      "Solar Units Generated (KWh)",
      "Day_Generation_kWh",
      "Total Generation (kWh)",
    ]);
  });

  dieselRows.forEach((row) => {
    const bucket = ensureDateBucket(row?.Date);
    bucket["Diesel Generator Energy Consumed (kWh)"] += asNumber(row, [
      "Diesel KWh",
      "DG Units Consumed (KWh)",
    ]);
  });

  return Object.values(groupedByDate).sort((a, b) =>
    String(a.Date).localeCompare(String(b.Date)),
  );
};

const sanitizeInsightWording = (items = []) => {
  const cleanupText = (item) => {
    let text = String(item || "")
      .replace(/\{current_date\}/gi, "")
      .trim();

    // Remove leading/trailing as-of phrases and explicit date tokens.
    text = text
      .replace(
        /^\s*as of\s+(today|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}-[A-Za-z]{3}-\d{4})\s*[,:-]?\s*/i,
        "",
      )
      .replace(
        /\s*[,:-]?\s*as of\s+(today|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}-[A-Za-z]{3}-\d{4})\s*\.?\s*$/i,
        "",
      )
      .replace(
        /^\s*for\s+(today|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}-[A-Za-z]{3}-\d{4})\s*[,:-]?\s*/i,
        "",
      )
      .replace(
        /\s*[,:-]?\s*for\s+(today|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|\d{1,2}-[A-Za-z]{3}-\d{4})\s*\.?\s*$/i,
        "",
      )
      .replace(/\bcurrent day\b/gi, "")
      .replace(/\(\s*\d{4}-\d{2}-\d{2}\s*\)/g, "")
      .replace(/\(\s*\d{1,2}-[A-Za-z]{3}-\d{4}\s*\)/g, "")
      .replace(/\bfor\s+\d{4}-\d{2}-\d{2}\b/gi, "")
      .replace(/\bfor\s+\d{1,2}-[A-Za-z]{3}-\d{4}\b/gi, "")
      .replace(/\b\d{4}-\d{2}-\d{2}\b/g, "")
      .replace(/\b\d{1,2}-[A-Za-z]{3}-\d{4}\b/g, "")
      .replace(/\s{2,}/g, " ")
      .trim();

    text = text.replace(/^[,;:\-\s]+/, "").trim();
    if (!text) return "";

    const sentence = text[0].toUpperCase() + text.slice(1);
    return /[.!?]$/.test(sentence) ? sentence : `${sentence}.`;
  };

  return items.map(cleanupText).filter(Boolean);
};

export const OverviewTab = () => {
  const [isExporting, setIsExporting] = useState(false);
  const { startDate, endDate } = useDateStore();

  const reportEndDate = subDays(new Date(), 1);
  const reportStartDate = subDays(reportEndDate, 29);
  const reportStartDateKey = format(reportStartDate, "yyyy-MM-dd");
  const reportEndDateKey = format(reportEndDate, "yyyy-MM-dd");
  const reportDateLabel = formatDate(reportEndDate);

  const {
    data: kpiData,
    isLoading: kpiLoading,
    error: kpiError,
  } = useOverviewKPIs(reportEndDateKey, reportEndDateKey);

  const {
    data: gridData,
    isLoading: gridLoading,
    error: gridError,
  } = useGridData(startDate, endDate);
  const {
    data: solarData,
    isLoading: solarLoading,
    error: solarError,
  } = useSolarData(startDate, endDate);
  const {
    data: dieselData,
    isLoading: dieselLoading,
    error: dieselError,
  } = useDieselData(startDate, endDate);

  const {
    data: unifiedReportData,
    isLoading: unifiedLoading,
    error: unifiedError,
  } = useUnifiedData(reportStartDateKey, reportEndDateKey);

  const reportRows = normalizeOverviewReportRows(unifiedReportData?.data || []);

  const handleExport = async () => {
    try {
      setIsExporting(true);

      if (!reportRows.length) {
        alert("No report rows available to export");
        return;
      }

      const headerRow = EXPORT_COLUMNS.map(
        (column) => `<th>${escapeForHtml(column)}</th>`,
      ).join("");
      const bodyRows = reportRows
        .map(
          (row) =>
            `<tr>${EXPORT_COLUMNS.map((column) => `<td>${escapeForHtml(getExportCellValue(column, row))}</td>`).join("")}</tr>`,
        )
        .join("");

      const htmlWorkbook = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office"
              xmlns:x="urn:schemas-microsoft-com:office:excel"
              xmlns="http://www.w3.org/TR/REC-html40">
          <head>
            <meta charset="UTF-8" />
          </head>
          <body>
            <table border="1">
              <thead><tr>${headerRow}</tr></thead>
              <tbody>${bodyRows}</tbody>
            </table>
          </body>
        </html>
      `;

      const blob = new Blob([`\ufeff${htmlWorkbook}`], {
        type: "application/vnd.ms-excel;charset=utf-8;",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `Detailed_Data_Last_30_Days_${format(new Date(), "yyyyMMdd")}.xls`,
      );
      document.body.appendChild(link);
      link.click();
      link.parentElement.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Failed to export file");
    } finally {
      setIsExporting(false);
    }
  };

  if (
    kpiLoading ||
    gridLoading ||
    solarLoading ||
    dieselLoading ||
    unifiedLoading
  ) {
    return <LoadingSpinner message="Loading overview data..." />;
  }

  if (gridError || solarError || dieselError || unifiedError) {
    return (
      <div className="text-center py-12">
        <p className="text-(--danger-600) text-lg">
          Error loading data. Please check backend connection.
        </p>
        <p className="text-(--text-muted) mt-2">
          {gridError?.message ||
            solarError?.message ||
            dieselError?.message ||
            unifiedError?.message}
        </p>
      </div>
    );
  }

  // Get yesterday's date (previous day) for KPI calculations
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayDate = yesterday.toISOString().split("T")[0]; // Format: YYYY-MM-DD

  const effectiveDate = yesterdayDate;

  // Use 30-day reportRows data (same as the chart above) for accurate source mix calculation
  const totalGridEnergy = reportRows.reduce(
    (sum, row) => sum + asFiniteNumber(row?.["Grid Units Consumed (kWh)"], 0),
    0,
  );
  const totalSolarEnergy = reportRows.reduce(
    (sum, row) => sum + asFiniteNumber(row?.["Solar Units Consumed (kWh)"], 0),
    0,
  );
  const totalDieselEnergy = reportRows.reduce(
    (sum, row) => sum + asFiniteNumber(row?.["Diesel Consumed (Litres)"], 0),
    0,
  );
  const combinedEnergyTotal = totalGridEnergy + totalSolarEnergy + totalDieselEnergy;

  // Build sourceMixData from 30-day totals for accurate percentages
  const sourceMixData = [
    {
      name: "Grid",
      value: combinedEnergyTotal ? (totalGridEnergy / combinedEnergyTotal) * 100 : 0,
    },
    {
      name: "Solar",
      value: combinedEnergyTotal ? (totalSolarEnergy / combinedEnergyTotal) * 100 : 0,
    },
    {
      name: "Diesel",
      value: combinedEnergyTotal ? (totalDieselEnergy / combinedEnergyTotal) * 100 : 0,
    },
  ];
  const trendChartData = buildOverviewTrendChartData(reportRows);
  const yesterdayRecord =
    reportRows.find((row) => row.__dateKey === reportEndDateKey) ||
    reportRows[0] ||
    null;

  const latestGridEnergyConsumed = asFiniteNumber(
    yesterdayRecord?.["Grid Units Consumed (kWh)"],
    0,
  );
  const latestSolarEnergyGenerated = asFiniteNumber(
    yesterdayRecord?.["Solar Units Consumed (kWh)"],
    0,
  );
  const latestTotalEnergyConsumed = asFiniteNumber(
    yesterdayRecord?.["Total Units Consumed (kWh)"],
    latestGridEnergyConsumed + latestSolarEnergyGenerated,
  );
  const latestTotalEnergyCost = asFiniteNumber(
    yesterdayRecord?.["Total Cost (INR)"],
    0,
  );
  const latestEstimatedSavings = asFiniteNumber(
    yesterdayRecord?.["Solar Cost Savings (INR)"],
    0,
  );

  const latestSolarContribution =
    latestTotalEnergyConsumed > 0
      ? (latestSolarEnergyGenerated / latestTotalEnergyConsumed) * 100
      : 0;

  const insightCards = [
    {
      title: "Best Source Mix",
      text: `${(sourceMixData[1]?.value || 0).toFixed(1)}% from solar keeps operating costs stable.`,
      icon: ShieldCheck,
      accent: "text-[#4f8d7d]",
    },
    {
      title: "Cost Exposure",
      text: `Diesel share is ${(sourceMixData[2]?.value || 0).toFixed(1)}%. Lowering it improves margin resilience.`,
      icon: IndianRupee,
      accent: "text-[#3f6894]",
    },
  ];

  const smartInsights = Array.isArray(kpiData?.insights)
    ? sanitizeInsightWording(kpiData.insights)
    : [];

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div>
        <h2 className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-800">
          <TrendingUp className="text-slate-400" size={18} />
          Key Metrics of as of {reportDateLabel}
        </h2>
        <p className="mb-4 text-xs text-slate-400">
          Metrics shown below are for report date: {reportDateLabel}
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <KPICard
            title="Total Campus Energy Consumption"
            value={latestTotalEnergyConsumed}
            unit="KWh"
            subtitle="Grid + Solar combined usage"
            color="blue"
            icon={Zap}
          />
          <KPICard
            title="Solar Energy Generated"
            value={latestSolarEnergyGenerated}
            unit="KWh"
            subtitle="From rooftop solar plant"
            color="yellow"
            icon={Sun}
          />
          <KPICard
            title="Solar Contribution to Total"
            value={latestSolarContribution}
            unit="%"
            subtitle="Renewable energy share"
            color="green"
            icon={Leaf}
          />
          <KPICard
            title="Total Energy Cost"
            displayValue={formatRupeeValue(latestTotalEnergyCost)}
            subtitle="Grid electricity expense"
            color="red"
            icon={IndianRupee}
          />
          <KPICard
            title="Cost Savings from Solar"
            displayValue={formatRupeeValue(latestEstimatedSavings)}
            color="green"
            icon={IndianRupee}
          />
        </div>
      </div>

      <div className="mt-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">
              Smart Insights as of {reportDateLabel}
            </h3>
            <span className="rounded-full border border-slate-200 bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
              AI Generated
            </span>
          </div>
          {smartInsights.length > 0 ? (
            <ul className="list-disc list-inside space-y-1.5">
              {smartInsights.map((item, idx) => (
                <li
                  key={`insight-${idx}`}
                  className="text-sm text-slate-600 leading-snug"
                >
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <ul className="list-disc list-inside space-y-1.5">
              {insightCards.map((item, idx) => (
                <li
                  key={`fallback-insight-${idx}`}
                  className="text-sm text-slate-600 leading-snug"
                >
                  {item.text}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Charts */}
      <div>
        <h2 className="mb-4 text-base font-semibold text-slate-800">
          Energy Trends (Last 30 Days)
        </h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <StackedBarChart
            data={trendChartData}
            title="Daily Energy Mix (Last 30 Days)"
            dataKeys={[
              "Grid Energy Consumed (kWh)",
              "Solar Energy Generated (kWh)",
              "Diesel Generator Energy Consumed (kWh)",
            ]}
            colors={["#3f6894", "#4f8d7d", "#b68656"]}
            xTickFormatter={formatDateDayMonth}
            yTickFormatter={(value) => safeNumeric(value, 0)}
            xAxisInterval={4}
          />
          <LineChartComponent
            data={trendChartData}
            title="Energy Distribution Trend (Last 30 Days)"
            dataKeys={[
              "Grid Energy Consumed (kWh)",
              "Solar Energy Generated (kWh)",
              "Diesel Generator Energy Consumed (kWh)",
            ]}
            colors={["#3f6894", "#4f8d7d", "#b68656"]}
            xTickFormatter={formatDateDayMonth}
            yTickFormatter={(value) => safeNumeric(value, 0)}
            xAxisInterval={4}
          />
        </div>
      </div>

      {/* Added visual features */}
      <DonutChart
        data={sourceMixData}
        title="Energy Source Contribution"
        colors={["#3f6894", "#4f8d7d", "#b68656"]}
      />

      {/* Data Table */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-base font-semibold text-slate-800">
            Detailed Data (Last 30 Days)
          </h2>
          <ExportButton
            onClick={handleExport}
            isLoading={isExporting}
            label="Export Excel"
          />
        </div>
        <DataTable
          data={reportRows}
          columns={REPORT_COLUMNS}
          preserveHeaderCase={true}
          enableAutoLayout={true}
          minTableWidth="1400px"
          columnMinWidths={REPORT_COLUMN_MIN_WIDTHS}
          columnAlignments={REPORT_COLUMN_ALIGNMENTS}
          numericColumns={REPORT_NUMERIC_COLUMNS}
          formatCellValue={formatOverviewReportCellValue}
          wrapColumn="Issues"
          hideColumns={["__dateKey"]}
        />
      </div>
    </div>
  );
};
