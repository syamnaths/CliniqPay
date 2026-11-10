#!/usr/bin/env python3
"""Internal Codex launch adapter for Loop task-level model routing.

The Loop skill classifies the bounded task. This adapter applies that decision
to a new, resumed, or forked Codex run without rewriting global config.toml.
Prompts travel over stdin and are never written to the routing decision log.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = PLUGIN_ROOT / "config" / "model-routing.json"
CHILD_MARKER = "[LOOP_ROUTED_CHILD]"
GLOBAL_FAILURE_MARKERS = (
    "operation not permitted",
    "permission denied",
    "not logged in",
    "authentication",
    "credentials",
    "command not found",
    "usage limit",
    "purchase more credits",
    "upgrade to pro",
)
TASK_CLASSES = {
    "simple",
    "focused",
    "standard",
    "reasoning",
    "high-risk",
    "large-context",
    "browser",
}
AUTO_TASK_CLASS = "auto"


class RoutingError(RuntimeError):
    pass


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


def load_policy(path: Path) -> Dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RoutingError(f"Cannot load routing policy {path}: {exc}") from exc
    if policy.get("schemaVersion") != 1 or not isinstance(policy.get("routes"), dict):
        raise RoutingError("Unsupported or incomplete routing policy")
    return policy


def candidates_for(policy: Dict[str, Any], task_class: str) -> List[Dict[str, str]]:
    route = policy["routes"].get(task_class)
    if not isinstance(route, dict):
        raise RoutingError(f"No Codex route for task class: {task_class}")
    primary = {"model": route.get("model"), "effort": route.get("effort")}
    candidates = [primary] + list(route.get("fallbacks", []))
    allowed_efforts = {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
    for candidate in candidates:
        if not candidate.get("model") or candidate.get("effort") not in allowed_efforts:
            raise RoutingError(f"Invalid candidate in route: {task_class}")
    return candidates


def classify_task(prompt: str) -> str:
    """Infer the smallest capable routing lane from a bounded task prompt."""
    text = " ".join(prompt.lower().split())
    if not text:
        raise RoutingError("Cannot auto-classify an empty bounded task prompt")

    high_risk_terms = (
        "production",
        "deploy",
        "push",
        "release",
        "security",
        "privacy",
        "auth",
        "permission",
        "token",
        "secret",
        "payment",
        "billing",
        "migration",
        "rollback",
        "recovery",
        "delete",
        "destructive",
        "data loss",
        "legal",
        "medical",
        "financial",
    )
    large_context_terms = (
        "whole app",
        "entire app",
        "full project",
        "all files",
        "every flow",
        "complete review",
        "audit everything",
        "repository map",
        "architecture map",
    )
    browser_terms = (
        "browser",
        "playwright",
        "screenshot",
        "responsive",
        "mobile",
        "desktop",
        "visual",
        "ui",
        "layout",
        "canvas",
        "webgl",
        "animation",
    )
    reasoning_terms = (
        "architecture",
        "algorithm",
        "root cause",
        "diagnose",
        "debug",
        "complex",
        "race",
        "concurrency",
        "performance",
        "refactor",
        "research",
        "compare",
        "design",
        "strategy",
    )
    focused_terms = (
        "small",
        "tiny",
        "copy",
        "wording",
        "label",
        "opacity",
        "color",
        "rename",
        "one file",
        "single file",
        "minor",
    )
    simple_terms = (
        "format",
        "extract",
        "summarize",
        "count",
        "list",
        "find",
        "grep",
        "search",
        "status",
        "diff",
    )

    if _contains_any(text, high_risk_terms):
        return "high-risk"
    if _contains_any(text, large_context_terms) or len(prompt) > 12000:
        return "large-context"
    if _contains_any(text, browser_terms):
        return "browser"
    if _contains_any(text, reasoning_terms):
        return "reasoning"
    if _contains_any(text, focused_terms):
        return "focused"
    if _contains_any(text, simple_terms) and len(prompt) < 2000:
        return "simple"
    return "standard"


def build_command(
    codex_bin: str,
    mode: str,
    candidate: Dict[str, str],
    project_root: Path,
    session_id: Optional[str],
) -> List[str]:
    config_override = f'model_reasoning_effort="{candidate["effort"]}"'
    model_args = ["--model", candidate["model"], "-c", config_override]
    if mode == "new":
        return [
            codex_bin,
            "exec",
            *model_args,
            "-C",
            str(project_root),
            "--skip-git-repo-check",
            "--json",
            "-",
        ]
    if not session_id:
        raise RoutingError(f"--session-id is required for {mode}")
    return [
        codex_bin,
        "exec",
        mode,
        *model_args,
        "--skip-git-repo-check",
        "--json",
        session_id,
        "-",
    ]


def routed_prompt(prompt: str, route_id: str, task_class: str) -> str:
    return (
        f"{CHILD_MARKER}\n"
        f"Route checkpoint: {route_id}\n"
        f"Task class: {task_class}\n"
        "You are a bounded child execution selected by Loop. Do not invoke or "
        "delegate to another model-routing adapter. Use the supplied project "
        "context, complete only this bounded task, validate proportionately, "
        "and return a concise result for the supervising Loop session.\n\n"
        f"{prompt.strip()}\n"
    )


def prompt_digest(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def is_global_failure(stderr: str) -> bool:
    lowered = stderr.lower()
    return any(marker in lowered for marker in GLOBAL_FAILURE_MARKERS)


def structured_error(stdout: str) -> str:
    messages: List[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "error" and isinstance(event.get("message"), str):
            messages.append(event["message"])
        nested = event.get("error")
        if event.get("type") == "turn.failed" and isinstance(nested, dict):
            message = nested.get("message")
            if isinstance(message, str):
                messages.append(message)
    return messages[-1] if messages else ""


def failure_kind(message: str) -> str:
    lowered = message.lower()
    if any(term in lowered for term in ("usage limit", "purchase more credits", "upgrade to pro")):
        return "account-usage-limit"
    if any(term in lowered for term in ("authentication", "credentials", "not logged in")):
        return "authentication"
    if any(term in lowered for term in ("operation not permitted", "permission denied")):
        return "permission"
    if any(term in lowered for term in ("429", "rate limit", "too many requests")):
        return "rate-limit"
    if any(term in lowered for term in ("model", "unsupported", "unavailable")):
        return "model-unavailable"
    return "dispatch"


def atomic_json_write(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def decision_path(project_root: Path, route_id: str) -> Path:
    return project_root / ".codex" / "loop-routing" / f"{route_id}.json"


def read_prompt(prompt_file: Optional[Path]) -> str:
    if prompt_file:
        return prompt_file.read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise RoutingError("Provide --prompt-file or pipe the bounded task on stdin")
    return sys.stdin.read()


def public_plan(
    route_id: str,
    task_class: str,
    mode: str,
    candidates: Sequence[Dict[str, str]],
    command: Sequence[str],
    session_id: Optional[str],
) -> Dict[str, Any]:
    return {
        "routeId": route_id,
        "routeState": "PLANNED",
        "taskClass": task_class,
        "mode": mode,
        "recommendedModel": candidates[0]["model"],
        "reasoningEffort": candidates[0]["effort"],
        "fallbacks": list(candidates[1:]),
        "session": session_id,
        "command": list(command),
    }


def execute_route(args: argparse.Namespace, policy: Dict[str, Any]) -> int:
    project_root = args.project_root.resolve()
    prompt: Optional[str] = None
    task_class = args.task_class
    if task_class == AUTO_TASK_CLASS:
        prompt = read_prompt(args.prompt_file)
        task_class = classify_task(prompt)
    candidates = candidates_for(policy, task_class)
    route_id = args.route_id or f"route-{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    first_command = build_command(
        args.codex_bin, args.mode, candidates[0], project_root, args.session_id
    )
    if not args.execute:
        print(
            json.dumps(
                public_plan(
                    route_id,
                    task_class,
                    args.mode,
                    candidates,
                    first_command,
                    args.session_id,
                ),
                indent=2,
            )
        )
        return 0

    if shutil.which(args.codex_bin) is None:
        raise RoutingError(f"Codex executable not found: {args.codex_bin}")

    if prompt is None:
        prompt = read_prompt(args.prompt_file)
    if not prompt.strip():
        raise RoutingError("The bounded task prompt is empty")
    child_prompt = routed_prompt(prompt, route_id, task_class)
    record: Dict[str, Any] = {
        "routeId": route_id,
        "routeState": "DISPATCHING",
        "taskClass": task_class,
        "autoClassified": args.task_class == AUTO_TASK_CLASS,
        "mode": args.mode,
        "session": args.session_id,
        "promptSha256": prompt_digest(prompt),
        "policyCatalogAsOf": policy.get("catalogAsOf"),
        "attempts": [],
    }
    record_file = decision_path(project_root, route_id)
    if not args.no_record:
        atomic_json_write(record_file, record)

    terminal_failure_kind: Optional[str] = None
    for candidate in candidates:
        command = build_command(
            args.codex_bin, args.mode, candidate, project_root, args.session_id
        )
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=child_prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        error_message = structured_error(completed.stdout) or completed.stderr.strip()
        kind = failure_kind(error_message)
        attempt = {
            "model": candidate["model"],
            "effort": candidate["effort"],
            "exitCode": completed.returncode,
            "durationMs": round((time.monotonic() - started) * 1000),
            "failureKind": None if completed.returncode == 0 else kind,
        }
        record["attempts"].append(attempt)
        if completed.returncode == 0:
            record.update(
                {
                    "routeState": "AUTO_SELECTED",
                    "selectedModel": candidate["model"],
                    "reasoningEffort": candidate["effort"],
                    "validation": "child-result-returned; supervisor validation pending",
                }
            )
            if not args.no_record:
                atomic_json_write(record_file, record)
            sys.stdout.write(completed.stdout)
            return 0

        if completed.stderr:
            sys.stderr.write(completed.stderr)
        if error_message and not completed.stderr:
            print(f"Codex child failed ({kind}): {error_message}", file=sys.stderr)
        terminal_failure_kind = kind
        if is_global_failure(error_message or completed.stderr):
            break

    recommendation = candidates[0]
    if terminal_failure_kind in {"account-usage-limit", "authentication", "permission"}:
        record.update(
            {
                "routeState": "BLOCKED",
                "failureKind": terminal_failure_kind,
                "resumeReference": route_id,
            }
        )
        if not args.no_record:
            atomic_json_write(record_file, record)
        print(
            json.dumps(
                {
                    "routeState": "BLOCKED",
                    "failureKind": terminal_failure_kind,
                    "resumeReference": route_id,
                    "action": "Resolve the account/permission condition or use a verified local-offline route, then resume this checkpoint.",
                }
            ),
            file=sys.stderr,
        )
        return 76
    record.update(
        {
            "routeState": "AWAITING_HUMAN_MODEL_SWITCH",
            "recommendedModel": recommendation["model"],
            "reasoningEffort": recommendation["effort"],
            "resumeReference": route_id,
        }
    )
    if not args.no_record:
        atomic_json_write(record_file, record)
    print(
        json.dumps(
            {
                "routeState": record["routeState"],
                "recommendedModel": recommendation["model"],
                "reasoningEffort": recommendation["effort"],
                "resumeReference": route_id,
                "action": "Use /model or the host model selector, then resume this checkpoint.",
            }
        ),
        file=sys.stderr,
    )
    return 75


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Internal Loop Codex model adapter")
    result.add_argument(
        "--task-class",
        choices=sorted(TASK_CLASSES | {AUTO_TASK_CLASS}),
        default=AUTO_TASK_CLASS,
        help="Use auto to infer task intensity from the bounded prompt.",
    )
    result.add_argument("--mode", choices=("new", "fork", "resume"), default="new")
    result.add_argument("--session-id")
    result.add_argument("--project-root", type=Path, default=Path.cwd())
    result.add_argument("--prompt-file", type=Path)
    result.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    result.add_argument("--route-id")
    result.add_argument("--codex-bin", default="codex")
    result.add_argument("--execute", action="store_true")
    result.add_argument("--no-record", action="store_true")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        return execute_route(args, load_policy(args.policy))
    except (RoutingError, OSError) as exc:
        print(json.dumps({"routeState": "BLOCKED", "error": str(exc)}), file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
