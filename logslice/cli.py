"""Command-line interface for logslice."""

import argparse
import sys
from pathlib import Path

from logslice.filter import FilterConfig, LogFilter
from logslice.formatter import LogFormatter, OutputFormat
from logslice.tailer import TailConfig, LogTailer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice",
        description="A lightweight log filtering and tailing utility.",
    )
    parser.add_argument("file", help="Path to the log file")
    parser.add_argument(
        "-i", "--include",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Include only lines matching this regex (repeatable)",
    )
    parser.add_argument(
        "-e", "--exclude",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Exclude lines matching this regex (repeatable)",
    )
    parser.add_argument(
        "-n", "--lines",
        type=int,
        default=0,
        metavar="N",
        help="Number of initial lines to read (0 = all)",
    )
    parser.add_argument(
        "-f", "--follow",
        action="store_true",
        help="Follow the file for new lines (tail -f behaviour)",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.PLAIN.value,
        help="Output format (default: plain)",
    )
    parser.add_argument(
        "--no-line-numbers",
        action="store_true",
        help="Hide line numbers in output",
    )
    parser.add_argument(
        "--no-source",
        action="store_true",
        help="Hide source filename in output",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_path = Path(args.file)
    if not log_path.exists():
        print(f"logslice: error: file not found: {args.file}", file=sys.stderr)
        return 1

    filter_cfg = FilterConfig(
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )
    tail_cfg = TailConfig(
        filepath=str(log_path),
        initial_lines=args.lines,
        follow=args.follow,
        filter_config=filter_cfg,
    )
    formatter = LogFormatter(
        output_format=OutputFormat(args.format),
        show_line_numbers=not args.no_line_numbers,
        show_source=not args.no_source,
    )

    tailer = LogTailer(tail_cfg)
    try:
        for match in tailer.tail():
            print(formatter.format_match(match))
    except KeyboardInterrupt:
        pass
    finally:
        tailer.stop()

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
