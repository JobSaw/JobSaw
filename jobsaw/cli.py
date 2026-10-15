"""Command-line interface and composition root for the application."""

import argparse
import datetime
import logging
import sys
from pathlib import Path

from jobsaw.application.pipeline import CvPipeline, select_profile
from jobsaw.application.services import CvWriter, JobAnalyzer, ProfileSelector
from jobsaw.config import Settings
from jobsaw.infrastructure.gemini import GeminiModel
from jobsaw.infrastructure.latex import LatexCompiler
from jobsaw.infrastructure.mock_profile import MockProfileProvider
from jobsaw.infrastructure.profile_file import JsonProfileProvider

RESOURCES = Path(__file__).parent / "resources"


def build_parser() -> argparse.ArgumentParser:
    """Define one CLI for analysis, selection, generation, and recovery."""
    parser = argparse.ArgumentParser(description="Analyze jobs and generate tailored CVs with Gemini.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("analyze", "select", "generate"):
        command = commands.add_parser(name)
        command.add_argument("job", help="Job description file, or - for stdin")
        command.add_argument("--output", type=Path, help="New output directory")
        if name != "analyze":
            source = command.add_mutually_exclusive_group(required=True)
            source.add_argument("--profile", type=Path, help="Candidate profile JSON")
            source.add_argument("--demo", action="store_true", help="Use fictional sample profile")
    for name in ("retry", "compile"):
        command = commands.add_parser(name)
        command.add_argument("output", type=Path, help="Existing run directory")
    commands.add_parser("demo-profile", help="Print a fictional profile as JSON; no API call")
    return parser


def configure_logging(output: Path, append: bool = False) -> list[logging.Handler]:
    """Send progress to stderr and diagnostic logs to the run directory."""
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    file = logging.FileHandler(output / "run.log", mode="a" if append else "w", encoding="utf-8")
    file.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s | %(levelname)s | %(message)s",
                        handlers=[console, file], force=True)
    # Keep SDK transport noise out of progress output and debug traces.
    for name in ("httpx", "httpcore", "google.genai"):
        logging.getLogger(name).setLevel(logging.WARNING)
    return [console, file]


def main(argv: list[str] | None = None) -> int:
    """Validate inputs, wire dependencies, and execute a single use case."""
    args = build_parser().parse_args(argv)
    model = None
    handlers = []
    try:
        if args.command == "demo-profile":
            print(MockProfileProvider().get_profile().model_dump_json(indent=2))
            return 0
        description = ""
        # Offline commands do not need credentials. Online commands validate them
        # before reserving an output folder, so a config typo leaves no empty run.
        settings = None if args.command == "compile" else Settings.from_env()
        if args.command in ("analyze", "select", "generate"):
            description = sys.stdin.read() if args.job == "-" else Path(args.job).read_text(encoding="utf-8")
            if not description.strip():
                raise ValueError("Job description must not be empty.")
            output = args.output or Path("output") / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
            output.mkdir(parents=True, exist_ok=False)
        else:
            output = args.output
            if not output.is_dir():
                raise ValueError(f"Run directory does not exist: {output}")
        handlers = configure_logging(output, append=args.command in ("retry", "compile"))
        if args.command == "compile":
            pdf, pages = LatexCompiler().compile(output / "04_tailored_cv.tex")
            if pages != 1:
                raise ValueError(f"Compiled CV has {pages} pages; expected one. PDF saved at {pdf}.")
            final = output / "05_tailored_cv.pdf"
            pdf.replace(final)
            print(final.resolve())
            return 0
        # This is the composition root: concrete adapters are constructed here,
        # while application services only receive the interfaces they use.
        model = GeminiModel(settings)
        analyzer = JobAnalyzer(model)
        if args.command == "analyze":
            job = analyzer.analyze(description)
            (output / "02_job_analysis.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")
            print(job.model_dump_json(indent=2))
            return 0
        selector = ProfileSelector(model)
        if args.command == "select":
            provider = JsonProfileProvider(args.profile) if args.profile else MockProfileProvider()
            _, _, selected = select_profile(description, provider, output, analyzer, selector)
            print(selected.model_dump_json(indent=2))
            return 0
        writer = CvWriter(
            model,
            (RESOURCES / "cv_template.tex").read_text(encoding="utf-8"),
            (RESOURCES / "latex_rules.md").read_text(encoding="utf-8"),
        )
        pipeline = CvPipeline(analyzer, selector, writer, LatexCompiler())
        if args.command == "retry":
            print(pipeline.retry(output).resolve())
        else:
            provider = JsonProfileProvider(args.profile) if args.profile else MockProfileProvider()
            print(pipeline.generate(description, provider, output).resolve())
        return 0
    except Exception as exc:
        logging.getLogger(__name__).debug("Command failed", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            if model is not None:
                model.close()
        finally:
            # Release file handles for repeated CLI calls and Windows cleanup.
            for handler in handlers:
                logging.getLogger().removeHandler(handler)
                handler.close()
