import type { APIRoute } from 'astro';

export const prerender = false; // dynamic — moet als serverless API draaien

const ZAPIER_WEBHOOK_URL = import.meta.env.ZAPIER_WEBHOOK_URL;
const SUPABASE_URL = import.meta.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = import.meta.env.SUPABASE_SERVICE_ROLE_KEY;
const SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE = import.meta.env.SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE;

interface QuotePayload {
  naam: string;
  telefoon: string;
  email?: string;
  postcode?: string;
  type_werk?: string;
  situatie?: string;
  eigenaar?: string;
  opmerking?: string;
  bron_pagina: string;
  session_id?: string;
  tags?: string;
  timestamp?: string;
  user_agent?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  gclid?: string;
}

const ALWAYS_REQUIRED: Array<keyof QuotePayload> = ['naam', 'telefoon', 'bron_pagina'];

function isRateLimited(_ip: string): boolean {
  // Edge serverless heeft geen persistent state — Zapier doet zelf dedup/throttle indien nodig.
  return false;
}

function sanitize(v: unknown, maxLen = 1000): string {
  if (typeof v !== 'string') return '';
  return v.trim().slice(0, maxLen).replace(/[\x00-\x1F\x7F]/g, '');
}

async function readBody(request: Request): Promise<Record<string, unknown>> {
  const contentType = request.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return await request.json();
  }
  const form = await request.formData();
  const out: Record<string, unknown> = {};
  form.forEach((v, k) => { out[k] = v; });
  return out;
}

export const POST: APIRoute = async ({ request, clientAddress }) => {
  if (isRateLimited(clientAddress)) {
    return new Response(JSON.stringify({ error: 'Te veel aanvragen' }), { status: 429 });
  }

  let raw: Record<string, unknown>;
  try {
    raw = await readBody(request);
  } catch {
    return new Response(JSON.stringify({ error: 'Ongeldige aanvraag' }), { status: 400 });
  }

  // Honeypot check — als bot het invult, doen alsof het OK ging maar niets doorzetten
  const honeypot = sanitize(raw.company_url);
  if (honeypot) {
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }

  const payload: QuotePayload = {
    naam: sanitize(raw.naam, 120),
    telefoon: sanitize(raw.telefoon, 40),
    email: sanitize(raw.email, 160),
    postcode: sanitize(raw.postcode, 12).toUpperCase().replace(/\s+/g, ' '),
    type_werk: sanitize(raw.type_werk, 40),
    situatie: sanitize(raw.situatie, 40),
    eigenaar: sanitize(raw.eigenaar, 8),
    opmerking: sanitize(raw.opmerking, 4000),
    bron_pagina: sanitize(raw.bron_pagina, 200),
    session_id: sanitize(raw.session_id, 80),
    timestamp: sanitize(raw.timestamp, 40) || new Date().toISOString(),
    user_agent: sanitize(raw.user_agent, 500),
    utm_source: sanitize(raw.utm_source, 80),
    utm_medium: sanitize(raw.utm_medium, 80),
    utm_campaign: sanitize(raw.utm_campaign, 120),
    utm_content: sanitize(raw.utm_content, 120),
    utm_term: sanitize(raw.utm_term, 120),
    gclid: sanitize(raw.gclid, 200),
  };

  // Verplichte velden voor alle aanvragen
  for (const field of ALWAYS_REQUIRED) {
    if (!payload[field]) {
      return new Response(JSON.stringify({ error: `Veld ontbreekt: ${field}` }), { status: 400 });
    }
  }

  // Per form-shape extra verplicht
  const isDakinspectieFlow = !!payload.situatie || !!payload.eigenaar || !!payload.email;
  if (isDakinspectieFlow) {
    if (!payload.email)    return new Response(JSON.stringify({ error: 'Veld ontbreekt: email' }), { status: 400 });
    if (!payload.situatie) return new Response(JSON.stringify({ error: 'Veld ontbreekt: situatie' }), { status: 400 });
    if (!payload.eigenaar) return new Response(JSON.stringify({ error: 'Veld ontbreekt: eigenaar' }), { status: 400 });
  } else {
    // Originele Google-Ads flow heeft postcode + type_werk nodig
    if (!payload.postcode)  return new Response(JSON.stringify({ error: 'Veld ontbreekt: postcode' }), { status: 400 });
    if (!payload.type_werk) return new Response(JSON.stringify({ error: 'Veld ontbreekt: type_werk' }), { status: 400 });
  }

  // Telefoon: minstens 8 cijfers
  const digits = payload.telefoon.replace(/\D/g, '');
  if (digits.length < 8) {
    return new Response(JSON.stringify({ error: 'Telefoonnummer lijkt niet te kloppen' }), { status: 400 });
  }

  // E-mail (alleen valideren als meegestuurd)
  if (payload.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
    return new Response(JSON.stringify({ error: 'E-mailadres lijkt niet te kloppen' }), { status: 400 });
  }

  // Postcode NL-formaat (alleen valideren als meegestuurd)
  if (payload.postcode && !/^\d{4}\s?[A-Z]{2}$/.test(payload.postcode)) {
    return new Response(JSON.stringify({ error: 'Postcode lijkt niet te kloppen' }), { status: 400 });
  }

  // Interne tags voor Zapier-routing
  const tags: string[] = [];
  if (payload.eigenaar === 'nee') tags.push('huurder');
  if (payload.situatie === 'lekkage') tags.push('spoed-kandidaat');
  if (tags.length) payload.tags = tags.join(',');

  // Best-effort: ook in Supabase leads-tabel schrijven (geen blocker voor Zapier)
  if (SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY && SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE && payload.bron_pagina === '/gratis-dakinspectie') {
    try {
      const leadRow = {
        session_id: payload.session_id || null,
        landing_page_id: SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE,
        naam: payload.naam,
        telefoon: payload.telefoon,
        email: payload.email || null,
        opmerking: payload.opmerking || null,
        situatie: payload.situatie || null,
        eigenaar: payload.eigenaar || null,
        postcode: payload.postcode || null,
        type_werk: payload.type_werk || null,
        tags: payload.tags || null,
        user_agent: payload.user_agent || null,
        utm_source: payload.utm_source || null,
        utm_medium: payload.utm_medium || null,
        utm_campaign: payload.utm_campaign || null,
        utm_content: payload.utm_content || null,
        utm_term: payload.utm_term || null,
        gclid: payload.gclid || null,
      };
      // Geen await op de promise zou crash betekenen — wel await maar in try/catch
      const supaRes = await fetch(`${SUPABASE_URL}/rest/v1/leads`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify(leadRow),
      });
      if (!supaRes.ok) {
        console.error('[submit-quote] Supabase lead insert failed:', supaRes.status, await supaRes.text().catch(() => ''));
      }
    } catch (err) {
      console.error('[submit-quote] Supabase write threw:', err);
    }
  }

  // Zapier-webhook URL niet geconfigureerd → log + fail-soft
  if (!ZAPIER_WEBHOOK_URL) {
    console.error('[submit-quote] ZAPIER_WEBHOOK_URL niet geconfigureerd. Payload:', payload);
    return new Response(JSON.stringify({ ok: true, warn: 'webhook not configured' }), { status: 200 });
  }

  try {
    const res = await fetch(ZAPIER_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      console.error('[submit-quote] Zapier error:', res.status, await res.text().catch(() => '(geen body)'));
      return new Response(JSON.stringify({ error: 'Doorgeven aan systeem mislukte' }), { status: 502 });
    }
  } catch (err) {
    console.error('[submit-quote] Zapier fetch failed:', err);
    return new Response(JSON.stringify({ error: 'Doorgeven aan systeem mislukte' }), { status: 502 });
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};

export const GET: APIRoute = () => {
  return new Response('Method Not Allowed', { status: 405 });
};
