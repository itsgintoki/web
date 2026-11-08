# Ankit Sinha — portfolio

Static portfolio at [itsgintoki.github.io/web](https://itsgintoki.github.io/web/).

## Structure

```text
index.html               home: identity, selected work, OSS, activity, contact
work/
├── llm-gateway.html     case study
├── gatekeep.html        case study
├── idleforge.html       case study
├── holdfast.html        case study
└── case-study.css       case-study shell and typography
assets/
├── base.css             design tokens, reset, shared elements
├── site.css             home-only layout
├── activity.js          activity.json → mix, radar, contribution graph, orgs
└── ui.js                stack popover + resume modal (focus trap, inert background)
activity.json            GitHub activity snapshot used by the home page
scripts/update_activity.py   snapshot generator (run by GitHub Actions)
resume.pdf / resume-preview.jpg
```

## Local preview

No build step. Serve the repository root over HTTP so `activity.json` can be fetched:

```sh
python3 -m http.server 8000
# open http://localhost:8000/
```

Opening `index.html` directly with `file://` will block the `activity.json` fetch; the static fallback values still render.

## Editing

- Home layout and components: `assets/site.css` + `index.html`.
- Shared tokens/reset: `assets/base.css`; case-study pages link it before `work/case-study.css`.
- Activity rendering: `assets/activity.js`. The DOM keeps static fallback values so the page is useful before the snapshot loads.
- Modal/popover behavior: `assets/ui.js`. The resume modal marks `.site` as `inert` while open.
- Case studies are standalone HTML pages. Keep their `<head>` meta, canonical URL, and the `.next` chain in sync when adding one.
- The project cards in `index.html` and the case-study footers should stay in the same order: LLM Gateway → GateKeep → IdleForge → HoldFast.

## Activity snapshot

`.github/workflows/update-activity.yml` runs `scripts/update_activity.py` daily (and on manual dispatch), then commits `activity.json` if it changed. The page fetches that file at runtime; no GitHub API call happens in the browser.

## Deployment

GitHub Pages serves the `main` branch from the repository root. Push to `main`; there is no build or deploy workflow. The site is published under `/web/`, so keep asset paths relative (`assets/...`, `../assets/...`) rather than root-absolute, except in `404.html`, where the request path depth is unknown.

`robots.txt` and `sitemap.xml` use the public URL. `404.html` is picked up automatically by GitHub Pages.

## Adding a project

1. Add the card to the Selected work list in `index.html`.
2. Add `work/<slug>.html`, reusing the case-study head and footer.
3. Add it to the `.next` chain on the previous and last case studies.
4. Add the URL to `sitemap.xml`.
5. Update the "Currently working on" block if it is the active project.
