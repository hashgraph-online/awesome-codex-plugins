#!/usr/bin/env python3
"""Inspect or render one strict Perform action as compact JSON."""

import pathlib
import sys

import toolkit_perform_runtime.cli as runtime_cli
import toolkit_perform_runtime.validation as validation


def _parser():
    """Build the strict-action direct-argument parser."""
    parser = runtime_cli.JsonArgumentParser(description="Inspect or render one strict Perform action as compact JSON.")
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--inspect", action="store_once", metavar="ACTION[LANGUAGE]", help="Inspect one canonical strict selector.")
    operation.add_argument("--render", action="store_once", metavar="ACTION[LANGUAGE]", help="Render one canonical strict selector.")
    parser.add_argument("--var", action="append", default=[], metavar="NAME=VALUE", help="Bind one prompt variable; repeat for multiple variables.")
    parser.add_argument("--qualification", "--question", dest="qualification", action="store_once", help="Append one compatible qualification, or ask built-in help one question.")
    parser.add_argument("--cwd", action="store_once", default=str(pathlib.Path.cwd()), help="Working directory used for conventional local discovery.")
    return parser


def main(argv=None):
    """Load the catalog and fulfill one strict inspect or render request."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.inspect is not None and (args.var or args.qualification is not None):
        parser.error("--var, --qualification, and --question are valid only with --render.")

    def command(context):
        variables = validation.parse_variable_bindings(args.var)
        catalog = context.load_catalog(args.cwd)
        if args.inspect is not None:  # noqa: SIM108 - Keep operation dispatch readable.
            result = catalog.inspect(args.inspect).to_dict()
        else:
            result = catalog.render(args.render, variables, qualification=args.qualification).to_dict()
        return runtime_cli.CliOutcome(result=result)

    return runtime_cli.run_cli(command)


if __name__ == "__main__":
    sys.exit(main())
