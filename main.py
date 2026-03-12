"""
main.py -- CLI entry point for the job description analysis pipeline.

Reads a raw job description from a file or stdin, runs the three
specialized agents, and prints the structured analysis as formatted JSON.

Usage:
    python main.py <path_to_job_description.txt>
    cat job.txt | python main.py
"""

import json
import logging
import sys

from agents import JobAnalysisOrchestrator


def _read_input() -> str:
    """Read job description text from a file argument or stdin.

    Returns:
        Raw job description text.

    Raises:
        SystemExit: If no input is provided.
    """
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, "r", encoding="utf-8") as fh:
                return fh.read()
        except FileNotFoundError:
            print(f"Error: File not found -- {filepath}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        return sys.stdin.read()
    else:
        print(
            "Usage: python main.py <job_description.txt>\n"
            "       or pipe text via stdin.",
            file=sys.stderr,
        )
        sys.exit(1)


def _print_section(title: str, items: list[str] | dict) -> None:
    """Pretty-print a labelled section to stdout."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    if isinstance(items, list):
        for item in items:
            print(f"  - {item}")
        if not items:
            print("  (none found)")
    elif isinstance(items, dict):
        for key, value in items.items():
            if isinstance(value, list):
                print(f"\n  [{key}]")
                for v in value:
                    print(f"    - {v}")
                if not value:
                    print(f"    (none)")
            else:
                print(f"  {key}: {value}")


def main() -> None:
    """Run the full analysis pipeline and display results."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)-25s | %(levelname)s | %(message)s",
    )

    job_text = _read_input()

    if not job_text.strip():
        print("Error: Empty job description.", file=sys.stderr)
        sys.exit(1)

    orchestrator = JobAnalysisOrchestrator()
    result = orchestrator.analyze(job_text)

    # --- Pretty console output ---
    print("\n" + "#" * 60)
    print("  JOB DESCRIPTION ANALYSIS")
    print("#" * 60)

    hard = result.hard_skills
    _print_section("HARD SKILLS -- Programming Languages", hard.programming_languages)
    _print_section("HARD SKILLS -- Frameworks & Libraries", hard.frameworks_and_libraries)
    _print_section("HARD SKILLS -- Tools & Platforms", hard.tools_and_platforms)
    _print_section("HARD SKILLS -- Databases", hard.databases)
    _print_section("HARD SKILLS -- Other Technical", hard.other_technical)

    _print_section("SOFT SKILLS", result.soft_skills.skills)

    scope = result.work_scope
    _print_section("WORK SCOPE", {
        "Summary": scope.summary,
        "Key Responsibilities": scope.key_responsibilities,
        "Projects / Domains": scope.projects_or_domains,
        "Team Structure": scope.team_structure,
    })

    # --- Raw JSON output ---
    print(f"\n{'=' * 60}")
    print("  RAW JSON")
    print(f"{'=' * 60}")
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
