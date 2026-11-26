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

  /* ---- 0. Bereikbaarheidslabel (Europe/Amsterdam) -------------------------
     In de HTML staat een neutrale tekst. Pas hier wordt bepaald of de lijn
     nu open is (07:00 tot 22:00) of niet. Zonder JavaScript blijft de
     neutrale tekst staan, dus nooit 'nu bereikbaar' als het 's nachts is. */
  function uurInAmsterdam() {
    try {
      var h = new Intl.DateTimeFormat('nl-NL', {
        timeZone: 'Europe/Amsterdam', hour: '2-digit', hourCycle: 'h23'
      }).format(new Date());
      var n = parseInt(h, 10);
      return isNaN(n) ? null : n;
    } catch (ignored) { return null; }
  }

  var uur = uurInAmsterdam();
  if (uur !== null) {
    var labels = document.querySelectorAll('[data-bereikbaar]');
    for (var i = 0; i < labels.length; i++) {
      var el = labels[i];
      var tekst = el.querySelector('.pill-text') || el;
      if (uur >= 7 && uur < 22) {
        tekst.textContent = el.getAttribute('data-open') || 'Nu bereikbaar';
        el.classList.add('is-open');
      } else {
        tekst.textContent = uur < 7
          ? 'Nu buiten openingstijd. Bel vanaf 07:00 of stuur een WhatsApp'
          : 'Nu buiten openingstijd. Bel morgen vanaf 07:00 of stuur een WhatsApp';
        el.classList.add('is-closed');
      }
    }
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

  /* ---- 1b. Google Ads gesprekken via website (doorschakelnummer) ---------
     De awcc-tag in GTM vervangt alleen het zichtbare nummer. Hier zetten we
     ook de href van alle tel-links om, zodat een tik op mobiel via het
     doorschakelnummer loopt. Komt _googWcmGet niet binnen ~10 s (geen
     bezoeker uit een advertentie), dan verandert er niets. De klikmeting
     hierboven blijft werken: die kijkt naar a[href^="tel:"] en data-cta. */
  var WCM_NUMMER = '06 12 60 20 82';

  function vervangNummer(formatted, mobile) {
    var nieuw = String(mobile || formatted || '').replace(/[^\d+]/g, '');
    if (!nieuw || nieuw.length < 8) return;

    var links = document.querySelectorAll('a[href^="tel:"]');
    for (var j = 0; j < links.length; j++) links[j].setAttribute('href', 'tel:' + nieuw);

    if (!formatted) return;
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode && n.parentNode.nodeName;
        if (p === 'SCRIPT' || p === 'STYLE' || p === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
        return n.nodeValue.indexOf(WCM_NUMMER) !== -1 ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (var k = 0; k < nodes.length; k++) {
      nodes[k].nodeValue = nodes[k].nodeValue.split(WCM_NUMMER).join(formatted);
    }
  }

  var wcmPogingen = 0;
  var wcmTimer = setInterval(function () {
    wcmPogingen++;
    if (typeof window._googWcmGet === 'function') {
      clearInterval(wcmTimer);
      try { window._googWcmGet(vervangNummer, WCM_NUMMER); } catch (ignored) { /* nummer blijft staan */ }
    } else if (wcmPogingen >= 34) {
      clearInterval(wcmTimer);
    }
  }, 300);

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
