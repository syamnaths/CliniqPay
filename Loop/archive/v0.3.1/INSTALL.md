# Install and invoke Loop in Codex

Loop is a Codex plugin containing a skill. It does not register `/loop` as a slash command in Codex CLI 0.147.0.

After installing the plugin, start a new Codex thread so the skill catalog refreshes. Invoke Loop with natural language:

```text
Use Loop for this project.
Apply Loop to plan and implement this feature.
Resume this project using Loop.
```

When the host displays namespaced skills, explicitly select the Loop skill using the name shown in the skill picker, typically `loop:loop`. Slash commands beginning with `/` are host commands and are not created merely by naming a skill.

Local personal-marketplace installation:

```text
codex plugin add loop@personal
```

Verify installation with `codex plugin list`. The expected state is `loop@personal  installed, enabled`. After updating the local plugin source, use the plugin cachebuster/reinstall workflow and open a new thread.

## Troubleshooting wrong activation

If “Use Loop for this project” invokes OpenAI Docs, web search, or a generic interpretation of Loop, the current thread did not load the Loop skill catalog. Do not continue that activation or let it create project artifacts. Verify `loop@personal` is installed and enabled, close the stale thread, and start a completely new thread in the target project. Then use the exact natural-language instruction `Use Loop for this project.` or select `loop:loop` if the skill picker exposes namespaced skills.

For an empty target with no idea supplied, correct activation asks what you are building, who it serves, and what the first release must accomplish before Git initialization, full preflight, architecture selection, or detailed handoff creation.

## Model-switch fallback

Loop analyzes every bounded task internally. When an automatic model adapter cannot switch or launch the recommended model, Loop enters `AWAITING_HUMAN_MODEL_SWITCH`, recommends the model and reasoning level, and gives the engineer a resume checkpoint. In Codex, the engineer uses `/model` or the displayed model selector, then continues the thread. `/model` is a host command operated by the user; Loop must not claim it executed that command itself.

Loop 0.3 includes an internal Codex adapter. With Codex CLI 0.148.0 or later, the skill may delegate a bounded task through `codex exec fork` using per-run `--model` and reasoning overrides. This does not alter the current supervisor model or rewrite `~/.codex/config.toml`. The Codex launch may require host approval because it creates or updates local Codex session state; if permission is denied or launch fails, Loop uses the human-switch fallback.

The files in `config/codex-profiles/` are optional templates for sessions the engineer launches manually. Codex profile files belong directly under `$CODEX_HOME` and are selected with `codex --profile <name>`. Do not install or overwrite them silently; automatic routing does not depend on them.
