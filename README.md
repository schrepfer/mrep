# mrep
My REPlace (MREP): Replaces occurrences of text within a file.

## Usage

```
usage: mrep.py [-h] [-v LEVEL] [-V] [-b] [--backup_format FORMAT] [-r] [-n] [-f RegexFlag] [-e] SEARCH REPLACEMENT FILE [FILE ...]

My REPlace (MREP): Replaces occurrences of text within a file.

positional arguments:
  SEARCH                search string or pattern (with --regexp)
  REPLACEMENT           replacement string
  FILE                  files to consider

options:
  -h, --help            show this help message and exit
  -v LEVEL, --verbosity LEVEL
                        the logging verbosity
  -V, --version         show program's version number and exit
  -b, --backup          backup files being modified
  --backup_format FORMAT
                        backup files in this format; %s is expanded
  -r, --regexp, --regex, --re
                        make the search string a regexp pattern
  -n, --pretend         only pretend to do the replacements
  -f RegexFlag, --flags RegexFlag
                        See https://docs.python.org/3/library/re.html#re.RegexFlag for options
  -e, --backslash       enable usage of backslash escapes
```
