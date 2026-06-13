import type { APIRoute } from 'astro';

export const prerender = false;

// Env-vars (alleen aanwezig zodra Welgraven-Dashboards Supabase project is gekoppeld)
const SUPABASE_URL = import.meta.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = import.meta.env.SUPABASE_SERVICE_ROLE_KEY;
const LANDING_PAGE_ID = import.meta.env.SUPABASE_LANDING_PAGE_ID_DAKINSPECTIE;

const ALLOWED_EVENT_TYPES = new Set([
  'page_view', 'step_view', 'option_select',
  'submit_attempt', 'submit_success', 'submit_error',
]);

function sanitize(v: unknown, maxLen = 500): string | null {
  if (typeof v !== 'string') return null;
  const trimmed = v.trim().slice(0, maxLen).replace(/[\x00-\x1F\x7F]/g, '');
  return trimmed || null;
}

function isUuid(v: unknown): boolean {
  return typeof v === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
}

async function readBody(request: Request): Promise<Record<string, unknown>> {
  const ct = request.headers.get('content-type') ?? '';
  if (ct.includes('application/json')) return await request.json();
  // sendBeacon stuurt vaak text/plain met JSON body
  const text = await request.text();
  try { return JSON.parse(text); } catch { return {}; }
}

export const POST: APIRoute = async ({ request }) => {
  // No-op als Supabase nog niet is geconfigureerd — beacon-call faalt nooit
  if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !LANDING_PAGE_ID) {
    return new Response(JSON.stringify({ ok: true, warn: 'supabase not configured' }), { status: 200 });
  }

  let raw: Record<string, unknown>;
  try { raw = await readBody(request); } catch {
    return new Response(JSON.stringify({ error: 'invalid body' }), { status: 400 });
  }

  const event_type = sanitize(raw.event_type, 24);
  const session_id = isUuid(raw.session_id) ? raw.session_id as string : null;
  if (!event_type || !ALLOWED_EVENT_TYPES.has(event_type) || !session_id) {
    return new Response(JSON.stringify({ error: 'invalid event' }), { status: 400 });
  }

  const stepNum = typeof raw.step_number === 'number' ? Math.floor(raw.step_number) : null;
  const payload = {
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
    const res = await fetch(`${SUPABASE_URL}/rest/v1/funnel_events`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      console.error('[track-event] supabase error:', res.status, text);
      return new Response(JSON.stringify({ error: 'persist failed' }), { status: 502 });
    }
  } catch (err) {
    console.error('[track-event] supabase fetch failed:', err);
    return new Response(JSON.stringify({ error: 'persist failed' }), { status: 502 });
  }

  return new Response(null, { status: 204 });
};

export const GET: APIRoute = () => new Response('Method Not Allowed', { status: 405 });
