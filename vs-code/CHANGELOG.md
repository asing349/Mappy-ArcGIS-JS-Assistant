# Change Log

All notable changes to the "Mappy - ArcGIS JavaScript SDK Assistant" extension will be documented in this file.

## [0.5.0] - 2025-10-29

### Fixed
- Increased API timeout to 50 seconds to prevent timeouts on slow responses.

## [0.4.0] - 2025-10-25

### Added
- **Right-Click Context Menu** - Ask Mappy About This
  - Right-click on any ArcGIS class name to ask questions
  - Automatically populates chat with relevant query
  - Works in JavaScript, TypeScript, React files
  - Zero-friction workflow for quick documentation lookup
- **Production Backend Integration**
  - Connected to Railway production API
  - Default API URL: `https://mappy-arcgis-js-assistant-production.up.railway.app`
  - No localhost required - works out of the box
- **Webview UI Files**
  - Properly packaged HTML, CSS, JS for chat interface
  - Chat sidebar now works in packaged extension
  - Beautiful VS Code theme integration maintained

### Changed
- Disabled automatic hover provider (prevented excessive API calls)
- Updated to ArcGIS JavaScript SDK 4.34 documentation
- Optimized package size with proper .vscodeignore
- Improved cache management for both API and hover data

### Fixed
- Chat interface not loading in packaged .vsix
- Connection errors with production backend
- Webview files missing from package

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

## Skipped Features

### Module 4: Code Insertion
- Skipped in favor of existing Copy button functionality
- Insert button in chat provides sufficient code insertion capabilities

## Future Plans

- Offline mode with bundled documentation
- Smarter symbol detection using TypeScript AST
- Signature help (parameter hints while typing)
- Auto-import suggestions
- Code actions and quick fixes
- Multi-language support (i18n)