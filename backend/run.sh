#!/usr/bin/env bash
set -euo pipefail

XLSX="${1:-dcat-v3-example.xlsx}"
YARRRML="${2:-dcat-v3.yarrrml.yml}"

# Output files
CSV="datasets.csv"
RML="mapping.rml.ttl"
TTL="out.ttl"
SHAPES="shapes.ttl"
REPORT="shacl-report.txt"

echo "[1/4] XLSX -> CSV (sheet: datasets)"
docker run --rm -v "$PWD":/data python:3.11-slim bash -lc "
  pip -q install pandas openpyxl >/dev/null
  python - << 'PY'
import pandas as pd
xlsx = '/data/${XLSX}'
df = pd.read_excel(xlsx, sheet_name='datasets')
df.to_csv('/data/${CSV}', index=False)
print('Wrote /data/${CSV} with', len(df), 'rows')
PY
"

echo "[2/4] YARRRML -> RML"
docker run --rm -v "$PWD":/data node:20-slim bash -lc "
  npm -g --silent install @rmlio/yarrrml-parser >/dev/null
  yarrrml-parser -i /data/${YARRRML} -o /data/${RML}
"

echo "[3/4] RML -> RDF (Turtle)"
docker run --rm -v "$PWD":/data rmlio/rmlmapper-java:latest \
  -m /data/${RML} -o /data/${TTL} -s turtle

echo "[4/4] SHACL validate"
docker run --rm -v "$PWD":/data python:3.11-slim bash -lc "
  pip -q install pyshacl rdflib >/dev/null
  python - << 'PY'
import sys
from pyshacl import validate
from rdflib import Graph

# Paths
TTL_FILE = '/data/${TTL}'
SHAPES_FILE = '/data/shacl/constructDCAT_shacl.ttl'
ONTOLOGY_FILE = '/data/ontology/constructDCAT.ttl'
REPORT_FILE = '/data/${REPORT}'

print(f'Validating {TTL_FILE} against {SHAPES_FILE} with ontology {ONTOLOGY_FILE}...')

data_g = Graph().parse(TTL_FILE, format='turtle')
shapes_g = Graph().parse(SHAPES_FILE, format='turtle')
ontology_g = Graph().parse(ONTOLOGY_FILE, format='turtle')

# We mix ontology into data graph for RDFS inference if needed, 
# or pass it as 'ont_graph' to pyshacl if we want to separate logic. 
# Typically for 'rdfs' inference, pyshacl looks at the data graph.
# But allow pyshacl to handle the ontology graph separately via ont_graph is cleaner.

conforms, report_g, report_text = validate(
    data_g,
    shacl_graph=shapes_g,
    ont_graph=ontology_g,
    inference='rdfs',
    abort_on_first=False,
    meta_shacl=False,
    advanced=False,
    debug=False,
)
open(REPORT_FILE,'w',encoding='utf-8').write(report_text)
print('SHACL conforms:', conforms)
print(f'Report written to {REPORT_FILE}')

if not conforms:
    sys.exit(1)
PY
"
"

echo
echo "✅ Done."
echo "RDF:    ${TTL}"
echo "SHACL:  ${REPORT}"
