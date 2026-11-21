# Data pipeline

Algorithm data goes **speedcubedb.com → scraper → `shared/data/raw/*.json` → seed → Postgres**. Scraping is run by hand. Seeding runs on every `docker compose up` (the `migrate` service). The Celery worker is a separate, placeholder path.

## Scraper

[`scraper/`](../scraper/) is a standalone script (requests + BeautifulSoup, [`scraper/requirements.txt`](../scraper/requirements.txt), UTF-16). It isn't in Docker Compose.

```bash
cd scraper && python main.py     # must run from scraper/: output paths are relative ("../shared/data/raw/...")
```

- [`main.py`](../scraper/main.py) runs the three subset scrapers in turn. Each ([`f2l_scraper.py`](../scraper/scrapers/f2l_scraper.py), [`oll_scraper.py`](../scraper/scrapers/oll_scraper.py), [`pll_scraper.py`](../scraper/scrapers/pll_scraper.py)) calls `scrape_subset(url)` and writes `{"subset": ..., "cases": [...]}`.
- [`base_scraper.py`](../scraper/scrapers/base_scraper.py) `scrape_subset`:
  - GETs the page with a 5 s timeout.
  - Selects `.singlealgorithm` elements and reads `data-alg` (name), `data-subgroup` and the `.setup-case` text.
  - Groups by `(name, subgroup)`. For each `div[data-ori]` it collects every `.formatted-alg` as `{orientation, alg}`.
- If the request fails, the error is printed and the function then crashes with an unbound `html_doc`. There's no retry and no partial output.
- **Open question:** whether the scraper still works against the current site. The committed JSON is the only known output.

## Raw JSON shape

Files: [`shared/data/raw/f2l.json`](../shared/data/raw/f2l.json), [`oll.json`](../shared/data/raw/oll.json), [`pll.json`](../shared/data/raw/pll.json).

```json
{
  "subset": "OLL",
  "cases": [
    {
      "name": "OLL 1",
      "subgroup": "Dot Case",
      "setup": "F R' F' R U2' F R' F' R2' U2' R'",
      "solutions": [
        { "orientation": "0", "alg": "R U2 R2 F R F' U2 R' F R F'" }
      ]
    }
  ]
}
```

| Subset | Cases | Solutions | Subgroups | `orientation` values |
|---|---|---|---|---|
| F2L | 41 | 622 | 6 | "0"–"3" |
| OLL | 57 | 228 | 14 | "0" |
| PLL | 21 | 84 | 3 | "0" |

- `orientation` is a **string** in the JSON and an **int** in the database.
- **Open question:** what `orientation` means on speedcubedb. The engine tests read F2L "0"–"3" as the target slot (FR, FL, BL, BR) and pass with that reading ([`algorithms.test.ts`](../frontend/tests/engine/algorithms.test.ts)). The app doesn't use it yet.
- `setup` and `alg` use standard notation, including wide moves, slices, rotations, `2'` and parentheses. All 934 solutions parse and solve their setup in the engine tests.

## Seeding

[`backend/seed/seed_algorithms.py`](../backend/seed/seed_algorithms.py):

- **On start:** the Compose `migrate` service runs `alembic upgrade head && python -m seed.seed_algorithms`. `backend` and `celery` start only after it exits 0 ([ADR 0005](decisions/0005-one-python-package-uv.md)).
- **By hand** (e.g. after re-scraping): `docker compose run --rm migrate`, or `docker compose exec backend python -m seed.seed_algorithms`.
- **Data dir:** `$SEED_DATA_DIR` if set, else `<repo root>/shared/data/raw`, resolved from the script's own path (`Path(__file__).parents[2]`), not the working directory. In the image the code is at `/app` and the Dockerfile copies the data to `/shared/data/raw`, so the same default works on the host and in the container. Tests point `SEED_DATA_DIR` at a temp folder ([`test_seed.py`](../backend/tests/test_seed.py)).
- `main()` loads `f2l.json`, `oll.json` and `pll.json`, then seeds. Nothing runs at import time.
- For each subset and case, it looks up `algorithmcase` by `(subset, name, subgroup)` and inserts it if missing (committing per case to get its id). For each solution, it looks up `algorithmsolution` by `(case_id, solution, orientation)` and inserts it if missing. One final commit.
- **Idempotent:** re-running adds only new rows. It never updates or deletes, so a changed `setup` or a removed solution in the JSON isn't reflected.
- **Open question:** `orientation` is inserted as the JSON string (`"0"`) into an int column. It works today, presumably through implicit casting by SQLModel/psycopg2/Postgres. I haven't checked which layer does the conversion.
- The tables must already exist. The backend container creates them with `alembic upgrade head` before the API starts ([backend.md](backend.md#migrations)).

## Celery tasks

| Piece | Code |
|---|---|
| Celery app `cube_tutor`: broker `CELERY_BROKER_URL`, result backend `CELERY_RESULT_BACKEND` (Compose: Redis db 0 / 1; see [configuration](backend.md#configuration)), includes `app.worker.tasks` | [`backend/app/worker/celery_app.py`](../backend/app/worker/celery_app.py) |
| Worker: the backend image, run as `celery -A app.worker.celery_app worker --loglevel=info` | [`docker-compose.yml`](../docker-compose.yml) |
| The only task: `process_image(data: str)` prints its input, sleeps 3 s, returns `"done"` | [`backend/app/worker/tasks.py`](../backend/app/worker/tasks.py) |
| Producer: `POST /v1/images/upload` calls `process_image.delay("fake data!")` | [`backend/app/api/routes/images.py`](../backend/app/api/routes/images.py) |

- The API and the worker are one package with one dependency set, so tasks can import the models and `app.core.db` ([ADR 0005](decisions/0005-one-python-package-uv.md)).
- **Open question:** results go to Redis db 1, but nothing reads them and no API endpoint exposes a task's status.
