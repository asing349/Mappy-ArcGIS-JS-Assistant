# Change Log

All notable changes to the "Mappy - ArcGIS JavaScript SDK Assistant" extension will be documented in this file.

## [0.2.0] - 2024-10-25

### Added
- **Module 2: API Client** - Complete backend integration
  - HTTP client using Axios for API communication
  - Response caching with configurable TTL (default 5 minutes)
  - Comprehensive error handling (network errors, timeouts, rate limits)
  - Session ID tracking for analytics
  - Health check endpoint integration
  - API connection testing command
- Functional "Ask Question" command with real API responses
- Working cache clearing command
- Automatic API client reset on configuration changes
- User-friendly error messages for common issues

### Changed
- Commands now fully functional with backend integration
- Status bar shows loading state during API calls
- Configuration changes trigger API client updates

## [0.1.0] - 2024-10-24

### Added
- Initial release
- Extension core and activation logic
- Configuration settings for API URL and features
- Status bar indicator
- Basic command palette commands
- TypeScript type definitions matching backend API
- Logging utility
- Configuration manager

### Planned for Next Release (0.3.0)
- Module 3: Chat sidebar interface
- Module 4: Code insertion functionality
- Module 5: Hover documentation provider

## [Unreleased]

### In Development
- Module 2: API Client
- Module 3: Chat Interface
- Module 4: Code Insertion
- Module 5: Hover Provider
- Module 6: Packaging & Distribution