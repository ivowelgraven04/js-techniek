# jschoutentechniek.com | Landingspagina's

Astro + Tailwind website met twee landingspagina's voor de Google Ads-campagne van JS Techniek.

- `/lekkage-spoed`: Ad Group 1 (Lekkage & Spoed), **telefoon-first** CTA
- `/plat-dak-vervangen`: Ad Group 2 (Plat Dak) + Ad Group 3 (Bitumen/Zink-Lood), **formulier-first** CTA
- `/`: homepage met 2 keuzeblokken
- `/bedankt`: bedankpagina na form-submit (fires Google Ads conversion pixel)
- `/privacy`: privacyverklaring

Deploy: **GitHub → Vercel → jschoutentechniek.com**

---

## Lokaal draaien

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # productie-build naar .vercel/output/
npm run preview  # serve de build lokaal
```

Node ≥ 18 vereist (Vercel zelf draait op Node 18). Lokaal werkt elke recente versie.

---

## Project-structuur

```
src/
├── data/site.ts                  # Single source of truth: bedrijfsgegevens, testimonials, FAQ's, serviceregio
├── layouts/BaseLayout.astro      # <head>, SEO meta, fonts, GA4 tag
├── components/
│   ├── TopBar.astro              # Sticky desktop nav met telefoon + WhatsApp + primaire CTA
│   ├── HeroSplit.astro           # Generieke split-hero (tekst links + foto rechts)
│   ├── UspStrip.astro            # 3-koloms USP-strip met SVG iconen
│   ├── EmergencyBlock.astro      # LEKKAGE-LP: 24/7 belofte + grote belknop
│   ├── ServiceList.astro         # PLAT-DAK-LP: 8 diensten in grid
│   ├── QuoteForm.astro           # PLAT-DAK-LP: offerteformulier → /api/submit-quote
│   ├── TestimonialGrid.astro     # 3 quotes met sterren-badges
│   ├── ServiceAreaBlock.astro    # 26 NH-steden, gesplitst tier 1/2
│   ├── FaqAccordion.astro        # Native <details>/<summary>: geen JS
│   ├── CtaBlock.astro            # Full-width CTA-blok
│   ├── StickyMobileCta.astro     # FAB-knop (phone of form variant) mobiel-only
│   └── Footer.astro              # KvK, contact, navigatie
└── pages/
    ├── index.astro
    ├── lekkage-spoed.astro
    ├── plat-dak-vervangen.astro
    ├── bedankt.astro
    ├── privacy.astro
    └── api/
        └── submit-quote.ts       # Serverless endpoint → Zapier webhook
```

**Foto's** komen uit `../raw/raw_photo/25-05-2026/` en zijn gekopieerd naar `src/assets/images/`. Astro genereert automatisch responsive WebP-varianten tijdens build.

---

## Configuratie: Environment variables

Maak een `.env` (gitignored, lokaal) of stel ze in via **Vercel dashboard → Project → Settings → Environment Variables**:

| Variabele | Doel | Voorbeeld |
|---|---|---|
| `ZAPIER_WEBHOOK_URL` | Server-side webhook waar form-submits heen gaan | `https://hooks.zapier.com/hooks/catch/12345/abcdef/` |
| `PUBLIC_GA4_MEASUREMENT_ID` | Google Analytics 4: laadt alleen als gezet | `G-XXXXXXXXXX` |
| `PUBLIC_GOOGLE_ADS_CONVERSION_ID` | Google Ads conversie-tracking | `AW-XXXXXXXXXX` |
| `PUBLIC_GOOGLE_ADS_CONVERSION_LABEL` | Conversie-label voor /bedankt event | `xxxXXXxxXXX` |

> **Veiligheid:** `PUBLIC_`-prefix variabelen zijn bedoeld voor client-side gebruik. `ZAPIER_WEBHOOK_URL` heeft géén prefix en wordt alleen server-side gelezen: komt nooit in de browser.

---

## Zapier-webhook opzetten

1. Login op [zapier.com](https://zapier.com) → **Create Zap**
2. **Trigger:** "Webhooks by Zapier" → "Catch Hook" → kopieer de webhook-URL
3. Zet deze URL als `ZAPIER_WEBHOOK_URL` in Vercel
4. **Action 1: Email:**
   - App: Gmail / Outlook / Email by Zapier
   - To: `info@jschoutentechniek.com`
   - Subject: `Nieuwe aanvraag van {{naam}} ({{postcode}})`
   - Body: Sjabloon met alle velden uit de payload (zie `src/pages/api/submit-quote.ts` voor structuur)
5. **Action 2: Google Sheet:**
   - App: Google Sheets → "Create Spreadsheet Row"
   - Sheet: maak in Drive "JS Techniek - Lead Tracker" met kolommen: `timestamp, naam, telefoon, postcode, type_werk, opmerking, bron_pagina, utm_source, utm_campaign, gclid`
6. **Action 3 (optioneel): WhatsApp/Slack notificatie** naar Jonathan
7. Test de Zap met een dummy webhook-aanroep
8. Activeer

**Payload-structuur** die Zapier ontvangt:

```json
{
  "naam": "Jan Jansen",
  "telefoon": "0612345678",
  "postcode": "1781 AB",
  "type_werk": "vervangen",
  "opmerking": "...",
  "bron_pagina": "/plat-dak-vervangen",
  "timestamp": "2026-06-10T14:23:11.000Z",
  "user_agent": "Mozilla/5.0 ...",
  "utm_source": "google",
  "utm_medium": "cpc",
  "utm_campaign": "JSTechniek-Search-2026Q3",
  "utm_content": "...",
  "utm_term": "...",
  "gclid": "..."
}
```

---

## Deployen naar Vercel

### Eenmalig (eerste deploy)

1. Push deze folder naar een **nieuwe GitHub-repo** (alleen de `website/` content, niet de parent JS-Techniek folder):
   ```bash
   cd website/
   git init
   git add .
   git commit -m "Initial: JS Techniek LP's"
   gh repo create jschoutentechniek-website --private --source=. --push
   ```

2. Ga naar [vercel.com/new](https://vercel.com/new) → **Import Git Repository** → kies `jschoutentechniek-website`
3. Framework Preset: **Astro** (auto-detect)
4. Root directory: `./` (laat staan)
5. Build command: `npm run build` (auto)
6. Output directory: `dist` (auto)
7. **Environment Variables**: voeg de 4 vars hierboven toe
8. Klik **Deploy**

### Domain koppelen

1. Vercel project → **Settings → Domains** → voeg `jschoutentechniek.com` + `www.jschoutentechniek.com` toe
2. Vercel toont DNS-records die je moet zetten bij je domain-registrar:
   - **A-record** `@` → `76.76.21.21`
   - **CNAME** `www` → `cname.vercel-dns.com`
3. Wacht ~10 min op DNS propagation. SSL-certificaat wordt automatisch geregeld door Vercel.
4. Test: `https://www.jschoutentechniek.com/lekkage-spoed` moet werken.

### Automatische deploys

Elke `git push` naar main = automatische deploy. PR's krijgen preview-URLs.

---

## Brand-systeem

Kleuren staan in `tailwind.config.mjs`:

```js
brand: {
  'blue-900': '#001060',   // deep: footer, dark blocks
  'blue-700': '#104080',   // primary CTA, headlines
  'blue-500': '#1a4382',   // secondary fills
  'blue-50':  '#eef3fb',   // light backgrounds
  'yellow-500': '#FFCE22', // accent, CTA hover, badges
  'yellow-600': '#f0c020', // yellow-on-dark
  'ink':    '#0a1733',     // body text
  'paper':  '#f8f9fb',     // page background
}
```

Lettertype: **Inter** via rsms.me CDN (preconnect + stylesheet in `BaseLayout.astro`).

---

## Content updaten

Veel content is gecentraliseerd in `src/data/site.ts`:

- **Bedrijfsgegevens:** `company` object (telefoon, KvK, e-mail, garantie-termijn)
- **Werkgebied steden:** `serviceArea.tier1` + `tier2`
- **Testimonials:** `testimonialsLekkage` + `testimonialsPlatDak` arrays
- **FAQ's:** `faqLekkage` + `faqPlatDak` arrays
- **SEO meta:** `seo.lekkage` + `seo.platDak`

Update daar één keer → propagatie over beide LP's.

**TODO (door klant te leveren):**
- 3-5 echte Google Review quotes vervangen voor de placeholders
- KvK-nummer verifiëren (`70974306`?)
- E-mailadres voor form-submits bevestigen (`info@jschoutentechniek.com`?)
- Garantie-termijnen verifiëren (10 jaar bitumen, 5 jaar zink/lood)
- Reactietijd-belofte lekkage-LP (30 min terugbellen?)

---

## SEO & Performance

- **Pre-rendered HTML** voor alle public pages: geen JS nodig om content te zien
- **Astro Image** maakt automatisch responsive WebP-varianten (originele 691KB → 42-202KB)
- **Inline critical CSS** via Astro's `inlineStylesheets: 'auto'`
- **Inter via preconnect** voor snellere font-load
- **Native HTML accordion** (`<details>/<summary>`): geen JS-library
- **Lighthouse-target:** Performance 95+, Accessibility 100, SEO 100

---

## Verificatie checklist

Na deploy, controleer:

- [ ] `https://www.jschoutentechniek.com/` → 200, toont 2 keuzeblokken
- [ ] `/lekkage-spoed` → 200, hero + sticky FAB op mobiel
- [ ] `/plat-dak-vervangen` → 200, hero + offerteformulier
- [ ] `/bedankt` → 200, conversie-pixel firet (test met Google Tag Assistant)
- [ ] Telefoonlink op desktop opent `tel:+31612602082`
- [ ] WhatsApp-link opent `wa.me/31612602082`
- [ ] Form-submit op `/plat-dak-vervangen` → 200 van API → redirect naar `/bedankt`
- [ ] Zapier ontvangt webhook → email arriveert → Sheet rij wordt aangemaakt
- [ ] Lighthouse mobiel: Performance 95+, Accessibility 100
- [ ] OG-image laadt correct op LinkedIn/WhatsApp share-preview
- [ ] Google Search Console + Bing Webmaster Tools verifieerd

---

## Bekende beperkingen v1

- **Geen voor-na blok** (foto-inventaris beperkt: toevoegen in v2 na fotoshoot)
- **Statische testimonials** (geen live Google Reviews via Places API: v2 optie)
- **Geen cookie-banner** (GA4 staat op anonymize_ip; juridisch advies voor of we banner nodig hebben)
- **Geen A/B-test infrastructuur** (na 30 dagen data bouwen)
- **Geen blog/SEO-content pagina's** (los project)

Voor v2-roadmap, zie het plan-bestand in `~/.claude/plans/ok-wat-we-nu-shiny-mist.md`.
