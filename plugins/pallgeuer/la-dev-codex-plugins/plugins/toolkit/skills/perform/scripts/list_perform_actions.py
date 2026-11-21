#!/usr/bin/env python3
"""List effective Perform actions as compact JSON."""

import pathlib
import sys

import toolkit_perform_runtime.cli as runtime_cli
from toolkit_perform_runtime.diagnostics import PerformRequestError


def _parser():
    """Build the stable bundled-script argument parser."""
    parser = runtime_cli.JsonArgumentParser(description="List effective Perform action variants as compact JSON.")
    parser.add_argument("--name", action="store_once", help="Narrow to one exact bare action name.")
    parser.add_argument("--fallback", action="store_once", nargs=0, const=True, default=False, help="List the full catalog when --name has no effective variants.")
    parser.add_argument("--cwd", action="store_once", default=str(pathlib.Path.cwd()), help="Working directory used for conventional local discovery.")
    return parser


def main(argv=None):
    """Discover, load, and list actions with an optional one-call fallback."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.fallback and args.name is None:
        parser.error("--fallback requires --name.")

    def command(context):
        catalog = context.load_catalog(args.cwd)
        summaries = catalog.list_actions(name=args.name)
        if args.name is not None and not summaries and args.fallback:
            summaries = catalog.list_actions()
        result = {"variants": [summary.to_dict() for summary in summaries]}
        if catalog.precedence_incomplete:
            error = PerformRequestError("fatal_catalog", "Catalog precedence is incomplete; fix the fatal discovery or file diagnostic before executing an action.")
            return runtime_cli.CliOutcome(result=result, error=error)
        return runtime_cli.CliOutcome(result=result)

    return runtime_cli.run_cli(command)


if __name__ == "__main__":
    sys.exit(main())
