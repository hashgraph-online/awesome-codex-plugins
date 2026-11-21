"""The command line every ``sync_datasheets_<provider>.py`` script shares."""

import argparse
import sys

from distributor_core.download import add_download_args, apply_download_args


def sync_main(sync, *, description: str, vendor: str, delay: float, delay_help: str,
              add_extra=None, extra_kwargs: tuple = ()) -> None:
    """Parse the sync command line, run ``sync(**kwargs)`` and exit 1 on an error, else 0.

    *vendor* names the distributor in ``--force``'s help. *add_extra(parser)*, when given,
    adds the provider's own options after ``--output``; *extra_kwargs* names the ones
    forwarded to *sync*. A run with failed parts still exits 0.
    """
    parser = argparse.ArgumentParser(description=description)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "input",
        nargs="?",
        help="Path to .kicad_sch file or pre-computed analyzer JSON",
    )
    input_group.add_argument(
        "--mpn-list",
        metavar="FILE",
        help=("Path to a text file with one MPN per line (batch mode, no project). "
              "Skips blank lines and '#' comments. Output defaults to "
              "./datasheets/ in cwd when --output is not given."),
    )
    parser.add_argument(
        "--output", "-o",
        help=("Output directory (default: datasheets/ next to input, "
              "or ./datasheets/ in cwd when --mpn-list is used)"),
    )
    if add_extra is not None:
        add_extra(parser)
    parser.add_argument(
        "--force", action="store_true",
        help=(f"Retry parts a previous run failed at {vendor} "
              "(parts that failed only at other distributors are retried anyway)"),
    )
    parser.add_argument(
        "--force-all", action="store_true",
        help=("Re-download everything, including already-present files; "
              "a present file and its entry are kept when the refresh fails"),
    )
    parser.add_argument(
        "--delay", type=float, default=delay,
        help=delay_help,
    )
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Number of parallel download workers (default: 1)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be downloaded without doing it",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Print the summary as one JSON document on stdout (progress goes to stderr)",
    )
    add_download_args(parser)
    args = parser.parse_args()
    apply_download_args(args)

    result = sync(
        input_path=args.input,
        output_dir=args.output,
        force=args.force,
        force_all=args.force_all,
        delay=args.delay,
        parallel=args.parallel,
        dry_run=args.dry_run,
        as_json=args.json,
        mpn_list=args.mpn_list,
        **{k: getattr(args, k) for k in extra_kwargs},
    )
    sys.exit(1 if "error" in result else 0)
