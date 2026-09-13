import { apiBaseUrl } from "@/lib/api";

/**
 * Placeholder landing page. The real trend-intelligence dashboard is out of
 * scope for Phase 0 — this only confirms the frontend builds and can see its
 * configured backend URL.
 */
export default function Home() {
  return (
    <main style={{ maxWidth: 720, margin: "4rem auto", padding: "0 1.5rem" }}>
      <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>TIDE</h1>
      <p style={{ color: "#555" }}>
        Concept Graph and Trend Intelligence System — Phase 0 scaffold.
      </p>
      <p style={{ marginTop: "1.5rem" }}>
        Backend API base URL: <code>{apiBaseUrl()}</code>
      </p>
      <p style={{ color: "#888", fontSize: "0.9rem", marginTop: "2rem" }}>
        The dashboard is intentionally not implemented in this phase.
      </p>
    </main>
  );
}
