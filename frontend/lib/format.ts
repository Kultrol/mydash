/**
 * Presentation helpers ported from the CLI Rich renderer
 * (packages/mydash-cli/.../cli/renderers/brief.py) for the web dashboard.
 */

import type { DayForecast, HourForecast, WeatherUnits } from "@/lib/api";

export const WEATHER_HOURS = 6;

export type HourSlot = {
  month: number;
  day: number;
  hour: HourForecast;
};

/** Next *n* hourly slots from now, or the first *n* as fallback. */
export function nextHours(
  days: DayForecast[],
  n: number = WEATHER_HOURS,
): HourSlot[] {
  const flat: HourSlot[] = [];
  for (const day of days) {
    for (const hour of day.hours) {
      flat.push({ month: day.month, day: day.day, hour });
    }
  }
  if (flat.length === 0) return [];

  const now = new Date();
  const upcoming = flat.filter(
    ({ month, day, hour }) =>
      month > now.getMonth() + 1 ||
      (month === now.getMonth() + 1 && day > now.getDate()) ||
      (month === now.getMonth() + 1 &&
        day === now.getDate() &&
        hour.hour >= now.getHours()),
  );
  return (upcoming.length > 0 ? upcoming : flat).slice(0, n);
}

export function money(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

export function formatTemp(temp: number, units: WeatherUnits): string {
  const suffix = units === "imperial" ? "°F" : "°C";
  return `${temp.toFixed(1)}${suffix}`;
}

export function tempUnitLabel(units: WeatherUnits): string {
  return units === "imperial" ? "°F" : "°C";
}

export function windLabel(speed: number, units: WeatherUnits): string {
  const unit = units === "imperial" ? "mph" : "km/h";
  return `${speed.toFixed(1)} ${unit}`;
}

export function rainAmountLabel(amount: number, units: WeatherUnits): string {
  const unit = units === "imperial" ? "in" : "mm";
  return `${amount.toFixed(2)} ${unit}`;
}

export type PriceChange = {
  delta: number;
  arrow: "↑" | "↓" | "→";
  direction: "up" | "down" | "flat";
};

export function priceChange(open: number, close: number): PriceChange {
  const delta = close - open;
  if (delta > 0) return { delta, arrow: "↑", direction: "up" };
  if (delta < 0) return { delta, arrow: "↓", direction: "down" };
  return { delta, arrow: "→", direction: "flat" };
}

/** Prefer mid when both sides live; else the non-zero side. */
export function primaryQuotePrice(
  bid: number,
  ask: number,
): number | null {
  if (bid > 0 && ask > 0) return (bid + ask) / 2;
  if (ask > 0) return ask;
  if (bid > 0) return bid;
  return null;
}

export function friendlyTime(iso: string): string {
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return iso;
  return when.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function friendlyPublished(iso: string): string {
  const when = new Date(iso);
  if (Number.isNaN(when.getTime())) return iso;
  return when.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function hourLabel(month: number, day: number, hour: number): string {
  return `${String(month).padStart(2, "0")}/${String(day).padStart(2, "0")} ${String(hour).padStart(2, "0")}:00`;
}

/** Map WMO weather codes (Open-Meteo) to a short emoji cue. */
export function weatherEmoji(weatherCode: number): string {
  if (weatherCode === 0) return "☀️";
  if (weatherCode === 1 || weatherCode === 2) return "🌤️";
  if (weatherCode === 3) return "☁️";
  if (weatherCode === 45 || weatherCode === 48) return "🌫️";
  if ([51, 53, 55, 56, 57].includes(weatherCode)) return "🌦️";
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(weatherCode)) return "🌧️";
  if ([71, 73, 75, 77, 85, 86].includes(weatherCode)) return "❄️";
  if ([95, 96, 99].includes(weatherCode)) return "⛈️";
  return "🌡️";
}

export function changeClass(direction: PriceChange["direction"]): string {
  if (direction === "up") return "text-emerald-600 dark:text-emerald-400";
  if (direction === "down") return "text-red-600 dark:text-red-400";
  return "text-muted-foreground";
}
