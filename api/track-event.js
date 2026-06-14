// Vercel serverless function: /api/track-event
// Ontvangt sendBeacon JSON-payloads en schrijft naar Supabase funnel_events.
// Resolves landing_page_id by slug — werkt voor alle LP's, niet alleen dakinspectie.

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const ALLOWED_EVENT_TYPES = new Set([
  'page_view', 'step_view', 'option_select',
  'submit_attempt', 'submit_success', 'submit_error',
  'form_focus', 'phone_click', 'whatsapp_click',
]);

// In-memory cache: slug → uuid (per cold-start lifetime, perf only)
const slugCache = new Map();

function sanitize(v, maxLen = 500) {
  if (typeof v !== 'string') return null;
  const t = v.trim().slice(0, maxLen).replace(/[\x00-\x1F\x7F]/g, '');
  return t || null;
}

function isUuid(v) {
  return typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
}

function normalizeSlug(raw) {
  if (typeof raw !== 'string') return null;
  return raw.trim().toLowerCase().replace(/^\/+|\/+$/g, '').split('/')[0] || null;
}

async function lookupLandingPageId(slug) {
  if (!slug) return null;
  if (slugCache.has(slug)) return slugCache.get(slug);
  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/landing_pages?select=id&slug=eq.${encodeURIComponent(slug)}&limit=1`,
      {
        headers: {
          'apikey': SUPABASE_SERVICE_ROLE_KEY,
          'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        },
      }
    );
    if (!res.ok) return null;
    const rows = await res.json();
    const id = Array.isArray(rows) && rows[0]?.id;
    if (id) { slugCache.set(slug, id); return id; }
  } catch (err) {
    console.error('[track-event] slug lookup failed:', err);
  }
  return null;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  let raw = req.body;
  if (typeof raw === 'string') {
    try { raw = JSON.parse(raw); } catch { raw = {}; }
  }
  raw = raw || {};

  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
    return res.status(200).json({ ok: true, warn: 'supabase not configured' });
  }

  const event_type = sanitize(raw.event_type, 24);
  const session_id = isUuid(raw.session_id) ? raw.session_id : null;
  if (!event_type || !ALLOWED_EVENT_TYPES.has(event_type) || !session_id) {
    return res.status(400).json({ error: 'invalid event' });
  }

  // Resolve landing_page_id via slug (preferred) of legacy env-var fallback
  let landing_page_id = null;
  const slug = normalizeSlug(raw.landing_page_slug);
  if (slug) landing_page_id = await lookupLandingPageId(slug);
  if (!landing_page_id) {
    // Legacy: oude dakinspectie env-var voor backward-compatibility
    landing_page_id = process.env.SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE || null;
  }
  if (!landing_page_id) {
    return res.status(400).json({ error: 'unknown landing page' });
  }

  const stepNum = typeof raw.step_number === 'number' ? Math.floor(raw.step_number) : null;
  const row = {
    session_id,
    landing_page_id,
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
