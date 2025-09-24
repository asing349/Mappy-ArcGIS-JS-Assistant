// src/app/layout.tsx
import '@mantine/core/styles.css';
import '@mantine/code-highlight/styles.css';
import { MantineProvider, ColorSchemeScript } from '@mantine/core';
import { Inter, Orbitron } from 'next/font/google'; // 1. Import Orbitron
import { theme } from '@/styles/theme';
import './globals.css';

// 2. Setup Inter font with a CSS variable
const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
});

// 3. Setup Orbitron font with a CSS variable
const orbitron = Orbitron({
  subsets: ['latin'],
  weight: ['400', '700', '900'],
  variable: '--font-orbitron',
});

// 4. Updated metadata to be more general
export const metadata = {
  title: 'Mappy - AI Assistant',
  description: 'Your intelligent companion for building amazing things.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      {/* 5. Apply font variables to the body */}
      <body className={`${inter.variable} ${orbitron.variable}`} suppressHydrationWarning>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}