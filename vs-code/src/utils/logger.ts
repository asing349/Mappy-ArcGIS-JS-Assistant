/**
 * Simple logging utility for Mappy extension
 */

import * as vscode from 'vscode';

export enum LogLevel {
    DEBUG = 0,
    INFO = 1,
    WARN = 2,
    ERROR = 3
}

class Logger {
    private outputChannel: vscode.OutputChannel;
    private logLevel: LogLevel = LogLevel.INFO;

    constructor() {
        this.outputChannel = vscode.window.createOutputChannel('Mappy Assistant');
    }

    setLogLevel(level: LogLevel) {
        this.logLevel = level;
    }

    private log(level: LogLevel, message: string, ...args: any[]) {
        if (level < this.logLevel) {
            return;
        }

        const timestamp = new Date().toISOString();
        const levelStr = LogLevel[level];
        const formattedMessage = `[${timestamp}] [${levelStr}] ${message}`;
        
        this.outputChannel.appendLine(formattedMessage);
        
        if (args.length > 0) {
            this.outputChannel.appendLine(JSON.stringify(args, null, 2));
        }

        // Also log to console for debugging
        if (level === LogLevel.ERROR) {
            console.error(formattedMessage, ...args);
        } else if (level === LogLevel.WARN) {
            console.warn(formattedMessage, ...args);
        } else {
            console.log(formattedMessage, ...args);
        }
    }

    debug(message: string, ...args: any[]) {
        this.log(LogLevel.DEBUG, message, ...args);
    }

    info(message: string, ...args: any[]) {
        this.log(LogLevel.INFO, message, ...args);
    }

    warn(message: string, ...args: any[]) {
        this.log(LogLevel.WARN, message, ...args);
    }

    error(message: string, ...args: any[]) {
        this.log(LogLevel.ERROR, message, ...args);
    }

    show() {
        this.outputChannel.show();
    }

    dispose() {
        this.outputChannel.dispose();
    }
}

// Singleton instance
export const logger = new Logger();