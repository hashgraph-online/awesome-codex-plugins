#!/usr/bin/env python3
"""Write a stable Markdown catalogue of effective Perform actions."""

import pathlib
import sys

import toolkit_perform_runtime.action_catalogue as action_catalogue
import toolkit_perform_runtime.cli as runtime_cli


def _parser():
    """Build the stable bundled-script argument parser."""
    parser = runtime_cli.JsonArgumentParser(description="Write a stable Markdown catalogue of effective Perform actions.")
    parser.add_argument("--output", action="store_once", help="Output path; relative paths resolve from the repository root and may use parent traversal.")
    parser.add_argument("--cwd", action="store_once", default=str(pathlib.Path.cwd()), help="Working directory used for conventional local discovery.")
    return parser


def main(argv=None):
    """Discover actions and safely update their Markdown catalogue."""
    args = _parser().parse_args(argv)

    def command(context):
        catalog = context.load_catalog(args.cwd)
        result = action_catalogue.write_action_catalogue(catalog, output=args.output)
        return runtime_cli.CliOutcome(result=result)

    return runtime_cli.run_cli(command)


if __name__ == "__main__":
    sys.exit(main())
