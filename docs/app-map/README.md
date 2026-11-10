# CliniqPay flow atlas

Open [index.html](./index.html) in a browser to see every map. Edit only `atlas-data.mjs`.

| Command | What it does |
| --- | --- |
| `npm run atlas` | Validate all maps and rebuild `index.html`, `FLOW-REFERENCE.md`, `atlas.json`. |
| `npm run atlas:status` | Delivered / building / planned, next map, drift issues. |
| `npm run atlas:next` | The next map to build with its steps and track. |
| `npm run atlas:verify` | Optional browser check of this atlas page (needs Playwright). |
| `npm run atlas:check` | Atlas contract: builds, tracks exist, delivered maps have source, build order complete. |

Status values: `planned` (not built), `building` (partly delivered), `delivered` (built, with source references). See `Loop/ATLAS-FIRST.md`. The atlas tools need Node 18+ for development only; the product can use any stack.
