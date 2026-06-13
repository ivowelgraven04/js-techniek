// Vercel serverless function: /api/submit-quote
// Accepts both form shapes:
//   - Google Ads LPs (/plat-dak-vervangen, /lekkage-spoed): naam + telefoon + postcode + type_werk
//   - Dakinspectie quiz (/gratis-dakinspectie): naam + telefoon + email + situatie + eigenaar
// Posts validated payload to Zapier (env var ZAPIER_WEBHOOK_URL). Node 18+.

const ZAPIER_WEBHOOK_URL = process.env.ZAPIER_WEBHOOK_URL;
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE = process.env.SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE;

const ALWAYS_REQUIRED = ['naam', 'telefoon', 'bron_pagina'];

function sanitize(v, maxLen = 1000) {
  if (typeof v !== 'string') return '';
  return v.trim().slice(0, maxLen).replace(/[\x00-\x1F\x7F]/g, '');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // Vercel parseert application/json automatisch
  const body = req.body || {};

  // Honeypot: bots vullen dit veld, mensen niet. Fake-OK retourneren.
  if (sanitize(body.company_url)) {
    return res.status(200).json({ ok: true });
  }

  const payload = {
    naam: sanitize(body.naam, 120),
    telefoon: sanitize(body.telefoon, 40),
    email: sanitize(body.email, 160),
    postcode: sanitize(body.postcode, 12).toUpperCase().replace(/\s+/g, ' '),
    type_werk: sanitize(body.type_werk, 40),
    situatie: sanitize(body.situatie, 40),
    eigenaar: sanitize(body.eigenaar, 8),
    opmerking: sanitize(body.opmerking, 4000),
    bron_pagina: sanitize(body.bron_pagina, 200),
    session_id: sanitize(body.session_id, 80),
    timestamp: sanitize(body.timestamp, 40) || new Date().toISOString(),
    user_agent: sanitize(body.user_agent, 500),
    utm_source: sanitize(body.utm_source, 80),
    utm_medium: sanitize(body.utm_medium, 80),
    utm_campaign: sanitize(body.utm_campaign, 120),
    utm_content: sanitize(body.utm_content, 120),
    utm_term: sanitize(body.utm_term, 120),
    gclid: sanitize(body.gclid, 200),
  };

  for (const field of ALWAYS_REQUIRED) {
    if (!payload[field]) {
      return res.status(400).json({ error: `Veld ontbreekt: ${field}` });
    }
  }

  // Welke flow: dakinspectie (situatie+eigenaar+email) of Google-Ads (postcode+type_werk)?
  const isDakinspectieFlow = !!(payload.situatie || payload.eigenaar || payload.email);
  if (isDakinspectieFlow) {
    if (!payload.email)    return res.status(400).json({ error: 'Veld ontbreekt: email' });
    if (!payload.situatie) return res.status(400).json({ error: 'Veld ontbreekt: situatie' });
    if (!payload.eigenaar) return res.status(400).json({ error: 'Veld ontbreekt: eigenaar' });
  } else {
    if (!payload.postcode)  return res.status(400).json({ error: 'Veld ontbreekt: postcode' });
    if (!payload.type_werk) return res.status(400).json({ error: 'Veld ontbreekt: type_werk' });
  }

  const digits = payload.telefoon.replace(/\D/g, '');
  if (digits.length < 8) {
    return res.status(400).json({ error: 'Telefoonnummer lijkt niet te kloppen' });
  }

  if (payload.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
    return res.status(400).json({ error: 'E-mailadres lijkt niet te kloppen' });
  }

  if (payload.postcode && !/^\d{4}\s?[A-Z]{2}$/.test(payload.postcode)) {
    return res.status(400).json({ error: 'Postcode lijkt niet te kloppen' });
  }

  // Interne tags voor Zapier-routing
  const tags = [];
  if (payload.eigenaar === 'nee') tags.push('huurder');
  if (payload.situatie === 'lekkage') tags.push('spoed-kandidaat');
  if (tags.length) payload.tags = tags.join(',');

  // Best-effort: ook in Supabase leads-tabel schrijven
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

  if (!ZAPIER_WEBHOOK_URL) {
    console.error('[submit-quote] ZAPIER_WEBHOOK_URL niet geconfigureerd. Payload:', payload);
    return res.status(200).json({ ok: true, warn: 'webhook not configured' });
  }

  try {
    const upstream = await fetch(ZAPIER_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!upstream.ok) {
      const text = await upstream.text().catch(() => '(geen body)');
      console.error('[submit-quote] Zapier error:', upstream.status, text);
      return res.status(502).json({ error: 'Doorgeven aan systeem mislukte' });
    }
  } catch (err) {
    console.error('[submit-quote] Zapier fetch failed:', err);
    return res.status(502).json({ error: 'Doorgeven aan systeem mislukte' });
  }

  return res.status(200).json({ ok: true });
}
