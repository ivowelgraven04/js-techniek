// Vercel serverless function: /api/submit-quote
// Accepts both form shapes:
//   - Google Ads LPs (/plat-dak-vervangen, /lekkage-spoed): naam + telefoon + postcode + type_werk
//   - Dakinspectie quiz (/gratis-dakinspectie): naam + telefoon + email + situatie + eigenaar
//   - Plat-dak-probleem quiz (/plat-dak-probleem): naam + telefoon + postcode + situatie
//     + eigenaar + termijn + bereikbaar (+ optioneel email). Server bepaalt de
//     kwalificatie opnieuw en stuurt bij 'gekwalificeerd' een Lead naar de Meta CAPI.
// Posts validated payload to Zapier (env var ZAPIER_WEBHOOK_URL). Node 18+.

import { sendMetaEvent } from './_lib/meta-capi.js';
import {
  bepaalKwalificatie, PROBLEEM_WAARDEN, TERMIJN_WAARDEN, BEREIKBAAR_WAARDEN,
} from './_lib/plat-dak-probleem.js';

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

  // Extra velden alleen voor /plat-dak-probleem (andere flows blijven ongewijzigd)
  const bronSlug = payload.bron_pagina.replace(/^\/+|\/+$/g, '').split('/')[0];
  const isPlatDakProbleemFlow = bronSlug === 'plat-dak-probleem';
  let meta = null;
  if (isPlatDakProbleemFlow) {
    payload.termijn = sanitize(body.termijn, 20);
    payload.bereikbaar = sanitize(body.bereikbaar, 20);
    payload.kwalificatie = sanitize(body.kwalificatie, 20);
    payload.event_id = sanitize(body.event_id, 80);
    meta = {
      fbp: sanitize(body.fbp, 200),
      fbc: sanitize(body.fbc, 300),
      event_source_url: sanitize(body.event_source_url, 500),
    };
  }

  for (const field of ALWAYS_REQUIRED) {
    if (!payload[field]) {
      return res.status(400).json({ error: `Veld ontbreekt: ${field}` });
    }
  }

  // Welke flow: plat-dak-probleem, dakinspectie (situatie+eigenaar+email) of Google-Ads (postcode+type_werk)?
  const isDakinspectieFlow = !isPlatDakProbleemFlow && !!(payload.situatie || payload.eigenaar || payload.email);
  if (isPlatDakProbleemFlow) {
    if (!payload.postcode) return res.status(400).json({ error: 'Veld ontbreekt: postcode' });
    if (!PROBLEEM_WAARDEN.includes(payload.situatie)) return res.status(400).json({ error: 'Veld ontbreekt: situatie' });
    if (!payload.eigenaar) return res.status(400).json({ error: 'Veld ontbreekt: eigenaar' });
    if (!TERMIJN_WAARDEN.includes(payload.termijn)) return res.status(400).json({ error: 'Veld ontbreekt: termijn' });
    if (!BEREIKBAAR_WAARDEN.includes(payload.bereikbaar)) return res.status(400).json({ error: 'Veld ontbreekt: bereikbaar' });
  } else if (isDakinspectieFlow) {
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

  if (isPlatDakProbleemFlow) {
    // Server is leidend: huurder of buiten werkgebied wordt geen lead,
    // en de browser kan zichzelf niet "gekwalificeerd" maken.
    const kwalificatie = bepaalKwalificatie(payload);
    if (!kwalificatie) {
      return res.status(422).json({ error: 'Deze aanvraag valt buiten ons werkgebied of is voor een huurwoning' });
    }
    payload.kwalificatie = kwalificatie;
    // Zichtbaar in bestaande Zapier-mail en Sheet zonder de Zap aan te passen
    payload.type_werk = payload.type_werk || payload.situatie;
    const samenvatting = `Termijn: ${payload.termijn} | Bereikbaar: ${payload.bereikbaar} | Kwalificatie: ${kwalificatie}`;
    payload.opmerking = payload.opmerking ? `${payload.opmerking}\n${samenvatting}` : samenvatting;
  }

  // Interne tags voor Zapier-routing
  const tags = [];
  if (payload.eigenaar === 'nee') tags.push('huurder');
  if (payload.situatie === 'lekkage' || payload.situatie === 'lekt_nu') tags.push('spoed-kandidaat');
  if (isPlatDakProbleemFlow) {
    tags.push(payload.kwalificatie, `termijn:${payload.termijn}`, `bereikbaar:${payload.bereikbaar}`);
  }
  if (tags.length) payload.tags = tags.join(',');

  // Best-effort: óók in Supabase leads-tabel schrijven.
  // Landing-page-id wordt afgeleid van bron_pagina (slug-lookup); werkt voor alle LP's.
  if (SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY && payload.bron_pagina) {
    try {
      const slug = String(payload.bron_pagina).trim().replace(/^\/+|\/+$/g, '').split('/')[0] || null;
      let landing_page_id = null;
      if (slug) {
        const lpRes = await fetch(
          `${SUPABASE_URL}/rest/v1/landing_pages?select=id&slug=eq.${encodeURIComponent(slug)}&limit=1`,
          { headers: { 'apikey': SUPABASE_SERVICE_ROLE_KEY, 'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}` } }
        );
        if (lpRes.ok) {
          const rows = await lpRes.json();
          if (Array.isArray(rows) && rows[0]?.id) landing_page_id = rows[0].id;
        }
      }
      // Legacy fallback: env-var
      if (!landing_page_id && SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE && slug === 'gratis-dakinspectie') {
        landing_page_id = SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE;
      }
      if (landing_page_id) {
        const leadRow = {
          session_id: payload.session_id || null,
          landing_page_id,
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
      } else {
        console.warn('[submit-quote] No landing_page_id resolved for bron_pagina:', payload.bron_pagina);
      }
    } catch (err) {
      console.error('[submit-quote] Supabase write threw:', err);
    }
  }

  if (!ZAPIER_WEBHOOK_URL) {
    console.error('[submit-quote] ZAPIER_WEBHOOK_URL niet geconfigureerd. Payload:', payload);
    const capi = await sendPlatDakLead(req, payload, meta);
    return res.status(200).json(isPlatDakProbleemFlow
      ? { ok: true, warn: 'webhook not configured', kwalificatie: payload.kwalificatie, capi }
      : { ok: true, warn: 'webhook not configured' });
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

  const capi = await sendPlatDakLead(req, payload, meta);
  return res.status(200).json(isPlatDakProbleemFlow ? { ok: true, kwalificatie: payload.kwalificatie, capi } : { ok: true });
}

// Meta CAPI: alleen voor /plat-dak-probleem en alleen bij 'gekwalificeerd'.
// Zelfde event_id als de browser-pixel, zodat Meta dedupliceert.
async function sendPlatDakLead(req, payload, meta) {
  if (!meta || payload.kwalificatie !== 'gekwalificeerd' || !payload.event_id) return 'skipped';
  try {
    const r = await sendMetaEvent({
      eventName: 'Lead',
      eventId: payload.event_id,
      eventSourceUrl: meta.event_source_url || 'https://www.jschoutentechniek.com/plat-dak-probleem',
      req,
      user: {
        telefoon: payload.telefoon,
        email: payload.email,
        naam: payload.naam,
        postcode: payload.postcode,
        externalId: payload.session_id,
        fbp: meta.fbp,
        fbc: meta.fbc,
      },
      customData: {
        content_name: 'Plat dak probleem',
        content_category: payload.situatie,
        lead_type: payload.termijn,
      },
    });
    return r.sent ? 'sent' : r.reason;
  } catch (err) {
    console.error('[submit-quote] CAPI threw:', err);
    return 'error';
  }
}
