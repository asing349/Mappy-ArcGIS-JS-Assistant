/**
 * Mappy API Client
 * Handles all communication with the backend API
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { QueryRequest, QueryResponse, ErrorResponse, HealthResponse } from '../types';
import { logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';
import { ResponseCache } from './ResponseCache';

export class MappyAPIClient {
    private client: AxiosInstance;
    private cache: ResponseCache<QueryResponse>;
    private sessionId: string;

    constructor(baseURL?: string) {
        const apiUrl = baseURL || ConfigManager.getNormalizedApiUrl();
        
        this.client = axios.create({
            baseURL: apiUrl,
            timeout: 30000, // 30 second timeout
            headers: {
                'Content-Type': 'application/json'
            }
        });

        this.cache = new ResponseCache<QueryResponse>();
        this.sessionId = this.generateSessionId();

        logger.info(`API Client initialized: ${apiUrl}`);
    }

    /**
     * Generate unique session ID for this VS Code session
     */
    private generateSessionId(): string {
        return `vscode-${Date.now()}-${Math.random().toString(36).substring(7)}`;
    }

    /**
     * Query the Mappy API
     */
    async query(queryText: string, contextFocus?: string): Promise<QueryResponse> {
        // Check cache first
        const cached = this.cache.getCached(queryText, contextFocus);
        if (cached) {
            logger.info('Returning cached response');
            return cached;
        }

        const startTime = Date.now();
        
        try {
            logger.info(`Querying API: "${queryText}"`);

            const request: QueryRequest = {
                query: queryText,
                session_id: this.sessionId,
                context_focus: contextFocus
            };

            const response = await this.client.post<QueryResponse>('/query', request);
            const data = response.data;

            // Validate response
            if (!data.success) {
                throw new Error('API returned unsuccessful response');
            }

            const elapsed = Date.now() - startTime;
            logger.info(`Query successful (${elapsed}ms)`);

            // Cache the response
            this.cache.setCached(data, queryText, contextFocus);

            return data;

        } catch (error) {
            return this.handleError(error, queryText);
        }
    }

    /**
     * Check API health
     */
    async checkHealth(): Promise<HealthResponse> {
        try {
            logger.debug('Checking API health...');
            const response = await this.client.get<HealthResponse>('/health');
            return response.data;
        } catch (error) {
            logger.error('Health check failed', error);
            return {
                status: 'unhealthy',
                components: {
                    error: error instanceof Error ? error.message : 'Unknown error'
                },
                timestamp: Date.now()
            };
        }
    }

    /**
     * Test API connectivity
     */
    async testConnection(): Promise<boolean> {
        try {
            const health = await this.checkHealth();
            return health.status === 'healthy' || health.status === 'degraded';
        } catch {
            return false;
        }
    }

    /**
     * Handle API errors with user-friendly messages
     */
    private handleError(error: unknown, query: string): QueryResponse {
        let errorMessage = 'An unexpected error occurred';
        let statusCode = 500;

        if (axios.isAxiosError(error)) {
            const axiosError = error as AxiosError<ErrorResponse>;

            if (axiosError.response) {
                // Server responded with error
                statusCode = axiosError.response.status;
                errorMessage = axiosError.response.data?.error || axiosError.message;

                if (statusCode === 429) {
                    errorMessage = 'Rate limit exceeded. Please wait a moment and try again.';
                } else if (statusCode === 400) {
                    errorMessage = 'Invalid query. Please try rephrasing your question.';
                } else if (statusCode === 500) {
                    errorMessage = 'The API encountered an error. Please try again.';
                }
            } else if (axiosError.request) {
                // Request made but no response
                if (axiosError.code === 'ECONNREFUSED') {
                    errorMessage = 'Cannot connect to Mappy API. Is the backend running?';
                } else if (axiosError.code === 'ETIMEDOUT') {
                    errorMessage = 'Request timed out. The API might be slow or unavailable.';
                } else {
                    errorMessage = 'Network error. Please check your connection.';
                }
            } else {
                // Error setting up request
                errorMessage = axiosError.message;
            }
        } else if (error instanceof Error) {
            errorMessage = error.message;
        }

        logger.error(`API Error (${statusCode}): ${errorMessage}`, error);

        // Return error response in QueryResponse format
        return {
            answer: `❌ **Error**: ${errorMessage}\n\nPlease check:\n- Is the Mappy backend running at \`${ConfigManager.getNormalizedApiUrl()}\`?\n- Check the Output panel (View → Output → Mappy Assistant) for details.`,
            sources: [],
            query_type: 'error',
            performance_metrics: {
                total_time: 0
            },
            session_id: this.sessionId,
            success: false
        };
    }

    /**
     * Clear the response cache
     */
    clearCache(): void {
        this.cache.clear();
        logger.info('API cache cleared');
    }

    /**
     * Get cache statistics
     */
    getCacheStats() {
        return this.cache.getStats();
    }

    /**
     * Update API base URL
     */
    updateBaseURL(newURL: string): void {
        const normalized = newURL.endsWith('/') ? newURL.slice(0, -1) : newURL;
        this.client.defaults.baseURL = normalized;
        this.clearCache(); // Clear cache on URL change
        logger.info(`API URL updated: ${normalized}`);
    }

    /**
     * Get current API URL
     */
    getBaseURL(): string {
        return this.client.defaults.baseURL || '';
    }
}

// Singleton instance
let apiClientInstance: MappyAPIClient | null = null;

/**
 * Get or create API client singleton
 */
export function getAPIClient(): MappyAPIClient {
    if (!apiClientInstance) {
        apiClientInstance = new MappyAPIClient();
    }
    return apiClientInstance;
}

/**
 * Reset API client (useful for testing or config changes)
 */
export function resetAPIClient(): void {
    apiClientInstance = null;
}