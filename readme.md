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
    %% Styles
    classDef dcat fill:#f9f,stroke:#333,stroke-width:2px;
    class Role
    class Dataset
    class Relationship
    class CatalogRecord
    class Resource
    class Distribution
    class Catalog
    class HealthDataset
    class DataService
    class DatasetSeries
    Dataset <|-- HealthDataset
    Dataset <|-- Catalog
    Dataset <|-- DatasetSeries
    Resource <|-- DataService
    Resource <|-- Dataset
    CatalogRecord ..> CatalogRecord : primaryTopic
    Distribution ..> DataService : accessService
    Distribution ..> Resource : accessURL
    Distribution ..> Resource : downloadURL
    Relationship ..> Resource : relation
    Resource ..> DataService : accessService
    Resource ..> Resource : langingPage
    Resource ..> Relationship : qualifiedRelation
    Resource ..> Resource : relation
    Resource ..> Relationship : qualifiedAttribution
    Resource ..> Resource : hasPart
    Resource ..> Resource : isPartOf
    Resource ..> Resource : isReferencedBy
    Resource ..> Resource : version
    Resource ..> Resource : hasVersion
    Resource ..> Resource : hasCurrentVersion
    Resource ..> Resource : previousVersion
    Resource ..> Resource : replaces
    Resource ..> Resource : isReplacedBy
    Resource ..> Resource : requiredBy
    Resource ..> Resource : requires
    Resource ..> Resource : source
    Resource ..> DatasetSeries : inSeries
    Resource ..> DatasetSeries : prev
    Catalog ..> Catalog : catalog
    Catalog ..> Dataset : dataset
    Catalog ..> DataService : service
    Catalog ..> Resource : hasPart
    Catalog ..> CatalogRecord : record
    DataService ..> Dataset : servesDataset
    DataService ..> Resource : endpointURL
    DataService ..> Resource : endpointDescription
    Dataset ..> Distribution : distribution
    Dataset ..> DatasetSeries : inSeries
    Dataset ..> Dataset : prev
    Dataset ..> Dataset : hasVersion
    Dataset ..> Dataset : hasCurrentVersion
    Dataset ..> Dataset : previousVersion
    Dataset ..> Dataset : version
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
