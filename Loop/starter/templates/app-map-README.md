# {{name}} flow atlas

Open [index.html](./index.html) in a browser to see every map. Edit only `atlas-data.mjs`.

| Command | What it does |
| --- | --- |
| `{{cmdAtlas}}` | Validate all maps and rebuild `index.html`, `FLOW-REFERENCE.md`, `atlas.json`. |
| `{{cmdStatus}}` | Delivered / building / planned, next map, drift issues. |
| `{{cmdNext}}` | The next map to build with its steps and track. |
| `{{cmdVerify}}` | Optional browser check of this atlas page (needs Playwright). |
| `{{cmdCheck}}` | Atlas contract: builds, tracks exist, delivered maps have source, build order complete. |

Status values: `planned` (not built), `building` (partly delivered), `delivered` (built, with source references). See `Loop/ATLAS-FIRST.md`. The atlas tools need Node 18+ for development only; the product can use any stack.
