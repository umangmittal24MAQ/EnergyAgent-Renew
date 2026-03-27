import { useQuery } from "@tanstack/react-query";
import { dataAPI, kpiAPI } from "../api/endpoints";

const LIVE_REFRESH_MS = 60 * 1000;

// Data fetching hooks using TanStack Query

export const useUnifiedData = (startDate, endDate) => {
  return useQuery({
    queryKey: ["unified-data", startDate, endDate],
    queryFn: () =>
      dataAPI.getUnified(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useGridData = (startDate, endDate) => {
  return useQuery({
    queryKey: ["grid-data", startDate, endDate],
    queryFn: () => dataAPI.getGrid(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useSolarData = (startDate, endDate) => {
  return useQuery({
    queryKey: ["solar-data", startDate, endDate],
    queryFn: () => dataAPI.getSolar(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useLast7DaysData = (startDate, endDate) => {
  return useQuery({
    queryKey: ["last-7-days-data", startDate, endDate],
    queryFn: () =>
      dataAPI.getLast7Days(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useDieselData = (startDate, endDate) => {
  return useQuery({
    queryKey: ["diesel-data", startDate, endDate],
    queryFn: () =>
      dataAPI.getDiesel(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useDailySummary = (startDate, endDate) => {
  return useQuery({
    queryKey: ["daily-summary", startDate, endDate],
    queryFn: () =>
      dataAPI.getDailySummary(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useSmbStatusData = () => {
  return useQuery({
    queryKey: ["smb-status-live"],
    queryFn: () => dataAPI.getSmbStatus().then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useInverterStatusData = () => {
  return useQuery({
    queryKey: ["inverter-status-live"],
    queryFn: () => dataAPI.getInverterStatus().then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

// KPI hooks
export const useOverviewKPIs = (startDate, endDate) => {
  return useQuery({
    queryKey: ["overview-kpis", startDate, endDate],
    queryFn: () =>
      kpiAPI.getOverview(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useGridKPIs = (startDate, endDate) => {
  return useQuery({
    queryKey: ["grid-kpis", startDate, endDate],
    queryFn: () => kpiAPI.getGrid(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useSolarKPIs = (startDate, endDate) => {
  return useQuery({
    queryKey: ["solar-kpis", startDate, endDate],
    queryFn: () => kpiAPI.getSolar(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};

export const useDieselKPIs = (startDate, endDate) => {
  return useQuery({
    queryKey: ["diesel-kpis", startDate, endDate],
    queryFn: () => kpiAPI.getDiesel(startDate, endDate).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    refetchInterval: LIVE_REFRESH_MS,
    refetchIntervalInBackground: true,
  });
};
