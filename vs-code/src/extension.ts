/**
 * Mappy VS Code Extension - Main Entry Point
 * 
 * This file handles:
 * - Extension activation
 * - Command registration
 * - Status bar setup
 * - Provider initialization
 */

import * as vscode from 'vscode';
import { logger, LogLevel } from './utils/logger';
import { ConfigManager } from './utils/config';
import { getAPIClient, resetAPIClient } from './api/MappyAPIClient';
import { ChatPanelProvider } from './webview/ChatPanelProvider';
import { MappyHoverProvider } from './hover/HoverProvider';

// Status bar item
let statusBarItem: vscode.StatusBarItem;
let chatPanelProvider: ChatPanelProvider;
let hoverProvider: MappyHoverProvider;

/**
 * Extension activation
 * Called when user opens a JavaScript/TypeScript/HTML file (see activationEvents in package.json)
 */
export function activate(context: vscode.ExtensionContext) {
    logger.info('🚀 Mappy ArcGIS Assistant is activating...');

    // Check if current file has ArcGIS imports
    const hasArcGISImports = checkForArcGISImports();
    
    if (hasArcGISImports) {
        logger.info('✅ ArcGIS imports detected in workspace');
    }

    // Initialize status bar
    setupStatusBar(context);

    // Register chat panel provider
    chatPanelProvider = new ChatPanelProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            ChatPanelProvider.viewType,
            chatPanelProvider
        )
    );
    logger.info('Chat panel provider registered');

    // Initialize hover provider (but don't register automatic hover - too many API calls!)
    // Instead, we'll use it via context menu command
    hoverProvider = new MappyHoverProvider();
    logger.info('Hover provider initialized (context menu only)');

    // Register commands
    registerCommands(context);

    // Log configuration
    const config = ConfigManager.getConfig();
    logger.info('Configuration loaded:', config);

    // Validate API URL
    if (!ConfigManager.isValidApiUrl(config.apiUrl)) {
        vscode.window.showWarningMessage(
            `Mappy: Invalid API URL "${config.apiUrl}". Please check your settings.`
        );
    }

    // Listen for config changes
    context.subscriptions.push(
        ConfigManager.onConfigChange(() => {
            updateStatusBar();
            
            // Reset API client if URL changed
            const newConfig = ConfigManager.getConfig();
            const apiClient = getAPIClient();
            
            if (apiClient.getBaseURL() !== newConfig.apiUrl) {
                logger.info('API URL changed, resetting client');
                resetAPIClient();
            }
            
            vscode.window.showInformationMessage('Mappy configuration updated');
        })
    );

    // Update status to ready
    updateStatusBar('Ready');

    logger.info('✅ Mappy ArcGIS Assistant activated successfully');
    
    // Show welcome message on first activation
    showWelcomeMessage(context);
}

/**
 * Extension deactivation
 * Cleanup resources
 */
export function deactivate() {
    logger.info('🛑 Mappy ArcGIS Assistant is deactivating...');
    
    if (statusBarItem) {
        statusBarItem.dispose();
    }
    
    logger.dispose();
}

/**
 * Setup status bar indicator
 */
function setupStatusBar(context: vscode.ExtensionContext) {
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    
    statusBarItem.command = 'mappy.openChat';
    statusBarItem.text = '$(comment-discussion) Mappy';
    statusBarItem.tooltip = 'Click to open Mappy chat';
    statusBarItem.show();
    
    context.subscriptions.push(statusBarItem);
}

/**
 * Update status bar with current state
 */
function updateStatusBar(state?: string) {
    if (!statusBarItem) {
        return;
    }

    const config = ConfigManager.getConfig();
    
    if (state === 'Loading') {
        statusBarItem.text = '$(loading~spin) Mappy';
        statusBarItem.tooltip = 'Mappy is processing...';
    } else if (!config.enableChat && !config.enableHover) {
        statusBarItem.text = '$(circle-slash) Mappy';
        statusBarItem.tooltip = 'Mappy is disabled';
    } else {
        statusBarItem.text = '$(comment-discussion) Mappy';
        statusBarItem.tooltip = `Mappy: Ready (SDK ${config.sdkVersion})`;
    }
}

/**
 * Register all commands
 */
function registerCommands(context: vscode.ExtensionContext) {
    // Command: Open Chat
    const openChatCmd = vscode.commands.registerCommand('mappy.openChat', () => {
        logger.info('Command: Open Chat');
        vscode.commands.executeCommand('mappy.chatView.focus');
    });

    // Command: Populate Chat Query (from hover link)
    const populateChatQueryCmd = vscode.commands.registerCommand('mappy.populateChatQuery', (symbol: string) => {
        logger.info(`Command: Populate Chat Query for "${symbol}"`);
        
        // Open the chat panel first
        vscode.commands.executeCommand('mappy.chatView.focus');
        
        // Send message to webview to populate the input (but not send)
        if (chatPanelProvider) {
            const queryText = `Tell me about ${symbol} in ArcGIS JavaScript SDK`;
            chatPanelProvider.sendMessage({ 
                type: 'populate-input',
                data: { text: queryText }
            });
        }
    });

    // Command: Ask About Symbol (right-click context menu)
    const askAboutSymbolCmd = vscode.commands.registerCommand('mappy.askAboutSymbol', async () => {
        logger.info('Command: Ask About Symbol');
        
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        // Get the word under cursor or selection
        const selection = editor.selection;
        const wordRange = editor.document.getWordRangeAtPosition(selection.active);
        
        if (!wordRange) {
            vscode.window.showWarningMessage('No symbol selected. Place cursor on an ArcGIS class name.');
            return;
        }

        const symbol = editor.document.getText(wordRange);
        
        // Check if it looks like an ArcGIS symbol
        if (!/^[A-Z]/.test(symbol)) {
            vscode.window.showWarningMessage(`"${symbol}" doesn't look like an ArcGIS class. Try a capitalized name like "Map" or "MapView".`);
            return;
        }

        logger.info(`Asking about symbol: "${symbol}"`);

        // Open chat and populate with the question
        vscode.commands.executeCommand('mappy.chatView.focus');
        
        if (chatPanelProvider) {
            const queryText = `What is ${symbol} in ArcGIS JavaScript SDK?`;
            chatPanelProvider.sendMessage({ 
                type: 'populate-input',
                data: { text: queryText }
            });
        }
    });

    // Command: Ask Question
    const askQuestionCmd = vscode.commands.registerCommand('mappy.askQuestion', async () => {
        logger.info('Command: Ask Question');
        
        const question = await vscode.window.showInputBox({
            prompt: 'Ask Mappy about ArcGIS JavaScript SDK',
            placeHolder: 'e.g., How do I create a 3D map?'
        });

        if (question) {
            logger.info(`User asked: "${question}"`);
            
            // Show loading state
            showLoading();
            
            try {
                // Get API client and query
                const apiClient = getAPIClient();
                const response = await apiClient.query(question);
                
                // Show ready state
                showReady();
                
                if (response.success) {
                    // Show answer in information message
                    const action = await vscode.window.showInformationMessage(
                        `✅ Answer received! Check Output panel for full response.`,
                        'View Answer',
                        'View Sources'
                    );
                    
                    // Log full response
                    logger.info('=== MAPPY RESPONSE ===');
                    logger.info(`Question: ${question}`);
                    logger.info(`Answer:\n${response.answer}`);
                    logger.info(`Sources: ${response.sources.length}`);
                    response.sources.forEach((source, i) => {
                        logger.info(`  ${i + 1}. ${source.title} (${source.relevance_score.toFixed(2)})`);
                        logger.info(`     ${source.url}`);
                    });
                    logger.info('======================');
                    
                    if (action === 'View Answer') {
                        logger.show();
                    } else if (action === 'View Sources') {
                        // Open first source in browser
                        if (response.sources.length > 0) {
                            vscode.env.openExternal(vscode.Uri.parse(response.sources[0].url));
                        }
                    }
                } else {
                    vscode.window.showErrorMessage(
                        'Failed to get response from Mappy. Check Output panel for details.'
                    );
                    logger.show();
                }
                
            } catch (error) {
                showReady();
                logger.error('Error querying API:', error);
                vscode.window.showErrorMessage(
                    'Error communicating with Mappy API. Check Output panel for details.'
                );
                logger.show();
            }
        }
    });

    // Command: Clear Cache
    const clearCacheCmd = vscode.commands.registerCommand('mappy.clearCache', () => {
        logger.info('Command: Clear Cache');
        const apiClient = getAPIClient();
        const apiStatsBefore = apiClient.getCacheStats();
        apiClient.clearCache();
        
        // Also clear hover cache
        const hoverStatsBefore = hoverProvider.getCacheStats();
        hoverProvider.clearCache();
        
        vscode.window.showInformationMessage(
            `Cache cleared successfully (API: ${apiStatsBefore.size}, Hover: ${hoverStatsBefore.size} entries)`
        );
    });

    // Command: Show Logs (hidden, for debugging)
    const showLogsCmd = vscode.commands.registerCommand('mappy.showLogs', () => {
        logger.show();
    });

    // Command: Test API Connection
    const testConnectionCmd = vscode.commands.registerCommand('mappy.testConnection', async () => {
        logger.info('Command: Test Connection');
        
        const apiClient = getAPIClient();
        const apiUrl = apiClient.getBaseURL();
        
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Testing Mappy API connection...',
            cancellable: false
        }, async () => {
            const isConnected = await apiClient.testConnection();
            
            if (isConnected) {
                vscode.window.showInformationMessage(
                    `✅ Successfully connected to Mappy API at ${apiUrl}`
                );
            } else {
                vscode.window.showErrorMessage(
                    `❌ Cannot connect to Mappy API at ${apiUrl}. Is the backend running?`
                );
            }
        });
    });

    // Command: Reset Chat Panel
    const resetChatCmd = vscode.commands.registerCommand('mappy.resetChat', async () => {
        logger.info('Command: Reset Chat');
        
        const confirmed = await vscode.window.showWarningMessage(
            'Reset chat panel? This will clear all message history.',
            { modal: true },
            'Reset'
        );
        
        if (confirmed === 'Reset') {
            if (chatPanelProvider) {
                chatPanelProvider.sendMessage({ type: 'reset' });
                vscode.window.showInformationMessage('Chat panel reset successfully');
                logger.info('Chat panel reset');
            } else {
                vscode.window.showErrorMessage('Chat panel not available.');
            }
        }
    });

    // Command: Show Hover Cache Stats (hidden, for debugging)
    const hoverStatsCmd = vscode.commands.registerCommand('mappy.hoverStats', () => {
        const stats = hoverProvider.getCacheStats();
        vscode.window.showInformationMessage(
            `Hover Cache: ${stats.size} symbols cached\n${stats.symbols.join(', ')}`
        );
        logger.info('Hover cache stats:', stats);
    });

    // Register all commands for disposal
    context.subscriptions.push(
        openChatCmd,
        populateChatQueryCmd,
        askAboutSymbolCmd,
        askQuestionCmd,
        clearCacheCmd,
        showLogsCmd,
        testConnectionCmd,
        resetChatCmd,
        hoverStatsCmd
    );

    logger.info('✅ Commands registered');
}

/**
 * Check if workspace has ArcGIS imports
 */
function checkForArcGISImports(): boolean {
    const editor = vscode.window.activeTextEditor;
    
    if (!editor) {
        return false;
    }

    const document = editor.document;
    const text = document.getText();

    // Check for common ArcGIS import patterns
    const arcgisPatterns = [
        /@arcgis\/core/,
        /esri\//,
        /require\(["']esri\//,
        /from ["']@arcgis\/core/
    ];

    return arcgisPatterns.some(pattern => pattern.test(text));
}

/**
 * Show welcome message on first activation
 */
function showWelcomeMessage(context: vscode.ExtensionContext) {
    const hasShownWelcome = context.globalState.get<boolean>('mappy.hasShownWelcome', false);
    
    if (!hasShownWelcome) {
        const message = '🗺️ Welcome to Mappy! Your AI assistant for ArcGIS JavaScript SDK is ready.';
        const openSettings = 'Configure';
        const openChat = 'Open Chat';

        vscode.window.showInformationMessage(message, openSettings, openChat).then(selection => {
            if (selection === openSettings) {
                vscode.commands.executeCommand('workbench.action.openSettings', 'mappy');
            } else if (selection === openChat) {
                vscode.commands.executeCommand('mappy.openChat');
            }
        });

        context.globalState.update('mappy.hasShownWelcome', true);
    }
}

/**
 * Helper to show loading state in status bar
 */
export function showLoading() {
    updateStatusBar('Loading');
}

/**
 * Helper to show ready state in status bar
 */
export function showReady() {
    updateStatusBar('Ready');
}