import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("./timestamp.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 }
}).outputText;
const { formatTimestamp } = await import(
  `data:text/javascript,${encodeURIComponent(compiled)}`
);

test("UTC input displays the same instant in Danish winter time", () => {
  assert.equal(
    formatTimestamp("2026-01-15T12:00:00Z"),
    "15.01.2026 13:00 Europe/Copenhagen (UTC+01:00)"
  );
  assert.equal(
    formatTimestamp("2026-01-15T13:00:00+01:00"),
    "15.01.2026 13:00 Europe/Copenhagen (UTC+01:00)"
  );
});

test("UTC input displays Danish summer time", () => {
  assert.equal(
    formatTimestamp("2026-07-15T12:00:00Z"),
    "15.07.2026 14:00 Europe/Copenhagen (UTC+02:00)"
  );
  assert.equal(formatTimestamp("2026-07-15T12:00:00Z", "short"), "07-15 14:00 CEST");
});

test("spring and autumn DST transitions retain the correct offset", () => {
  assert.equal(formatTimestamp("2026-03-29T00:30:00Z", "short"), "03-29 01:30 CET");
  assert.equal(formatTimestamp("2026-03-29T01:30:00Z", "short"), "03-29 03:30 CEST");
  assert.equal(formatTimestamp("2026-10-25T00:30:00Z", "short"), "10-25 02:30 CEST");
  assert.equal(formatTimestamp("2026-10-25T01:30:00Z", "short"), "10-25 02:30 CET");
});

test("naive values remain unassigned to a timezone", () => {
  assert.equal(
    formatTimestamp("2026-04-04T21:00:00"),
    "2026-04-04T21:00:00 (timezone unspecified)"
  );
  assert.equal(formatTimestamp(null), "n/a");
});
