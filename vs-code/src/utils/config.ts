/**
 * Configuration manager for Mappy extension
 * Reads settings from VS Code workspace configuration
 */

import * as vscode from 'vscode';
import { MappyConfig } from '../types';
import { logger } from './logger';

export class ConfigManager {
    private static readonly CONFIG_SECTION = 'mappy';

    /**
     * Get current extension configuration
     */
    static getConfig(): MappyConfig {
        const config = vscode.workspace.getConfiguration(this.CONFIG_SECTION);

        return {
            apiUrl: config.get<string>('apiUrl', 'http://localhost:8000'),
            enableChat: config.get<boolean>('enableChat', true),
            enableHover: config.get<boolean>('enableHover', true),
            cacheTimeout: config.get<number>('cacheTimeout', 300),
            sdkVersion: config.get<string>('sdkVersion', '4.34')
        };
    }

    /**
     * Get a specific config value
     */
    static get<T>(key: keyof MappyConfig, defaultValue: T): T {
        const config = vscode.workspace.getConfiguration(this.CONFIG_SECTION);
        return config.get<T>(key, defaultValue);
    }

    /**
     * Update a config value
     */
    static async set(key: keyof MappyConfig, value: any): Promise<void> {
        const config = vscode.workspace.getConfiguration(this.CONFIG_SECTION);
        await config.update(key, value, vscode.ConfigurationTarget.Global);
        logger.info(`Configuration updated: ${key} = ${value}`);
    }

    /**
     * Validate API URL format
     */
    static isValidApiUrl(url: string): boolean {
        try {
            const parsed = new URL(url);
            return parsed.protocol === 'http:' || parsed.protocol === 'https:';
        } catch {
            return false;
        }
    }

    /**
     * Get normalized API URL (remove trailing slash)
     */
    static getNormalizedApiUrl(): string {
        const url = this.get<string>('apiUrl', 'http://localhost:8000');
        return url.endsWith('/') ? url.slice(0, -1) : url;
    }

    /**
     * Listen for configuration changes
     */
    static onConfigChange(callback: () => void): vscode.Disposable {
        return vscode.workspace.onDidChangeConfiguration(event => {
            if (event.affectsConfiguration(this.CONFIG_SECTION)) {
                logger.info('Configuration changed');
                callback();
            }
        });
    }
}