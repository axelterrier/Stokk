# FoodTracker — Claude Code Context

Household food stock management app for a shared home. Multi-user, barcode scanning, expiry date tracking.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 (async), asyncpg |
| Database (business) | PostgreSQL — households, users, stock, expiry dates |
| Database (product ref) | MongoDB — OpenFoodFacts dump (read-only) |
| Frontend | Vue 3 + TypeScript + Vite |
| Package manager (front) | npm |

---

## Project Structure

```
foodtracker-poc/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, lifespan (init_db)
│   ├── requirements.txt
│   ├── .env                           # Local config (not committed)
│   ├── .env.example                   # Template
│   ├── seed.sql                       # Creates default household + admin user
│   └── app/
│       ├── core/
│       │   └── config.py              # pydantic-settings — reads .env
│       ├── db/
│       │   └── database.py            # AsyncSession factory, MongoDB client, init_db()
│       ├── models/
│       │   └── models.py              # SQLAlchemy ORM models
│       ├── schemas/
│       │   └── schemas.py             # Pydantic request/response schemas
│       ├── services/
│       │   └── product_service.py     # Barcode lookup: PG cache → MongoDB fallback
│       └── routes/
│           └── stock.py               # All API routes
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── .env                           # VITE_API_URL, VITE_HOUSEHOLD_ID
    └── src/
        ├── main.ts
        ├── App.vue                    # Root component — orchestrates all state
        ├── style.css                  # Global design system (CSS variables, dark theme)
        ├── types/
        │   └── index.ts               # TypeScript interfaces mirroring backend schemas
        ├── composables/
        │   └── useApi.ts              # All fetch calls to the backend
        └── components/
            ├── ScanInput.vue          # Barcode input field (USB HID + keyboard Enter)
            ├── ProductCard.vue        # Displays scanned product info
            ├── AddStockForm.vue       # Form: quantity, unit, location, expiry date
            ├── StockList.vue          # Stock list with edit + delete buttons
            ├── EditStockModal.vue     # Modal for editing an existing stock item
            └── NutriScore.vue         # Colored badge A→E
```

---

## Environment Variables

### Backend — `backend/.env`

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/foodtracker
MONGO_URL=mongodb://localhost:27017
MONGO_DB=openfoodfacts          # MongoDB database name
MONGO_COLLECTION=products       # Collection name in that database
SECRET_KEY=changeme
CORS_ORIGINS=http://localhost:5173
```

### Frontend — `frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_HOUSEHOLD_ID=00000000-0000-0000-0000-000000000001   # Must match a row in households table
```

---

## Running Locally

```bash
# Backend (activate venv first)
cd backend
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm run dev
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Frontend: http://localhost:5173

---

## Database

### PostgreSQL Tables

| Table | Purpose |
|---|---|
| `households` | Root entity — a shared home (UUID PK) |
| `users` | Household members, bcrypt passwords |
| `products` | Local cache of OpenFoodFacts product data (PK = EAN barcode) |
| `stock_items` | Physical items currently in stock |
| `expiry_dates` | One optional DLC per stock item (1-to-0..1) |

All PK/FK columns use the native PostgreSQL `UUID` type. **Do not use VARCHAR for UUID columns** — asyncpg enforces strict type matching.

Tables are auto-created at startup via `init_db()` (SQLAlchemy `create_all`). Models must be imported in `main.py` before `init_db()` is called, otherwise `Base.metadata` is empty.

### MongoDB — OpenFoodFacts dump

Used **read-only** for product lookups by EAN barcode. Documents are indexed by `code` field (or `_id`). Fields used: `product_name_fr`, `product_name`, `brands`, `categories`, `image_front_url`, `nutriscore_grade`, `nutriments`.

### Product Cache Logic (`product_service.py`)

1. Check `products` table in PostgreSQL (cache hit → return immediately)
2. Query MongoDB by barcode if not cached
3. Save to `products` using `INSERT ... ON CONFLICT DO NOTHING` (safe for concurrent scans)
4. Return product with source tag (`"cache"` or `"openfoodfacts"`)

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/api/v1/scan/{barcode}` | Lookup product (PG cache → MongoDB) |
| POST | `/api/v1/stock` | Add item to stock |
| GET | `/api/v1/stock?household_id=…` | List all stock for a household |
| PATCH | `/api/v1/stock/{item_id}` | Update item (qty, unit, location, expiry…) |
| DELETE | `/api/v1/stock/{item_id}` | Remove item (returns 204 No Content) |
| GET | `/health` | Health check |

### Key Schema Notes

- `POST /stock` requires a prior `GET /scan/{barcode}` — the product must already be in PG cache before adding to stock.
- `PATCH /stock/{item_id}` uses partial updates (all fields optional). Pass `clear_expiry: true` to remove an existing DLC.
- `DELETE` returns **204 No Content** — the frontend must not try to parse the response body.

---

## Frontend Architecture

All API state lives in `App.vue`. Child components are purely presentational and communicate via props + emits.

```
App.vue
├── ScanInput       → emits: scan(barcode)
├── ProductCard     → displays scanned product, source badge
├── AddStockForm    → emits: submit(StockItemCreate), cancel()
├── StockList       → emits: edit(StockItem), delete(id)
│   └── NutriScore  → pure display
└── EditStockModal  → emits: submit(StockItemUpdate), close()
```

`useApi.ts` wraps all `fetch` calls. The 204 case is handled explicitly:
```typescript
if (res.status === 204) return undefined as T
```

---

## Key Design Decisions

- **No authentication** for this POC — `household_id` is hardcoded in `frontend/.env`. Auth can be added later.
- **MongoDB is sync** (pymongo) wrapped in `asyncio.get_event_loop().run_in_executor()` — acceptable for a POC, replace with Motor for production.
- **DLC is not derivable from barcode** — it's per-physical-item and must always be entered manually by the user.
- **Expiry date cascade** — `StockItem.expiry_date` relationship has `cascade="all, delete-orphan"` so deleting a stock item automatically deletes its DLC row.

---

## Known Issues / TODOs

- No authentication / authorization
- No pagination on stock list
- No unit tests
- MongoDB accessed synchronously (pymongo) — should use Motor for async
- No push notifications for expiry alerts (the `alerted` flag exists in DB but nothing reads it)
- No multi-household UI (household is hardcoded in frontend `.env`)
- `image_url` from OpenFoodFacts is often `None` — fallback emoji shown