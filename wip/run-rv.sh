#!/bin/sh
# Private: the Rechtsverordnungen fetch (list, then every zip), one process, one request at a time.
cd "$(dirname "$0")"
python -X utf8 -u fetch.py list rv && python -X utf8 -u fetch.py zip --all-rv
