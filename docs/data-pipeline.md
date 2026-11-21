# Data pipeline

Algorithm data goes **speedcubedb.com → scraper → `shared/data/raw/*.json` → seed → Postgres**. All steps are run by hand; nothing is scheduled. The Celery worker is a separate, placeholder path.

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

```powershell
docker compose exec backend python -m seed.seed_algorithms
```

- The script does its work at **import time** (there is no `main()` or `__main__` guard). It reads `shared/data/raw/` relative to the working directory, which is `/backend` in the container, where `shared/` is bind-mounted.
- For each subset and case, it looks up `algorithmcase` by `(subset, name, subgroup)` and inserts it if missing (committing per case to get its id). For each solution, it looks up `algorithmsolution` by `(case_id, solution, orientation)` and inserts it if missing. One final commit.
- **Idempotent:** re-running adds only new rows. It never updates or deletes, so a changed `setup` or a removed solution in the JSON isn't reflected.
- **Open question:** `orientation` is inserted as the JSON string (`"0"`) into an int column. It works today, presumably through implicit casting by SQLModel/psycopg2/Postgres. I haven't checked which layer does the conversion.
- The tables must already exist. They're created by `create_all` when the API starts ([backend.md](backend.md#migration-status)).

## Celery tasks

| Piece | Code |
|---|---|
| Celery app `cube_tutor`: broker `redis://$REDIS_HOST:6379/0`, result backend `.../1`, includes `shared.tasks` | [`shared/celery_app.py`](../shared/celery_app.py) |
| Worker entry point: imports `celery_app`; Compose runs `celery -A main worker` | [`worker/main.py`](../worker/main.py), [`docker-compose.yml`](../docker-compose.yml) |
| The only task: `process_image(data: str)` prints its input, sleeps 3 s, returns `"done"` | [`shared/tasks.py`](../shared/tasks.py) |
| Producer: `POST /v1/images/upload` calls `process_image.delay("fake data!")` | [`backend/app/api/routes/images.py`](../backend/app/api/routes/images.py) |

- The API and the worker share the task code through the `shared/` bind mount, not a package.
- The worker image installs only Celery and Redis ([`worker/requirements.txt`](../worker/requirements.txt)), so tasks can't touch the database today.
- **Open question:** results go to Redis db 1, but nothing reads them and no API endpoint exposes a task's status.
- **Open question:** the worker image installs `ffmpeg`, `libsm6` and `libxext6` ([`worker/dockerfile`](../worker/dockerfile)), the usual OpenCV system dependencies, but OpenCV isn't in its requirements. These look like preparation for image processing that hasn't been written.
