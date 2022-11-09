#!/usr/bin/env python3

"""My REPlace (MREP): Replaces occurrences of text within a file."""

import argparse
import difflib
import itertools
import logging
import os
import re
import shutil
import sys


flagsChoices = [
    're.ASCII',      're.A',
    're.DEBUG',
    're.DOTALL',     're.S',
    're.IGNORECASE', 're.I',
    're.LOCALE',     're.L',
    're.MULTILINE',  're.M',
    're.NOFLAG',
    're.VERBOSE',    're.X',
]


def defineFlags() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/3/library/argparse.html
  parser.add_argument(
      '-v', '--verbosity',
      action='store',
      default=20,
      type=int,
      help='The logging verbosity.',
      metavar='LEVEL')
  parser.add_argument(
      '-V', '--version',
      action='version',
      version='%(prog)s version 0.2')
  parser.add_argument(
      '-b', '--backup',
      action='store_true',
      default=False,
      help='Backup files being modified. See --backup_format for options on the format.')
  parser.add_argument(
      '--backup_format',
      action='store',
      default='%s~',
      type=str,
      help='Backup files in this format; %s is expanded to the current file name.',
      metavar='FORMAT')
  parser.add_argument(
      '-r', '--regexp', '--regex', '--re',
      action='store_true',
      default=False,
      help=(
          'Make the search string a regexp pattern. With this option you can use regexp capturing '
          r'groups, and reference those values in the replacement with \1, \2, etc.'),
  )
  parser.add_argument(
      '-n', '--diff',
      action='store_true',
      default=False,
      help='Diff the proposed changes only. Do not actually touch the files.',
  )
  parser.add_argument(
      '-f', '--flags',
      action='append',
      choices=flagsChoices,
      nargs=1,
      type=str,
      metavar='RegexFlag',
      help=(
          'See https://docs.python.org/3/library/re.html#re.RegexFlag for options. '
          'RegexFlags: ' + ', '.join(filter(lambda x: len(x) > 4, flagsChoices))),
  )
  parser.add_argument(
      '-e', '--escape',
      action='store_true',
      default=False,
      help='Enable usage of backslash escapes. Useful if you want to replace \\r, etc.',
  )
  parser.add_argument(
      'search',
      nargs=1,
      type=str,
      help='Search string or pattern.',
      metavar='SEARCH',
  )
  parser.add_argument(
      'replacement',
      nargs=1,
      type=str,
      help=(
          'Replacement string. If --regexp is enabled, you can reference capturing groups with '
          r'\1, \2, etc.'),
      metavar='REPLACEMENT',
  )
  parser.add_argument(
      'files',
      nargs='+',
      type=str,
      help='Files to consider in the search replacement.',
      metavar='FILE',
  )

  args = parser.parse_args()
  checkFlags(parser, args)
  return args


def checkFlags(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
  # See: http://docs.python.org/3/library/argparse.html#exiting-methods
  if args.backup_format and args.backup_format.count('%s') != 1:
    parser.error('--backup_format must contain %s exactly once')

  if args.search == args.replacement and not args.regexp:
    parser.error('SEARCH and REPLACEMENT must be different')

  if len(args.flags) and not args.regexp:
    parser.error('--flags specified but --regexp is not')


def regexpFlags(args: argparse.Namespace) -> int:
  flags = 0
  for f in itertools.chain.from_iterable(args.flags):
    flags |= eval(f).value
  return flags


class Replacer(object):
  """Replacer keeps state and replaces content in files."""

  args: argparse.Namespace
  flags: int

  def __init__(self, args: argparse.Namespace):
    self.args = args
    self.flags = regexpFlags(args)

  def replaceOne(self, file_path: str) -> bool:
    """Replace text in the given file."""
    if not os.path.isfile(file_path):
      logging.error('Not a valid/readable file: %s', file_path)
      return False

    try:
      with open(file_path, 'r') as file_handle:
        file_contents: str = file_handle.read()
    except:
      logging.error('Could not open file for reading: %s', file_path)
      return False

    search: str = self.args.search[0]
    replacement: str = self.args.replacement[0]

    if self.args.escape:
      search = search.encode('utf-8').decode('unicode_escape')
      replacement = replacement.encode('utf-8').decode('unicode_escape')

    if self.args.regexp:
      new_file_contents = re.sub(search, replacement, file_contents, flags=self.flags)
    else:
      new_file_contents = file_contents.replace(search, replacement)

    if file_contents == new_file_contents:
      logging.warning('Nothing replaced: %s', file_path)
      return True

    if self.args.backup and self.args.backup_format and not self.args.diff:
      backup_file_path: str = self.args.backup_format % file_path
      try:
        shutil.copyfile(file_path, backup_file_path)
        logging.info('Created backup for %s: %s', file_path, backup_file_path)
      except:
        logging.error('Could not create backup for %s, skipping: %s', file_path, backup_file_path)
        return False

    if self.args.diff:
      print('\n'.join(difflib.unified_diff(
          file_contents.split('\n'),
          new_file_contents.split('\n'),
          fromfile='before',
          tofile='after',
      )))
      return True

    try:
      file_handle = open(file_path, 'w')
    except:
      logging.error('Could not open file for writing: %s', file_path)
      return False
    with file_handle:
      file_handle.write(new_file_contents)
    logging.info('Replaced %r with %r in %s', search, replacement, file_path)

    return True

  def replace(self) -> bool:
    """Replace text in all files."""
    errors = False
    for file_path in self.args.files:
      if not self.replaceOne(file_path):
        errors = True
    return not errors


def main(args: argparse.Namespace) -> int:
  if not Replacer(args).replace():
    return os.EX_DATAERR

  return os.EX_OK


if __name__ == '__main__':
  a = defineFlags()
  logging.basicConfig(
      level=a.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(a))
