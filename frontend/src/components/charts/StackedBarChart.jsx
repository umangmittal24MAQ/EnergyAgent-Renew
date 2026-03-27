import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export const StackedBarChart = ({
  data,
  title,
  dataKeys,
  colors,
  xDataKey = "Date",
  xTickFormatter = undefined,
  yTickFormatter = undefined,
  xAxisInterval = 0,
  xAxisAngle = 0,
}) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 8, right: 16, left: -8, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={xDataKey}
            stroke="#94a3b8"
            style={{ fontSize: "11px" }}
            tickFormatter={xTickFormatter}
            interval={xAxisInterval}
            angle={xAxisAngle}
            textAnchor={xAxisAngle === 0 ? "middle" : "end"}
            height={xAxisAngle === 0 ? 30 : 60}
          />
          <YAxis
            stroke="#94a3b8"
            style={{ fontSize: "11px" }}
            tickFormatter={yTickFormatter}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
            }}
            labelStyle={{ color: "#0f172a", fontSize: "12px" }}
            formatter={(value) => {
              const numeric = Number(value);
              if (Number.isNaN(numeric)) return value;
              return numeric.toLocaleString("en-IN", {
                maximumFractionDigits: 2,
              });
            }}
          />
          <Legend
            wrapperStyle={{
              paddingTop: "8px",
              color: "#64748b",
              fontSize: "12px",
            }}
          />
          {dataKeys.map((key, idx) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[idx]}
              stackId="a"
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
