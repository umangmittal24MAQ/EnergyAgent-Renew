import React, { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import { parseDateInput } from "../../utils/reportFormatting";

const COLUMN_LABELS = {
  // Date/Time/Day
  Date: "Date",
  Timestamp: "Timestamp",
  Time: "Time",
  Day: "Day",
  "Date Formatted": "Date Formatted",
  "Start Value": "Start Value",
  "End Value": "End Value",
  "Generation (Wh)": "Generation (Wh)",
  "Total Generation (Wh)": "Total Generation (Wh)",
  "Total Generation (KWh)": "Total Generation (KWh)",

  // Backend-renamed columns (from processor.build_unified_dataframe)
  "Grid KWh": "Grid Energy Consumed (kWh)",
  "Solar KWh": "Solar Energy Generated (kWh)",
  "Total KWh": "Total Energy Consumed (kWh)",
  "Grid Cost (INR)": "Grid Energy Cost (INR)",
  "Diesel Cost (INR)": "Diesel Energy Cost (INR)",
  "Total Cost (INR)": "Total Energy Cost (INR)",
  "Energy Saving (INR)": "Energy Cost Savings (INR)",
  "Solar %": "Solar Contribution (%)",
  "Diesel consumed": "Diesel Fuel Consumed (Litres)",
  "Ambient Temp (°C)": "Ambient Temperature (°C)",
  "Inverter Status": "Inverter Status",

  // Solar-specific columns
  "Plant Capacity (KW)": "Plant Capacity (KW)",
  "Irradiance (W/m²)": "Irradiance (W/m²)",

  // Original CSV column names (for backwards compatibility)
  "Grid Units Consumed (KWh)": "Grid Energy Consumed (kWh)",
  "Total Units Consumed (KWh)": "Total Energy Consumed (kWh)",
  "DG Units Consumed (KWh)": "Diesel Generator Energy Consumed (kWh)",
  "Solar Units Generated (KWh)": "Solar Energy Generated (kWh)",
  "Generation (kWh)": "Solar Energy Generated (kWh)",
  "Total Units Consumed in INR": "Total Energy Cost (INR)",
  "Fuel Consumed (Litres)": "Diesel Fuel Consumed (Litres)",
  "DG Runtime (hrs)": "Diesel Generator Runtime (hrs)",
  "Avg Temp": "Ambient Temperature (°C)",
  "Ambient Temperature °C": "Ambient Temperature (°C)",
  "Energy Saving in INR": "Energy Cost Savings (INR)",

  // Email-report detailed table columns
  "Ambient Temperature (°C)": "Ambient Temperature (°C)",
  "Grid Units Consumed (kWh)": "Grid Units Consumed (kWh)",
  "Solar Units Consumed (kWh)": "Solar Units Consumed (kWh)",
  "Total Units Consumed (kWh)": "Total Units Consumed (kWh)",
  "Total Cost (INR)": "Total Cost (INR)",
  "Solar Cost Savings (INR)": "Solar Cost Savings (INR)",
  "solar cost savings (INR)": "Solar Cost Savings (INR)",
  "Panels Cleaned": "Panels Cleaned",
  "Diesel Consumed (Litres)": "Diesel Consumed (Litres)",
  "Water Treated through STP (kilo Litres)":
    "Water Treated through STP (kilo Litres)",
  "Water Treated through WTP (kilo Litres)":
    "Water Treated through WTP (kilo Litres)",
  Issues: "Issues",
  inv1: "Inverter 1",
  inv2: "Inverter 2",
  inv3: "Inverter 3",
  inv4: "Inverter 4",
  inv5: "Inverter 5",

  // Live Google Sheets column names
  DC_Power_kW: "DC Power (kW)",
  AC_Power_kW: "AC Power (kW)",
  Current_Total_A: "Current Total (A)",
  Active_Power_kW: "Active Power (kW)",
  Power_Factor: "Power Factor",
  Frequency_Hz: "Frequency (Hz)",
  Voltage_VLL: "Voltage VLL",
  Voltage_VLN: "Voltage VLN",
  V1: "V1",
  V2: "V2",
  V3: "V3",
  Day_Generation_kWh: "Day Generation (kWh)",
  Total_Import_kWh: "Total Import (kWh)",
  Total_Export_kWh: "Total Export (kWh)",
  DC_Capacity_kWp: "DC Capacity (kWp)",
  AC_Capacity_kW: "AC Capacity (kW)",
  "Total Generation (kWh)": "Total Generation (kWh)",
  "Average Generation (kWh)": "Average Generation (kWh)",
  "Peak Generation (kWh)": "Peak Generation (kWh)",
  "Efficiency (%)": "Efficiency (%)",
  "Import (kWh)": "Import (kWh)",
  "Export (kWh)": "Export (kWh)",
  "SMB1 (kW)": "SMB1 (kW)",
  "SMB2 (kW)": "SMB2 (kW)",
  "SMB3 (kW)": "SMB3 (kW)",
  "SMB4 (kW)": "SMB4 (kW)",
  "SMB5 (kW)": "SMB5 (kW)",
};

const getColumnLabel = (columnName) => {
  if (COLUMN_LABELS[columnName]) {
    return COLUMN_LABELS[columnName];
  }

  return String(columnName).replace(/_/g, " ").replace(/\s+/g, " ").trim();
};

const parseSortableDate = (value) => {
  if (value === undefined || value === null || value === "") return null;

  const text = String(value).trim();
  if (!text) return null;

  const dmyMatch = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (dmyMatch) {
    const parsed = new Date(
      `${dmyMatch[3]}-${dmyMatch[2]}-${dmyMatch[1]}T00:00:00`,
    ).getTime();
    return Number.isNaN(parsed) ? null : parsed;
  }

  const dMmmYyyyMatch = text.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if (dMmmYyyyMatch) {
    const parsed = parseDateInput(text);
    if (parsed) {
      const ts = parsed.getTime();
      return Number.isNaN(ts) ? null : ts;
    }
  }

  const ymdMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (ymdMatch) {
    const parsed = new Date(
      `${ymdMatch[1]}-${ymdMatch[2]}-${ymdMatch[3]}T00:00:00`,
    ).getTime();
    return Number.isNaN(parsed) ? null : parsed;
  }

  const parsed = new Date(text).getTime();
  return Number.isNaN(parsed) ? null : parsed;
};

export const DataTable = ({
  data = [],
  columns = [],
  hideColumns = [],
  centered = false,
  preserveHeaderCase = false,
  enableAutoLayout = false,
  columnMinWidths = {},
  wrapColumn = null,
  columnAlignments = {},
  numericColumns = [],
  formatCellValue = null,
  minTableWidth = "100%",
}) => {
  const [sortColumn, setSortColumn] = useState("Date");
  const [sortDirection, setSortDirection] = useState("desc");

  if (!data || data.length === 0) {
    return (
      <div className="py-6 text-center text-sm text-slate-500">
        No data available
      </div>
    );
  }

  // Get columns to display - only show columns defined in COLUMN_LABELS
  const visibleColumns =
    columns.length > 0
      ? columns.filter(
          (col) => !hideColumns.includes(col) && COLUMN_LABELS[col],
        )
      : Object.keys(data[0]).filter(
          (key) => !hideColumns.includes(key) && COLUMN_LABELS[key],
        );

  // Sort data
  let sortedData = [...data];
  if (sortColumn) {
    sortedData.sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      const aDate = parseSortableDate(aVal);
      const bDate = parseSortableDate(bVal);
      if (aDate !== null && bDate !== null) {
        return sortDirection === "asc" ? aDate - bDate : bDate - aDate;
      }

      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      return sortDirection === "asc"
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr);
    });
  }

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const getMinWidth = (column) => {
    const configured = columnMinWidths?.[column];
    if (configured === undefined || configured === null || configured === "") {
      return undefined;
    }
    return typeof configured === "number"
      ? `${configured}px`
      : String(configured);
  };

  const getColumnAlignment = (column) => {
    const align = columnAlignments?.[column];
    if (align === "left" || align === "right" || align === "center") {
      return align;
    }
    return centered ? "center" : "left";
  };

  const isNumericColumn = (column) =>
    Array.isArray(numericColumns) && numericColumns.includes(column);

  const getHeaderStyle = (column) => {
    const baseStyle = {
      textAlign: getColumnAlignment(column),
    };

    if (!enableAutoLayout) return baseStyle;
    return {
      ...baseStyle,
      minWidth: getMinWidth(column),
      whiteSpace: "normal",
      wordBreak: "break-word",
      lineHeight: 1.4,
      verticalAlign: "bottom",
      fontFamily: "Inter, Segoe UI, Roboto, -apple-system, sans-serif",
      fontSize: "12px",
      fontWeight: 600,
      overflow: "visible",
      textOverflow: "unset",
    };
  };

  const getCellStyle = (column) => {
    const baseStyle = {
      textAlign: getColumnAlignment(column),
      fontVariantNumeric: isNumericColumn(column) ? "tabular-nums" : undefined,
    };

    if (!enableAutoLayout) return baseStyle;

    const isWrapColumn = wrapColumn && column === wrapColumn;
    return {
      ...baseStyle,
      minWidth: getMinWidth(column),
      whiteSpace: isWrapColumn ? "normal" : "nowrap",
      wordBreak: isWrapColumn ? "break-word" : "normal",
      lineHeight: isWrapColumn ? 1.4 : undefined,
      overflow: "visible",
      textOverflow: "unset",
      verticalAlign: "middle",
      fontFamily: "Inter, Segoe UI, Roboto, -apple-system, sans-serif",
      fontSize: "14px",
      fontWeight: 400,
      maxWidth: isWrapColumn ? "280px" : undefined,
    };
  };

  const getDisplayCellValue = (column, row) => {
    const rawValue = row[column];

    if (typeof formatCellValue === "function") {
      return formatCellValue(column, rawValue, row);
    }

    return typeof rawValue === "number"
      ? rawValue.toLocaleString("en-IN", {
          maximumFractionDigits: 2,
        })
      : String(rawValue);
  };

  return (
    <div className="data-table-scroll-container w-full overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table
        className="w-full"
        style={
          enableAutoLayout
            ? {
                tableLayout: "auto",
                width: "max-content",
                minWidth: minTableWidth,
                borderCollapse: "collapse",
              }
            : undefined
        }
      >
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            {visibleColumns.map((column) => (
              <th
                key={column}
                onClick={() => handleSort(column)}
                className={`cursor-pointer select-none px-4 py-3 text-xs font-semibold tracking-wide text-slate-500 transition-colors hover:bg-slate-100 ${preserveHeaderCase ? "" : "uppercase"}`}
                style={getHeaderStyle(column)}
              >
                <div
                  className={`flex items-center gap-2 ${getColumnAlignment(column) === "center" ? "justify-center" : getColumnAlignment(column) === "right" ? "justify-end" : "justify-start"}`}
                >
                  {getColumnLabel(column)}
                  {sortColumn === column &&
                    (sortDirection === "asc" ? (
                      <ChevronUp size={14} className="text-slate-500" />
                    ) : (
                      <ChevronDown size={14} className="text-slate-500" />
                    ))}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, idx) => (
            <tr
              key={idx}
              className={`border-b border-slate-100 transition-colors duration-100 hover:bg-slate-50 ${
                idx % 2 === 0 ? "bg-white" : "bg-slate-50/60"
              }`}
            >
              {visibleColumns.map((column) => (
                <td
                  key={column}
                  className="whitespace-nowrap px-4 py-3 text-sm font-normal text-slate-700"
                  style={getCellStyle(column)}
                >
                  {getDisplayCellValue(column, row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 text-xs font-normal text-slate-400">
        Showing {sortedData.length} records
      </div>
    </div>
  );
};
