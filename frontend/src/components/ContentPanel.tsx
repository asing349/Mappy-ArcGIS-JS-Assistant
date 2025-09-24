'use client';

import { Box, Center, Text, useMantineColorScheme } from '@mantine/core';
import { IconBox } from '@tabler/icons-react';

// A generic placeholder for the main content area.
const ContentPanel = () => {
  const { colorScheme } = useMantineColorScheme();

  return (
    <Box
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: colorScheme === 'dark' ? '#1A1B1E' : '#F1F3F5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Center>
        <div style={{ textAlign: 'center' }}>
          <IconBox size={48} stroke={1.5} style={{ color: '#909296' }}/>
          <Text c="dimmed" mt="md">
            Main Content Area
          </Text>
        </div>
      </Center>
    </Box>
  );
};

export default ContentPanel;