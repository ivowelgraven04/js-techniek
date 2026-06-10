// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel/serverless';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.jschoutentechniek.com',
  integrations: [tailwind()],
  output: 'hybrid', // Static pages by default, API route uses serverless
  adapter: vercel({
    webAnalytics: { enabled: false },
    maxDuration: 10,
  }),
  image: {
    domains: [],
  },
  build: {
    inlineStylesheets: 'auto',
  },
});
