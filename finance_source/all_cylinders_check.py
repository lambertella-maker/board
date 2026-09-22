#!/usr/bin/env python3
"""
all_cylinders_check.py
Checks that the finance dashboards stay aligned across:
- dashboard.html (Mac / main live dashboard)
- dashboard_ipad.html (iPad)
- dashboard_iphone.html (iPhone)

It compares shared goal-row content and key HTML anchors, while allowing
known variant-specific differences. Any drift in shared finance logic/copy
should fail the check.

Run standalone:  python3 ~/Desktop/Finances/all_cylinders_check.py
Auto-run:        wired into deploy_dashboards.sh before every git push
"""

import re
import sys
import json
import subprocess
from datetime import date
from pathlib import Path
from build_finance import check_generated
from finance_model import load_plan

FINANCES  = Path.home() / "Desktop" / "Finances"
MAC       = FINANCES / "dashboard.html"
IPAD      = FINANCES / "dashboard_ipad.html"
IPHONE    = FINANCES / "dashboard_iphone.html"
NOTEBOOK  = FINANCES / "LAB_NOTEBOOK.md"
LOG       = Path.home() / ".claude" / "logs" / "dashpush.log"
HANDOFFS  = Path.home() / "Documents" / "AI_Handoffs"
PUBLISH_REPO = Path.home() / ".claude" / "repos" / "board_autopush"
AUTOPUSH_CONFIG = HANDOFFS / "Finances" / "autopush.json"
DEPLOY_SCRIPT = Path.home() / ".claude" / "scripts" / "deploy_dashboards.sh"
PAGES_WORKFLOW = PUBLISH_REPO / ".github" / "workflows" / "pages.yml"
REMOTE_URL = "git@github.com:lambertella-maker/board.git"
BRANCH = "main"

# ── intentional differences between devices ──────────────────────────────────
INTENTIONAL = set()

# Structural markers deliberately avoid fixing financial values in test code.
ANCHORS = [
    ("ILR start date", r"ilrStart\s*=\s*new Date\(([^)]+)\)"),
    ("ILR deadline", r"ilrDeadline\s*=\s*new Date\(([^)]+)\)"),
]
DEVICE_NEEDLES = {
    "iPad": ["Fidelity Taxable", "Brokerage Roth", "data-live-sip", "window.Finance.moveBalance(today)"],
    "iPhone": ["Your contribution", "Building credit history", "data-live-sip", "window.Finance.moveBalance(today)"],
}

REQUIRED_PUBLISH_COPIES = {
    "dashboard.html": str(FINANCES / "dashboard.html"),
    "dashboard_ipad.html": str(FINANCES / "dashboard_ipad.html"),
    "dashboard_iphone.html": str(FINANCES / "dashboard_iphone.html"),
    "finance-apple-touch-icon.png": str(FINANCES / "finance-apple-touch-icon.png"),
    "finance-icon-512.png": str(FINANCES / "finance-icon-512.png"),
    "finance_lock.css": str(FINANCES / "finance_lock.css"),
    "finance_lock.js": str(FINANCES / "finance_lock.js"),
}


def extract_goal_rows(html):
    """Return list of (label, value) from all goal-row spans."""
    return re.findall(
        r'class="goal-row-label">([^<]+)</span><span[^>]*>([^<]+)<', html
    )


def extract_anchor(html, pattern):
    m = re.search(pattern, html)
    return m.group(1).strip() if m else None


def normalize_text(text: str) -> str:
    text = text.replace("~", "")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def git_value(repo: Path, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_publish_topology():
    """Validate the hard rules that make finance changes publish to GitHub Pages."""
    diffs = []

    if not AUTOPUSH_CONFIG.exists():
        return [f"  PUBLISH RULE missing autopush config {AUTOPUSH_CONFIG}"]

    try:
        config = json.loads(AUTOPUSH_CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"  PUBLISH RULE invalid autopush config: {exc}"]

    if config.get("enabled") is not True:
        diffs.append("  PUBLISH RULE autopush disabled for Finances")
    if config.get("source_root") != str(FINANCES):
        diffs.append(f"  PUBLISH RULE source_root must be {FINANCES}")
    if config.get("repo_dir") != str(PUBLISH_REPO):
        diffs.append(f"  PUBLISH RULE repo_dir must be {PUBLISH_REPO}")
    if config.get("repo_url") != REMOTE_URL:
        diffs.append(f"  PUBLISH RULE repo_url must be {REMOTE_URL}")
    if config.get("branch") != BRANCH:
        diffs.append(f"  PUBLISH RULE branch must be {BRANCH}")

    preflight = config.get("preflight", [])
    expected_preflight = f"python3 {FINANCES / 'all_cylinders_check.py'}"
    if expected_preflight not in preflight:
        diffs.append(f"  PUBLISH RULE preflight missing {expected_preflight!r}")

    copies = {
        item.get("dest"): item.get("src")
        for item in config.get("copies", [])
        if isinstance(item, dict)
    }
    for dest, src in REQUIRED_PUBLISH_COPIES.items():
        if copies.get(dest) != src:
            diffs.append(f"  PUBLISH RULE copy missing {src} -> {dest}")

    if "dashboard_mobile.html" in copies:
        diffs.append("  PUBLISH RULE legacy dashboard_mobile.html publish alias must be removed")

    if not DEPLOY_SCRIPT.exists():
        diffs.append(f"  PUBLISH RULE missing deploy script {DEPLOY_SCRIPT}")
    else:
        deploy_text = DEPLOY_SCRIPT.read_text(encoding="utf-8", errors="replace")
        if "project_autopush.py" not in deploy_text:
            diffs.append("  PUBLISH RULE deploy_dashboards.sh must exec project_autopush.py")

    if not (PUBLISH_REPO / ".git").exists():
        diffs.append(f"  PUBLISH RULE publish repo missing or not a git worktree: {PUBLISH_REPO}")
    else:
        remote = git_value(PUBLISH_REPO, "config", "--get", "remote.origin.url")
        if remote != REMOTE_URL:
            diffs.append(f"  PUBLISH RULE publish repo origin must be {REMOTE_URL}, found {remote!r}")
        branch = git_value(PUBLISH_REPO, "branch", "--show-current")
        if branch != BRANCH:
            diffs.append(f"  PUBLISH RULE publish repo branch must be {BRANCH}, found {branch!r}")

    if not PAGES_WORKFLOW.exists():
        diffs.append(f"  PUBLISH RULE missing GitHub Pages workflow {PAGES_WORKFLOW}")
    else:
        workflow_text = PAGES_WORKFLOW.read_text(encoding="utf-8", errors="replace")
        if re.search(r"(?m)^\s+push:\s*$", workflow_text):
            diffs.append("  PUBLISH RULE custom Pages workflow must be manual-only; push deploy is handled by GitHub Pages")

    bad_live = HANDOFFS / "Publishing" / "board_live"
    if bad_live.exists():
        diffs.append(f"  PUBLISH RULE deprecated board_live path exists; use {PUBLISH_REPO}")

    return diffs


def main():
    if not MAC.exists() or not IPAD.exists() or not IPHONE.exists():
        print("✗ Dashboard files not found — skipping check")
        return 0

    mac_text  = MAC.read_text(encoding="utf-8")
    ipad_text = IPAD.read_text(encoding="utf-8")
    iphone_text = IPHONE.read_text(encoding="utf-8")

    diffs = []
    try:
        diffs.extend("  GENERATED OUTPUT STALE: " + name for name in check_generated())
        expected = load_plan()
        for name, html in (("Mac", mac_text), ("iPad", ipad_text), ("iPhone", iphone_text)):
            models = re.findall(r"window.PLAN = Object.freeze\((\{.*?\})\);", html, re.S)
            if len(models) != 1 or json.loads(models[0]) != expected:
                diffs.append(f"  CANONICAL MODEL DRIFT on {name}")
            if "window.PLAN ||" in html:
                diffs.append(f"  DUPLICATE FALLBACK MODEL on {name}")
            if 'data-chatbot-enabled="false"' not in html:
                diffs.append(f"  CHATBOT POLICY DRIFT on {name}: chatbot must be disabled consistently")
        if expected.get("chatbotEnabled") is not False:
            diffs.append("  CHATBOT POLICY DRIFT: canonical chatbotEnabled must be false")
        for label, html in (("Mac", mac_text), ("iPad", ipad_text)):
            nav_targets = re.findall(r'data-nav-target="([^"]+)"', html)
            section_ids = set(re.findall(r'<(?:section|div)[^>]+id="([^"]+)"', html))
            for target in nav_targets:
                if target not in section_ids:
                    diffs.append(f"  NAV TARGET MISSING on {label}: {target}")
        tab_names = set(re.findall(r'<[^>]+data-tab="([^"]+)"', iphone_text))
        tab_sections = set(re.findall(r'id="tab-([^"]+)"', iphone_text))
        for tab in sorted(tab_names):
            if tab not in tab_sections:
                diffs.append(f"  IPHONE TAB TARGET MISSING: {tab}")
    except (ValueError, OSError) as exc:
        diffs.append(f"  CANONICAL MODEL ERROR: {exc}")

    # ── 1. Goal row comparison: Mac is the baseline; compare variants where
    # shared goal-row markup exists. iPhone uses different goal markup, so it
    # is validated via anchors rather than this exact extractor.
    mac_rows  = dict(extract_goal_rows(mac_text))
    ipad_rows = dict(extract_goal_rows(ipad_text))

    for label, mac_val in mac_rows.items():
        if mac_val in INTENTIONAL:
            continue
        if label not in ipad_rows:
            diffs.append(f"  MISSING on iPad  [{label}] = {mac_val!r}")
        elif normalize_text(ipad_rows[label]) != normalize_text(mac_val):
            if ipad_rows[label] not in INTENTIONAL:
                diffs.append(
                    f"  DRIFT  [{label}]\n"
                    f"    Mac:  {mac_val!r}\n"
                    f"    iPad: {ipad_rows[label]!r}"
                )

    for label in ipad_rows:
        if label not in mac_rows:
            diffs.append(f"  EXTRA on iPad    [{label}]")

    # ── 2. Key anchor comparison across shared Mac/iPad markup ───────────────
    for name, pattern in ANCHORS:
        mac_val  = extract_anchor(mac_text,  pattern)
        ipad_val = extract_anchor(ipad_text, pattern)
        if mac_val and ipad_val and mac_val != ipad_val:
            diffs.append(
                f"  ANCHOR DRIFT [{name}]\n"
                f"    Mac:  {mac_val!r}\n"
                f"    iPad: {ipad_val!r}"
            )
        elif mac_val and not ipad_val:
            diffs.append(f"  ANCHOR MISSING on iPad [{name}]")

    # ── 3. Global finance rule markers for iPhone parity ─────────────────────
    iphone_checks = [
        ("current budget badge", "Post-promotion salary"),
        ("Move progress id", 'id="m-move-prog"'),
        ("Move target binding", "window.PLAN.moveTargetGbp"),
        ("ILR label id", 'id="m-ilr-lbl"'),
    ]
    for label, needle in iphone_checks:
        if needle not in iphone_text:
            diffs.append(f"  IPHONE MISSING [{label}] = {needle!r}")

    # ── 4. Concise-copy parity checks for audited wrap-risk areas ────────────
    device_text = {
        "iPad": ipad_text,
        "iPhone": iphone_text,
    }
    for device, needles in DEVICE_NEEDLES.items():
        for needle in needles:
            if needle not in device_text[device]:
                diffs.append(f"  {device.upper()} COPY DRIFT missing {needle!r}")

    # ── 5. Publish topology checks: all finance changes must flow through the
    # durable board_autopush repo, not the deprecated board_live path.
    diffs.extend(check_publish_topology())

    # ── Report ────────────────────────────────────────────────────────────────
    today = date.today().isoformat()
    if diffs:
        report = "\n".join(diffs)
        msg = f"[{today}] ⚠ ALL CYLINDERS DRIFT:\n{report}"
        print(msg)
        # Append to deploy log
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(msg + "\n")
        # Append warning to lab notebook
        notebook_warning = (
            f"\n> **⚠ All-cylinders drift detected {today}** — "
            f"run `python3 ~/Desktop/Finances/all_cylinders_check.py` to review.\n"
        )
        nb = NOTEBOOK.read_text(encoding="utf-8")
        if notebook_warning.strip() not in nb:
            with NOTEBOOK.open("a") as f:
                f.write(notebook_warning)
        return 1
    else:
        print(f"[{today}] ✓ All cylinders clean — Mac/iPad/iPhone finance checks match")
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a") as f:
            f.write(f"[{today}] ✓ all_cylinders OK\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
