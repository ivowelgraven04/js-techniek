/* ==========================================================================
   JS Techniek - Landingspagina's lekkagecampagne
   Meet telefoonklikken, WhatsApp-klikken en formulierinzendingen.
   Alles gaat via dataLayer -> GTM (container GTM-NN4SJRXV staat al live).
   In GTM koppel je deze events aan de Google Ads conversieacties.
   ========================================================================== */
(function () {
  'use strict';

  window.dataLayer = window.dataLayer || [];

  function push(event, extra) {
    var payload = { event: event, lp_slug: document.body.getAttribute('data-lp') || '' };
    if (extra) { for (var k in extra) { if (Object.prototype.hasOwnProperty.call(extra, k)) payload[k] = extra[k]; } }
    window.dataLayer.push(payload);
  }

  /* ---- 1. Telefoon- en WhatsApp-klikken ---------------------------------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || typeof t.closest !== 'function') return;

    var tel = t.closest('a[href^="tel:"]');
    if (tel) {
      push('lp_phone_click', { cta_id: tel.getAttribute('data-cta') || 'onbekend' });
      return;
    }
    var wa = t.closest('a[href*="wa.me"]');
    if (wa) {
      push('lp_whatsapp_click', { cta_id: wa.getAttribute('data-cta') || 'onbekend' });
    }
  });

  /* ---- 2. Pageview met campagneparameters -------------------------------- */
  var params = new URLSearchParams(window.location.search);
  push('lp_view', {
    gclid: params.get('gclid') || '',
    utm_campaign: params.get('utm_campaign') || '',
    utm_content: params.get('utm_content') || '',
    utm_term: params.get('utm_term') || ''
  });

  /* ---- 3. Formulier ------------------------------------------------------ */
  var form = document.getElementById('lead-form');
  if (!form) return;

  var errBox = document.getElementById('form-error');
  var firstFocus = false;

  form.addEventListener('focusin', function () {
    if (firstFocus) return;
    firstFocus = true;
    push('lp_form_start');
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    if (errBox) errBox.classList.remove('show');

    var btn = form.querySelector('button[type=submit]');
    var label = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; btn.innerHTML = 'Versturen...'; }

    var fd = new FormData(form);

    // Honeypot: bots vullen dit in, mensen niet.
    if (fd.get('company_url')) {
      window.location.href = '/bedankt-lekkage';
      return;
    }

    var body = {};
    fd.forEach(function (v, k) { body[k] = typeof v === 'string' ? v.trim() : v; });

    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid'].forEach(function (k) {
      var v = params.get(k);
      if (v) body[k] = v;
    });
    body.user_agent = navigator.userAgent;
    body.timestamp = new Date().toISOString();

    push('lp_form_submit_attempt');

    try {
      var res = await fetch('/api/submit-quote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        var msg = 'Er ging iets mis bij het versturen.';
        try {
          var data = await res.json();
          if (data && data.error) msg = data.error;
        } catch (ignored) { /* geen JSON-body */ }
        throw new Error(msg);
      }

      push('lp_form_submit_success', { type_werk: body.type_werk || '' });
      window.location.href = '/bedankt-lekkage';
    } catch (err) {
      push('lp_form_submit_error');
      if (errBox) {
        errBox.textContent = (err && err.message ? err.message : 'Er ging iets mis.') +
          ' Probeer het nogmaals of bel ons direct op 06 12 60 20 82.';
        errBox.classList.add('show');
      }
      if (btn) { btn.disabled = false; btn.innerHTML = label; }
    }
  });
})();
