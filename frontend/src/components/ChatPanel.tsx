'use client';

import { 
  Box, 
  ScrollArea, 
  Paper, 
  Text, 
  Textarea, 
  ActionIcon, 
  Group, 
  Button,
  Stack,
  Flex,
  useMantineColorScheme,
  useComputedColorScheme,
  Menu,
  Tooltip,
  Badge,
  Collapse,
  Code
} from '@mantine/core';
import { 
  IconX, 
  IconSend, 
  IconUser, 
  IconRobot, 
  IconCopy, 
  IconTrash,
  IconDots,
  IconCheck,
  IconChevronDown,
  IconExternalLink,
  IconAlertCircle
} from '@tabler/icons-react';
import { useState, useRef, useEffect } from 'react';
import React from 'react';

type Source = {
  title: string;
  url?: string;
  snippet?: string;
  document_type?: string;
  relevance_score?: number;
};

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'mappy';
  timestamp: Date;
  sources?: Source[];
  query_type?: string;
  error?: boolean;
};

type ChatPanelProps = {
  onClose: () => void;
};

// Code Block Component with individual copy functionality
const CodeBlock = ({ 
  code, 
  language = '', 
  isDark 
}: { 
  code: string; 
  language?: string; 
  isDark: boolean; 
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  return (
    <Box
      style={{
        backgroundColor: isDark ? 'rgba(31, 41, 55, 0.9)' : 'rgba(249, 250, 251, 0.95)',
        border: `1px solid ${isDark ? 'rgba(55, 65, 81, 0.5)' : 'rgba(229, 231, 235, 0.8)'}`,
        borderRadius: '8px',
        margin: '12px 0',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Code header with language and copy button */}
      <Flex
        justify="space-between"
        align="center"
        p="xs"
        style={{
          backgroundColor: isDark ? 'rgba(17, 24, 39, 0.8)' : 'rgba(243, 244, 246, 0.8)',
          borderBottom: `1px solid ${isDark ? 'rgba(55, 65, 81, 0.3)' : 'rgba(229, 231, 235, 0.5)'}`
        }}
      >
        <Text size="xs" c="dimmed" fw={500}>
          {language || 'Code'}
        </Text>
        <Tooltip label={copied ? 'Copied!' : 'Copy code'}>
          <ActionIcon
            size="sm"
            variant="subtle"
            color="gray"
            onClick={handleCopy}
          >
            {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
          </ActionIcon>
        </Tooltip>
      </Flex>
      
      {/* Code content */}
      <Box
        p="md"
        style={{
          fontFamily: 'JetBrains Mono, Consolas, Monaco, monospace',
          fontSize: '14px',
          lineHeight: 1.5,
          overflow: 'auto',
          whiteSpace: 'pre',
          color: isDark ? '#e5e7eb' : '#374151'
        }}
      >
        {code}
      </Box>
    </Box>
  );
};

// Enhanced markdown parser that creates proper components
const parseMessageContent = (text: string, isDark: boolean) => {
  const parts = [];
  let currentIndex = 0;
  
  // Remove References section entirely (it's redundant with sources dropdown)
  const cleanedText = text.replace(/## References[\s\S]*$/i, '').trim();
  
  // Split by code blocks first
  const codeBlockRegex = /```(\w+)?\n?([\s\S]*?)```/g;
  let match;
  
  while ((match = codeBlockRegex.exec(cleanedText)) !== null) {
    // Add text before code block
    if (match.index > currentIndex) {
      const beforeText = cleanedText.slice(currentIndex, match.index);
      if (beforeText.trim()) {
        parts.push({
          type: 'text',
          content: beforeText,
          key: `text-${currentIndex}`
        });
      }
    }
    
    // Add code block
    parts.push({
      type: 'code',
      content: match[2].trim(),
      language: match[1] || '',
      key: `code-${match.index}`
    });
    
    currentIndex = match.index + match[0].length;
  }
  
  // Add remaining text
  if (currentIndex < cleanedText.length) {
    const remainingText = cleanedText.slice(currentIndex);
    if (remainingText.trim()) {
      parts.push({
        type: 'text',
        content: remainingText,
        key: `text-${currentIndex}`
      });
    }
  }
  
  // If no code blocks found, treat as all text
  if (parts.length === 0) {
    parts.push({
      type: 'text',
      content: cleanedText,
      key: 'text-0'
    });
  }
  
  return parts.map(part => {
    if (part.type === 'code') {
      return (
        <CodeBlock
          key={part.key}
          code={part.content}
          language={part.language}
          isDark={isDark}
        />
      );
    } else {
      return (
        <FormattedText
          key={part.key}
          content={part.content}
          isDark={isDark}
        />
      );
    }
  });
};

// Text formatting component for non-code content
const FormattedText = ({ content, isDark }: { content: string; isDark: boolean }) => {
  const formatTextContent = (text: string) => {
    // Split by line breaks and process each part
    const lines = text.split('\n');
    const result = [];
    let currentParagraph = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Check for markdown headers (## Header)
      if (line.startsWith('## ')) {
        // Finish current paragraph if exists
        if (currentParagraph.length > 0) {
          result.push({
            type: 'paragraph',
            content: currentParagraph.join('\n'),
            key: `para-${i}`
          });
          currentParagraph = [];
        }
        // Add header
        result.push({
          type: 'header',
          content: line.replace(/^## /, ''),
          key: `header-${i}`
        });
      }
      // Check for bold headers (**Header**)
      else if (line.startsWith('**') && line.endsWith('**') && line.includes(':')) {
        // Finish current paragraph if exists
        if (currentParagraph.length > 0) {
          result.push({
            type: 'paragraph',
            content: currentParagraph.join('\n'),
            key: `para-${i}`
          });
          currentParagraph = [];
        }
        // Add bold header
        result.push({
          type: 'boldHeader',
          content: line.replace(/\*\*/g, ''),
          key: `boldHeader-${i}`
        });
      }
      // Check for bullet lists (starting with *)
      else if (line.startsWith('* ')) {
        // Finish current paragraph if exists
        if (currentParagraph.length > 0) {
          result.push({
            type: 'paragraph',
            content: currentParagraph.join('\n'),
            key: `para-${i}`
          });
          currentParagraph = [];
        }
        // Collect consecutive bullet items
        const bulletItems = [];
        let j = i;
        while (j < lines.length && lines[j].trim().startsWith('* ')) {
          bulletItems.push(lines[j].trim());
          j++;
        }
        result.push({
          type: 'bulletList',
          content: bulletItems,
          key: `bulletList-${i}`
        });
        i = j - 1; // Skip processed lines
      }
      // Check for numbered lists
      else if (/^\d+\./.test(line)) {
        // Finish current paragraph if exists
        if (currentParagraph.length > 0) {
          result.push({
            type: 'paragraph',
            content: currentParagraph.join('\n'),
            key: `para-${i}`
          });
          currentParagraph = [];
        }
        // Collect consecutive list items
        const listItems = [];
        let j = i;
        while (j < lines.length && /^\d+\./.test(lines[j].trim())) {
          listItems.push(lines[j].trim());
          j++;
        }
        result.push({
          type: 'list',
          content: listItems,
          key: `list-${i}`
        });
        i = j - 1; // Skip processed lines
      }
      // Empty line - finish paragraph
      else if (line === '') {
        if (currentParagraph.length > 0) {
          result.push({
            type: 'paragraph',
            content: currentParagraph.join('\n'),
            key: `para-${i}`
          });
          currentParagraph = [];
        }
      }
      // Regular text line
      else {
        currentParagraph.push(lines[i]); // Keep original spacing
      }
    }
    
    // Add final paragraph if exists
    if (currentParagraph.length > 0) {
      result.push({
        type: 'paragraph',
        content: currentParagraph.join('\n'),
        key: `para-final`
      });
    }
    
    return result.map(item => {
      switch (item.type) {
        case 'header':
          return (
            <Text
              key={item.key}
              size="xl"
              fw={700}
              mb="sm"
              mt="lg"
              style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}
            >
              {item.content}
            </Text>
          );
        case 'boldHeader':
          return (
            <Text
              key={item.key}
              size="lg"
              fw={700}
              mb="sm"
              mt="md"
              style={{ color: isDark ? '#f1f5f9' : '#1e293b' }}
            >
              {item.content}
            </Text>
          );
        case 'bulletList':
          return (
            <Box key={item.key} component="ul" mb="md" style={{ paddingLeft: '20px' }}>
              {(item.content as string[]).map((listItem, index) => (
                <Box
                  key={`${item.key}-item-${index}`}
                  component="li"
                  mb="xs"
                  style={{
                    color: isDark ? '#f1f5f9' : '#1e293b',
                    lineHeight: 1.6
                  }}
                >
                  {formatInlineText(listItem.replace(/^\*\s*/, ''))}
                </Box>
              ))}
            </Box>
          );
        case 'list':
          return (
            <Box key={item.key} component="ol" mb="md" style={{ paddingLeft: '20px' }}>
              {(item.content as string[]).map((listItem, index) => (
                <Box
                  key={`${item.key}-item-${index}`}
                  component="li"
                  mb="xs"
                  style={{
                    color: isDark ? '#f1f5f9' : '#1e293b',
                    lineHeight: 1.6
                  }}
                >
                  {formatInlineText(listItem.replace(/^\d+\.\s*/, ''))}
                </Box>
              ))}
            </Box>
          );
        case 'paragraph':
          return (
            <Text
              key={item.key}
              mb="sm"
              style={{
                color: isDark ? '#f1f5f9' : '#1e293b',
                lineHeight: 1.6,
                wordWrap: 'break-word',
                overflowWrap: 'break-word'
              }}
            >
              {formatInlineText(item.content as string)}
            </Text>
          );
        default:
          return null;
      }
    });
  };
  
  const formatInlineText = (text: string) => {
    const parts = [];
    let currentIndex = 0;
    
    // First handle bold text **text**
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before bold
      if (match.index > currentIndex) {
        const beforeText = text.slice(currentIndex, match.index);
        parts.push({ type: 'text', content: beforeText });
      }
      
      // Add bold text
      parts.push({ type: 'bold', content: match[1] });
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push({ type: 'text', content: text.slice(currentIndex) });
    }
    
    // If no bold found, treat as all text
    if (parts.length === 0) {
      parts.push({ type: 'text', content: text });
    }
    
    // Now process each part for inline code
    return parts.map((part, index) => {
      if (part.type === 'bold') {
        return (
          <Text key={index} component="strong" fw={700}>
            {part.content}
          </Text>
        );
      } else {
        // Handle inline code in text parts
        const codeParts = part.content.split(/(`[^`]+`)/g);
        return codeParts.map((codePart, cIndex) => {
          if (codePart.startsWith('`') && codePart.endsWith('`')) {
            return (
              <Code
                key={`${index}-${cIndex}`}
                style={{
                  backgroundColor: isDark ? 'rgba(55, 65, 81, 0.6)' : 'rgba(243, 244, 246, 0.9)',
                  color: isDark ? '#fbbf24' : '#d97706',
                  fontSize: '0.875rem'
                }}
              >
                {codePart.slice(1, -1)}
              </Code>
            );
          }
          return codePart;
        });
      }
    }).flat();
  };
  
  return <Box>{formatTextContent(content)}</Box>;
};

const ChatPanel = React.forwardRef<HTMLDivElement, ChatPanelProps>(({ onClose }, ref) => {
  const computedColorScheme = useComputedColorScheme('dark');
  const isDark = computedColorScheme === 'dark';
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hello! I'm **Mappy**, your ArcGIS JavaScript SDK documentation assistant. Ask me anything about ArcGIS development, APIs, or implementation questions!\n\nTry asking: `How do I create a map?` or `Show me feature layer examples`",
      sender: 'mappy',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [typingDots, setTypingDots] = useState('');
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Typing animation when loading
  useEffect(() => {
    if (!isLoading) {
      setTypingDots('');
      return;
    }

    const interval = setInterval(() => {
      setTypingDots(prev => {
        if (prev === '●●●') return '●';
        if (prev === '●●') return '●●●';
        if (prev === '●') return '●●';
        return '●';
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isLoading]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue.trim(),
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.text,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        let errorMessage = 'Something went wrong. Please try again.';
        
        if (response.status === 429) {
          errorMessage = 'Rate limit exceeded. Please wait a moment before sending another message.';
        } else if (response.status === 400) {
          const errorData = await response.json();
          errorMessage = errorData.detail || 'Invalid request. Please check your message.';
        } else if (response.status >= 500) {
          errorMessage = 'Server error. Please try again in a moment.';
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();

      const mappyResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: data.answer,
        sender: 'mappy',
        timestamp: new Date(),
        sources: data.sources || [],
        query_type: data.query_type
      };
      
      setMessages(prev => [...prev, mappyResponse]);
      
    } catch (error) {
      console.error('Chat API error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? error.message : 'Failed to get response. Please try again.',
        sender: 'mappy',
        timestamp: new Date(),
        error: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const copyMessage = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  };

  const clearChatHistory = () => {
    setMessages([{
      id: Date.now().toString(),
      text: "Chat history cleared! How can I help you with **ArcGIS JavaScript SDK** today?",
      sender: 'mappy',
      timestamp: new Date()
    }]);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const toggleSourcesExpanded = (messageId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const SourceCitations = ({ message }: { message: Message }) => {
    if (!message.sources || message.sources.length === 0) return null;
    
    const isExpanded = expandedSources.has(message.id);
    
    return (
      <Box mt="md">
        <Button
          variant="subtle"
          size="xs"
          onClick={() => toggleSourcesExpanded(message.id)}
          leftSection={<IconChevronDown 
            size={12} 
            style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }} 
          />}
          color={isDark ? 'gray.5' : 'gray.7'}
        >
          {message.sources.length} source{message.sources.length === 1 ? '' : 's'}
        </Button>
        
        <Collapse in={isExpanded}>
          <Stack gap="xs" mt="sm">
            {message.sources.map((source, index) => (
              <Paper
                key={index}
                p="sm"
                radius="md"
                style={{
                  backgroundColor: isDark ? 'rgba(71, 85, 105, 0.2)' : 'rgba(241, 245, 249, 0.6)',
                  border: `1px solid ${isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(37, 99, 235, 0.1)'}`
                }}
              >
                {/* Direct link display - show URL or title */}
                <Group gap="xs" mb="xs" wrap="nowrap">
                  <Text
                    component="a"
                    href={source.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    size="sm"
                    style={{
                      color: isDark ? '#60a5fa' : '#2563eb',
                      textDecoration: 'underline',
                      wordBreak: 'break-all',
                      flex: 1
                    }}
                  >
                    {source.url || (source.title !== 'No title' ? source.title : 'Source link')}
                  </Text>
                  {source.document_type && (
                    <Badge size="xs" color="blue" variant="light" style={{ flexShrink: 0 }}>
                      {source.document_type}
                    </Badge>
                  )}
                  <ActionIcon
                    size="xs"
                    variant="subtle"
                    color="blue"
                    component="a"
                    href={source.url || '#'}
                    target="_blank"
                    style={{ flexShrink: 0 }}
                  >
                    <IconExternalLink size={10} />
                  </ActionIcon>
                </Group>
                {source.snippet && (
                  <Text size="xs" c="dimmed" style={{ lineHeight: 1.4 }}>
                    {source.snippet}
                  </Text>
                )}
              </Paper>
            ))}
          </Stack>
        </Collapse>
      </Box>
    );
  };

  const MessageBubble = ({ message }: { message: Message }) => {
    const isUser = message.sender === 'user';
    const isCopied = copiedMessageId === message.id;
    
    return (
      <Flex 
        justify={isUser ? 'flex-end' : 'flex-start'} 
        mb="lg"
        style={{ width: '100%' }}
      >
        <Paper
          withBorder
          p="lg"
          radius="xl"
          maw="90%"
          style={{
            backgroundColor: message.error 
              ? (isDark ? 'rgba(239, 68, 68, 0.1)' : 'rgba(254, 242, 242, 1)')
              : isUser 
              ? (isDark ? '#3b82f6' : '#2563eb')
              : (isDark ? 'rgba(51, 65, 85, 0.8)' : '#f8fafc'),
            borderColor: message.error
              ? (isDark ? 'rgba(239, 68, 68, 0.3)' : 'rgba(239, 68, 68, 0.3)')
              : isUser 
              ? (isDark ? '#3b82f6' : '#2563eb')
              : (isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)'),
            backdropFilter: !isUser ? 'blur(12px)' : 'none',
            position: 'relative',
            wordWrap: 'break-word',
            overflowWrap: 'break-word'
          }}
        >
          {/* Message Header */}
          <Group justify="space-between" mb="md" wrap="nowrap">
            <Group gap="xs" wrap="nowrap">
              <ActionIcon 
                size="sm" 
                variant="transparent"
                color={message.error 
                  ? 'red' 
                  : isUser 
                  ? 'white' 
                  : (isDark ? 'blue' : 'blue.6')
                }
              >
                {message.error ? <IconAlertCircle size={14} /> : isUser ? <IconUser size={14} /> : <IconRobot size={14} />}
              </ActionIcon>
              <Text 
                size="sm" 
                fw={600}
                c={message.error 
                  ? 'red' 
                  : isUser 
                  ? 'white' 
                  : (isDark ? 'blue.3' : 'blue.6')
                }
              >
                {isUser ? 'You' : 'Mappy'}
              </Text>
              <Text 
                size="xs" 
                c={isUser ? 'rgba(255,255,255,0.7)' : 'dimmed'}
              >
                {formatTime(message.timestamp)}
              </Text>
              {message.query_type && (
                <Badge size="xs" color="teal" variant="light">
                  {message.query_type}
                </Badge>
              )}
            </Group>
            
            {/* Copy Button */}
            <Tooltip label={isCopied ? 'Copied!' : 'Copy message'}>
              <ActionIcon
                size="sm"
                variant="subtle"
                color={isUser ? 'white' : (isDark ? 'gray' : 'gray.6')}
                onClick={() => copyMessage(message.text, message.id)}
                style={{ opacity: 0.8 }}
              >
                {isCopied ? <IconCheck size={14} /> : <IconCopy size={14} />}
              </ActionIcon>
            </Tooltip>
          </Group>

          {/* Message Content - Enhanced parsing */}
          <Box style={{ 
            color: message.error 
              ? (isDark ? '#fca5a5' : '#dc2626')
              : isUser 
              ? '#ffffff'
              : (isDark ? '#f1f5f9' : '#1e293b')
          }}>
            {parseMessageContent(message.text, isDark)}
          </Box>

          {/* Source Citations */}
          {!isUser && <SourceCitations message={message} />}
        </Paper>
      </Flex>
    );
  };

  return (
    <Box 
      ref={ref} 
      p="xl" 
      h="100vh" 
      style={{ 
        display: 'flex', 
        flexDirection: 'column',
        background: isDark 
          ? 'linear-gradient(135deg, rgba(10, 14, 26, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%)'
          : 'linear-gradient(135deg, rgba(248, 250, 252, 0.95) 0%, rgba(241, 245, 249, 0.95) 100%)',
        backdropFilter: 'blur(20px)',
        borderLeft: `1px solid ${isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)'}`
      }}
    >
      {/* Header */}
      <Group justify="space-between" mb="lg">
        <Stack gap="xs">
          <Text size="lg" fw={700} c={isDark ? 'gray.1' : 'gray.8'}>
            Chat with Mappy
          </Text>
          <Text size="xs" c="dimmed">
            {isLoading ? 'Mappy is thinking...' : 'ArcGIS JavaScript SDK Documentation Assistant'}
          </Text>
        </Stack>
        
        <Group gap="xs">
          {/* Chat Options Menu */}
          <Menu shadow="md" width={200}>
            <Menu.Target>
              <ActionIcon
                variant="subtle"
                color="gray"
                size="lg"
                radius="xl"
                aria-label="Chat options"
                style={{
                  backdropFilter: 'blur(12px)',
                  backgroundColor: isDark ? 'rgba(51, 65, 85, 0.6)' : 'rgba(255, 255, 255, 0.6)',
                }}
              >
                <IconDots size={18} />
              </ActionIcon>
            </Menu.Target>

            <Menu.Dropdown>
              <Menu.Item
                leftSection={<IconTrash size={16} />}
                color="red"
                onClick={clearChatHistory}
              >
                Clear Chat History
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>

          {/* Close Button */}
          <ActionIcon
            onClick={onClose}
            variant="subtle"
            color="gray"
            size="lg"
            radius="xl"
            aria-label="Close chat"
            style={{
              backdropFilter: 'blur(12px)',
              backgroundColor: isDark ? 'rgba(51, 65, 85, 0.6)' : 'rgba(255, 255, 255, 0.6)',
            }}
          >
            <IconX size={20} />
          </ActionIcon>
        </Group>
      </Group>

      {/* Chat Messages */}
      <ScrollArea 
        style={{ flex: 1 }} 
        mb="lg"
        viewportRef={scrollAreaRef}
        scrollbarSize={6}
        styles={{
          scrollbar: {
            backgroundColor: isDark ? 'rgba(51, 65, 85, 0.3)' : 'rgba(203, 213, 225, 0.3)',
          },
          thumb: {
            backgroundColor: isDark ? 'rgba(59, 130, 246, 0.5)' : 'rgba(37, 99, 235, 0.5)',
          }
        }}
      >
        <Stack gap="sm" p="xs">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {/* Typing Animation */}
          {isLoading && (
            <Flex justify="flex-start" mb="md">
              <Paper
                withBorder
                p="md"
                radius="xl"
                style={{
                  backgroundColor: isDark ? 'rgba(51, 65, 85, 0.8)' : '#f8fafc',
                  borderColor: isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)',
                  backdropFilter: 'blur(12px)'
                }}
              >
                <Group gap="xs" mb="xs">
                  <ActionIcon size="sm" variant="transparent" color={isDark ? 'blue.3' : 'blue.6'}>
                    <IconRobot size={14} />
                  </ActionIcon>
                  <Text size="xs" fw={600} c={isDark ? 'blue.3' : 'blue.6'}>Mappy</Text>
                  <Text size="xs" c="dimmed">{formatTime(new Date())}</Text>
                </Group>
                <Text 
                  size="sm" 
                  c="dimmed" 
                  style={{ 
                    fontFamily: 'monospace',
                    minHeight: '20px',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {typingDots}
                </Text>
              </Paper>
            </Flex>
          )}
        </Stack>
      </ScrollArea>

      {/* Chat Input */}
      <Paper
        withBorder
        p="md"
        radius="xl"
        style={{
          backgroundColor: isDark ? 'rgba(51, 65, 85, 0.8)' : 'rgba(255, 255, 255, 0.8)',
          borderColor: isDark ? 'rgba(59, 130, 246, 0.3)' : 'rgba(37, 99, 235, 0.3)',
          backdropFilter: 'blur(16px)'
        }}
      >
        <Group align="flex-end" gap="sm">
          <Textarea
            ref={textareaRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.currentTarget.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about ArcGIS JavaScript SDK... (Press Enter to send, Shift+Enter for new line)"
            autosize
            minRows={1}
            maxRows={4}
            style={{ flex: 1 }}
            styles={{
              input: {
                backgroundColor: 'transparent',
                border: 'none',
                fontSize: '14px',
                '&:focus': {
                  outline: 'none'
                }
              }
            }}
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            loading={isLoading}
            size="sm"
            radius="xl"
            variant="gradient"
            gradient={{ from: '#3b82f6', to: '#06b6d4', deg: 135 }}
            leftSection={<IconSend size={16} />}
          >
            Send
          </Button>
        </Group>
      </Paper>
    </Box>
  );
});

ChatPanel.displayName = 'ChatPanel';
export default ChatPanel;