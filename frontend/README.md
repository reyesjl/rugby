# Rugby Frontend

Proprietary — Biasware LLC.

Next.js + TypeScript UI that talks to the FastAPI backend in this monorepo (`api/main.py`). Provides a simple semantic video search UI calling `/videos/search`.

---
## Quick Start
1. Start backend API (from repo root):
	 ```bash
	 uvicorn api.main:app --reload --port 8000
	 ```
2. Start frontend (recommended pnpm):
	 ```bash
	 cd frontend
	 pnpm install
	 pnpm dev
	 ```
3. Open http://localhost:3000 and run a search.

---
## Requirements
- Node 14.17+ (project `engines` currently set to <19). If you use Node 20/22 you can either ignore the warning or relax the `engines` field.
- pnpm (recommended) or npm / yarn.
- Running backend (FastAPI) + Postgres + populated `videos` table for meaningful results (otherwise searches return empty arrays).

### Using nvm (optional)
```bash
nvm install 18
nvm use 18
```

---
## Installation
With pnpm (preferred):
```bash
pnpm install
```
With npm:
```bash
npm install
```

---
## Development
```bash
pnpm dev   # or npm run dev
```
Visit http://localhost:3000

Hot reload is enabled. Type checking runs separately (`pnpm typecheck`) if you add such a script later.

---
## Environment Variables
Create `frontend/.env.local` (not committed):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```
Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Defaults to `http://localhost:8000` if unset.

Add more (e.g. feature flags) here. Never commit secrets; treat this file as developer‑local.

---
## Project Structure
```
frontend/
	package.json
	next.config.js
	tsconfig.json
	src/
		pages/
			_app.tsx         # App wrapper
			index.tsx        # Search UI
		lib/
			api.ts           # API helper (searchVideos)
```

---
## API Integration
The page uses `searchVideos(query, limit)` which calls:
```
GET /videos/search?query=<q>&limit=<n>
```
Expected JSON response:
```json
[
	{ "summary": "...", "path": "/path/to/video1.mp4" },
	{ "summary": "...", "path": "/path/to/video2.mp4" }
]
```
If the backend / DB isn’t ready you’ll get `[]`.

---
## Scripts
| Command            | Purpose                                    |
|--------------------|---------------------------------------------|
| `pnpm dev`         | Start dev server (port 3000)                |
| `pnpm build`       | Production build                            |
| `pnpm start`       | Start prod server (after build)             |
| `pnpm lint`        | Run ESLint (Next core-web-vitals config)    |

You can add a `typecheck` script: `"typecheck": "tsc --noEmit"`.

---
## Build & Run (Production)
```bash
pnpm build
pnpm start  # serves optimized build
```

---
## Docker (Future)
You can containerize by adding a `Dockerfile` like:
```Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY frontend .
RUN pnpm build
EXPOSE 3000
CMD ["pnpm", "start"]
```
Then integrate with existing `compose.yaml` (add a service exposing port 3000 and depending on the backend service).

---
## Linting / Formatting
Run:
```bash
pnpm lint
```
Add Prettier (optional) and a pre-commit hook later if desired.

---
## Testing (Not Yet Added)
Recommended stack: Jest + React Testing Library. Example dev deps to add:
```
pnpm add -D jest @types/jest ts-jest @testing-library/react @testing-library/jest-dom
```
Then configure `jest.config.ts` and add a script.

---
## Troubleshooting
| Issue | Fix |
|-------|-----|
| CORS error in browser | Ensure backend running with updated CORS (http://localhost:3000 allowed) |
| Empty search results | Confirm DB running and `videos` table populated; otherwise indexing pipeline must be executed |
| Engine warning (Node 20+) | Update `"engines"` in `package.json` to include your version |
| 404 on /videos/search | Confirm you hit `http://localhost:8000/videos/search?query=...` and backend path prefix matches |

---
## Next Steps (Suggestions)
1. Add Jest tests for `searchVideos`.
2. Add a global layout & styling (Tailwind or CSS Modules).
3. Introduce API error toast component.
4. Implement pagination or infinite scroll for results.
5. Share typed models by generating TS types from Pydantic (avoid drift).

---
## License
Internal proprietary use only (see root `LICENSE`).
