import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/**',
        'convex/_generated/**',
        'tests/**',
        '*.config.js',
        'research/**',
        'memory/**',
        'deployment/**',
      ],
    },
  },
});
