# Change Log

All notable changes to the "Mappy - ArcGIS JavaScript SDK Assistant" extension will be documented in this file.

## [0.3.0] - 2024-10-25

### Added
- **Module 3: Chat Sidebar Interface** - Beautiful chat UI in VS Code
  - Chat panel in sidebar with VS Code theme integration
  - Message history with user/AI message bubbles
  - Syntax-highlighted code blocks
  - Copy and Insert buttons for code
  - Clickable source citations with relevance scores
  - Loading animation during API calls
  - Example questions on empty state
  - Persistent message history across sessions
  - Auto-resizing text input
  - Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Chat panel integrates seamlessly with existing API client
- All messages styled to match VS Code theme

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

### Planned for Next Release (0.4.0)
- Module 4: Code insertion with smart indentation
- Module 5: Hover documentation provider
- Module 6: Packaging and distribution

## [Unreleased]

### In Development
- Module 2: API Client
- Module 3: Chat Interface
- Module 4: Code Insertion
- Module 5: Hover Provider
- Module 6: Packaging & Distribution