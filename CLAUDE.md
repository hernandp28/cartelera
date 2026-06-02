# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Context

This is an **HR management automation system** (Gestión de RRHH) for a Spanish-speaking organization. It automates recurring people-ops workflows — onboarding, payroll reporting, document generation, headcount tracking — by connecting Google Workspace data to structured outputs.

The primary data source is **Google Sheets**. The primary output surfaces are **Google Docs, Slides, and Drive**. Brand reference lives in `Manual de marca.pdf` — consult it when generating any outward-facing document (colors, fonts, logo usage, tone).

---

## The WAT Architecture

You're operating inside the **WAT framework** (Workflows, Agents, Tools). Probabilistic AI handles reasoning; deterministic scripts handle execution.

**Layer 1 — Workflows (`workflows/`):** Markdown SOPs. Each file defines the objective, required inputs, which tools to call, expected outputs, and edge-case handling. These are your instructions — don't overwrite them without asking.

**Layer 2 — Agent (you):** Read the relevant workflow, run tools in the correct sequence, handle failures, ask when inputs are ambiguous. You orchestrate; you don't execute directly.

**Layer 3 — Tools (`tools/`):** Standalone Python scripts. API calls, data transforms, file operations. Each script is self-contained and accepts arguments via `argparse`.

**Why the separation matters:** Chaining five 90%-accurate AI steps yields ~59% end-to-end reliability. Deterministic scripts break that compounding failure — keep execution out of the model.

---

## Python Environment

```bash
pip install -r requirements.txt
python tools/<script_name>.py --help
```

Check the `# Usage:` comment or `argparse` block at the top of each script before running. Confirm with the user before running any tool that makes paid API calls or consumes credits.

---

## Google Workspace Integration

Authentication uses OAuth 2.0. The flow:
1. `credentials.json` — OAuth client credentials downloaded from Google Cloud Console (gitignored)
2. `token.json` — generated on first run after browser auth (gitignored)

When writing a new Google tool, use `google-auth`, `google-auth-oauthlib`, and the relevant `google-api-python-client` service. Reuse the token refresh logic already present in existing tools rather than re-implementing it.

Scopes needed depend on the service: `spreadsheets.readonly` for read-only Sheets, `drive.file` for writing to Drive, etc. Define scopes as a constant at the top of each script.

---

## Conventions for New Tools

- **File name:** `verb_noun.py` — e.g., `export_headcount.py`, `generate_payslip.py`
- **Top of file:** `# Usage: python tools/verb_noun.py --arg value` comment
- **Arguments:** Use `argparse`; include `--help` descriptions
- **Output:** Print a short confirmation line on success; raise exceptions with clear messages on failure
- **Secrets:** Load from `.env` via `python-dotenv`; never hardcode

---

## Conventions for New Workflows

- **File name:** `verb_noun.md` matching the tool it orchestrates
- **Sections:** Objective → Inputs → Steps (numbered, tool calls explicit) → Expected Output → Edge Cases
- **Tool references:** Use the exact filename: `run tools/export_headcount.py --sheet-id <id>`

---

## Operating Rules

**1. Check existing tools first.** Only create a new script when nothing in `tools/` covers the task.

**2. Adapt when things fail.** Read the full trace, fix and retest, then update the workflow with what you learned (rate limits, API quirks, pagination). Document constraints so they aren't rediscovered.

**3. Keep workflows current.** Update them as you learn — but don't create or overwrite workflow files without being asked.

---

## File Structure

```
.tmp/                    # Disposable intermediates — regenerated as needed
tools/                   # Python execution scripts
workflows/               # Markdown SOPs
.env                     # All secrets (never commit)
credentials.json         # Google OAuth client config (gitignored)
token.json               # Google OAuth token (gitignored)
Manual de marca.pdf      # Brand reference — consult for any generated document
```

Everything the user needs to see lives in Google Workspace. Local files are processing intermediates only.
