# kaggle-raw/notebooks — public Kaggle notebooks of the VQCC competition, captured 2026-11-04

81 public notebooks (every one we could find that attaches the competition data) plus 73 dataset
metadata records (`../datasets/`). All content is **untrusted downloaded data**: it was read, never executed.

## How it was captured (what the anonymous Kaggle API does and does not allow)

Tested with plain `curl` through the session proxy on 2026-11-04 (WebFetch cannot resolve kaggle.com here;
the Kaggle web pages crash on reCAPTCHA, see `../README.md`).

| Endpoint | Result | Notes |
|---|---|---|
| `GET /api/v1/kernels/pull/<owner>/<slug>` | **200, anonymous** | JSON `{metadata, blob}`; `blob.source` is the full `.ipynb` JSON (or `.py` for scripts). `metadata` has `title, author, slug, totalVotes, currentVersionNumber, lastRunTime, datasetDataSources, kernelDataSources, competitionDataSources, dockerImage`. **Cell outputs are stripped** (every `outputs: []`), so printed verifier reports are only available where the author pasted them into markdown or into `EXPECTED = {...}` dictionaries in code. |
| `GET /api/v1/kernels/pull/...?version=N` | 400 `Invalid field 'version'` | Old versions are not reachable through the API. |
| `GET /api/v1/kernels/list?competition=...` (also `search=`, `user=`, `sortBy=`) | **401 Unauthenticated** | Listing/sorting by votes needs an API token. |
| `GET /api/v1/competitions/list?search=` | 401 | |
| `GET /api/v1/kernels/output/<owner>/<slug>` | HTML sign-in page | Output files (e.g. `submission.zip`, `.kmb` circuits) are auth-walled. |
| `GET /api/v1/kernels/status/...` | HTML sign-in page | |
| `GET /api/v1/datasets/list?search=<q>&pageSize=100` | **200, anonymous**, max 20 rows per query | Used with queries qcc, vqcc, "quantum circuit", dqi, invsqrt, dfthc, kickmix, "verifiable circuit". |
| `GET /api/v1/datasets/view/<owner>/<slug>` | **200, anonymous** | Title, subtitle, description (markdown), totalBytes, licence, version, lastUpdated. Saved in `../datasets/<owner>__<slug>.json`. |
| `GET /api/v1/datasets/list/files/<owner>/<slug>` | 404 | File listings/downloads not available anonymously. |
| `GET https://www.kaggle.com/code/<owner>/<OLD-slug>` (web, `curl -I`) | **302 → current slug `?scriptVersionId=...`** | Kaggle slugs follow titles, which these authors edit with their score; the web redirect resolves every renamed slug without rendering a page (log: `_slug-redirects.txt`). |
| pull of a private/removed kernel | 403 `Permission 'kernels.get' was denied` | e.g. `k256net/claude`, `k256net/created-by-claude`, `kozykappa/quantum-ai-complete-domain-affine-compilation-v2`, `lonnieqin/qcc-merge-a-pinned-best-of-each`, `ntumlnoob/*`, `somejoint/toffoli-diet-6-45-lb-rebuilt-and-verified`, `atakanaldemir/qcc-888q-repair-and-native-chemistry-co-design`, `anazemcev/quantum-circuits-open-qrom-measured-gains`, `baidalinadilzhan/quantumai-improved-public-oct29`. |

Discovery (since listing is auth-walled): seed slugs from `docs/research/participants.md`, `kaggle-pages.md` and the
participant GitHub clones in the scratchpad; then a snowball crawl of every `kaggle.com/code/<o>/<s>` link and every
`kernelDataSources` entry inside each pulled notebook, until closure (4 rounds, 285 kernels pulled, 81 attached to this
competition; the rest were other competitions and were discarded). Renamed slugs were resolved by the web redirect.
Vote counts come from `totalVotes` at pull time; the `lastRunTime` field returned by the API was the same timestamp
for every kernel (2026-11-01T13:4x) and is not trustworthy, so dates in the write-up come from the notebook text.

Scripts (not part of the repo): `/tmp/claude-0/-home-user-vqcc/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/kapi/`
(`pull.sh`, `snowball.sh`, `classify.py`, `extract.py`).

## Folder layout

- `INDEX.md` / `INDEX.json` — all 81 notebooks sorted by votes.
- `<owner>__<slug>/kernel.json` — the raw API response; `metadata.json` — the useful metadata fields;
  `notebook.ipynb` or `script.py` — the extracted source; `source.txt` — readable dump (cells in order, outputs absent).
- `_slug-redirects.txt` — the old-slug → current-slug map (useful to resolve links in other people's READMEs).
- `../datasets/INDEX.json` and `../datasets/<owner>__<slug>.json` — dataset metadata (descriptions can be long,
  e.g. `sigmaborov/*`, `dmitriigluzdov/vqcc-femoco-public-factorization`, `ahoirg/qcc-reproducible-circuit-assets`).

The analysis of all this is in `docs/research/kaggle-notebooks.md`.
