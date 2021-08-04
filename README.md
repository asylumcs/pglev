# pglev
edit distance text analysis program used before/during upload to Project Gutenberg.
It may be used standalone by cloning this repo locally. It is also
part of the Uploader's Workbench (UWB) at Project Gutenberg.

## Overview

This is a Python program used to analyze a UTF-8 text file by looking at the
edit distance ("Levenshtein distance") between candidate words.
It accepts a UTF-8 source file and produces a report file in HTML for display in
a browser, where color-coding may be used.

## Usage

### Standalone

As a standalone program use this command line:

    python3 pglev.py -i sourcefile.txt -o report.htm

### In the UWB

This is one of the tests available in the
[UWB](https://uwb.pglaf.org).
You must have a user account on the pglaf server to use the UWB.

## Restrictions

This program is useful only for English-language texts.
