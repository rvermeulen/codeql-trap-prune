# CodeQL TRAP prune

**Experimental** tool to reduce the size of databases created for a compiled language.

## Usage

This tool works on databases that aren't finalized.
To create such a database we need to perform the plumbing steps normally executed by `codeql database create`.

1. First initialize an empty database with `codeql database init --language cpp --source-root <source-root> <database>`
1. Index source files by tracing a build command with `codeql database trace-command -- <database> <build-command>`

With the unfinalized database, perform a dry run of the prune command to validate the results `./codeql-trap-prune.py --dry-run --include <include-regex> --exclude <exclude-regex> <database>`

If no include pattern is provided it matches `.*`.
The exclude pattern takes precedence of the include pattern so you can use that for fine grained exclusions.

The pattern is matched against the files paths relative to the source root (passed to the `codeql database init ...` command).

When happy with the results, perform an actual run and finalize the database with `codeql database finalize <database>`.
