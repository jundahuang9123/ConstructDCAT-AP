#!/usr/bin/env bash
set -euo pipefail

echo "🔄 Updating Ontology from Excel..."

docker run --rm -v "$PWD":/data python:3.11-slim bash -lc "
  pip -q install pandas openpyxl rdflib >/dev/null
  cd /data
  python excel_to_ontology.py
  echo "📊 Generating visualization..."
  python viz_gen.py ontology/constructDCAT.ttl
"

echo "✅ Ontology updated."
echo "   - Ontology: backend/ontology/constructDCAT.ttl"
echo "   - SHACL:    backend/shacl/constructDCAT_shacl.ttl"
