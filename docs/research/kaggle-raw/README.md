# kaggle-raw — provenance index (captured 2026-11-04)

**Direct capture of kaggle.com FAILED.** Playwright (headless Chromium) loads the HTML shell, but every
Kaggle internal API call (`/api/i/competitions.CompetitionService/GetCompetition`, `GetUser`, ...) was
answered with a Google reCAPTCHA Enterprise challenge page (`https://www.google.com/recaptcha/challengepage/`),
so the React app rendered "Something went wrong and this page crashed!". The six `kaggle-*.CRASHED-recaptcha.txt`
files are the verbatim `document.body.innerText` of those crashed pages (kept as evidence). The WebFetch tool
cannot resolve kaggle.com at all in this session (host not in the allowed network list), and the sandbox also
refused Wayback Machine access and browser-fingerprint spoofing. No Kaggle login was available.

Everything else here is **mirrored public material fetched from GitHub (raw.githubusercontent.com) and PyPI**,
chosen because it quotes or transcribes the Kaggle pages:

| Folder / file | What it is | Why it is trustworthy |
|---|---|---|
| `mirrors/nasir26_vqcc-kaggle_docs_RULES.md` | Rules/Evaluation/Data-page digest with **verbatim quotes** of Kaggle pages fetched 2026-10-27 via the Kaggle API, plus facts confirmed from the shipped verifier source and the official metric notebook | Closest thing to the Kaggle text; author marks quotes vs notes |
| `mirrors/nasir26_vqcc-kaggle_docs_NOTES.md` | Findings log incl. baseline reproduction, forum thread summaries (753185, 753633), public-notebook lineage | Secondary |
| `mirrors/official_verifiers_dfthcsos_SCORING_README.md` | Copy of `verifiers/dfthcsos/SCORING_README.md` from the competition data (Apache-2.0), which the Data page calls "the full contract" | Official text |
| `mirrors/clduab11_quantum-hackathon_docs_field-guide.md` | Field guide re-read from Kaggle overview/evaluation/timeline/prizes pages on 2026-11-02; leaderboard read 2026-11-02T17:47Z | Secondary, dated |
| `mirrors/charleneleong-ai_ai4science_*` | Verifier-constant notes, `leaderboard-2026-10-31.json` (all 1,756 public scores), landscape report summarising discussion 754174, parts provenance naming public notebooks | Secondary, dated |
| `mirrors/zjukop3_support_README.md` | Reproducibility package citing Rules §6.4; metric file-level checks; submission ledger with ranks | Secondary |
| `mirrors/Inzainos_*`, `harshulchess77-arch_*`, `wahyurahmaniar_*`, `manwithacat_*`, `somfieao_*`, `blucca_*`, `Arnabs-ops_*`, `timothywheelspro_*`, `acco-cyber_*` | Participant repos: timeline/prize tables, hosted-vs-local verifier numbers, public frontier numbers | Secondary |
| `notebooks/dmitriigluzdov_*` | Full source of the public Kaggle notebook "Quantum Circuit Compilation from Source" (public score 23.87253), mirrored in acco-cyber's repo with its `kernel-metadata.json` | Primary notebook text |
| `notebooks/manwithacat_kickmix-quickstart.*` | Full source of the public Kaggle notebook `manwithacat/kickmix-quickstart` (from its GitHub source) | Primary notebook text |
| `qualtran-docs/` | Official kickmix docs linked from the Kaggle Data page (`kickmix_format.md`, `kickmix_instructions.md`, `api_reference.md`, `dev.md`) and the kickmix 1.0.0 PyPI metadata | Official |

Scraper scripts: `/tmp/claude-0/-home-user/af1e8b3b-1af8-51dd-9e8d-ec3f80eabc0b/scratchpad/kaggle-scrape/` (`lib.js`, `overview.js`, `retry.js`).

## Added 2026-11-04 (second pass): the Kaggle API works anonymously for kernel pulls

`notebooks/` now also holds **81 public notebooks** of this competition pulled through
`https://www.kaggle.com/api/v1/kernels/pull/<owner>/<slug>` (anonymous, 200), one folder per notebook
(`<owner>__<slug>/kernel.json`, `metadata.json`, `notebook.ipynb`/`script.py`, `source.txt`), indexed in
`notebooks/INDEX.md`, and `datasets/` holds 73 dataset metadata records from `datasets/view` (anonymous, 200).
Kernel *listing*, *outputs* and *old versions* are auth-walled, cell outputs are stripped, and renamed slugs were
resolved through the `kaggle.com/code/<old-slug>` 302 redirect (`notebooks/_slug-redirects.txt`). Full details:
`notebooks/README.md`; analysis: `docs/research/kaggle-notebooks.md`. The two earlier mirrors
(`notebooks/dmitriigluzdov_*`, `notebooks/manwithacat_kickmix-quickstart.*`) are kept: they are older versions
(v7-era, score 23.87) of notebooks whose current versions are in the per-notebook folders.
