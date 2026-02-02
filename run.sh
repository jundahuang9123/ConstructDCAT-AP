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

echo "[4/4] SHACL validate (minimal shapes)"
# Minimal shapes: checks core DCAT bits exist
cat > "${SHAPES}" <<'TTL'
@prefix sh:   <http://www.w3.org/ns/shacl#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

:DatasetShape a sh:NodeShape ;
  sh:targetClass dcat:Dataset ;
  sh:property [
    sh:path dct:title ;
    sh:minCount 1 ;
  ] ;
  sh:property [
    sh:path dcat:distribution ;
    sh:minCount 1 ;
  ] .

:DistributionShape a sh:NodeShape ;
  sh:targetClass dcat:Distribution ;
  sh:property [
    sh:path dcat:accessURL ;
    sh:minCount 1 ;
  ] .
TTL

docker run --rm -v "$PWD":/data python:3.11-slim bash -lc "
  pip -q install pyshacl rdflib >/dev/null
  python - << 'PY'
from pyshacl import validate
from rdflib import Graph
data_g = Graph().parse('/data/${TTL}', format='turtle')
shapes_g = Graph().parse('/data/${SHAPES}', format='turtle')
conforms, report_g, report_text = validate(
    data_g,
    shacl_graph=shapes_g,
    inference='rdfs',
    abort_on_first=False,
    meta_shacl=False,
    advanced=False,
    debug=False,
)
open('/data/${REPORT}','w',encoding='utf-8').write(report_text)
print('SHACL conforms:', conforms)
print('Report written to /data/${REPORT}')
PY
"

echo
echo "✅ Done."
echo "RDF:    ${TTL}"
echo "SHACL:  ${REPORT}"
