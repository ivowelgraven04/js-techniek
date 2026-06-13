// Vercel serverless function: /api/track-event
// Ontvangt sendBeacon JSON-payloads van de quiz-funnel en schrijft ze naar
// Supabase funnel_events. No-op (200) als Supabase env vars niet gezet zijn.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const LANDING_PAGE_ID = process.env.SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE;

const ALLOWED_EVENT_TYPES = new Set([
  'page_view', 'step_view', 'option_select',
  'submit_attempt', 'submit_success', 'submit_error',
]);

function sanitize(v, maxLen = 500) {
  if (typeof v !== 'string') return null;
  const t = v.trim().slice(0, maxLen).replace(/[\x00-\x1F\x7F]/g, '');
  return t || null;
}

function isUuid(v) {
  return typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  // sendBeacon stuurt vaak text/plain met JSON body — Vercel parsest dat niet automatisch.
  let raw = req.body;
  if (typeof raw === 'string') {
    try { raw = JSON.parse(raw); } catch { raw = {}; }
  }
  raw = raw || {};

  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !LANDING_PAGE_ID) {
    return res.status(200).json({ ok: true, warn: 'supabase not configured' });
  }

  const event_type = sanitize(raw.event_type, 24);
  const session_id = isUuid(raw.session_id) ? raw.session_id : null;
  if (!event_type || !ALLOWED_EVENT_TYPES.has(event_type) || !session_id) {
    return res.status(400).json({ error: 'invalid event' });
  }

  const stepNum = typeof raw.step_number === 'number' ? Math.floor(raw.step_number) : null;
  const row = {
    session_id,
    landing_page_id: LANDING_PAGE_ID,
    event_type,
    step_number: (stepNum != null && stepNum >= 1 && stepNum <= 10) ? stepNum : null,
    field_name:  sanitize(raw.field_name, 40),
    field_value: sanitize(raw.field_value, 100),
    user_agent:  sanitize(raw.user_agent, 500),
    utm_source:  sanitize(raw.utm_source, 80),
    utm_medium:  sanitize(raw.utm_medium, 80),
    utm_campaign:sanitize(raw.utm_campaign, 120),
    utm_content: sanitize(raw.utm_content, 120),
    utm_term:    sanitize(raw.utm_term, 120),
    gclid:       sanitize(raw.gclid, 200),
    referrer:    sanitize(raw.referrer, 500),
  };

  try {
    const upstream = await fetch(`${SUPABASE_URL}/rest/v1/funnel_events`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify(row),
    });
    if (!upstream.ok) {
      console.error('[track-event] supabase error:', upstream.status, await upstream.text().catch(() => ''));
      return res.status(502).json({ error: 'persist failed' });
    }
  } catch (err) {
    console.error('[track-event] supabase fetch failed:', err);
    return res.status(502).json({ error: 'persist failed' });
  }

  return res.status(204).end();
}
