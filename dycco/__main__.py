import argparse
import logging
import sys

from .dycco import document


def main(paths, output_dir, use_ascii:bool):
    try:
        document(paths, output_dir, use_ascii)
    except IOError as e:
        logging.error('Unable to open file: %s', e)
        return 1
    except Exception as e:
        logging.error('An error occurred: %s', e)
        return 1
    else:
        return 0


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(prog='dycco', description='Literate-style documentation generator.')
    arg_parser.add_argument('source_file', nargs='+', default=sys.stdin, help='Source files to document')
    arg_parser.add_argument('-o', '--output-dir', default='docs', help='Output directory (will be created if necessary)')
    arg_parser.add_argument('-a', '--asciidoc3', action='store_true', default=False, dest='use_ascii',
        help='Process with asciidoc3 instead of markdown (you will have to install asciidoc3, of course)')

    args = arg_parser.parse_args()
    sys.exit(main(args.source_file, args.output_dir, args.use_ascii))
