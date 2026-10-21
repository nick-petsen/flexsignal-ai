const copenhagenFormatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Europe/Copenhagen",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZoneName: "longOffset"
});

const awareTimestamp = /(?:Z|[+-]\d{2}:\d{2})$/i;

/** Presentation only: never assign a timezone to a naive source value. */
export function formatTimestamp(
  value: unknown,
  style: "full" | "short" = "full"
): string {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }

  const source = String(value);
  if (!awareTimestamp.test(source)) {
    return `${source} (timezone unspecified)`;
  }

  const instant = new Date(source);
  if (!Number.isFinite(instant.getTime())) {
    return `${source} (invalid timestamp)`;
  }

  const parts = Object.fromEntries(
    copenhagenFormatter.formatToParts(instant).map(({ type, value }) => [
      type,
      value
    ])
  );
  const offset = parts.timeZoneName.replace("GMT", "UTC");
  const clock = `${parts.hour}:${parts.minute}`;

  if (style === "short") {
    const zone =
      offset === "UTC+01:00"
        ? "CET"
        : offset === "UTC+02:00"
          ? "CEST"
          : offset;
    return `${parts.month}-${parts.day} ${clock} ${zone}`;
  }

  return `${parts.day}.${parts.month}.${parts.year} ${clock} Europe/Copenhagen (${offset})`;
}
