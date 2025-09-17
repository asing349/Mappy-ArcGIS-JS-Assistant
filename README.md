# Mappy - ArcGIS JavaScript SDK Assistant

An AI-powered documentation assistant for ArcGIS JavaScript SDK using Retrieval-Augmented Generation (RAG).

## Project Overview

Mappy processes ArcGIS JavaScript SDK documentation to create an intelligent assistant that can:
- Answer questions about API methods and properties
- Provide relevant code examples
- Explain concepts with proper context
- Guide developers through complex workflows

## Corpus Stats
- **Total Pages**: 1,351
- **API Reference**: 930 pages (68.8%)
- **Guide Pages**: 39 pages (2.9%)
- **Sample Pages**: 382 pages (28.3%)

## Setup Instructions

### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd mappy-arcgis-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys and preferences
nano .env  # or your preferred editor
```

### 3. Data Setup

Place your ArcGIS documentation JSON files in the `data/raw/` directory:
```
data/raw/
├── arcgis_docs_main.json      # Your 67MB file
├── arcgis_docs_additional1.json
└── arcgis_docs_additional2.json
```

### 4. Run Processing Pipeline

```bash
# Process corpus (Module 1-4)
python src/main.py --process-corpus

# Start interactive assistant (after Phase 2)
python src/main.py --interactive
```

## Project Structure

```
mappy-arcgis-assistant/
├── src/                    # Source code
│   ├── corpus_loader.py   # Module 1: Load & validate JSON
│   ├── content_cleaner.py # Module 2: Clean & deduplicate
│   ├── sectionizer.py     # Module 3: Parse document types
│   ├── chunking.py        # Module 4: Intelligent chunking
│   └── main.py           # Main application
├── data/                  # Data storage
│   ├── raw/              # Original JSON files
│   ├── processed/        # Cleaned data
│   └── embeddings/       # Vector database
├── tests/                # Unit tests
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Development Phases

- **Phase 1**: Foundation & Data Pipeline ✅ (Modules 0-4)
- **Phase 2**: Search Infrastructure (Modules 5-9)
- **Phase 3**: Intelligence Layer (Modules 10-13)
- **Phase 4**: API & Core UX (Modules 14-17)
- **Phase 5**: Operations & Scale (Modules 18-22)
- **Phase 6**: Documentation & Handoff (Module 23)

## Current Status

- ✅ Module 0: Repository setup
- 🔄 Module 1: Corpus loader (in progress)
- ⏳ Module 2: Content cleaning
- ⏳ Module 3: Document sectionizing
- ⏳ Module 4: Intelligent chunking

## Contributing

1. Follow the module-by-module development approach
2. Each module must pass criteria before proceeding
3. Maintain comprehensive tests
4. Document all major decisions

## License

[Add your license here]
