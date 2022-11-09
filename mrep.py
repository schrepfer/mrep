#!/usr/bin/env python3

"""My REPlace (MREP): Replaces occurrences of text within a file."""

import argparse
import logging
import os
import re
import shutil
import sys


def defineFlags():
  parser = argparse.ArgumentParser(description=__doc__)
  # See: http://docs.python.org/3/library/argparse.html
  parser.add_argument(
      '-v', '--verbosity',
      action='store',
      default=20,
      type=int,
      help='the logging verbosity',
      metavar='LEVEL')
  parser.add_argument(
      '-V', '--version',
      action='version',
      version='%(prog)s version 0.1')
  parser.add_argument(
      '-b', '--backup',
      action='store_true',
      default=False,
      help='backup files being modified')
  parser.add_argument(
      '--backup_format',
      action='store',
      default='%s~',
      type=str,
      help='backup files in this format; %%s is expanded',
      metavar='FORMAT')
  parser.add_argument(
      '-r', '--regexp', '--regex', '--re',
      action='store_true',
      default=False,
      help='make the search string a regexp pattern')
  parser.add_argument(
      '-n', '--pretend',
      action='store_true',
      default=False,
      help='only pretend to do the replacements')
  parser.add_argument(
      '-f', '--flags',
      choices={
          're.ASCII',      're.A',
          're.DEBUG',
          're.DOTALL',     're.S',
          're.IGNORECASE', 're.I',
          're.LOCALE',     're.L',
          're.MULTILINE',  're.M',
          're.NOFLAG',
          're.VERBOSE',    're.X',
      },
      nargs='*',
      type=str,
      metavar='RegexFlag',
      help='See https://docs.python.org/3/library/re.html#re.RegexFlag for options')
  parser.add_argument(
      '-e', '--backslash',
      action='store_true',
      default=False,
      help='enable usage of backslash escapes')

  parser.add_argument(
      'search',
      nargs=1,
      type=str,
      help='search string or pattern (with --regexp)',
      metavar='SEARCH')
  parser.add_argument(
      'replacement',
      nargs=1,
      type=str,
      help='replacement string',
      metavar='REPLACEMENT')
  parser.add_argument(
      'files',
      nargs='+',
      type=str,
      help='files to consider',
      metavar='FILE')

  args = parser.parse_args()
  checkFlags(parser, args)
  return args


def checkFlags(parser, args):
  # See: http://docs.python.org/3/library/argparse.html#exiting-methods
  if args.backup_format and args.backup_format.count('%s') != 1:
    parser.error('--backup_format must contain %s exactly once')

  if args.search == args.replacement and not args.regexp:
    parser.error('SEARCH and REPLACEMENT must be different')

  if len(args.flags) and not args.regexp:
    parser.error('--flags specified but --regexp is not')


def regexpFlags(args):
  flags = 0
  for f in args.flags:
    flags |= eval(f).value
  return flags


class Replacer(object):
  """Replacer keeps state and replaces content in files."""

  def __init__(self, args):
    self.args = args
    self.flags = regexpFlags(args)

  def replaceOne(self, file_path):
    """Replace text in the given file."""
    if not os.path.isfile(file_path):
      logging.error('Not a valid/readable file: %s', file_path)
      return False

    try:
      with open(file_path, 'r') as file_handle:
        file_contents = file_handle.read()
    except:
      logging.error('Could not open file for reading: %s', file_path)
      return False

    search = self.args.search[0]
    replacement = self.args.replacement[0]

    if self.args.backslash:
      search = search.decode('string_escape')
      replacement = replacement.decode('string_escape')

    if self.args.regexp:
      new_file_contents = re.sub(search, replacement, file_contents, flags=self.flags)
    else:
      new_file_contents = file_contents.replace(search, replacement)

    if file_contents == new_file_contents:
      logging.warning('Nothing replaced: %s', file_path)
      return True

    if self.args.backup and self.args.backup_format:
      backup_file_path = self.args.backup_format % file_path
      try:
        if not self.args.pretend:
          shutil.copyfile(file_path, backup_file_path)
        logging.info('Created backup for %s: %s', file_path, backup_file_path)
      except:
        logging.error('Could not create backup for %s, skipping: %s', file_path, backup_file_path)
        return False

    if not self.args.pretend:
      try:
        file_handle = open(file_path, 'w')
      except:
        logging.error('Could not open file for writing: %s', file_path)
        return False
      with file_handle:
        file_handle.write(new_file_contents)

    logging.info('Replaced %r with %r in %s', search, replacement, file_path)

    return True

  def replace(self):
    """Replace text in all files."""
    errors = False
    for file_path in self.args.files:
      if not self.replaceOne(file_path):
        errors = True
    return not errors


def main(args):
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
