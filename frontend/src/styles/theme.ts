// src/styles/theme.ts
import { createTheme } from '@mantine/core';

export const theme = createTheme({
  primaryColor: 'blue',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  fontFamilyMonospace: 'JetBrains Mono, Fira Code, Consolas, monospace',
  colors: {
    dark: [
      '#f1f5f9', // 0 - lightest text
      '#cbd5e1', // 1 - secondary text  
      '#94a3b8', // 2 - muted text
      '#64748b', // 3
      '#475569', // 4
      '#334155', // 5 - input background
      '#1e293b', // 6 - surface
      '#0f172a', // 7
      '#0a0e1a', // 8 - main background
      '#020617', // 9 - darkest
    ],
    gray: [
      '#f8fafc', // 0 - light mode bg
      '#f1f5f9', // 1 - light surface
      '#e2e8f0', // 2 - light border
      '#cbd5e1', // 3
      '#94a3b8', // 4
      '#64748b', // 5
      '#475569', // 6
      '#334155', // 7
      '#1e293b', // 8 - light mode text
      '#0f172a', // 9
    ],
    blue: [
      '#eff6ff', // 0
      '#dbeafe', // 1
      '#bfdbfe', // 2
      '#93c5fd', // 3
      '#60a5fa', // 4
      '#3b82f6', // 5 - primary (dark mode)
      '#2563eb', // 6 - primary (light mode)
      '#1d4ed8', // 7
      '#1e40af', // 8
      '#1e3a8a', // 9
    ],
    cyan: [
      '#ecfeff', // 0
      '#cffafe', // 1
      '#a5f3fc', // 2
      '#67e8f9', // 3
      '#22d3ee', // 4
      '#06b6d4', // 5 - accent (dark mode)
      '#0891b2', // 6 - accent (light mode)
      '#0e7490', // 7
      '#155e75', // 8
      '#164e63', // 9
    ],
  },
  other: {
    // Custom theme variables
    glassBackground: 'rgba(51, 65, 85, 0.8)',
    glassBorder: 'rgba(59, 130, 246, 0.2)',
    glassBorderFocus: 'rgba(59, 130, 246, 0.6)',
  }
});