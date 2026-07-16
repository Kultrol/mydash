import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { MultiDayForecast, WeatherUnits } from "@/lib/api";
import {
  formatTemp,
  hourLabel,
  nextHours,
  rainAmountLabel,
  tempUnitLabel,
  weatherEmoji,
  windLabel,
  WEATHER_HOURS,
} from "@/lib/format";

type WeatherCarouselProps = {
  city: string;
  weather: MultiDayForecast;
  weatherUnits: WeatherUnits;
};

export function WeatherCarousel({
  city,
  weather,
  weatherUnits,
}: WeatherCarouselProps) {
  const hours = nextHours(weather.days, WEATHER_HOURS);
  const unit = tempUnitLabel(weatherUnits);

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2 text-base">
          <span aria-hidden>🌤️</span>
          Weather
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2">
          <span>{city}</span>
          <Badge variant="outline">{unit}</Badge>
          <Badge variant="secondary">Next {WEATHER_HOURS} hours</Badge>
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {hours.length === 0 ? (
          <p className="text-muted-foreground text-sm italic">
            No forecast data right now
          </p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-1">
            {hours.map(({ month, day, hour }) => (
              <div
                key={`${month}-${day}-${hour.hour}`}
                className="bg-muted/40 ring-border min-w-[11.5rem] shrink-0 rounded-lg p-3 ring-1"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-heading text-xs font-medium tracking-wide">
                    {hourLabel(month, day, hour.hour)}
                  </p>
                  <span className="text-lg" aria-hidden>
                    {weatherEmoji(hour.weather_code)}
                  </span>
                </div>

                <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight">
                  {formatTemp(hour.temperature, weatherUnits)}
                </p>
                <p className="text-muted-foreground text-xs">
                  Feels {formatTemp(hour.feels_like_temperature, weatherUnits)}
                </p>

                <Separator className="my-3" />

                <dl className="space-y-1.5 text-xs">
                  <Row
                    label="Rain"
                    value={`${hour.chance_of_rain}% · ${rainAmountLabel(hour.amount_of_rain, weatherUnits)}`}
                  />
                  <Row label="Clouds" value={`${hour.cloud_cover}%`} />
                  <Row
                    label="Wind"
                    value={windLabel(hour.wind_speed, weatherUnits)}
                  />
                  <Row label="UV" value={hour.uv_index.toFixed(1)} />
                  <Row label="Code" value={String(hour.weather_code)} />
                </dl>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right tabular-nums font-medium">{value}</dd>
    </div>
  );
}
