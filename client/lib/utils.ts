import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function pct(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "n/a";
  return `${(value * 100).toFixed(digits)}%`;
}

export function num(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "n/a";
  return value.toFixed(digits);
}

export const MATCH_LABEL: Record<string, string> = {
  good: "Good",
  partial: "Partial",
  no_match: "No match",
  absent: "Absent",
};

export const LEDGER_LABEL: Record<string, string> = {
  robust: "Robust",
  id_dependent: "ID-dependent",
  no_data: "No data",
};

export const STATUS_LABEL: Record<string, string> = {
  reported: "Reported",
  not_reported: "Not reported",
  no_data: "No data",
};
