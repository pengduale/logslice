"""CLI helpers for bookmark/checkpoint management subcommands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from logslice.bookmark import BookmarkConfig, LogBookmark


def build_bookmark_parser(subparsers) -> None:
    p = subparsers.add_parser("bookmark", help="Manage read-position bookmarks")
    sub = p.add_subparsers(dest="bookmark_cmd", required=True)

    show = sub.add_parser("show", help="Show bookmark for a source file")
    show.add_argument("source", help="Log file path")
    show.add_argument("--store-dir", default=".logslice_bookmarks")

    clear = sub.add_parser("clear", help="Clear bookmark for a source file")
    clear.add_argument("source", help="Log file path")
    clear.add_argument("--store-dir", default=".logslice_bookmarks")

    list_cmd = sub.add_parser("list", help="List all bookmarks in the store")
    list_cmd.add_argument("--store-dir", default=".logslice_bookmarks")


def run_bookmark_command(args: argparse.Namespace) -> int:
    store_dir = getattr(args, "store_dir", ".logslice_bookmarks")
    config = BookmarkConfig(enabled=True, store_dir=store_dir)
    bm = LogBookmark(config)

    if args.bookmark_cmd == "show":
        bookmark = bm.load(args.source)
        if bookmark is None:
            print(f"No bookmark found for '{args.source}'", file=sys.stderr)
            return 1
        print(json.dumps(bookmark.to_dict(), indent=2))
        return 0

    if args.bookmark_cmd == "clear":
        bm.clear(args.source)
        print(f"Bookmark cleared for '{args.source}'")
        return 0

    if args.bookmark_cmd == "list":
        store = Path(store_dir)
        if not store.exists():
            print("No bookmark store found.")
            return 0
        files = sorted(store.glob("*.json"))
        if not files:
            print("No bookmarks stored.")
            return 0
        for f in files:
            try:
                data = json.loads(f.read_text())
                print(f"{data.get('source', f.stem)!r:40s}  line={data.get('line_number', 0)}")
            except (json.JSONDecodeError, OSError):
                print(f"  (unreadable: {f.name})")
        return 0

    return 1
