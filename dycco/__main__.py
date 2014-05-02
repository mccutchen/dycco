import argparse
import logging
import sys

from .dycco import document


def main(paths, output_dir):
    try:
        document(paths, output_dir)
    except IOError, e:
        logging.error('Unable to open file: %s', e)
        return 1
    except Exception, e:
        logging.error('An error occurred: %s', e)
        return 1
    else:
        return 0


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        prog='dycco',
        description='Literate-style documentation generator.')
    arg_parser.add_argument(
        'source_file', nargs='+', default=sys.stdin,
        help='Source files to document')
    arg_parser.add_argument(
        '-o', '--output-dir', default='docs',
        help='Output directory (will be created if necessary)')

    args = arg_parser.parse_args()
    sys.exit(main(args.source_file, args.output_dir))
