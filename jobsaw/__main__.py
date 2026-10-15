"""Allow running the CLI with python -m jobsaw."""

from jobsaw.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
