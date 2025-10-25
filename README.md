# 🗺️ Mappy - ArcGIS JavaScript SDK Assistant

An AI-powered documentation assistant that helps developers work with the ArcGIS JavaScript SDK through intelligent search, conversational responses, and seamless IDE integration.

**SDK Version:** 4.34 (Latest)

### Documentation owned by Esri
Link: [ArcGIS Maps SDK for JavaScript](https://developers.arcgis.com/javascript/latest/)

---

## 🚀 Available On

### 🔌 VS Code Extension
**NEW!** Get AI-powered ArcGIS help directly in your editor.

[![VS Code Marketplace](https://img.shields.io/badge/VS%20Code-Marketplace-blue)](https://marketplace.visualstudio.com/items?itemName=ajitsingh.mappy-js-sdk)
[![Version](https://img.shields.io/badge/version-0.4.0-green)](https://marketplace.visualstudio.com/items?itemName=ajitsingh.mappy-js-sdk)

**Install:**
```bash
code --install-extension ajitsingh.mappy-js-sdk
```

**Or:** Search "Mappy" in VS Code Extensions

**Features:**
- 💬 AI chat sidebar with persistent history
- 🎯 Right-click context menu: "Ask Mappy About This"
- 📝 Code examples with copy & insert buttons
- 📚 Source citations with relevance scores
- ⚡ Response caching for speed
- 🎨 Automatic VS Code theme integration

### 🌐 Web Application
Interactive chat interface for ArcGIS JavaScript SDK documentation.

**Live at:** [mappy-js-sdk.vercel.app](https://mappy-js-sdk.vercel.app)

**Features:**
- Real-time AI responses
- Code syntax highlighting
- Source citations with direct links
- Clean, modern Mantine UI

### 🔧 Backend API
Production-ready FastAPI server with RAG system.

**Hosted on:** Railway
**Endpoint:** `https://mappy-arcgis-js-assistant-production.up.railway.app`

---

## What Mappy Does

Mappy transforms the extensive ArcGIS JavaScript SDK 4.34 documentation into an intelligent, multi-platform assistant that:

- **Answers technical questions** about API methods, properties, and workflows
- **Provides relevant code examples** from the official documentation
- **Explains complex concepts** with proper context and implementation guidance
- **Searches semantically** - understands what you mean, not just keyword matching
- **Integrates with your workflow** - VS Code extension, web app, or API
- **Offers interactive help** through multiple interfaces

---

## 📸 Screenshots

### VS Code Extension
![VS Code Chat Interface](vs-code/media/chat-screenshot.png)

### Right-Click Context Menu
![Right-Click Menu](vs-code/media/right-click-menu.png)

### Code Examples
![Code Examples](vs-code/media/code-example.png)

---

## Features

### 🤖 AI-Powered RAG System
- **34,325+ processed documentation chunks** covering the entire ArcGIS JS SDK 4.34
- **Semantic search** using Vertex AI embeddings for accurate results
- **Real-time responses** powered by Google Gemini with proper context
- **Source citations** with direct links to official documentation
- **Session tracking** for analytics and personalization

### 🔌 VS Code Extension
- **Chat sidebar** with full conversation history
- **Right-click menu** on any ArcGIS class name
- **Code insertion** with one click
- **Response caching** (5-minute TTL)
- **Auto-updates** from marketplace
- **Zero configuration** - works out of the box

### 🌐 Web Interface
- **Modern UI** built with Next.js 14 and Mantine
- **Responsive design** for desktop and mobile
- **Syntax highlighting** for code examples
- **Direct API integration** with Railway backend

### ⚡ Performance
- **Search speed:** 0.3-0.6 seconds per query
- **Accuracy:** 85%+ relevance scores on technical queries
- **Uptime:** 99.9% with cloud hosting (Railway + Qdrant Cloud)
- **Scalability:** Cloud infrastructure handles concurrent users

---

## Quick Start

### 🔌 Install VS Code Extension (Easiest)

```bash
code --install-extension ajitsingh.mappy-js-sdk
```

**Usage:**
1. Open any JavaScript/TypeScript file
2. Click Mappy icon in Activity Bar
3. Ask questions in the chat
4. Or right-click on `MapView`, `FeatureLayer`, etc. → "Ask Mappy About This"

---

### 🌐 Use Web App

Visit: [mappy-js-sdk.vercel.app](https://mappy-js-sdk.vercel.app)

No installation required!

---

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: Mantine UI
- **Styling**: CSS Modules
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI (Python)
- **Vector DB**: Qdrant Cloud
- **AI Models**: 
  - Google Vertex AI (embeddings)
  - Google Gemini (generation)
- **Deployment**: Railway

### VS Code Extension
- **Language**: TypeScript
- **Framework**: VS Code Extension API
- **HTTP Client**: Axios
- **Build Tool**: TypeScript Compiler
- **Distribution**: VS Code Marketplace

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Links

- **VS Code Extension**: [Marketplace](https://marketplace.visualstudio.com/items?itemName=ajitsingh.mappy-js-sdk)
- **Web App**: [mappy-js-sdk.vercel.app](https://mappy-js-sdk.vercel.app)
- **GitHub**: [Mappy-ArcGIS-JS-Assistant](https://github.com/asing349/Mappy-ArcGIS-JS-Assistant)
- **Report Issues**: [GitHub Issues](https://github.com/asing349/Mappy-ArcGIS-JS-Assistant/issues)

---

**Made for the ArcGIS developer community**

*Happy mapping!* 🗺️✨