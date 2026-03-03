#!/usr/bin/env python3
"""
codepipeline — Multi-model coding pipeline for OpenClaw

Chains three specialist LLMs in sequence:
  1. Orchestrator (GLM 4.7 Flash, local)  — plans the implementation
  2. Coder       (GLM 4.7 Cloud)           — generates code from the plan
  3. Reviewer    (Kimi K2.5 Cloud)         — reviews and approves or rejects

On reviewer FAIL, the coder receives the feedback and revises.
Loops up to --max-iterations times.

Output: final code printed to stdout + saved to a timestamped file.
Transcript: full plan/code/review history saved as a .md file.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ── Model configuration ────────────────────────────────────────────────────────

# Ollama.com account API key (usmlabs org)
OLLAMA_API_KEY = "6006cbfdca9e427493ddc8d86aab2fdc.js3MeboyXqiB8Y84IixerbZ8"

MODELS = {
    "orchestrator": {
        "name": "Orchestrator (GLM 4.7 Flash)",
        "base_url": "http://192.168.20.105:11434/v1",
        "model": "glm-4.7-flash:latest",
        "api_key": None,        # no auth required
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    "coder": {
        "name": "Coder (GLM 4.7 Cloud)",
        "base_url": "http://192.168.20.217:11434/v1",
        "model": "glm-4.7:cloud",
        "api_key": None,        # machine-level auth via ollama.com connect
        "max_tokens": 16384,
        "temperature": 0.1,
    },
    # Fallback coder used when primary coder server is unreachable/unauthorized
    "coder_fallback": {
        "name": "Coder fallback (GLM 4.7 Flash)",
        "base_url": "http://192.168.20.105:11434/v1",
        "model": "glm-4.7-flash:latest",
        "api_key": None,
        "max_tokens": 8192,
        "temperature": 0.1,
    },
    "reviewer": {
        "name": "Reviewer (Kimi K2.5 Cloud)",
        "base_url": "http://192.168.10.242:11434/v1",
        "model": "kimi-k2.5:cloud",
        "api_key": OLLAMA_API_KEY,   # confirmed working
        "max_tokens": 8192,
        "temperature": 0.1,
    },
}

# ── Core LLM call ──────────────────────────────────────────────────────────────

def _do_chat(cfg: dict, messages: list, verbose: bool) -> tuple[str, bool]:
    """
    Make a single chat request. Returns (content, success).
    Does not exit on failure — callers decide how to handle errors.
    """
    payload = json.dumps({
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": cfg["max_tokens"],
        "temperature": cfg["temperature"],
        "stream": False,
    }).encode()

    headers = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    req = urllib.request.Request(
        f"{cfg['base_url']}/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"\n  [WARN] {cfg['name']} returned HTTP {e.code}: {body[:120]}",
              file=sys.stderr)
        return "", False
    except urllib.error.URLError as e:
        print(f"\n  [WARN] Could not reach {cfg['name']}: {e}", file=sys.stderr)
        return "", False

    if "choices" not in data:
        print(f"\n  [WARN] {cfg['name']} returned unexpected response: {str(data)[:120]}",
              file=sys.stderr)
        return "", False

    choice = data["choices"][0]["message"]
    content = choice.get("content", "").strip()
    reasoning = choice.get("reasoning", "").strip()

    if verbose and reasoning:
        print(f"\n  [thinking] {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}",
              file=sys.stderr)

    return content, True


def chat(role: str, messages: list, verbose: bool = False) -> str:
    """
    Call the model for the given role, with automatic fallback for the coder.
    Exits on unrecoverable failure.
    """
    cfg = MODELS[role]
    content, ok = _do_chat(cfg, messages, verbose)

    if not ok and role == "coder":
        fb_cfg = MODELS["coder_fallback"]
        print(f"\n  [INFO] Primary coder unavailable — falling back to {fb_cfg['name']}",
              file=sys.stderr)
        # Rebuild messages with fallback model name unchanged (same prompts)
        content, ok = _do_chat(fb_cfg, messages, verbose)

    if not ok:
        print(f"\n[ERROR] {cfg['name']} failed and no fallback available. Aborting.",
              file=sys.stderr)
        sys.exit(1)

    return content

# ── Pipeline stages ────────────────────────────────────────────────────────────

def orchestrate(task: str, verbose: bool) -> str:
    print(f"\n{'─'*60}", file=sys.stderr)
    print(f"[1/3] {MODELS['orchestrator']['name']} — Planning", file=sys.stderr)
    print(f"{'─'*60}", file=sys.stderr)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a software architect. Given a coding task, produce a concise, "
                "structured implementation plan with numbered steps. Be specific about "
                "data structures, function signatures, error handling, and edge cases. "
                "The plan will be handed directly to a developer to implement."
            ),
        },
        {"role": "user", "content": f"Task: {task}"},
    ]

    plan = chat("orchestrator", messages, verbose)
    print(plan, file=sys.stderr)
    return plan


def generate_code(task: str, plan: str, feedback: str | None, iteration: int,
                  verbose: bool) -> str:
    label = f"revision {iteration}" if feedback else "initial draft"
    print(f"\n{'─'*60}", file=sys.stderr)
    print(f"[2/3] {MODELS['coder']['name']} — Coding ({label})", file=sys.stderr)
    print(f"{'─'*60}", file=sys.stderr)

    user_content = f"Task: {task}\n\nImplementation plan:\n{plan}"
    if feedback:
        user_content += (
            f"\n\n---\nPrevious attempt was rejected by code review. "
            f"Reviewer feedback:\n{feedback}\n\n"
            "Please address ALL issues identified above in your revised implementation."
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert software developer. Write clean, production-quality code "
                "that exactly follows the provided plan. Include docstrings for all public "
                "functions and classes. Handle edge cases and errors. "
                "Output the complete implementation — do not truncate or omit sections."
            ),
        },
        {"role": "user", "content": user_content},
    ]

    code = chat("coder", messages, verbose)
    print(code, file=sys.stderr)
    return code


def review_code(task: str, plan: str, code: str, verbose: bool) -> tuple[str, str]:
    print(f"\n{'─'*60}", file=sys.stderr)
    print(f"[3/3] {MODELS['reviewer']['name']} — Reviewing", file=sys.stderr)
    print(f"{'─'*60}", file=sys.stderr)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior code reviewer. Carefully analyze the provided code against "
                "the original task and implementation plan. Check for:\n"
                "  1. Correctness — does it fully solve the task?\n"
                "  2. Logic errors or bugs\n"
                "  3. Security vulnerabilities\n"
                "  4. Missing edge cases\n"
                "  5. Incomplete implementation (truncated or stubbed sections)\n"
                "  6. Code quality and maintainability\n\n"
                "You MUST respond in exactly this format:\n"
                "VERDICT: PASS\n"
                "ISSUES: None\n"
                "FEEDBACK: The code correctly implements the requirements.\n\n"
                "or:\n\n"
                "VERDICT: FAIL\n"
                "ISSUES: <numbered list of specific issues>\n"
                "FEEDBACK: <specific, actionable instructions for the developer>\n\n"
                "Be strict. Only PASS code that is correct, complete, and handles edge cases."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original task: {task}\n\n"
                f"Implementation plan:\n{plan}\n\n"
                f"Code to review:\n{code}"
            ),
        },
    ]

    review = chat("reviewer", messages, verbose)
    print(review, file=sys.stderr)

    verdict = "FAIL"
    for line in review.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("VERDICT:"):
            verdict = stripped.split(":", 1)[1].strip().upper()
            break

    return verdict, review

# ── Pipeline runner ────────────────────────────────────────────────────────────

def run_pipeline(task: str, max_iterations: int, verbose: bool) -> tuple[str, str, bool]:
    """
    Returns (final_code, transcript_md, passed).
    """
    transcript = []
    transcript.append(f"# codepipeline transcript\n")
    transcript.append(f"**Task:** {task}\n")
    transcript.append(f"**Started:** {datetime.now().isoformat()}\n")
    transcript.append(f"**Max iterations:** {max_iterations}\n\n---\n")

    print(f"\n{'═'*60}", file=sys.stderr)
    print(f"  MULTI-MODEL CODING PIPELINE", file=sys.stderr)
    print(f"  Task: {task}", file=sys.stderr)
    print(f"{'═'*60}", file=sys.stderr)

    plan = orchestrate(task, verbose)
    transcript.append(f"## Plan\n\n{plan}\n\n---\n")

    feedback = None
    final_code = ""
    passed = False

    for i in range(1, max_iterations + 1):
        print(f"\n{'═'*60}", file=sys.stderr)
        print(f"  ITERATION {i}/{max_iterations}", file=sys.stderr)
        print(f"{'═'*60}", file=sys.stderr)

        transcript.append(f"## Iteration {i}\n")

        code = generate_code(task, plan, feedback, i, verbose)
        transcript.append(f"### Code\n\n```\n{code}\n```\n\n")

        verdict, review = review_code(task, plan, code, verbose)
        transcript.append(f"### Review\n\nVERDICT: **{verdict}**\n\n{review}\n\n---\n")

        final_code = code

        if verdict == "PASS":
            passed = True
            print(f"\n✓ PASSED review on iteration {i}.", file=sys.stderr)
            break

        feedback = review
        if i < max_iterations:
            print(f"\n✗ FAILED review. Sending feedback to coder for revision...",
                  file=sys.stderr)
        else:
            print(f"\n✗ FAILED review after {max_iterations} iterations. "
                  f"Returning best attempt.", file=sys.stderr)

    transcript.append(
        f"## Result\n\n"
        f"**Verdict:** {'PASS' if passed else 'FAIL (max iterations reached)'}\n"
        f"**Finished:** {datetime.now().isoformat()}\n"
    )

    return final_code, "\n".join(transcript), passed

# ── Output helpers ─────────────────────────────────────────────────────────────

def save_outputs(task: str, code: str, transcript: str, output_path: str | None) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_task = "".join(c if c.isalnum() or c in "-_" else "_" for c in task[:40])

    if output_path:
        code_path = Path(output_path)
    else:
        code_path = Path(f"pipeline_{timestamp}_{safe_task}.py")

    transcript_path = code_path.with_suffix(".transcript.md")

    code_path.write_text(code)
    transcript_path.write_text(transcript)

    print(f"\n{'═'*60}", file=sys.stderr)
    print(f"  OUTPUT FILES", file=sys.stderr)
    print(f"{'═'*60}", file=sys.stderr)
    print(f"  Code:       {code_path.resolve()}", file=sys.stderr)
    print(f"  Transcript: {transcript_path.resolve()}", file=sys.stderr)

# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Multi-model coding pipeline: plan → code → review → iterate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Models used:
  Orchestrator  GLM 4.7 Flash (192.168.20.105) — local, fast planner
  Coder         GLM 4.7 Cloud (192.168.20.217) — coding specialist
  Reviewer      Kimi K2.5 Cloud (192.168.10.242) — reasoning reviewer

Examples:
  codepipeline "write a Python class for a thread-safe LRU cache"
  codepipeline "implement a CLI argument parser in Go" --max-iterations 2
  echo "REST API client for GitHub in TypeScript" | codepipeline
  codepipeline "binary search tree in Python" --output bst.py
        """,
    )
    parser.add_argument(
        "task", nargs="?", help="Coding task description (or pipe via stdin)"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=3, metavar="N",
        help="Maximum coder→reviewer iterations (default: 3)"
    )
    parser.add_argument(
        "--output", metavar="FILE",
        help="Output file path for final code (default: auto-named)"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show model reasoning/thinking traces"
    )
    args = parser.parse_args()

    if args.task:
        task = args.task
    elif not sys.stdin.isatty():
        task = sys.stdin.read().strip()
    else:
        parser.print_help()
        sys.exit(1)

    if not task:
        print("Error: task cannot be empty.", file=sys.stderr)
        sys.exit(1)

    final_code, transcript, passed = run_pipeline(task, args.max_iterations, args.verbose)

    save_outputs(task, final_code, transcript, args.output)

    print(f"\n{'═'*60}", file=sys.stderr)
    print(f"  FINAL CODE", file=sys.stderr)
    print(f"{'═'*60}\n", file=sys.stderr)
    print(final_code)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
