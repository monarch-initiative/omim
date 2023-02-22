#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command Line Interface."""
from argparse import ArgumentParser

from omim2obo import omim2obo


def get_parser():
    """Add required fields to parser.

    Returns:
        ArgumentParser: Argeparse object.
    """
    package_description = 'OMIM data pipeline: Builds omim.ttl from omim.org sources'
    parser = ArgumentParser(description=package_description)

    parser.add_argument(
        '-c', '--use-cache',
        action='store_true',
        help='Use cache instead of downloading sources')

    # out_help = ('Path to save output file. If not present, same directory of'
    #             'any input files passed will be used.')
    # parser.add_argument('-o', '--outpath', help=out_help)

    return parser


def cli():
    """Command line interface for package.

    Side Effects: Executes program.

    Command Syntax:

    Examples:

    """
    parser = get_parser()
    kwargs = parser.parse_args()
    omim2obo(use_cache=kwargs.use_cache)


if __name__ == '__main__':
    cli()
