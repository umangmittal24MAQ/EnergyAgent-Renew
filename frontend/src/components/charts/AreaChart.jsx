import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export const AreaChartComponent = ({
  data,
  title,
  dataKeys,
  colors,
  xDataKey = "Date",
}) => {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">{title}</h3>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
        >
          <defs>
            {colors.map((color, idx) => (
              <linearGradient
                key={idx}
                id={`color${idx}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                <stop offset="95%" stopColor={color} stopOpacity={0.1} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey={xDataKey}
            stroke="#94a3b8"
            style={{ fontSize: "11px" }}
          />
          <YAxis stroke="#94a3b8" style={{ fontSize: "11px" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
            }}
            labelStyle={{ color: "#0f172a", fontSize: "12px" }}
            formatter={(value) =>
              value.toLocaleString("en-IN", { maximumFractionDigits: 2 })
            }
          />
          <Legend
            wrapperStyle={{ paddingTop: "8px", color: "#64748b", fontSize: "12px" }}
          />
          {dataKeys.map((key, idx) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[idx]}
              strokeWidth={2}
              fillOpacity={0.7}
              fill={`url(#color${idx})`}
              isAnimationActive={true}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
