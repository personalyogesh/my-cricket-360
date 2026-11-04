# My Cricket 360 — Web

Next.js App Router app with **hostname-based club branding**.

## Dev

```bash
npm install
npm run dev
```

Listens on **http://0.0.0.0:43123**.

- `localhost:43123` — platform chooser  
- `starks.localhost:43123` — Starks  
- `steelers.localhost:43123` — Steelers  

## Tests

```bash
npm test
```

Hostname allowlist tests live in `src/lib/clubs/resolve.test.ts`.
