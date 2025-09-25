'use client';

import { Box, Title, Text, Group, Anchor, Divider, ActionIcon } from '@mantine/core';
import { IconBrandGithub, IconBrandLinkedin } from '@tabler/icons-react';
import React from 'react';

type InfoPanelProps = {
  titleRef: React.Ref<HTMLHeadingElement>;
  taglineRef: React.Ref<HTMLParagraphElement>;
  linksRef: React.Ref<HTMLDivElement>;
};

const InfoPanel = React.forwardRef<HTMLDivElement, InfoPanelProps>(
  ({ titleRef, taglineRef, linksRef }, ref) => {
    return (
      <Box ref={ref} p="xl" h="100vh" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <Box style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', textAlign: 'center' }}>
          <Title
            ref={titleRef}
            data-flip-id="mappy-title"
            order={2}
            style={{
              fontFamily: 'var(--font-orbitron)',
              fontWeight: 900,
              fontSize: '2.5rem',
              background: 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            {'{ Mappy }'}
          </Title>
          <Text ref={taglineRef} data-flip-id="mappy-tagline" c="dimmed" size="sm" mt={4}>
            Esri ArcGIS Maps JS SDK...
          </Text>
        </Box>

        <Box ref={linksRef} data-flip-id="mappy-links">
          <Divider mb="md" />
          <Group justify="space-between" align="center">
            <Text size="sm" c="dimmed">Developed By Ajit Singh</Text>
            <Group gap="xs">
              <Anchor href="https://github.com/asing349" target="_blank" aria-label="GitHub">
                <ActionIcon variant="subtle" color="gray"><IconBrandGithub /></ActionIcon>
              </Anchor>
              <Anchor href="https://linkedin.com/in/itsmeajit" target="_blank" aria-label="LinkedIn">
                <ActionIcon variant="subtle" color="gray"><IconBrandLinkedin /></ActionIcon>
              </Anchor>
            </Group>
          </Group>
        </Box>
      </Box>
    );
  }
);

InfoPanel.displayName = 'InfoPanel';
export default InfoPanel;