const MONTHS_SHORT = {
  jan: 0,
  feb: 1,
  mar: 2,
  apr: 3,
  may: 4,
  jun: 5,
  jul: 6,
  aug: 7,
  sep: 8,
  oct: 9,
  nov: 10,
  dec: 11,
};

const asValidDate = (dateObj) =>
  dateObj instanceof Date && !Number.isNaN(dateObj.getTime()) ? dateObj : null;

export const parseDateInput = (dateInput) => {
  if (dateInput instanceof Date) {
    return asValidDate(new Date(dateInput.getTime()));
  }

  if (dateInput === null || dateInput === undefined) {
    return null;
  }

  const text = String(dateInput).trim();
  if (!text) return null;

  const dmySlash = text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (dmySlash) {
    return asValidDate(
      new Date(
        Number(dmySlash[3]),
        Number(dmySlash[2]) - 1,
        Number(dmySlash[1]),
      ),
    );
  }

  const ymdDash = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (ymdDash) {
    return asValidDate(
      new Date(Number(ymdDash[1]), Number(ymdDash[2]) - 1, Number(ymdDash[3])),
    );
  }

  const dMmmYyyy = text.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if (dMmmYyyy) {
    const monthIndex = MONTHS_SHORT[dMmmYyyy[2].toLowerCase()];
    if (monthIndex !== undefined) {
      return asValidDate(
        new Date(Number(dMmmYyyy[3]), monthIndex, Number(dMmmYyyy[1])),
      );
    }
  }

  return asValidDate(new Date(text));
};

export const toDateKey = (dateInput) => {
  const parsed = parseDateInput(dateInput);
  if (!parsed) return "";

  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export const formatDate = (dateInput) => {
  const parsed = parseDateInput(dateInput);
  if (!parsed) {
    return String(dateInput ?? "").trim();
  }

  const day = parsed.getDate();
  const month = parsed.toLocaleString("en-GB", { month: "short" });
  const year = parsed.getFullYear();
  return `${day}-${month}-${year}`;
};

export const formatDateDayMonth = (dateInput) => {
  const parsed = parseDateInput(dateInput);
  if (!parsed) {
    return String(dateInput ?? "").trim();
  }

  const day = parsed.getDate();
  const month = parsed.toLocaleString("en-GB", { month: "short" });
  return `${day}-${month}`;
};

const formatEnIn = (num, decimals) =>
  num.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

export const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined || value === "") return "-";

  const num = parseFloat(String(value).replace(/,/g, "").trim());
  if (Number.isNaN(num)) return String(value);

  return formatEnIn(num, decimals);
};

export const safeNumeric = (value, decimals = 0) => {
  if (value === null || value === undefined || value === "" || value === "-") {
    return decimals > 0 ? (0).toFixed(decimals) : "0";
  }

  const raw = String(value).replace(/,/g, "").trim();
  const num = Number(raw);
  if (Number.isNaN(num)) {
    return decimals > 0 ? (0).toFixed(decimals) : "0";
  }

  return num.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const normalizeIssueText = (value) => {
  if (!value || String(value).trim() === "") return "No issues";

  const lower = String(value).trim().toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
};
