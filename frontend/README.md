# Codent — Frontend

Next.js UI for Codent: repo input → indexing status → a tabbed workspace
(Chat, Impact Explorer, Stats), with inline citations and a code viewer.

## Setup
```bash
npm install
cp .env.local.example .env.local   # point NEXT_PUBLIC_API_BASE at your backend
npm run dev
```
Open http://localhost:3000.

## Backend CORS
Add this to `backend/app/main.py` right after `app = FastAPI(...)`:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])
```

## What's here
```
app/
  layout.tsx, globals.css, page.tsx     # routing, tabbed workspace
components/
  Header.tsx, Logo.tsx, AboutModal.tsx  # branding + about
  Tabs.tsx                               # segmented tab control
  Chat.tsx, Message.tsx, CitationChip.tsx, CodeViewer.tsx   # /ask + /query
  ImpactExplorer.tsx                     # radial graph over /impact (Phase 10)
  StatsPanel.tsx                         # charts from /ingest's own numbers
lib/
  api.ts      # typed calls to /ingest, /ask, /query, /impact
  github.ts   # client-side URL validation
```

**Impact Explorer** and **Stats** both use backend endpoints/data that already
existed (Phase 10's `/impact`, and the numbers `/ingest` already returns) — no
backend changes were needed to add them.

## Deploy (Vercel)
```bash
npm i -g vercel
vercel
```
Set `NEXT_PUBLIC_API_BASE` to your deployed backend URL in Vercel project
settings, then redeploy. Your backend's `allow_origins` needs that same
Vercel domain added.
