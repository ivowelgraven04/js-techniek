// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import vercel from '@astrojs/vercel';

// https://astro.build/config
// Astro 5: pages prerender by default; opt-in to serverless via `export const prerender = false`
export default defineConfig({
  site: 'https://www.jschoutentechniek.com',
  integrations: [tailwind()],
  output: 'static',
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
