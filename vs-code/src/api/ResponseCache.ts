/**
 * Response cache for API calls
 * Reduces duplicate requests and improves performance
 */

import { CacheEntry } from '../types';
import { logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';

export class ResponseCache<T> {
    private cache: Map<string, CacheEntry<T>> = new Map();
    private defaultTTL: number = 300; // 5 minutes in seconds

    constructor(ttl?: number) {
        if (ttl) {
            this.defaultTTL = ttl;
        }
    }

    /**
     * Generate cache key from query parameters
     */
    private generateKey(...params: any[]): string {
        return JSON.stringify(params);
    }

    /**
     * Get item from cache if not expired
     */
    get(key: string): T | null {
        const entry = this.cache.get(key);

        if (!entry) {
            logger.debug(`Cache miss: ${key}`);
            return null;
        }

        // Check if expired
        const now = Date.now();
        if (now > entry.expiresAt) {
            logger.debug(`Cache expired: ${key}`);
            this.cache.delete(key);
            return null;
        }

        logger.debug(`Cache hit: ${key}`);
        return entry.data;
    }

    /**
     * Store item in cache with TTL
     */
    set(key: string, data: T, ttl?: number): void {
        const effectiveTTL = ttl || this.defaultTTL;
        const now = Date.now();

        const entry: CacheEntry<T> = {
            data,
            timestamp: now,
            expiresAt: now + (effectiveTTL * 1000)
        };

        this.cache.set(key, entry);
        logger.debug(`Cache set: ${key} (TTL: ${effectiveTTL}s)`);
    }

    /**
     * Get with automatic key generation from params
     */
    getCached(...params: any[]): T | null {
        const key = this.generateKey(params);
        return this.get(key);
    }

    /**
     * Set with automatic key generation from params
     */
    setCached(data: T, ...params: any[]): void {
        const key = this.generateKey(params);
        const ttl = ConfigManager.get('cacheTimeout', 300);
        this.set(key, data, ttl);
    }

    /**
     * Clear entire cache
     */
    clear(): void {
        const size = this.cache.size;
        this.cache.clear();
        logger.info(`Cache cleared (${size} entries removed)`);
    }

    /**
     * Remove expired entries
     */
    cleanup(): void {
        const now = Date.now();
        let removed = 0;

        for (const [key, entry] of this.cache.entries()) {
            if (now > entry.expiresAt) {
                this.cache.delete(key);
                removed++;
            }
        }

        if (removed > 0) {
            logger.debug(`Cache cleanup: ${removed} expired entries removed`);
        }
    }

    /**
     * Get cache statistics
     */
    getStats(): { size: number; keys: string[] } {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }

    /**
     * Check if key exists and is not expired
     */
    has(key: string): boolean {
        return this.get(key) !== null;
    }
}