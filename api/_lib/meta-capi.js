// Meta Conversions API (server-side) voor JS Techniek.
// Geen eigen route: bestanden onder api/_lib worden door Vercel niet als
// functie gepubliceerd. submit-quote.js roept sendMetaEvent() aan nadat een
// aanvraag is gevalideerd, zodat niemand rechtstreeks nep-Leads naar Meta
// kan sturen.
//
// Env:
//   META_CAPI_TOKEN        verplicht; ontbreekt hij, dan wordt stil overgeslagen
//   META_TEST_EVENT_CODE   optioneel; voor de "Test events"-tab in Events Manager
//   META_PIXEL_ID          optioneel; standaard 3056730661197575

import { createHash } from 'node:crypto';

const DEFAULT_PIXEL_ID = '3056730661197575';
const GRAPH_VERSION = 'v21.0';

function sha256(v) {
  return createHash('sha256').update(v, 'utf8').digest('hex');
}

function hashOrUndef(v) {
  return v ? [sha256(v)] : undefined;
}

// Meta wil telefoon als cijfers met landcode, zonder + of voorloopnullen.
export function normalizePhoneNL(raw) {
  let d = String(raw || '').replace(/\D/g, '');
  if (!d) return '';
  if (d.startsWith('0031')) d = d.slice(2);
  if (d.startsWith('31')) return d;
  if (d.startsWith('0')) return '31' + d.slice(1);
  return d;
}

function firstName(naam) {
  const f = String(naam || '').trim().split(/\s+/)[0] || '';
  return f.toLowerCase();
}

export function clientIp(req) {
  const xff = req.headers?.['x-forwarded-for'];
  if (typeof xff === 'string' && xff) return xff.split(',')[0].trim();
  return req.headers?.['x-real-ip'] || req.socket?.remoteAddress || '';
}

/**
 * Stuurt één event naar de Conversions API.
 * Faalt nooit naar de bezoeker toe: retourneert { sent, reason }.
 */
export async function sendMetaEvent({
  eventName,
  eventId,
  eventSourceUrl,
  req,
  user = {},
  customData = {},
  timeoutMs = 3000,
}) {
  const token = process.env.META_CAPI_TOKEN;
  if (!token) return { sent: false, reason: 'no-token' };
  if (!eventName || !eventId) return { sent: false, reason: 'missing-event' };

  const pixelId = process.env.META_PIXEL_ID || DEFAULT_PIXEL_ID;
  const testCode = process.env.META_TEST_EVENT_CODE;

  const phone = normalizePhoneNL(user.telefoon);
  const email = String(user.email || '').trim().toLowerCase();
  const fn = firstName(user.naam);
  const zp = String(user.postcode || '').replace(/\s+/g, '').toLowerCase();

  const user_data = {
    ph: hashOrUndef(phone),
    em: hashOrUndef(email),
    fn: hashOrUndef(fn),
    zp: hashOrUndef(zp),
    country: [sha256('nl')],
    external_id: hashOrUndef(user.externalId),
    fbp: user.fbp || undefined,
    fbc: user.fbc || undefined,
    client_ip_address: (req && clientIp(req)) || undefined,
    client_user_agent: (req && req.headers?.['user-agent']) || user.userAgent || undefined,
  };
  Object.keys(user_data).forEach(k => user_data[k] === undefined && delete user_data[k]);

  const body = {
    data: [{
      event_name: eventName,
      event_time: Math.floor(Date.now() / 1000),
      event_id: eventId,
      action_source: 'website',
      event_source_url: eventSourceUrl || undefined,
      user_data,
      custom_data: customData,
    }],
  };
  if (testCode) body.test_event_code = testCode;

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(
      `https://graph.facebook.com/${GRAPH_VERSION}/${pixelId}/events?access_token=${encodeURIComponent(token)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      }
    );
    if (!res.ok) {
      console.error('[meta-capi] Graph error:', res.status, await res.text().catch(() => ''));
      return { sent: false, reason: `http-${res.status}` };
    }
    return { sent: true };
  } catch (err) {
    console.error('[meta-capi] fetch failed:', err?.message || err);
    return { sent: false, reason: 'fetch-failed' };
  } finally {
    clearTimeout(timer);
  }
}
