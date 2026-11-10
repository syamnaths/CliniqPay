# Loop

Loop is a local-first framework for building software with an AI agent and a human owner. From version 0.4 it is **atlas-first**: every project starts from a flow atlas, every feature is built to its map, and a feature is done only when its map is flipped to delivered with real source references.

Loop is **platform-independent**. You choose the platform at the start: web, Android, iPhone/iPad, mobile for both (Flutter, React Native…), desktop, backend/API, command-line/library, other, or several together. The choice shapes the proof ladder, platform rules, version bumps and the release map. The atlas tools need Node 18+ on your machine only.

## How to use

### What you need

- **Node 18 or later** on your computer. Loop's atlas tools use it. Your app itself can be built with anything.
- **A coding agent**, for example Codex, Claude or Cursor.
- **The agent must know where Loop is.** Either install the Codex plugin (see `INSTALL.md`), or add one line to your first message: *"Loop is at ~/Desktop/Ikigai/Loop."*

### Start a new project (3 ways)

**Way 1: just talk (easiest)**

1. Make an empty folder, for example `~/Desktop/Ikigai/my-app`.
2. Open it in your agent and say: **"Use Loop for this project."**
3. Loop asks all its questions in one message: name, who it is for, what the first release must do, platform, stack, languages, features and whether you have a template page.
4. Answer in plain words. If you are not sure about the platform or stack, Loop gives A/B/C options with a recommendation.
5. Loop sets up the project and starts building the first feature by itself.

**Way 2: fill the form first**

1. Copy `start/START.md` into the empty project folder and fill it in. It is plain text with help lines.
2. Have a basic template page (an HTML page, screenshot, Figma export or folder)? Copy `start/template-page/` into the same folder and put your files inside.
3. Say **"Use Loop for this project."** Loop reads the form, asks only what is missing, and starts building.

**Way 3: terminal**

```
node scripts/loop-init.mjs ~/Desktop/Ikigai/my-app --git            # reads my-app/START.md, or asks the questions here
node scripts/loop-init.mjs ~/Desktop/Ikigai/my-app --git --start    # same, then opens your agent to start building
node scripts/loop-init.mjs ~/Desktop/Ikigai/my-app --brief my-brief.json --platform android
```

`--start` opens Codex by default. To use another agent command, set `LOOP_AGENT`, for example `LOOP_AGENT=claude`. JSON briefs still work (see `examples/`).

### Filling START.md

| Field | Example | Needed? |
| --- | --- | --- |
| Name | Tiny Shop | Yes |
| For | local bakers | Good to have |
| First release must | take cake orders online | Good to have |
| Platform | `web`, `android`, `ios`, `mobile`, `desktop`, `backend`, `cli`, `other`, or several like `web, android` | Yes |
| Stack | React, Flutter, Kotlin, FastAPI, or `to decide` | No |
| Languages | `en, ml` | No (default `en`) |
| Test command | `npm test`, `./gradlew test`, `pytest` | No |
| Template page | path to your page or folder, or use the `template-page/` folder | No |
| Features | `- Order: Choose size > Enter phone > Confirm` | Yes, at least one |

Under a feature you can add indented lines: `fails: ...` (what happens on error), `done when: ...` (how we know it works) and `release: 2` (build it later). If a needed field is empty, Loop tells you exactly which one.

### The template page

- Put your basic page in `template-page/`, or give its path in START.md.
- Loop moves it to `design/template-page/` in the project.
- Every screen then follows its layout, colours, fonts and spacing, until you decide to change the look.
- No template page? Loop designs the first screen and shows it to you.

### What happens after the start

1. Loop builds the **atlas**: a map of the whole product, the build order, one map per feature, how every feature is built, and the release path for your platform. Open `docs/app-map/index.html` to see it.
2. Loop takes the next map, builds it, tests it, and proves it the way your platform needs (browser, emulator, simulator, server or real device).
3. When a feature really works, its map turns from **planned** to **delivered**, with links to the real code.
4. Loop shows you the result in plain words (screenshots for screens) and moves on to the next feature.
5. Loop stops and asks you only for real decisions: publishing, pushing, spending money, deleting data or a product choice. You answer A, B or C.

### Things you can say to the agent

| Say this | What Loop does |
| --- | --- |
| "Use Loop for this project." | Starts a new project, or picks up an existing one |
| "Build the next atlas map." | Builds the next feature in the build order |
| "Resume with Loop." | Reads the handoff and continues from the exact next step |
| "Show status." | Tells you how many maps are delivered and what is next |
| "Add a feature: ..." | Adds a new planned map and track, then builds it in order |
| "Change ... in the ... screen." | Updates the map first, then the code, tests and docs |
| "Prepare the release." | Runs the final legal audit, works through the release map and stops before publishing for your OK |
| "Show legal status." | Shows the legal checklist count and only the items that need you or a lawyer |

### Check progress yourself

| JavaScript projects | Other platforms | What it shows |
| --- | --- | --- |
| `npm run atlas:status` | `node docs/app-map/atlas-status.mjs` | Delivered, building and planned maps, plus the next one |
| `npm run atlas:next` | `node docs/app-map/atlas-status.mjs --next` | The next map with its steps |
| `npm run atlas` | `node docs/app-map/build-atlas.mjs` | Rebuilds the atlas page after map changes |
| `npm run atlas:check` | `node --test docs/app-map/atlas-contract.test.mjs` | Checks the atlas is honest and complete |

`AGENTS.md` in each project lists the exact commands for that project.

### Coming back later

Open the project folder in your agent and say **"Resume with Loop."** The `CURRENT RESUME` block in `HANDOFF.md` tells the agent exactly where it stopped, so you never have to explain again. This works across sessions, agents and computers.

### What the starter creates

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Working agreement every agent reads first |
| `HANDOFF.md` | One `CURRENT RESUME` block: status and the exact next action |
| `.loop/workflow.md`, `.loop/tracks/<map>/spec.md` | Delivery path, modes, and a done-checklist per feature and for release |
| `.loop/platform.md` | Chosen platform: stack, test commands, proof ladder, rules, release path |
| `.loop/legal-checklist.md` | The 20 legal checks for this project, with status and proof |
| `docs/app-map/` | Atlas data, builder, status, atlas check, interactive `index.html`, fix queue |
| `docs/project-brief.md`, `docs/START.md` | The brief, your answers and open questions |
| `design/template-page/` | Your basic template page, when given |
| `Loop/` | Project copy of the policy files |
| `package.json` (JavaScript projects only) | The `npm run atlas*` commands |

### Add Loop to an existing project

```
node scripts/loop-init.mjs ~/Desktop/Ikigai/existing-app --adopt --name "Existing App" --platform android
```

Without `--platform`, Loop guesses from the files and tells you. It adds the atlas tools, policy copy, tracks and platform notes. **Nothing existing is overwritten.** Then say "Use Loop for this project." Loop first maps what already exists as delivered maps, then plans new features.

### If something goes wrong

| Problem | Fix |
| --- | --- |
| The agent searches the web for "Loop" | It does not know about Loop. Say "Loop is at ~/Desktop/Ikigai/Loop", or install the plugin and open a new thread. |
| "Target is not empty" | Use an empty folder. Only `START.md` and `template-page/` may be there. For an existing app use `--adopt`. |
| "START.md is missing: ..." | Fill in the fields it names and run again. |
| "Atlas build stopped" | A map points to code that does not exist, or has a broken link. The message names the map; fix it and run `atlas` again. |
| `--start` says it could not start codex | Codex is not installed or not on your PATH. Open the folder in your agent and say "Build the next atlas map." |

## Files in this folder

| File | What it is |
| --- | --- |
| `loop.md` | The core policy (v0.4) |
| `ATLAS-FIRST.md` | Atlas format and the build loop |
| `OWNER-COMMUNICATION.md` | How to talk to the owner |
| `EFFICIENT-WORKFLOW.md` | Bounded context, modes, cost honesty |
| `DELIVERY-WORKFLOW.md` | Tracks, reviews, debugging, release |
| `SECURITY.md` | Security verification standard |
| `LEGAL-CHECKLIST.md` | The 20 legal checks every project goes through |
| `MODEL-ROUTING.md`, `LOCAL-MODEL-ROUTING.md`, `config/`, `scripts/codex_model_router.py` | Optional model routing |
| `start/START.md`, `start/template-page/` | The fill-in form and the folder for your basic template page |
| `scripts/loop-init.mjs`, `starter/` | The atlas-first project starter (`starter/platforms.mjs` holds the platform profiles) |
| `examples/` | Example briefs for a web app and an Android app |
| `tests/` | Checks for the router, policy wiring and the starter |
| `archive/v0.3.1/`, `archive/v0.4.2/` | The previous versions of changed files |
| `CHANGELOG.md` | What changed in each version |

## Check Loop itself

```
node --test tests/test_loop_init.mjs
python3 -m unittest tests/test_codex_model_router.py tests/test_efficiency_contract.py
```

Install as a Codex plugin: see `INSTALL.md`.
