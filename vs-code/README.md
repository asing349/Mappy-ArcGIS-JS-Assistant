# Mappy - ArcGIS JavaScript SDK Assistant

AI-powered documentation assistant for the ArcGIS JavaScript SDK. Get instant answers, code examples, and documentation directly in VS Code.

## Features

- **💬 Chat Interface**: Ask questions in natural language and get detailed answers
- **📚 Hover Documentation**: Hover over ArcGIS classes to see quick documentation
- **✨ Code Insertion**: Insert code examples directly into your editor with one click
- **🔍 Smart Search**: Semantic search across the entire ArcGIS JavaScript SDK documentation
- **📖 Source Citations**: Every answer includes links to official documentation

## Requirements

- VS Code 1.85.0 or higher
- Mappy backend API running (see setup instructions)

## Setup

### 1. Install the Extension

Install from VS Code Marketplace or manually:
```bash
code --install-extension mappy-arcgis-assistant-0.1.0.vsix
```

### 2. Configure API Endpoint

Open VS Code settings (Cmd+, or Ctrl+,) and search for "Mappy":

- **API URL**: Set to your Mappy backend URL
  - Local development: `http://localhost:8000`
  - Production: Your deployed backend URL

### 3. Start Using Mappy

- Click the Mappy icon in the sidebar
- Or use Command Palette (Cmd+Shift+P): "Mappy: Open Chat"

## Usage

### Chat Interface

1. Open the Mappy sidebar (click icon in activity bar)
2. Type your question in the input box
3. Get instant answers with code examples
4. Click "Insert" to add code to your editor

**Example questions:**
- "How do I create a 3D map?"
- "Add a feature layer with popup"
- "What are the properties of MapView?"

### Hover Documentation

Hover over any ArcGIS class or method in your code to see quick documentation:

```javascript
const map = new Map({  // ← Hover over "Map" to see docs
  basemap: "topo-vector"
});
```

### Commands

Access via Command Palette (Cmd+Shift+P / Ctrl+Shift+P):

- **Mappy: Open Chat** - Open the chat sidebar
- **Mappy: Ask Question** - Quick question input
- **Mappy: Clear Cache** - Clear cached responses

## Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `mappy.apiUrl` | Backend API URL | `http://localhost:8000` |
| `mappy.enableChat` | Enable chat sidebar | `true` |
| `mappy.enableHover` | Enable hover documentation | `true` |
| `mappy.cacheTimeout` | Cache timeout (seconds) | `300` |
| `mappy.sdkVersion` | ArcGIS SDK version | `4.34` |

## Backend Setup

This extension requires the Mappy backend API. See the [Mappy repository](https://github.com/asing349/Mappy-ArcGIS-JS-Assistant) for setup instructions.

Quick start:
```bash
git clone https://github.com/asing349/Mappy-ArcGIS-JS-Assistant
cd Mappy-ArcGIS-JS-Assistant/backend
pip install -r requirements.txt
python src/api/main.py  # Starts on http://localhost:8000
```

## Troubleshooting

### Extension not activating
- Make sure you have a JavaScript/TypeScript file open
- Check the Output panel (View → Output → Mappy Assistant) for errors

### API connection errors
- Verify the backend is running: `curl http://localhost:8000/health`
- Check the API URL in settings
- Look for CORS errors in the backend logs

### No responses in chat
- Check backend logs for errors
- Verify your API key (if authentication is enabled)
- Try clearing the cache: Command Palette → "Mappy: Clear Cache"

## Support

- **Issues**: [GitHub Issues](https://github.com/asing349/Mappy-ArcGIS-JS-Assistant/issues)
- **Documentation**: [Full docs](https://github.com/asing349/Mappy-ArcGIS-JS-Assistant)

## License

MIT

## Credits

Built with ❤️ for the ArcGIS developer community.

---

**Note**: This extension is not affiliated with or endorsed by Esri.