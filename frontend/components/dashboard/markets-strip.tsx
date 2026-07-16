import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { StockBar, StockQuote } from "@/lib/api";
import {
  changeClass,
  friendlyTime,
  money,
  priceChange,
  primaryQuotePrice,
} from "@/lib/format";
import { cn } from "@/lib/utils";

type MarketsStripProps = {
  symbols: string[];
  quotes: StockQuote[];
  bars: StockBar[];
};

type TickerView = {
  ticker: string;
  quote: StockQuote | undefined;
  bar: StockBar | undefined;
  livePrice: number | null;
  lastPrice: number | null;
  change: ReturnType<typeof priceChange> | null;
};

function buildTickers(
  symbols: string[],
  quotes: StockQuote[],
  bars: StockBar[],
): TickerView[] {
  const quotesByTicker = new Map(quotes.map((q) => [q.ticker_name, q]));
  const barsByTicker = new Map(bars.map((b) => [b.ticker_name, b]));

  const names =
    symbols.length > 0
      ? symbols
      : [
          ...new Set([
            ...quotes.map((q) => q.ticker_name),
            ...bars.map((b) => b.ticker_name),
          ]),
        ];

  return names.map((ticker) => {
    const quote = quotesByTicker.get(ticker);
    const bar = barsByTicker.get(ticker);
    const livePrice = quote
      ? primaryQuotePrice(quote.bid_price, quote.ask_price)
      : null;
    const lastPrice = bar ? bar.close : null;
    const change =
      bar !== undefined ? priceChange(bar.open, bar.close) : null;
    return { ticker, quote, bar, livePrice, lastPrice, change };
  });
}

export function MarketsStrip({ symbols, quotes, bars }: MarketsStripProps) {
  const tickers = buildTickers(symbols, quotes, bars);
  const titleSymbols = symbols.length > 0 ? symbols.join(", ") : "—";

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2 text-base">
          <span aria-hidden>📈</span>
          Markets
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2">
          <span>{titleSymbols}</span>
          <Badge variant="outline">
            {tickers.some((t) => t.livePrice !== null) ? "Live / last" : "Last"}
          </Badge>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {tickers.length === 0 ? (
          <p className="text-muted-foreground text-sm italic">
            No market data right now
          </p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-1">
            {tickers.map((t) => (
              <TickerCard key={t.ticker} view={t} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TickerCard({ view }: { view: TickerView }) {
  const { ticker, quote, bar, livePrice, lastPrice, change } = view;
  const isLive = livePrice !== null;
  const displayPrice = isLive ? livePrice : lastPrice;

  return (
    <div className="bg-muted/40 ring-border min-w-[12.5rem] shrink-0 rounded-lg p-3 ring-1">
      <div className="flex items-start justify-between gap-2">
        <p className="font-heading text-sm font-semibold tracking-wide">
          {ticker}
        </p>
        <Badge variant={isLive ? "default" : "secondary"}>
          {isLive ? "Current" : "Last"}
        </Badge>
      </div>

      <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight">
        {displayPrice !== null ? money(displayPrice) : "—"}
      </p>

      {change ? (
        <p
          className={cn(
            "mt-1 text-sm font-medium tabular-nums",
            changeClass(change.direction),
          )}
        >
          {change.arrow} {change.delta >= 0 ? "+" : ""}
          {change.delta.toFixed(2)}
        </p>
      ) : (
        <p className="text-muted-foreground mt-1 text-sm">—</p>
      )}

      <Separator className="my-3" />

      <dl className="space-y-1.5 text-xs">
        {quote ? (
          <>
            <Row label="Bid" value={money(quote.bid_price)} />
            <Row label="Ask" value={money(quote.ask_price)} />
            <Row label="Quote" value={friendlyTime(quote.time)} />
          </>
        ) : null}
        {bar ? (
          <>
            <Row label="Open" value={money(bar.open)} />
            <Row label="Close" value={money(bar.close)} />
            <Row label="Bar" value={friendlyTime(bar.time)} />
          </>
        ) : null}
        {!quote && !bar ? (
          <p className="text-muted-foreground italic">No data</p>
        ) : null}
      </dl>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="tabular-nums font-medium">{value}</dd>
    </div>
  );
}
