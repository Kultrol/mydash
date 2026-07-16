"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { HeadLine } from "@/lib/api";
import { friendlyPublished } from "@/lib/format";
import { cn } from "@/lib/utils";

type HeadlinesTableProps = {
  newsCategory: string;
  headlines: HeadLine[];
};

export function HeadlinesTable({
  newsCategory,
  headlines,
}: HeadlinesTableProps) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  function rowKey(item: HeadLine, index: number): string {
    return `${item.source_url}-${index}`;
  }

  function toggle(key: string) {
    setExpandedKey((prev) => (prev === key ? null : key));
  }

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2 text-base">
          <span aria-hidden>📰</span>
          Headlines
        </CardTitle>
        <CardDescription className="flex flex-wrap items-center gap-2">
          <span>Category</span>
          <Badge variant="outline">{newsCategory}</Badge>
          <Badge variant="secondary">{headlines.length} articles</Badge>
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0 pt-0">
        {headlines.length === 0 ? (
          <p className="text-muted-foreground px-4 py-6 text-sm italic">
            No headlines right now
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10 pl-4">#</TableHead>
                <TableHead>Headline</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="pr-4">Published</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {headlines.map((item, index) => {
                const key = rowKey(item, index);
                const expanded = expandedKey === key;
                return (
                  <FragmentRows
                    key={key}
                    index={index}
                    item={item}
                    expanded={expanded}
                    onToggle={() => toggle(key)}
                  />
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function FragmentRows({
  index,
  item,
  expanded,
  onToggle,
}: {
  index: number;
  item: HeadLine;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <TableRow
        className={cn(
          "cursor-pointer",
          expanded && "bg-muted/50",
        )}
        data-state={expanded ? "selected" : undefined}
        tabIndex={0}
        role="button"
        aria-expanded={expanded}
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <TableCell className="text-muted-foreground pl-4 tabular-nums">
          {index + 1}
        </TableCell>
        <TableCell className="max-w-md whitespace-normal font-medium">
          {item.headline}
        </TableCell>
        <TableCell className="max-w-[10rem] whitespace-normal">
          {item.source_url ? (
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary font-medium underline-offset-4 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              {item.publication || "Source"}
            </a>
          ) : (
            item.publication || "Source"
          )}
        </TableCell>
        <TableCell>
          <Badge variant="secondary">{item.category}</Badge>
        </TableCell>
        <TableCell className="text-muted-foreground pr-4">
          {friendlyPublished(item.published_time)}
        </TableCell>
      </TableRow>
      {expanded ? (
        <TableRow className="hover:bg-transparent">
          <TableCell colSpan={5} className="bg-muted/30 px-4 py-3 whitespace-normal">
            <p className="text-muted-foreground mb-1 text-xs font-medium tracking-wide uppercase">
              Description
            </p>
            <p className="text-sm leading-relaxed">
              {item.description?.trim()
                ? item.description
                : "No description available."}
            </p>
          </TableCell>
        </TableRow>
      ) : null}
    </>
  );
}
