#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command Line Interface."""
import sys
from argparse import ArgumentParser

from omim2obo.omim_code_scraper import get_codes_by_yyyy_mm, OmimDataPipelineError


def get_parser():
    """Add required fields to parser.

    Returns:
        ArgumentParser: Argeparse object.
    """
    package_description = 'OMIM data pipeline tools'
    parser = ArgumentParser(description=package_description)

    # TODO: More complicated arguments for later time
    # - When or if these are added, will need to make sure they are passed together
    # parser.add_argument(
    #     '-i',
    #     '--import_stats',
    #     help='Imports from https://omim.org/statistics/update. This is '
    #          'currently the only feature. If used, must also provide --month.')
    #
    # parser.add_argument(
    #     '-m',
    #     '--month',
    #     # TODO: allow multiple months to be fetched at oncce
    #     # nargs='+',
    #     help='The year and month to import, formatted as YYYY/MM. For example, '
    #          '2021/05. Must be passed with --import_stats.')

    parser.add_argument(
        'YYYY/MM',
        help='The year and month to import, formatted as YYYY/MM. For example, '
             '2021/05')

    parser.add_argument(
        '-o',
        '--outpath',
        help='Path to save output file. If not present, same directory of '
             'any input files passed will be used.')

    return parser


def cli():
    """Command line interface for package.

    Side Effects: Executes program.

    Command Syntax:

    Examples:

    """

    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    kwargs = parser.parse_args()

    try:
        code_tuples = get_codes_by_yyyy_mm(
            yyyy_mm=getattr(kwargs, 'YYYY/MM'),
            outpath=kwargs.outpath)
        from pprint import pprint
        pprint(code_tuples)
    except OmimDataPipelineError as err:
        err = 'An error occurred.\n\n' + str(err)
        print(err, file=sys.stderr)


if __name__ == '__main__':
    cli()
