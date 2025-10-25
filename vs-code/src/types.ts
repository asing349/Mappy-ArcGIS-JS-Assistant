/**
 * Type definitions for Mappy VS Code Extension
 * These types match the backend API structure in backend/src/api/models.py
 */

/**
 * Request to the /query endpoint
 */
export interface QueryRequest {
    query: string;
    session_id?: string;
    context_focus?: string;
}

/**
 * Source citation from documentation
 */
export interface Source {
    title: string;
    url: string;
    relevance_score: number;
    document_type: string;
    content_preview?: string;
}

/**
 * Response from the /query endpoint
 */
export interface QueryResponse {
    answer: string;
    sources: Source[];
    query_type: string;
    context_focus?: string;
    performance_metrics: {
        search_time?: number;
        generation_time?: number;
        total_time?: number;
        api_processing_time?: number;
    };
    session_id?: string;
    success: boolean;
}

/**
 * Error response from API
 */
export interface ErrorResponse {
    error: string;
    status_code: number;
    timestamp: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
    status: 'healthy' | 'degraded' | 'unhealthy';
    components: Record<string, string>;
    timestamp: number;
}

/**
 * Extension configuration
 */
export interface MappyConfig {
    apiUrl: string;
    enableChat: boolean;
    enableHover: boolean;
    cacheTimeout: number;
    sdkVersion: string;
}

/**
 * Chat message in the UI
 */
export interface ChatMessage {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: number;
    sources?: Source[];
    error?: boolean;
}

/**
 * Cache entry for API responses
 */
export interface CacheEntry<T> {
    data: T;
    timestamp: number;
    expiresAt: number;
}

/**
 * Message types between webview and extension
 */
export type WebviewMessageType = 
    | 'query'
    | 'response'
    | 'error'
    | 'insert-code'
    | 'clear-history'
    | 'open-url';

/**
 * Message sent from webview to extension
 */
export interface WebviewMessage {
    type: WebviewMessageType;
    data: any;
}