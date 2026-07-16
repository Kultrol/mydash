import { MarketsStrip } from "@/components/dashboard/markets-strip";
import { WeatherCarousel } from "@/components/dashboard/weather-carousel";
import { HeadlinesTable } from "@/components/dashboard/headlines-table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getBrief } from "@/lib/api";

/**
 * Daily brief home page.
 * Server-fetches GET /api/v1/brief and renders Markets · Weather · Headlines.
 */
export default async function Home() {
  let briefError: string | null = null;
  let brief = null;

  try {
    brief = await getBrief();
  } catch (err) {
    briefError =
      err instanceof Error ? err.message : "Failed to load daily brief";
  }

  return (
    <div className="bg-background flex flex-1 flex-col">
      <header className="border-border/60 border-b">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-5">
          <div>
            <p className="text-muted-foreground text-xs font-medium tracking-wider uppercase">
              mydash
            </p>
            <h1 className="text-foreground text-2xl font-semibold tracking-tight">
              Daily brief
            </h1>
          </div>
          {/* Settings deferred until config storage is reworked */}
          <Button variant="outline" size="sm" disabled>
            Settings (soon)
          </Button>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8">
        {briefError || !brief ? (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Could not load brief</CardTitle>
              <CardDescription>
                Is the FastAPI server running on port 8000?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p className="text-muted-foreground">
                Start the API, then refresh this page:
              </p>
              <code className="bg-muted block rounded-md px-3 py-2 text-xs">
                uv run uvicorn mydash.api.main:app --reload --port 8000
              </code>
              {briefError ? (
                <p className="text-destructive text-xs">{briefError}</p>
              ) : null}
            </CardContent>
          </Card>
        ) : (
          <section
            aria-label="Brief panels"
            className="flex flex-col gap-6"
          >
            <MarketsStrip
              symbols={brief.symbols}
              quotes={brief.stock_quotes.quotes}
              bars={brief.stock_bars.bars}
            />
            <WeatherCarousel
              city={brief.city}
              weather={brief.weather}
              weatherUnits={brief.weather_units}
            />
            <HeadlinesTable
              newsCategory={brief.news_category}
              headlines={brief.headlines.headlines}
            />
          </section>
        )}
      </main>

      <footer className="border-border/60 text-muted-foreground border-t py-4 text-center text-xs">
        Deploy this app from the{" "}
        <code className="bg-muted rounded px-1 py-0.5">frontend/</code> directory
        on Vercel · API is separate
      </footer>
    </div>
  );
}
