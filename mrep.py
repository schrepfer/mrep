#!/usr/bin/env python3

"""My REPlace (MREP): Replaces occurrences of text within a file."""

import argparse
import difflib
import io
import itertools
import logging
import os
import re
import shutil
import sys
import types

from typing import Callable, TextIO


flag_choices = [
    're.ASCII',      're.A',
    're.DEBUG',
    're.DOTALL',     're.S',
    're.IGNORECASE', 're.I',
    're.LOCALE',     're.L',
    're.MULTILINE',  're.M',
    're.NOFLAG',
    're.VERBOSE',    're.X',
]


def define_flags() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/3/library/argparse.html
  parser.add_argument(
      '-v', '--verbosity',
      action='store',
      default=logging.WARNING,
      type=int,
      metavar='LEVEL',
      help='The logging verbosity.',
  )
  parser.add_argument(
      '-V', '--version',
      action='version',
      version='%(prog)s version 0.2',
  )
  # Backup
  parser.add_argument(
      '-b', '--backup',
      action='store_true',
      default=False,
      help='Backup files being modified. See --backup_format for options on the format.',
  )
  parser.add_argument(
      '--backup_format',
      action='store',
      default='%s~',
      type=str,
      metavar='FORMAT',
      help='Backup files in this format; %%s is expanded to the current file name.',
  )
  # Diff
  parser.add_argument(
      '-n', '--diff',
      action='store_true',
      default=False,
      help='Diff the proposed changes only. Do not actually touch the files.',
  )
  parser.add_argument(
      '--diff_context',
      action='store',
      default=3,
      type=int,
      metavar='LINES',
      help='The amount of context to show in unified diffs.',
  )
  # Regexp
  parser.add_argument( '-r', '--regexp', '--regex', '--re',
      action='store_true',
      default=False,
      help=('Make the search string a regexp pattern. With this option you can use regexp '
            'capturing groups, and reference those values in the replacement with '
            r'\1, \2, etc.'),
  )
  parser.add_argument(
      '-f', '--flag',
      action='append',
      choices=flag_choices,
      default=[],
      type=str,
      metavar='RegexFlag',
      help=('See https://docs.python.org/3/library/re.html#re.RegexFlag for options. '
            'RegexFlags: ' + ', '.join(filter(lambda x: len(x) > 4, flag_choices))),
  )
  # Misc patterns
  parser.add_argument(
      '-e', '--escape',
      action='store_true',
      default=False,
      help='Enable usage of backslash escapes. Useful if you want to replace \\r, etc.',
  )
  # Replacements
  parser.add_argument(
      'search',
      nargs=1,
      type=str,
      metavar='SEARCH',
      help='Search string or pattern.',
  )
  parser.add_argument(
      'replacement',
      nargs=1,
      type=str,
      metavar='REPLACEMENT',
      help=('Replacement string. If --regexp is enabled, you can reference capturing groups with '
            r'\1, \2, etc.'),
  )
  parser.add_argument(
      '-x', '--func',
      action='store',
      default=None,
      type=str,
      metavar='LAMBDA',
      help='Lambda function body that takes a single argument (found str)',
  )

  # Files
  parser.add_argument(
      'files',
      nargs='*',
      type=str,
      metavar='FILE',
      default=['-'],
      help='Files to consider in the search replacement.',
  )

  args = parser.parse_args()
  check_flags(parser, args)
  return args


def check_flags(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
  # See: http://docs.python.org/3/library/argparse.html#exiting-methods
  if args.backup_format and args.backup_format.count('%s') != 1:
    parser.error('--backup_format must contain %s exactly once')

  if args.search == args.replacement and not args.regexp:
    parser.error('SEARCH and REPLACEMENT should (and must) be different')

  if len(args.flag) and not args.regexp:
    parser.error('--flag specified but --regexp is not (and required)')

  if len(args.files) > 1 and is_stdin(args.files[0]):
    parser.error('FILES contains stdin and must contain exactly one entry')

  if args.func and not args.regexp:
    parser.error('FUNC set but --regexp is not set (and required)')


def regexp_flags(args: argparse.Namespace) -> int:
  flags = 0
  for f in itertools.chain.from_iterable(args.flag):
    flags |= eval(f).value
  return flags


def is_stdin(file_path: str) -> bool:
  return file_path in {'/dev/stdin', '-'}


def regexp_replace_with_fn(
        search: str,
        replace_fn: Callable[[re.Match[str]], str],
        file_contents: str,
        flags: int = 0) -> str:
  buf = io.StringIO()
  end = 0
  for m in re.finditer(search, file_contents, flags=flags):
    buf.write(file_contents[end:m.start()])
    buf.write(replace_fn(m))
    end = m.end()
  buf.write(file_contents[end:])
  return buf.getvalue()


num_fake_matches = 20
fake_re_match = re.match(r'(.)'*num_fake_matches, 'X'*num_fake_matches)


class Replacer(object):
  """Replacer keeps state and replaces content in files."""

  args: argparse.Namespace
  flags: int

  def __init__(self, args: argparse.Namespace):
    self.args = args
    self.flags = regexp_flags(args)

  def replace_one(self, file_path: str) -> bool:
    """Replace text in the given file."""
    file_contents: str
    output_fn: Callable[[], TextIO]
    file_handle: TextIO

    if is_stdin(file_path):
      file_contents = sys.stdin.read()
      output_fn = lambda: sys.stdout
    else:
      if not os.path.isfile(file_path):
        logging.error('Not a valid/readable file: %s', file_path)
        return False
      try:
        with open(file_path, 'r') as file_handle:
          file_contents = file_handle.read()
        output_fn = lambda: open(file_path, 'w')
      except:
        logging.error('Could not open file for reading: %s', file_path)
        return False

    search: str = self.args.search[0]
    replacement: str = self.args.replacement[0]

    if self.args.escape:
      search = search.encode('utf-8').decode('unicode_escape')
      replacement = replacement.encode('utf-8').decode('unicode_escape')

    if self.args.regexp:
      #new_file_contents = re.sub(search, replacement, file_contents, flags=self.flags)
      fn: Callable[[re.Match[str]], str]
      if self.args.func:
        fn = eval(self.args.func, {'replacement': replacement})
      else:
        fn = lambda m: m.expand(replacement)
      # Simple check to verify that the function returns a string.
      if not isinstance(fn, types.LambdaType):
        logging.fatal('Replacement func must be of the format: `lambda m: str(...)`')
        return False
      try:
        if not isinstance(fn(fake_re_match), str):
          logging.fatal('Lambda func does not return a string')
          return False
      except TypeError:
        logging.fatal('Lambda func should have exactly 1 argument of type re.Match')
        return False
      new_file_contents = regexp_replace_with_fn(search, fn, file_contents, flags=self.flags)
    else:
      new_file_contents = file_contents.replace(search, replacement)

    if file_contents == new_file_contents:
      logging.debug('Nothing replaced: %s', file_path)
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
          n=self.args.diff_context,
      )))
      return True

    try:
      file_handle = output_fn()
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
      if not self.replace_one(file_path):
        errors = True
    return not errors


def main(args: argparse.Namespace) -> int:
  if not Replacer(args).replace():
    return os.EX_DATAERR

  return os.EX_OK


if __name__ == '__main__':
  a = define_flags()
  logging.basicConfig(
      level=a.verbosity,
      datefmt='%Y/%m/%d %H:%M:%S',
      format='[%(asctime)s] %(levelname)s: %(message)s')
  sys.exit(main(a))
