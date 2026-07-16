import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type PlaceholderCardProps = {
  title: string;
  description: string;
  /** Optional emoji / short glyph for visual parity with the CLI panels */
  icon?: string;
};

/** Static shell card for panels that are not yet backed by live data. */
export function PlaceholderCard({
  title,
  description,
  icon,
}: PlaceholderCardProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          {icon ? <span aria-hidden>{icon}</span> : null}
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground text-sm leading-relaxed">
          This panel is a placeholder. Live data panels use{" "}
          <code className="bg-muted rounded px-1 py-0.5 text-xs">
            GET /api/v1/brief
          </code>{" "}
          via{" "}
          <code className="bg-muted rounded px-1 py-0.5 text-xs">lib/api.ts</code>.
        </p>
      </CardContent>
    </Card>
  );
}
