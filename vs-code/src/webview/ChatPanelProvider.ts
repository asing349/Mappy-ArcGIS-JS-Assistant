/**
 * Chat Panel Provider
 * Manages the webview panel for the chat interface
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { getAPIClient } from '../api/MappyAPIClient';
import { logger } from '../utils/logger';
import { WebviewMessage, ChatMessage, QueryResponse } from '../types';

export class ChatPanelProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'mappy.chatView';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'ui'),
                vscode.Uri.joinPath(this._extensionUri, 'media')
            ]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async (message: WebviewMessage) => {
            await this._handleMessage(message);
        });

        logger.info('Chat panel initialized');
    }

    /**
     * Handle messages from webview
     */
    private async _handleMessage(message: WebviewMessage) {
        switch (message.type) {
            case 'query':
                await this._handleQuery(message.data.text);
                break;

            case 'insert-code':
                await this._handleInsertCode(message.data.code);
                break;

            case 'open-url':
                await this._handleOpenUrl(message.data.url);
                break;

            case 'clear-history':
                logger.info('Chat history cleared by user');
                // You could add additional cleanup here if needed
                break;

            case 'reset-from-webview':
                if (this._view) {
                    this._view.webview.postMessage({ type: 'reset' });
                }
                break;

            default:
                logger.warn('Unknown message type:', message.type);
        }
    }

    /**
     * Handle user query
     */
    private async _handleQuery(queryText: string) {
        if (!this._view) {
            return;
        }

        logger.info(`Processing query from chat: "${queryText}"`);

        // Show loading state
        this._view.webview.postMessage({
            type: 'loading',
            data: { isLoading: true }
        });

        try {
            // Query the API
            const apiClient = getAPIClient();
            const response: QueryResponse = await apiClient.query(queryText);

            // Send response back to webview
            if (response.success) {
                this._view.webview.postMessage({
                    type: 'response',
                    data: {
                        answer: response.answer,
                        sources: response.sources,
                        success: true
                    }
                });

                logger.info(`Query successful (${response.sources.length} sources)`);
            } else {
                // Error response
                this._view.webview.postMessage({
                    type: 'error',
                    data: {
                        error: response.answer,
                        success: false
                    }
                });

                logger.error('Query failed:', response.answer);
            }

        } catch (error) {
            // Handle unexpected errors
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            
            this._view.webview.postMessage({
                type: 'error',
                data: {
                    error: `Failed to process query: ${errorMessage}`,
                    success: false
                }
            });

            logger.error('Error processing query:', error);
        } finally {
            // Hide loading state
            this._view.webview.postMessage({
                type: 'loading',
                data: { isLoading: false }
            });
        }
    }

    /**
     * Handle code insertion into editor
     */
    private async _handleInsertCode(code: string) {
        const editor = vscode.window.activeTextEditor;

        if (!editor) {
            vscode.window.showWarningMessage('No active editor to insert code');
            return;
        }

        const position = editor.selection.active;
        
        await editor.edit(editBuilder => {
            editBuilder.insert(position, code);
        });

        vscode.window.showInformationMessage('Code inserted successfully');
        logger.info('Code inserted into editor');
    }

    /**
     * Handle opening URL in browser
     */
    private async _handleOpenUrl(url: string) {
        await vscode.env.openExternal(vscode.Uri.parse(url));
        logger.info(`Opened URL: ${url}`);
    }

    /**
     * Get HTML content for webview
     */
    private _getHtmlForWebview(webview: vscode.Webview): string {
        // Get URIs for scripts and styles
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'ui', 'chat.js')
        );
        const styleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'src', 'webview', 'ui', 'chat.css')
        );

        // Get URI for the icon
        const iconUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'media', 'icon.png')
        );

        // Get nonce for CSP
        const nonce = this._getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; img-src ${webview.cspSource};">
    <link href="${styleUri}" rel="stylesheet">
    <title>Mappy Chat</title>
</head>
<body>
    <div id="chat-container">
        <!-- Header -->
        <div id="chat-header">
            <div style="flex: 1; display: flex; align-items: center;">
                <img src="${iconUri}" width="24" height="24" style="margin-right: 8px;" />
                <div>
                    <h2 style="margin: 0; font-size: 16px;">Mappy Assistant</h2>
                    <p id="sdk-version" style="margin: 0; font-size: 11px; color: var(--vscode-descriptionForeground);">ArcGIS JS SDK 4.34</p>
                </div>
            </div>
            <p id="reset-instruction" style="font-size: 11px; color: var(--vscode-descriptionForeground); text-align: right;">
                To reset chat, run<br>
                "Mappy: Reset Chat Panel"<br>
                from the Command Palette.
            </p>
        </div>

        <!-- Messages Area -->
        <div id="messages-container">
            <div id="messages"></div>
        </div>

        <!-- Loading Indicator -->
        <div id="loading-indicator" style="display: none;">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <p>Mappy is thinking...</p>
        </div>

        <!-- Input Area -->
        <div id="input-container">
            <textarea 
                id="user-input" 
                placeholder="Ask about ArcGIS JavaScript SDK..."
                rows="2"
            ></textarea>
            <button id="send-button" title="Send message">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 3l16 7-16 7V3zm2 11.5l9.5-4.5L4 5.5v9z"/>
                </svg>
            </button>
        </div>
    </div>

    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }

    /**
     * Generate nonce for CSP
     */
    private _getNonce(): string {
        let text = '';
        const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        for (let i = 0; i < 32; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }

    /**
     * Send a message to the webview
     */
    public sendMessage(message: any) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }
}