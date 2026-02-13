#!/bin/bash
# Generate Documentation using Widoco

# Ensure Widoco exists
if [ ! -f "backend/tools/widoco.jar" ]; then
    echo "Widoco not found. Downloading..."
    python3 backend/download_widoco.py
fi

echo "Generating documentation..."
java -jar backend/tools/widoco.jar \
    -ontFile backend/ontology/constructDCAT.ttl \
    -outFolder docs \
    -rewriteAll \
    -webVowl \
    -lang en \
    -getOntologyMetadata \
    -licensius # Try to get license info

if [ -f "docs/index-en.html" ]; then
    mv docs/index-en.html docs/index.html
fi

echo "Documentation generated in docs/"
