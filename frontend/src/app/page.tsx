'use client';

import {
  Container,
  Stack,
  Title,
  Text,
  Button,
  Center,
  Box,
  ActionIcon,
  Flex,
  Group,
  Anchor,
  useMantineColorScheme,
  useComputedColorScheme
} from '@mantine/core';
import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { Flip } from 'gsap/Flip';
import { IconBrandGithub, IconBrandLinkedin } from '@tabler/icons-react';

import InfoPanel from '@/components/InfoPanel';
import ChatPanel from '@/components/ChatPanel';

gsap.registerPlugin(Flip);

// --- Helper Components ---
const ThemeToggle = () => {
  const { setColorScheme } = useMantineColorScheme();
  const computedColorScheme = useComputedColorScheme('dark');
  const toggleRef = useRef<HTMLButtonElement>(null);

  const toggleTheme = () => {
    setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark');
    gsap.to(toggleRef.current, { scale: 0.9, duration: 0.1, yoyo: true, repeat: 1, ease: "power2.inOut" });
  };

  return (
    <ActionIcon
      ref={toggleRef}
      variant="subtle"
      size="lg"
      radius="md"
      onClick={toggleTheme}
      style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 1000,
        backgroundColor: computedColorScheme === 'dark' ? 'rgba(51, 65, 85, 0.8)' : 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${computedColorScheme === 'dark' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)'}`,
        color: computedColorScheme === 'dark' ? '#f1f5f9' : '#1e293b'
      }}
    >
      {computedColorScheme === 'dark' ? '☀️' : '🌙'}
    </ActionIcon>
  );
};

const FloatingParticles = () => {
  const particlesRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!particlesRef.current) return;
    const particles = Array.from({ length: 20 }, () => {
      const particle = document.createElement('div');
      particle.style.cssText = `position: absolute; width: ${Math.random() * 6 + 2}px; height: ${Math.random() * 6 + 2}px; background: ${Math.random() > 0.5 ? '#3b82f6' : '#06b6d4'}; border-radius: 50%; opacity: ${Math.random() * 0.7 + 0.3}; left: ${Math.random() * 100}%; top: ${Math.random() * 100}%; pointer-events: none;`;
      particlesRef.current?.appendChild(particle);
      gsap.to(particle, { x: `random(-100, 100)`, y: `random(-100, 100)`, duration: `random(3, 6)`, repeat: -1, yoyo: true, ease: "sine.inOut", delay: Math.random() * 2 });
      return particle;
    });
    return () => { particles.forEach(p => p.remove()); };
  }, []);
  return <div ref={particlesRef} style={{ position: 'absolute', inset: 0 }} />;
};

const FloatingCodeElements = () => {
  const codeElements = ['{ mappy }', 'const ai =', 'function ask()', '=> response', 'import { Chat }', 'new Session()', '{ ...answers }', 'async query'];
  return (
    <>
      {codeElements.map((code, i) => (
        <Box key={i} style={{ position: 'absolute', left: `${15 + (i * 12)}%`, top: `${20 + (i % 3) * 25}%`, opacity: 0.15, fontSize: '14px', fontFamily: 'JetBrains Mono, monospace', color: i % 2 === 0 ? '#3b82f6' : '#06b6d4', pointerEvents: 'none', zIndex: 1}}>
          {code}
        </Box>
      ))}
    </>
  );
};


// --- Main Page Component ---
export default function InteractivePage() {
  const computedColorScheme = useComputedColorScheme('dark');
  const [isChatStarted, setChatStarted] = useState(false);
  const isDark = computedColorScheme === 'dark';

  const leftPanelRef = useRef<HTMLDivElement>(null);
  const rightPanelRef = useRef<HTMLDivElement>(null);
  const landingContentRef = useRef<HTMLDivElement>(null);
  const landingTitleRef = useRef<HTMLHeadingElement>(null);
  const landingTaglineRef = useRef<HTMLParagraphElement>(null);
  const landingButtonRef = useRef<HTMLButtonElement>(null);
  const landingLinksRef = useRef<HTMLDivElement>(null);
  const infoPanelRef = useRef<HTMLDivElement>(null);
  const infoPanelTitleRef = useRef<HTMLHeadingElement>(null);
  const infoPanelTaglineRef = useRef<HTMLParagraphElement>(null);
  const infoPanelLinksRef = useRef<HTMLDivElement>(null);
  const chatPanelRef = useRef<HTMLDivElement>(null);
  const flipState = useRef<gsap.Flip["FlipState"] | undefined>(undefined);

  useEffect(() => {
    gsap.set(landingContentRef.current, { opacity: 0, y: 50 });
    gsap.to(landingContentRef.current, { opacity: 1, y: 0, duration: 1.2, ease: 'elastic.out(1, 0.8)', delay: 0.5 });
  }, []);

  useEffect(() => {
    if (flipState.current === undefined) return;

    if (isChatStarted) {
      const tl = gsap.timeline();
      tl.add(
        Flip.from(flipState.current, {
          targets: [infoPanelTitleRef.current, infoPanelTaglineRef.current, infoPanelLinksRef.current],
          duration: 1.4,
          ease: 'power4.inOut',
          scale: true,
        })
      );
      tl.to(leftPanelRef.current, { width: '30%', duration: 1.4, ease: 'power4.inOut' }, '<');
      tl.to(rightPanelRef.current, { width: '70%', duration: 1.4, ease: 'power4.inOut' }, '<');
      tl.fromTo(infoPanelRef.current, { opacity: 0 }, { opacity: 1, duration: 0.7 }, '<');
      tl.fromTo(chatPanelRef.current, { opacity: 0 }, { opacity: 1, duration: 0.7, ease: 'power3.out' }, '>-0.8');
    } else {
      const tl = gsap.timeline();
      tl.add(
        Flip.from(flipState.current, {
          targets: [landingTitleRef.current, landingTaglineRef.current, landingLinksRef.current],
          duration: 1.4,
          ease: 'power4.inOut',
          scale: true,
        })
      );
      tl.to(leftPanelRef.current, { width: '100%', duration: 1.4, ease: 'power4.inOut' }, '<');
      tl.to(rightPanelRef.current, { width: '0%', duration: 1.4, ease: 'power4.inOut' }, '<');
      tl.to(landingContentRef.current, { opacity: 1, duration: 0.6, ease: 'power3.out'}, '>-0.8');
    }
  }, [isChatStarted]);

  const handleStartChat = () => {
    const morphElements = [landingTitleRef.current, landingTaglineRef.current, landingLinksRef.current];
    flipState.current = Flip.getState(morphElements);
    gsap.to(landingContentRef.current, { opacity: 0, duration: 0.5, ease: 'power2.in' });
    setChatStarted(true);
  };

  const handleCloseChat = () => {
    const morphElements = [infoPanelTitleRef.current, infoPanelTaglineRef.current, infoPanelLinksRef.current];
    flipState.current = Flip.getState(morphElements);
    gsap.to(chatPanelRef.current, {
      opacity: 0,
      duration: 0.5,
      ease: 'power3.in',
      onComplete: () => {
        setChatStarted(false);
      }
    });
  };

  return (
    <>
      <ThemeToggle />
      <Container fluid h="100vh" p={0} style={{ background: isDark ? '#0a0e1a' : '#ffffff', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: `linear-gradient(${isDark ? 'rgba(59, 130, 246, 0.12)' : 'rgba(59, 130, 246, 0.08)'} 1px, transparent 1px), linear-gradient(90deg, ${isDark ? 'rgba(59, 130, 246, 0.12)' : 'rgba(59, 130, 246, 0.08)'} 1px, transparent 1px)`, backgroundSize: '80px 80px', opacity: isDark ? 0.6 : 0.8, pointerEvents: 'none', zIndex: 1 }} />
        <FloatingParticles />
        <FloatingCodeElements />
      </Container>
      
      <Flex style={{ position: 'absolute', inset: 0, zIndex: 10 }}>
        {/* Left Panel */}
        <Box
          ref={leftPanelRef}
          w="100%"
          h="100%"
          style={{
            backdropFilter: isChatStarted ? 'blur(16px) saturate(120%)' : 'none',
            backgroundColor: isChatStarted ? (isDark ? 'rgba(10, 14, 26, 0.7)' : 'rgba(255, 255, 255, 0.7)') : 'transparent',
            transition: 'background-color 0.8s ease, backdrop-filter 0.8s ease',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {!isChatStarted && (
            <Center h="100%" style={{ transition: 'opacity 0.5s ease-out' }}>
              <Stack ref={landingContentRef} align="center" gap={40}>
                <Title ref={landingTitleRef} data-flip-id="mappy-title" order={1} style={{ fontSize: 'clamp(3rem, 10vw, 5.5rem)', fontFamily: 'var(--font-orbitron)', fontWeight: 900, background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #8b5cf6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', textAlign: 'center', letterSpacing: '0.02em' }}>
                  {'{ Mappy }'}
                </Title>
                <Text ref={landingTaglineRef} data-flip-id="mappy-tagline" size="xl" c={isDark ? "dimmed" : "gray.6"} ta="center" maw={600} style={{ fontSize: '1.4rem', lineHeight: 1.6, fontWeight: 400 }}>
                  RAG implementation on Esri ArcGIS Maps JS SDK Documentation.
                </Text>
                <Button ref={landingButtonRef} onClick={handleStartChat} size="xl" radius="xl" variant="gradient" gradient={{ from: '#3b82f6', to: '#06b6d4', deg: 135 }} style={{ padding: '16px 48px', fontSize: '1.2rem', fontWeight: 600, boxShadow: '0 8px 32px rgba(59, 130, 246, 0.4)' }}>
                  Start Conversation
                </Button>
                <Box ref={landingLinksRef} data-flip-id="mappy-links">
                  <Group gap="xs" mt="md">
                      <Anchor href="https://github.com/asing349" target="_blank" aria-label="GitHub"><ActionIcon variant="subtle" color="gray"><IconBrandGithub /></ActionIcon></Anchor>
                      <Anchor href="https://linkedin.com/in/itsmeajit" target="_blank" aria-label="LinkedIn"><ActionIcon variant="subtle" color="gray"><IconBrandLinkedin /></ActionIcon></Anchor>
                  </Group>
                </Box>
              </Stack>
            </Center>
          )}

          {isChatStarted && (
            <InfoPanel ref={infoPanelRef} titleRef={infoPanelTitleRef} taglineRef={infoPanelTaglineRef} linksRef={infoPanelLinksRef} />
          )}
        </Box>

        {/* Right Panel */}
        <Box ref={rightPanelRef} w="0%" h="100%" style={{ borderLeft: isChatStarted ? `1px solid ${isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(37, 99, 235, 0.2)'}` : 'none' }}>
          {isChatStarted && ( <ChatPanel ref={chatPanelRef} onClose={handleCloseChat} /> )}
        </Box>
      </Flex>
    </>
  );
}