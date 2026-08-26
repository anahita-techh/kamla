"use client";

import { SignInButton, SignedIn, SignedOut, UserButton, useAuth } from "@clerk/nextjs";
import { useCallback, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ProbeState = {
  health: string;
  me: string;
};

export default function HomePage() {
  const { getToken } = useAuth();
  const [probe, setProbe] = useState<ProbeState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runProbe = useCallback(async () => {
    setError(null);
    try {
      const healthRes = await fetch(`${apiUrl}/health`);
      const healthJson = await healthRes.json();
      const token = await getToken();
      const meRes = await fetch(`${apiUrl}/v1/me`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const meBody = await meRes.text();
      setProbe({
        health: JSON.stringify(healthJson),
        me: `${meRes.status} ${meBody}`,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    }
  }, [getToken]);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 640, margin: "3rem auto" }}>
      <h1>KAMLA</h1>
      <p>Sign in, then probe the API. This shell only calls GET /health and GET /v1/me.</p>
      <SignedOut>
        <SignInButton />
      </SignedOut>
      <SignedIn>
        <UserButton />
        <p>
          <button type="button" onClick={runProbe}>
            Call /health and /v1/me
          </button>
        </p>
      </SignedIn>
      {error ? <p role="alert">{error}</p> : null}
      {probe ? (
        <pre>
          {`GET /health → ${probe.health}
GET /v1/me → ${probe.me}`}
        </pre>
      ) : null}
    </main>
  );
}
