#!/bin/sh

find applications -type d -maxdepth 1 -mindepth 1 | grep -v "__pycache__" | while read -r APP; do
    APP="$(basename "$APP")"
    python3 web2py.py -Q -S "$APP" -M -R scripts/sessions2trash.py -A -o
    python3 web2py.py -Q -S "$APP" -R scripts/zip_static_files.py
done
