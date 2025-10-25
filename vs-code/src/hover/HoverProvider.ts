/**
 * Mappy Hover Documentation Provider
 * 
 * Provides inline documentation when hovering over ArcGIS JavaScript SDK symbols.
 * Features:
 * - Smart symbol detection (classes, methods, properties)
 * - Aggressive caching (<10ms on second hover)
 * - Optimized queries for quick responses
 * - Clickable links to chat and docs
 */

import * as vscode from 'vscode';
import { getAPIClient } from '../api/MappyAPIClient';
import { logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { QueryResponse } from '../types';

/**
 * Cache for hover responses
 * Key: symbol name (e.g., "MapView", "FeatureLayer")
 * Value: { markdown: string, timestamp: number }
 */
interface HoverCacheEntry {
    markdown: vscode.MarkdownString;
    timestamp: number;
}

export class MappyHoverProvider implements vscode.HoverProvider {
    private cache: Map<string, HoverCacheEntry> = new Map();
    private readonly CACHE_TTL = 3600000; // 1 hour (hover docs don't change often)
    private pendingRequests: Map<string, Promise<vscode.Hover | null>> = new Map();

    // Common ArcGIS JavaScript SDK symbols
    private readonly KNOWN_SYMBOLS = new Set([
        // Core classes
        'Map', 'MapView', 'SceneView', 'WebMap', 'WebScene',
        
        // Layers
        'FeatureLayer', 'GraphicsLayer', 'TileLayer', 'MapImageLayer',
        'VectorTileLayer', 'ImageryLayer', 'ElevationLayer', 'GeoJSONLayer',
        'CSVLayer', 'StreamLayer', 'IntegratedMeshLayer', 'PointCloudLayer',
        'SceneLayer', 'BuildingSceneLayer', 'WMSLayer', 'WMTSLayer',
        'KMLLayer', 'GroupLayer', 'BaseTileLayer', 'BaseElevationLayer',
        
        // Geometry
        'Point', 'Polyline', 'Polygon', 'Multipoint', 'Extent', 'Circle',
        'Mesh', 'SpatialReference', 'GeometryEngine', 'Geometry',
        
        // Symbols
        'SimpleMarkerSymbol', 'SimpleLineSymbol', 'SimpleFillSymbol',
        'PictureMarkerSymbol', 'TextSymbol', 'PointSymbol3D', 'LineSymbol3D',
        'PolygonSymbol3D', 'MeshSymbol3D', 'WebStyleSymbol',
        
        // Renderers
        'SimpleRenderer', 'UniqueValueRenderer', 'ClassBreaksRenderer',
        'DotDensityRenderer', 'HeatmapRenderer',
        
        // Widgets
        'Popup', 'Search', 'Locate', 'Track', 'Compass', 'Home', 'Legend',
        'LayerList', 'BasemapGallery', 'Expand', 'ScaleBar', 'Attribution',
        'Sketch', 'Editor', 'TimeSlider', 'Bookmarks', 'Print',
        
        // Tasks
        'Query', 'QueryTask', 'Geoprocessor', 'RouteTask', 'Locator',
        'GeometryService', 'PrintTask', 'FindTask', 'IdentifyTask',
        
        // Graphic
        'Graphic', 'GraphicCollection',
        
        // Popups
        'PopupTemplate', 'FieldInfo', 'ActionButton',
        
        // Other
        'Portal', 'PortalItem', 'Basemap', 'Ground', 'Camera', 'Viewpoint',
        'Collection', 'Accessor', 'request', 'urlUtils', 'config',
        'esriRequest', 'watchUtils', 'promiseUtils'
    ]);

    constructor() {
        logger.info('HoverProvider initialized (manual mode - no preloading)');
        
        // Preloading disabled to avoid excessive API calls
        // User triggers docs via right-click context menu instead
    }

    /**
     * VS Code calls this when user hovers over text
     */
    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        // Check if hover is enabled
        const config = ConfigManager.getConfig();
        if (!config.enableHover) {
            return null;
        }

        // Check if this is a supported file type
        if (!this.isSupportedLanguage(document.languageId)) {
            return null;
        }

        // Get the word under cursor
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return null;
        }

        const word = document.getText(wordRange);
        
        // Check if this looks like an ArcGIS symbol
        if (!this.isArcGISSymbol(word, document, position)) {
            return null;
        }

        logger.debug(`Hover detected on: "${word}"`);

        // Check cache first (super fast!)
        const cached = this.getCachedHover(word);
        if (cached) {
            logger.debug(`Returning cached hover for "${word}" (<10ms)`);
            return new vscode.Hover(cached, wordRange);
        }

        // Prevent duplicate requests for same symbol
        const pendingRequest = this.pendingRequests.get(word);
        if (pendingRequest) {
            logger.debug(`Reusing pending request for "${word}"`);
            return pendingRequest;
        }

        // Query API for documentation
        const hoverPromise = this.queryHoverDocs(word, wordRange, token);
        this.pendingRequests.set(word, hoverPromise);

        try {
            const hover = await hoverPromise;
            return hover;
        } finally {
            this.pendingRequests.delete(word);
        }
    }

    /**
     * Check if language is supported for hover
     */
    private isSupportedLanguage(languageId: string): boolean {
        return ['javascript', 'typescript', 'javascriptreact', 'typescriptreact', 'html'].includes(languageId);
    }

    /**
     * Check if word is likely an ArcGIS symbol
     */
    private isArcGISSymbol(word: string, document: vscode.TextDocument, position: vscode.Position): boolean {
        // Must start with capital letter (most ArcGIS classes do)
        if (!/^[A-Z]/.test(word)) {
            return false;
        }

        // Known symbol?
        if (this.KNOWN_SYMBOLS.has(word)) {
            return true;
        }

        // Check if file has ArcGIS imports
        const text = document.getText();
        const hasArcGISImports = /@arcgis\/core/.test(text) || /esri\//.test(text);
        
        if (!hasArcGISImports) {
            return false;
        }

        // Check if word appears in an import statement
        const importPattern = new RegExp(`import\\s+.*\\b${word}\\b.*from\\s+["']@arcgis\\/core`, 'i');
        const requirePattern = new RegExp(`\\b${word}\\b.*["']esri\\/`, 'i');
        
        if (importPattern.test(text) || requirePattern.test(text)) {
            return true;
        }

        // Check if preceded by 'new' keyword (likely a class instantiation)
        const line = document.lineAt(position.line).text;
        const wordIndex = line.indexOf(word);
        if (wordIndex > 0) {
            const precedingText = line.substring(0, wordIndex).trim();
            if (precedingText.endsWith('new')) {
                return true;
            }
        }

        // If it looks like a class name (PascalCase) and file has ArcGIS imports, give it a chance
        if (/^[A-Z][a-z]+([A-Z][a-z]+)+/.test(word) && hasArcGISImports) {
            return true;
        }

        return false;
    }

    /**
     * Get cached hover documentation
     */
    private getCachedHover(symbol: string): vscode.MarkdownString | null {
        const cached = this.cache.get(symbol);
        
        if (!cached) {
            return null;
        }

        // Check if cache expired
        const age = Date.now() - cached.timestamp;
        if (age > this.CACHE_TTL) {
            this.cache.delete(symbol);
            return null;
        }

        return cached.markdown;
    }

    /**
     * Query API for hover documentation
     */
    private async queryHoverDocs(
        symbol: string,
        wordRange: vscode.Range,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        const startTime = Date.now();

        try {
            // Optimize query for quick response
            const query = `What is ${symbol} in ArcGIS JavaScript SDK? Give a brief description with key properties and methods.`;
            
            logger.debug(`Querying hover docs for "${symbol}"`);

            const apiClient = getAPIClient();
            const response = await apiClient.query(query);

            // Check if request was cancelled
            if (token.isCancellationRequested) {
                logger.debug(`Hover request cancelled for "${symbol}"`);
                return null;
            }

            const elapsed = Date.now() - startTime;
            logger.debug(`Hover query completed in ${elapsed}ms for "${symbol}"`);

            // Format response as hover markdown
            const markdown = this.formatHoverMarkdown(symbol, response);

            // Cache the result
            this.cache.set(symbol, {
                markdown,
                timestamp: Date.now()
            });

            return new vscode.Hover(markdown, wordRange);

        } catch (error) {
            logger.error(`Error fetching hover docs for "${symbol}":`, error);
            
            // Return basic fallback hover
            const fallbackMarkdown = new vscode.MarkdownString();
            fallbackMarkdown.isTrusted = true;
            fallbackMarkdown.supportHtml = true;
            fallbackMarkdown.appendMarkdown(`**${symbol}**\n\n`);
            fallbackMarkdown.appendMarkdown(`*ArcGIS JavaScript SDK symbol*\n\n`);
            fallbackMarkdown.appendMarkdown(`[View in Chat](command:mappy.openChat) · [Search Docs](https://developers.arcgis.com/javascript/latest/api-reference/)`);
            
            return new vscode.Hover(fallbackMarkdown, wordRange);
        }
    }

    /**
     * Format API response as hover markdown
     */
    private formatHoverMarkdown(symbol: string, response: QueryResponse): vscode.MarkdownString {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;
        markdown.supportHtml = true;

        // Header with symbol name
        markdown.appendMarkdown(`### 🗺️ ${symbol}\n\n`);

        // Extract and format the answer
        let answer = response.answer;

        // Truncate if too long (hover should be concise)
        if (answer.length > 600) {
            const sentences = answer.split(/[.!?]+/);
            let truncated = '';
            for (const sentence of sentences) {
                if ((truncated + sentence).length > 550) {
                    break;
                }
                truncated += sentence + '. ';
            }
            answer = truncated.trim() + '...';
        }

        // Remove markdown headers (they look weird in hover)
        answer = answer.replace(/^#+\s+/gm, '**') + '**';
        answer = answer.replace(/\*\*\*\*/g, '**'); // Fix double bold

        markdown.appendMarkdown(answer);
        markdown.appendMarkdown('\n\n---\n\n');

        // Links section
        markdown.appendMarkdown('**Quick Actions:**\n\n');
        
        // "View in Chat" command link - encode the symbol in the command URI
        const encodedSymbol = encodeURIComponent(symbol);
        const chatCommand = `command:mappy.populateChatQuery?${encodedSymbol}`;
        markdown.appendMarkdown(`[💬 Ask in Chat](${chatCommand})`);
        
        markdown.appendMarkdown(' · ');

        // Link to first source (if available)
        if (response.sources && response.sources.length > 0) {
            const source = response.sources[0];
            markdown.appendMarkdown(`[📖 View Docs](${source.url})`);
        } else {
            // Fallback to search
            const searchUrl = `https://developers.arcgis.com/javascript/latest/api-reference/esri-${symbol}.html`;
            markdown.appendMarkdown(`[📖 Search Docs](${searchUrl})`);
        }

        return markdown;
    }

    /**
     * Preload documentation for common symbols in background
     * This makes first hovers much faster!
     */
    private async preloadCommonSymbols(): Promise<void> {
        // Wait 2 seconds after activation before preloading
        await new Promise(resolve => setTimeout(resolve, 2000));

        const config = ConfigManager.getConfig();
        if (!config.enableHover) {
            return;
        }

        logger.info('Preloading common ArcGIS symbols...');

        // Top 10 most commonly used classes
        const commonSymbols = [
            'Map',
            'MapView',
            'SceneView',
            'FeatureLayer',
            'GraphicsLayer',
            'Graphic',
            'Point',
            'Polyline',
            'Polygon',
            'Popup'
        ];

        for (const symbol of commonSymbols) {
            // Don't preload if already cached
            if (this.cache.has(symbol)) {
                continue;
            }

            try {
                const query = `What is ${symbol} in ArcGIS JavaScript SDK? Give a brief description with key properties and methods.`;
                const apiClient = getAPIClient();
                const response = await apiClient.query(query);

                const markdown = this.formatHoverMarkdown(symbol, response);
                this.cache.set(symbol, {
                    markdown,
                    timestamp: Date.now()
                });

                logger.debug(`Preloaded: ${symbol}`);

                // Small delay between preloads to not overwhelm API
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (error) {
                logger.debug(`Failed to preload ${symbol}:`, error);
            }
        }

        logger.info(`✅ Preloaded ${commonSymbols.length} common symbols`);
    }

    /**
     * Clear the hover cache
     */
    public clearCache(): void {
        this.cache.clear();
        logger.info('Hover cache cleared');
    }

    /**
     * Get cache statistics
     */
    public getCacheStats() {
        return {
            size: this.cache.size,
            symbols: Array.from(this.cache.keys())
        };
    }
}