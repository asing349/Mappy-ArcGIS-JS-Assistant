# Mappy - ArcGIS JavaScript SDK Assistant

An AI-powered documentation assistant that helps developers work with the ArcGIS JavaScript SDK through intelligent search and contextual responses.

## What Mappy Does

Mappy transforms the extensive ArcGIS JavaScript SDK documentation into an intelligent, conversational assistant that:

- **Answers technical questions** about API methods, properties, and workflows
- **Provides relevant code examples** from the official documentation
- **Explains complex concepts** with proper context and implementation guidance
- **Searches semantically** - understands what you mean, not just keyword matching
- **Offers interactive help** through a clean web interface

## Features

- **33,179+ processed documentation chunks** covering the entire ArcGIS JS SDK
- **Semantic search** using Vertex AI embeddings for accurate results
- **Real-time responses** powered by Google Gemini for contextual answers
- **Source citations** with direct links to official documentation
- **Modern web interface** built with Next.js and Mantine UI
- **Cloud-hosted vector database** using Qdrant for fast search

## Architecture

```
Frontend (Next.js) → Backend API (FastAPI) → Vector Search (Qdrant Cloud) → AI Models (Vertex AI + Gemini)
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud account with Vertex AI enabled
- Qdrant Cloud account (free tier available)

### Backend Setup

1. **Clone and setup environment:**
```bash
git clone 
cd mappy-arcgis-assistant
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create `backend/.env`:
```env
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# Qdrant Cloud
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# AI Models
GEMINI_API_KEY=your-gemini-api-key
```

4. **Start the API server:**
```bash
python src/api/main.py
# Server runs on http://localhost:8000
```

### Frontend Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure environment:**
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Start development server:**
```bash
npm run dev
# App runs on http://localhost:3000
```

## API Endpoints

### Query Endpoint
```http
POST /query
Content-Type: application/json

{
  "query": "How do I create a 3D map with elevation layers?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "To create a 3D map with elevation layers...",
  "sources": [
    {
      "title": "ElevationLayer",
      "url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-layers-ElevationLayer.html",
      "relevance_score": 0.85,
      "document_type": "api_reference"
    }
  ],
  "query_type": "how_to",
  "response_time": 1.2
}
```

### Health Check
```http
GET /health
```

## How It Works

1. **Document Processing**: ArcGIS JS SDK documentation is parsed into semantic chunks
2. **Vector Embeddings**: Each chunk is converted to 768-dimensional vectors using Vertex AI
3. **Intelligent Search**: User queries are embedded and matched against document vectors
4. **Context Assembly**: Relevant chunks are gathered and ranked by relevance
5. **AI Response**: Google Gemini generates contextual answers with proper citations

## Data Pipeline

The system processes documentation through several stages:

- **Content Extraction**: Parse HTML and extract meaningful content
- **Cleaning**: Remove boilerplate, normalize formatting
- **Chunking**: Split into semantically coherent sections
- **Embedding**: Generate vector representations
- **Storage**: Store in Qdrant Cloud for fast retrieval

## Project Structure

```
mappy-arcgis-assistant/
├── backend/                 # FastAPI server
│   ├── src/
│   │   ├── api/            # API endpoints
│   │   ├── rag/            # RAG pipeline
│   │   ├── simple_search.py # Search service
│   │   └── embedding_service.py # Vector generation
│   └── requirements.txt
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── components/     # UI components
│   │   └── app/           # App router pages
│   └── package.json
├── data/                  # Documentation data
│   ├── processed/         # Cleaned chunks
│   └── embeddings/        # Vector files
└── README.md
```

## Environment Variables

### Backend (.env)
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Service account JSON (as string) | Yes |
| `QDRANT_URL` | Qdrant Cloud cluster URL | Yes |
| `QDRANT_API_KEY` | Qdrant Cloud API key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes |

### Frontend (.env.local)
| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | Yes |

## Deployment

### Backend (Railway)
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically from main branch

### Frontend (Vercel)
1. Connect your GitHub repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` to your Railway backend URL
3. Deploy automatically from main branch

## Performance

- **Search Speed**: 0.3-0.6 seconds per query
- **Accuracy**: 85%+ relevance scores on technical queries
- **Coverage**: 33,179 documentation chunks
- **Uptime**: 99.9% with cloud hosting

## Usage Examples

**Creating Maps:**
```
Query: "How do I create a simple 2D map?"
Result: Step-by-step guide with MapView examples
```

**Working with Layers:**
```
Query: "Add elevation data to 3D scene"
Result: ElevationLayer documentation with code samples
```

**Styling and Symbols:**
```
Query: "Custom marker symbols"
Result: Symbol and renderer API references
```

## System Requirements

- **Memory**: 2GB+ RAM for backend
- **Storage**: 1GB for processed data
- **Network**: Stable internet for cloud services

## Troubleshooting

### Common Issues

**Authentication Errors:**
- Verify Google Cloud service account JSON is properly formatted
- Ensure Vertex AI API is enabled in Google Cloud Console

**Search Not Working:**
- Check Qdrant Cloud connection and API key
- Verify vector embeddings are properly uploaded

**Frontend Connection Issues:**
- Confirm API URL in environment variables
- Check CORS settings if running locally

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python src/api/main.py
```

## Data Stats

- **Total Documentation Pages**: 1,351
- **API Reference Pages**: 930 (68.8%)
- **Sample Code Pages**: 382 (28.3%)
- **Guide Pages**: 39 (2.9%)
- **Processed Chunks**: 33,179
- **Vector Dimensions**: 768
- **Average Chunk Size**: 150 words