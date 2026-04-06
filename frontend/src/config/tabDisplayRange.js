export const TAB_DISPLAY_RANGE_DAYS = {
  grid: 30,
  solar: 30,
  diesel: 30,
};

export const getTabDisplayRange = (tabKey, fallback = 7) => {
  const value = TAB_DISPLAY_RANGE_DAYS?.[tabKey];
  return Number.isFinite(value) && value > 0 ? value : fallback;
};
