import { describe, expect, it } from "vitest";
import { API_REQUEST_TIMEOUT_MS, BACKEND_CLI_TIMEOUT_MS } from "./api";

describe("API timeout policy", () => {
  it("keeps the browser request timeout longer than the backend CLI timeout", () => {
    expect(API_REQUEST_TIMEOUT_MS).toBeGreaterThan(BACKEND_CLI_TIMEOUT_MS);
  });
});
