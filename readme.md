# DCAT-AP Builder (Full Stack)

This repository provides a full-stack solution for converting Excel files to DCAT-AP RDF with SHACL validation.
It now features a **FastAPI backend** and a modern **web frontend**.

## Architecture

- **Frontend**: Lightweight HTML/JS application (`frontend/`).
- **Backend**: Python FastAPI service (`backend/`) that orchestrates the conversion pipeline.
- **Pipeline**: Uses Dockerized tools (RMLMapper, PySHACL) for robust RDF generation and validation.

## Ontology Visualization

Below is the class diagram for the `constructDCAT` extension ontology included in this repository.

```mermaid
classDiagram
    class Location
    class Checksum
    class PeriodOfTime
    class Policy
    class Relationship
    class Distribution
    class RightsStatement
    class Frequency
    class MediaType
    class CatalogRecord
    class Catalog
    class Role
    class Kind
    class DataService
    class HasFormat
    class DatasetSeries
    class Standard
    class Concept
    class Dataset
    class ProvenanceStatement
    class LicenseDocument
    class Identifier
    class Resource
    class LinguisticSystem
    class Agent
    class Usage
    Catalog <|-- Dataset
    Dataset <|-- Resource
    DataService <|-- Service
    DataService <|-- Resource
    CatalogRecord --o : primaryTopic 
    CatalogRecord --o : primaryTopic 
    DatasetSeries <|-- Dataset
    Distribution --o : accessService 
    Distribution --o : compressFormat 
    Distribution --o : packageFormat 
    Distribution --o : mediaType 
    Distribution --o : conformsTo 
    Distribution --o : accessURL 
    Distribution --o : downloadURL 
    Distribution --o : byteSize 
    Distribution --o : spatialResolutionInMeters 
    Distribution --o : temporalResolution 
    Relationship <|-- Concept
    Resource <|-- Catalogued resource
    Role <|-- Concept
    Catalog --o : catalog 
    Catalog --o : dataset 
    Catalog --o : service 
    Catalog --o : themeTaxonomy 
    Catalog --o : hasPart 
    Catalog --o : record 
    DataService --o : servesDataset 
    DataService --o : endpointURL 
    DataService --o : endpointDescription 
    Dataset --o : distribution 
    Dataset --o : spatialResolutionInMeters 
    Dataset --o : temporalResolution 
    Dataset --o : inSeries 
    Dataset --o : prev 
    Dataset --o : hasVersion 
    Dataset --o : hasCurrentVersion 
    Dataset --o : previousVersion 
    Dataset --o : version 
    Resource --o : accessService 
    Resource --o : contactPoint 
    Resource --o : keyword 
    Resource --o : landingPage 
    Resource --o : qualifiedRelation 
    Resource --o : theme 
    Resource --o : type 
    Resource --o : relation 
    Resource --o : qualifiedAttribution 
    Resource --o : license 
    Resource --o : rights 
    Resource --o : hasPart 
    Resource --o : isPartOf 
    Resource --o : policy 
    Resource --o : temporal 
    Resource --o : spatial 
    Resource --o : accrualPeriodicity 
    Resource --o : identifier 
    Resource --o : conformsTo 
    Resource --o : language 
    Resource --o : publisher 
    Resource --o : creator 
    Resource --o : isReferencedBy 
    Resource --o : version 
    Resource --o : hasVersion 
    Resource --o : hasCurrentVersion 
    Resource --o : previousVersion 
    Resource --o : replaces 
    Resource --o : isReplacedBy 
    Resource --o : requiredBy 
    Resource --o : requires 
    Resource --o : source 
    Resource --o : inSeries 
    Resource --o : prev 
    Concept --o : hadRole 
    Distribution --o : accessService 
    Resource --o : accessService
```

## Quick Start

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The API will be available at `http://localhost:8000`.

### 2. Frontend
Open `frontend/index.html` in your browser.

## Directory Structure

```
.
├── backend/                # FastAPI application and core logic
│   ├── ontology/           # DCAT-AP extensions (constructDCAT.ttl)
│   ├── shacl/              # SHACL constraints (constructDCAT_shacl.ttl)
│   ├── run.sh              # Conversion pipeline script
│   └── main.py             # API Entrypoint
├── frontend/               # Web Interface
│   ├── index.html
│   ├── style.css
│   └── app.js
└── .github/workflows/      # CI/CD Configuration
```

## Development
This project follows a standard branching model.
- **main**: Stable production code.
- **development**: Active development branch.

### Testing
Run the backend tests or manually verify using the frontend.
Changes to the repo are automatically tested via GitHub Actions.
