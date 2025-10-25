/**
 * Chat UI Logic
 * Runs in the webview context
 */

(function() {
    // Get VS Code API
    const vscode = acquireVsCodeApi();

    // DOM elements
    const messagesContainer = document.getElementById('messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading-indicator');

    // State
    let messages = [];
    let isLoading = false;

    // Initialize
    init();

    function init() {
        // Load previous messages from state
        const previousState = vscode.getState();
        
        if (previousState && previousState.messages && Array.isArray(previousState.messages) && previousState.messages.length > 0) {
            messages = previousState.messages;
            renderMessages();
        } else {
            messages = [];
            showEmptyState();
        }

        // Event listeners
        sendButton.addEventListener('click', handleSend);
        userInput.addEventListener('keydown', handleKeyDown);
        userInput.addEventListener('input', autoResizeTextarea);

        // Listen for messages from extension
        window.addEventListener('message', handleExtensionMessage);

        // Focus input
        userInput.focus();
    }

    /**
     * Handle send button click
     */
    function handleSend() {
        const text = userInput.value.trim();
        if (!text || isLoading) {
            return;
        }

        // Add user message
        addMessage({
            id: generateId(),
            text: text,
            isUser: true,
            timestamp: Date.now()
        });

        // Clear input
        userInput.value = '';
        autoResizeTextarea();

        // Send to extension
        vscode.postMessage({
            type: 'query',
            data: { text }
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    /**
     * Auto-resize textarea
     */
    function autoResizeTextarea() {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    }

    /**
     * Handle messages from extension
     */
    function handleExtensionMessage(event) {
        const message = event.data;

        switch (message.type) {
            case 'response':
                handleResponse(message.data);
                break;

            case 'error':
                handleError(message.data);
                break;

            case 'loading':
                setLoading(message.data.isLoading);
                break;
                
            case 'reset':
                clearHistory();
                break;
                
            case 'populate-input':
                handlePopulateInput(message.data);
                break;
        }
    }

    /**
     * Handle API response
     */
    function handleResponse(data) {
        addMessage({
            id: generateId(),
            text: data.answer,
            isUser: false,
            timestamp: Date.now(),
            sources: data.sources || []
        });
    }

    /**
     * Handle error
     */
    function handleError(data) {
        addMessage({
            id: generateId(),
            text: data.error,
            isUser: false,
            timestamp: Date.now(),
            error: true
        });
    }

    /**
     * Populate input field with text (from hover "Ask in Chat" link)
     * Does NOT auto-send the message
     */
    function handlePopulateInput(data) {
        if (!data || !data.text) {
            return;
        }

        // Set the input value
        userInput.value = data.text;
        
        // Auto-resize the textarea
        autoResizeTextarea();
        
        // Focus the input so user can see it's populated and ready to edit
        userInput.focus();
        
        // Move cursor to end of text
        userInput.setSelectionRange(data.text.length, data.text.length);
        
        console.log('Input populated with:', data.text);
    }

    /**
     * Set loading state
     */
    function setLoading(loading) {
        isLoading = loading;
        loadingIndicator.style.display = loading ? 'block' : 'none';
        sendButton.disabled = loading;
        userInput.disabled = loading;

        if (loading) {
            scrollToBottom();
        }
    }

    /**
     * Add message to chat
     */
    function addMessage(message) {
        messages.push(message);
        saveState();
        renderMessages();
        scrollToBottom();
    }

    /**
     * Render all messages
     */
    function renderMessages() {
        messagesContainer.innerHTML = '';

        if (messages.length === 0) {
            showEmptyState();
            return;
        }

        messages.forEach(message => {
            const messageEl = createMessageElement(message);
            messagesContainer.appendChild(messageEl);
        });
    }

    /**
     * Create message element
     */
    function createMessageElement(message) {
        const div = document.createElement('div');
        div.className = `message ${message.isUser ? 'user' : 'assistant'}${message.error ? ' error' : ''}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Process message text for code blocks and markdown
        contentDiv.innerHTML = formatMessage(message.text);

        // Add code block actions
        addCodeBlockActions(contentDiv);

        div.appendChild(contentDiv);

        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = formatTime(message.timestamp);
        div.appendChild(timestampDiv);

        // Add sources if present
        if (message.sources && message.sources.length > 0) {
            const sourcesEl = createSourcesElement(message.sources);
            div.appendChild(sourcesEl);
        }

        return div;
    }

    /**
     * Format message text (markdown-like parsing)
     */
    function formatMessage(text) {
        // Escape HTML first
        let formatted = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Code blocks (```...```)
        formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang || 'javascript'}">${code.trim()}</code></pre>`;
        });

        // Inline code (`...`)
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headers
        formatted = formatted.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        formatted = formatted.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        formatted = formatted.replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // Bold
        formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic
        formatted = formatted.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Links
        formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // Line breaks
        formatted = formatted.replace(/\n/g, '<br>');

        return formatted;
    }

    /**
     * Add copy and insert buttons to code blocks
     */
    function addCodeBlockActions(container) {
        const codeBlocks = container.querySelectorAll('pre code');
        
        codeBlocks.forEach(codeBlock => {
            const pre = codeBlock.parentElement;
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-container';
            
            const actions = document.createElement('div');
            actions.className = 'code-actions';

            // Copy button
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-action-btn';
            copyBtn.textContent = 'Copy';
            copyBtn.onclick = () => copyCode(codeBlock, copyBtn);
            actions.appendChild(copyBtn);

            // Insert button
            const insertBtn = document.createElement('button');
            insertBtn.className = 'code-action-btn';
            insertBtn.textContent = 'Insert';
            insertBtn.onclick = () => insertCode(codeBlock);
            actions.appendChild(insertBtn);

            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(actions);
            wrapper.appendChild(pre);
        });
    }

    /**
     * Copy code to clipboard
     */
    function copyCode(codeBlock, button) {
        const code = codeBlock.textContent;
        navigator.clipboard.writeText(code).then(() => {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        });
    }

    /**
     * Insert code into editor
     */
    function insertCode(codeBlock) {
        const code = codeBlock.textContent;
        vscode.postMessage({
            type: 'insert-code',
            data: { code }
        });
    }

    /**
     * Create sources element
     */
    function createSourcesElement(sources) {
        if (!sources || !Array.isArray(sources) || sources.length === 0) {
            return document.createElement('div'); // Return empty div
        }

        const container = document.createElement('div');
        container.className = 'sources';

        const title = document.createElement('div');
        title.className = 'sources-title';
        title.textContent = `📚 Sources (${sources.length})`;
        container.appendChild(title);

        sources.forEach((source, index) => {
            const item = document.createElement('a');
            item.className = 'source-item';
            item.href = '#';
            item.onclick = (e) => {
                e.preventDefault();
                openUrl(source.url);
            };

            const icon = document.createElement('div');
            icon.className = 'source-icon';
            icon.innerHTML = '🔗';
            item.appendChild(icon);

            const info = document.createElement('div');
            info.className = 'source-info';

            const sourceTitle = document.createElement('div');
            sourceTitle.className = 'source-title';
            sourceTitle.textContent = source.title || 'Untitled';
            info.appendChild(sourceTitle);

            const meta = document.createElement('div');
            meta.className = 'source-meta';
            const docType = source.document_type || 'document';
            const relevance = source.relevance_score || 0;
            meta.textContent = `${docType} • ${(relevance * 100).toFixed(0)}% relevant`;
            info.appendChild(meta);

            item.appendChild(info);
            container.appendChild(item);
        });

        return container;
    }

    /**
     * Open URL in browser
     */
    function openUrl(url) {
        vscode.postMessage({
            type: 'open-url',
            data: { url }
        });
    }

    /**
     * Show empty state with example questions
     */
    function showEmptyState() {
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <h3>👋 Welcome to Mappy!</h3>
                <p>Ask me anything about the ArcGIS JavaScript SDK</p>
                
                <div class="example-questions">
                    <button class="example-question-btn" data-question="How do I create a 3D map?">
                        How do I create a 3D map?
                    </button>
                    <button class="example-question-btn" data-question="What is FeatureLayer?">
                        What is FeatureLayer?
                    </button>
                    <button class="example-question-btn" data-question="How to add a popup to a map?">
                        How to add a popup to a map?
                    </button>
                    <button class="example-question-btn" data-question="Create a map with basemap selector">
                        Create a map with basemap selector
                    </button>
                </div>
            </div>
        `;

        const exampleButtons = messagesContainer.querySelectorAll('.example-question-btn');
        exampleButtons.forEach(button => {
            button.addEventListener('click', () => {
                const question = button.getAttribute('data-question');
                if (question) {
                    askExample(question);
                }
            });
        });
    }

    function askExample(question) {
        userInput.value = question;
        handleSend();
    }

    /**
     * Format timestamp
     */
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Generate unique ID
     */
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substring(2);
    }

    /**
     * Save state to persistence
     */
    function saveState() {
        vscode.setState({ messages: messages || [] });
    }

    /**
     * Scroll to bottom
     */
    function scrollToBottom() {
        setTimeout(() => {
            const container = document.getElementById('messages-container');
            container.scrollTop = container.scrollHeight;
        }, 100);
    }

    /**
     * Clear chat history
     */
    function clearHistory() {
        // Clear in-memory messages
        messages = [];
        
        // Clear persistent state
        vscode.setState({ messages: [] });
        
        // Re-render the UI
        renderMessages();
        
        // Notify the extension
        vscode.postMessage({
            type: 'clear-history',
            data: {}
        });
    }

    // Expose clearHistory globally for potential use
    window.clearHistory = clearHistory;

})();