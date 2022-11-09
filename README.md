# mrep
My REPlace (MREP): Replaces occurrences of text within a file.

## Usage

```
usage: mrep.py [-h] [-v LEVEL] [-V] [-b] [--backup_format FORMAT] [-r] [-n]
               [--diff_context DIFF_CONTEXT] [-f RegexFlag] [-e]
               SEARCH REPLACEMENT FILE [FILE ...]

My REPlace (MREP): Replaces occurrences of text within a file.

positional arguments:
  SEARCH                Search string or pattern.
  REPLACEMENT           Replacement string. If --regexp is enabled, you can
                        reference capturing groups with \1, \2, etc.
  FILE                  Files to consider in the search replacement.

options:
  -h, --help            show this help message and exit
  -v LEVEL, --verbosity LEVEL
                        The logging verbosity.
  -V, --version         show program's version number and exit
  -b, --backup          Backup files being modified. See --backup_format for
                        options on the format.
  --backup_format FORMAT
                        Backup files in this format; %s is expanded to the
                        current file name.
  -r, --regexp, --regex, --re
                        Make the search string a regexp pattern. With this
                        option you can use regexp capturing groups, and
                        reference those values in the replacement with \1, \2,
                        etc.
  -n, --diff            Diff the proposed changes only. Do not actually touch
                        the files.
  --diff_context DIFF_CONTEXT
                        The amount of context to show in unified diffs.
  -f RegexFlag, --flags RegexFlag
                        See
                        https://docs.python.org/3/library/re.html#re.RegexFlag
                        for options. RegexFlags: re.ASCII, re.DEBUG,
                        re.DOTALL, re.IGNORECASE, re.LOCALE, re.MULTILINE,
                        re.NOFLAG, re.VERBOSE
  -e, --escape          Enable usage of backslash escapes. Useful if you want
                        to replace \r, etc.
```
