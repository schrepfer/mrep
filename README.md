# mrep

My REPlace (MREP): Replaces occurrences of text within a file.

## Usage

```
usage: mrep.py [-h] [-v LEVEL] [-V] [-b] [--backup_format FORMAT] [-n]
               [--diff_context LINES] [-r] [-f RegexFlag] [-e] [-x LAMBDA]
               SEARCH REPLACEMENT FILE [FILE ...]

My REPlace (MREP): Replaces occurrences of text within a file.

positional arguments:
  SEARCH                Search string or pattern.
  REPLACEMENT           Replacement string. If --regexp is enabled, you can
                        reference capturing groups with \1, \2, etc. or use
                        --func to process the `re.Match[str]`.
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
  -n, --diff            Diff the proposed changes only. Do not actually touch
                        the files.
  --diff_context LINES  The amount of context to show in unified diffs.
  -r, --regexp, --regex, --re
                        Make the search string a regexp pattern. With this
                        option you can use regexp capturing groups, and
                        reference those values in the replacement with \1, \2,
                        etc.
  -f RegexFlag, --flag RegexFlag
                        See
                        https://docs.python.org/3/library/re.html#re.RegexFlag
                        for options. RegexFlags: re.ASCII, re.DEBUG,
                        re.DOTALL, re.IGNORECASE, re.LOCALE, re.MULTILINE,
                        re.NOFLAG, re.VERBOSE
  -e, --escape          Enable usage of backslash escapes. Useful if you want
                        to replace \r, etc.
  -x LAMBDA, --func LAMBDA, --lambda LAMBDA
                        A lambda function body that takes a single argument
                        (an `re.Match[str]` object). E.g. `lambda m:
                        m.group(1)`. You may also reference the `replacement`
                        global variable which contains the value of the
                        REPLACEMENT metavar provided.
```

## Examples

1.  Diff (`-n`) a delete of lines with `split_tests` from *.manifest files (and
    the preceeding comments). The `xargs` command will batch up 50 replacements
    at a time.

    ```
     find -type f -name '*.manifest' -print0 | xargs -0 -L50 -- \
           mrep -n -r -f re.MULTILINE '(\s+#.*$)*\s+split_tests\s*=\s*\d+,.*$' ''
    ```

1.  Replace simple string in all Go files in current directory (and back them up
    with `.old` suffix).

    ```
     mrep -b --backup_format='%s.old' 'spec.Run()' 'setup.RunSpec(ctx, p.Opts, spec)' *.go
    ```

1.  Replace all words (\w) with the capitalized version of that value. The
    lambda takes the 0 group (which is the full matched string) and uppers it.

    ```
    mrep -r -x 'lambda m: m.group(0).upper()' '\w+:' '' *.py
    ```
