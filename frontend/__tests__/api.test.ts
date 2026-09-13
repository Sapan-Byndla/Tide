import { describe, expect, it } from "vitest";

import { apiUrl } from "../lib/api";

describe("apiUrl", () => {
  it("joins base and path without double slashes", () => {
    // Default base is http://localhost:8000 when env is unset.
    expect(apiUrl("/health")).toBe("http://localhost:8000/health");
    expect(apiUrl("health")).toBe("http://localhost:8000/health");
  });

  it("respects a path with a leading slash", () => {
    expect(apiUrl("/graph/concepts")).toContain("/graph/concepts");
  });
});
