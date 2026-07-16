/**
 * Thin client for the mydash FastAPI backend.
 *
 * Env:
 *   NEXT_PUBLIC_API_BASE_URL  e.g. http://localhost:8000
 *   (copy from .env.local.example → .env.local for local dev)
 *   On Vercel: Project Settings → Environment Variables
 */

/** Base URL for the FastAPI server (no trailing slash). */
export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
  if (!base) {
    // Safe default for local dual-process dev; override via env when needed.
    return "http://localhost:8000";
  }
  return base;
}

function apiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${getApiBaseUrl()}${normalized}`;
}

// ---------------------------------------------------------------------------
// Domain types (mirrors mydash.core.models + DailyBrief)
// ---------------------------------------------------------------------------

export type WeatherUnits = "metric" | "imperial";

export type HeadLine = {
  headline: string;
  publication: string;
  description: string | null;
  source_url: string;
  category: string;
  published_time: string;
};

export type NewsHeadlines = {
  headlines: HeadLine[];
};

export type StockQuote = {
  ticker_name: string;
  ask_price: number;
  bid_price: number;
  time: string;
};

export type StockQuotes = {
  quotes: StockQuote[];
};

export type StockBar = {
  ticker_name: string;
  open: number;
  close: number;
  time: string;
};

export type StockBars = {
  bars: StockBar[];
};

export type HourForecast = {
  hour: number;
  temperature: number;
  feels_like_temperature: number;
  cloud_cover: number;
  wind_speed: number;
  chance_of_rain: number;
  amount_of_rain: number;
  weather_code: number;
  uv_index: number;
};

export type DayForecast = {
  month: number;
  day: number;
  hours: HourForecast[];
};

export type MultiDayForecast = {
  days: DayForecast[];
};

/** Aggregated brief DTO from GET /api/v1/brief */
export type DailyBrief = {
  headlines: NewsHeadlines;
  stock_quotes: StockQuotes;
  stock_bars: StockBars;
  weather: MultiDayForecast;
  city: string;
  news_category: string;
  symbols: string[];
  weather_units: WeatherUnits;
};

export type HealthResponse = {
  status: string;
  unique_msg?: string;
};

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/api/v1/health"), {
    next: { revalidate: 30 },
  });
  if (!res.ok) throw new Error(`health failed: ${res.status}`);
  return res.json() as Promise<HealthResponse>;
}

export async function getBrief(): Promise<DailyBrief> {
  const res = await fetch(apiUrl("/api/v1/brief"), {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`brief failed: ${res.status}`);
  return res.json() as Promise<DailyBrief>;
}

export { apiUrl };
