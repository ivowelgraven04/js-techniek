#!/usr/bin/env python3
"""
Generator voor de Google Ads-landingspagina's van JS Techniek.

Maakt uit één sjabloon:
  - dakdekker-<plaats>.html   (één per plaats in PLAATSEN, type_werk "plaats")
  - plat-dak-laten-vervangen.html   (type_werk "vervangen")

Alle pagina's gebruiken dezelfde look en meting als daklekkage.html:
GTM-NN4SJRXV in de head, /assets/lp-lekkage.css en /assets/lp-lekkage.js,
#lead-form naar /api/submit-quote met bron_pagina + type_werk, honeypot
company_url, data-cta op elke tel- en WhatsApp-link en body data-lp = slug.

Plaats toevoegen: zet een regel in PLAATSEN en draai
    python3 landingspagina/ads_plaatspaginas.py
vanuit de repo-root (of van waar dan ook; de uitvoer gaat altijd naar de repo-root).
De pagina's staan op noindex en horen NIET in sitemap.xml.

Regels van de klant (niet aan tornen):
  alleen platte daken, nooit 24/7 of dag en nacht, nooit beloven dat een lek
  binnen 24 uur verholpen is, geen bedragen of prijsindicaties, reviews 5,0 uit 20.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://jschoutentechniek.com"
TEL_HREF = "tel:+31612602082"
TEL_TXT = "06 12 60 20 82"
WA_BASE = "https://wa.me/31612602082?text="

# ---------------------------------------------------------------------------
# Plaatsen. "naam" komt in H1/title ("Dakdekker {naam} en omgeving"),
# "in_naam" in lopende zinnen ("in {in_naam}"). "dorpen" zijn echte
# omliggende kernen. "kern" = kerngebied rond Den Helder en Schagen, waar
# het vaak nog dezelfde dag lukt.
# ---------------------------------------------------------------------------
PLAATSEN = [
    dict(slug="dakdekker-den-helder", naam="Den Helder", in_naam="Den Helder", kern=True,
         dorpen=["Julianadorp", "Huisduinen", "De Kooy", "Anna Paulowna", "Callantsoog", "Breezand"]),
    dict(slug="dakdekker-julianadorp", naam="Julianadorp", in_naam="Julianadorp", kern=True,
         dorpen=["Callantsoog", "Groote Keeten", "Den Helder", "Anna Paulowna", "Breezand"]),
    dict(slug="dakdekker-schagen", naam="Schagen", in_naam="Schagen", kern=True,
         dorpen=["Schagerbrug", "Tuitjenhorn", "Warmenhuizen", "Dirkshorn", "Sint Maarten", "Waarland"]),
    dict(slug="dakdekker-anna-paulowna", naam="Anna Paulowna", in_naam="Anna Paulowna", kern=True,
         dorpen=["Breezand", "Kleine Sluis", "Van Ewijcksluis", "Wieringerwaard", "Julianadorp"]),
    dict(slug="dakdekker-heerhugowaard", naam="Heerhugowaard", in_naam="Heerhugowaard", kern=False,
         dorpen=["Broek op Langedijk", "Noord-Scharwoude", "Oudkarspel", "Sint Pancras", "Obdam", "Hensbroek"]),
    dict(slug="dakdekker-alkmaar", naam="Alkmaar", in_naam="Alkmaar", kern=False,
         dorpen=["Heiloo", "Bergen", "Koedijk", "Oudorp", "Sint Pancras"]),
    dict(slug="dakdekker-heiloo", naam="Heiloo", in_naam="Heiloo", kern=False,
         dorpen=["Limmen", "Akersloot", "Castricum", "Egmond-Binnen", "Alkmaar"]),
    dict(slug="dakdekker-medemblik", naam="Medemblik", in_naam="Medemblik", kern=False,
         dorpen=["Wervershoof", "Andijk", "Onderdijk", "Abbekerk", "Opperdoes", "Twisk"]),
    dict(slug="dakdekker-hoorn", naam="Hoorn", in_naam="Hoorn", kern=False,
         dorpen=["Zwaag", "Blokker", "Wognum", "Berkhout", "Avenhorn"]),
    dict(slug="dakdekker-kop-van-noord-holland", naam="Kop van Noord-Holland",
         in_naam="de Kop van Noord-Holland", kern=True,
         dorpen=["Den Helder", "Julianadorp", "Anna Paulowna", "Schagen", "Callantsoog",
                 "Hippolytushoef", "Den Oever", "Wieringerwerf"]),
]

# Algemeen werkgebied (zelfde lijst als daklekkage.html)
WERKGEBIED_KERN = ["Den Helder", "Julianadorp", "Anna Paulowna", "Schagen"]
WERKGEBIED_REST = ["Breezand", "Callantsoog", "Petten", "Hippolytushoef", "Den Oever",
                   "Wieringerwerf", "Middenmeer", "Medemblik", "Warmenhuizen", "Tuitjenhorn",
                   "Schoorl", "Bergen", "Egmond", "Alkmaar", "Heerhugowaard", "Heiloo",
                   "Castricum", "Hoorn", "Obdam"]

# ---------------------------------------------------------------------------
# Iconen (zelfde SVG's als daklekkage.html)
# ---------------------------------------------------------------------------
ICO_PHONE = '<svg width="{s}" height="{s}" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.774a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.06-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z"/></svg>'
ICO_WA = '<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654z"/></svg>'
ICO_CHECK = '<svg width="{s}" height="{s}" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.704 5.292a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.29-7.294a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>'
ICO_X_H = '<svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>'
ICO_X = '<svg width="11" height="11" viewBox="0 0 20 20" aria-hidden="true"><path d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/></svg>'
ICO_G = '<svg class="g-logo" viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>'
ICO_CLOCK = '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/></svg>'
ICO_BOLT = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
ICO_SHIELD = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
ICO_SHIELD_OK = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 12l2 2 4-4"/><path d="M12 3l7.5 3v5.4c0 4.3-3.1 8.3-7.5 9.6-4.4-1.3-7.5-5.3-7.5-9.6V6L12 3z"/></svg>'


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def wa_link(tekst: str) -> str:
    return WA_BASE + quote(tekst, safe="")


def opsomming(items: list[str]) -> str:
    """['a','b','c'] -> 'a, b en c'"""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " en " + items[-1]


# ---------------------------------------------------------------------------
# Gedeelde blokken
# ---------------------------------------------------------------------------
def head(slug: str, title: str, description: str, og_title: str, og_desc: str) -> str:
    url = f"{SITE}/{slug}"
    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <!-- Google Tag Manager -->
  <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
  new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
  j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
  'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
  }})(window,document,'script','dataLayer','GTM-NN4SJRXV');</script>
  <!-- End Google Tag Manager -->

  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="noindex, follow">
  <link rel="canonical" href="{url}">
  <meta name="theme-color" content="#FBFAF7">

  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">

  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(og_title)}">
  <meta property="og:description" content="{esc(og_desc)}">
  <meta property="og:url" content="{url}">
  <meta property="og:image" content="{SITE}/images/og-image.png">
  <meta property="og:locale" content="nl_NL">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/lp-lekkage.css">
</head>
<body data-lp="{slug}">
  <!-- Google Tag Manager (noscript) -->
  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NN4SJRXV"
  height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

  <header class="topbar">
    <div class="wrap bar">
      <a href="/" class="brand" aria-label="JS Techniek">
        <picture><source srcset="/images/logo-96.webp" type="image/webp"><img src="/images/logo-96.png" alt="" width="42" height="42"></picture>
        <span class="brandtext">
          <b>JS Techniek</b>
          <span class="sub">Specialist platte daken</span>
        </span>
      </a>
      <a href="{TEL_HREF}" class="tel" data-cta="topbar-phone">
        {ICO_PHONE.format(s=17)}
        {TEL_TXT}
      </a>
    </div>
  </header>
"""


def pill(open_tekst: str) -> str:
    # Neutrale tekst in de HTML; lp-lekkage.js zet hem tussen 07:00 en 22:00
    # op open_tekst en daarbuiten op "buiten openingstijd".
    return (f'<span class="pill" data-bereikbaar data-open="{esc(open_tekst)}"><span class="dot"></span> '
            f'<span class="pill-text">Bereikbaar overdag, \'s avonds en in het weekend</span></span>')


def proof() -> str:
    return f"""<div class="proof">
            {ICO_G}
            <span class="score">5,0</span>
            <span class="stars">★★★★★</span>
            <span class="sep"></span>
            <span>20 reviews</span>
            <span class="sep hide-sm"></span>
            <span class="hide-sm">25 jaar in Noord-Holland</span>
          </div>"""


def checks(items: list[str]) -> str:
    lis = "\n".join(
        f'            <li>\n              <span class="tick">{ICO_CHECK.format(s=13)}</span>\n              <span>{it}</span>\n            </li>'
        for it in items)
    return f'<ul class="checks">\n{lis}\n          </ul>'


def trustbar() -> str:
    return f"""
    <!-- ══════════════ VERTROUWENSBALK ══════════════ -->
    <section class="trustbar">
      <div class="wrap row">
        <div class="item">
          <span class="ic">{ICO_BOLT}</span>
          <div>
            <h3>U spreekt Jonathan zelf</h3>
            <p>Geen callcenter en geen wachtrij. Jonathan neemt op en komt ook zelf kijken.</p>
          </div>
        </div>
        <div class="item">
          <span class="ic">{ICO_SHIELD}</span>
          <div>
            <h3>Specialist platte daken</h3>
            <p>25 jaar ervaring met bitumen, dakleer, EPDM en PVC. Platte daken zijn ons enige vak.</p>
          </div>
        </div>
        <div class="item">
          <span class="ic">{ICO_SHIELD_OK}</span>
          <div>
            <h3>Vaste prijs vooraf</h3>
            <p>U weet de prijs voordat wij beginnen. Geen verrassingen op de rekening.</p>
          </div>
        </div>
      </div>
    </section>
"""


def scope_block(titel: str, intro: str) -> str:
    wel = [
        "Lekkages en reparaties van platte daken",
        "Bitumen, dakleer, EPDM en PVC dakbedekking",
        "Dakbedekking op een dakkapel, aanbouw, uitbouw, garage of schuur vervangen of repareren",
        "Lichtkoepels en dakdoorvoeren waterdicht maken",
        "Dakranden en daktrim",
        "Isoleren bij een nieuw plat dak",
    ]
    niet = [
        "Pannendaken en hellende daken",
        "Rieten daken en leien daken",
        "Schoorsteenwerk op een schuin dak",
        "Een hele dakkapel, aanbouw of garage bouwen",
    ]
    wel_li = "\n".join(f'                <li><span class="mk">{ICO_CHECK.format(s=12)}</span> {w}</li>' for w in wel)
    niet_li = "\n".join(f'                <li><span class="mk">{ICO_X}</span> {n}</li>' for n in niet)
    return f"""
    <!-- ══════════════ WAT WIJ WEL EN NIET DOEN ══════════════ -->
    <section class="scope section">
      <div class="wrap">
        <div class="panel">
          <div class="section-head">
            <span class="eyebrow">Wat wij doen</span>
            <h2>{titel}</h2>
            <p>{intro}</p>
          </div>

          <div class="cols">
            <div class="do">
              <h3>
                {ICO_CHECK.format(s=16)}
                Wat wij doen
              </h3>
              <ul>
{wel_li}
              </ul>
            </div>

            <div class="rule" aria-hidden="true"></div>

            <div class="dont">
              <h3>
                {ICO_X_H}
                Wat wij niet doen
              </h3>
              <ul>
{niet_li}
              </ul>
            </div>
          </div>

          <p class="foot-note">
            Twijfelt u welk type dak u heeft? <a href="{TEL_HREF}" data-cta="scope-phone">Bel gerust</a>, dan hoort u het binnen een minuut.
          </p>
        </div>
      </div>
    </section>
"""


def reviews() -> str:
    items = [
        ("Vanwege lekkage aan mijn dak kwam ik via google bij J.S terecht. Tijdens mijn eerste telefonische contact heel prettig te woord gestaan en gelijk een afspraak gepland voor een dakinspectie. …", "Jens K."),
        ("J.S techniek reageerde snel en correct. … Het gevraagde was snel gerepareerd.", "M. B."),
        ("Snel gehandeld na mijn hulpvraag. Ik kreeg uitleg over wat en hoe hij het ging doen. …", "Riny B."),
    ]
    figs = "\n".join(f"""          <figure class="review">
            <div class="stars">★★★★★</div>
            <blockquote>{q}</blockquote>
            <figcaption class="who">
              {ICO_G}
              {w}
            </figcaption>
          </figure>""" for q, w in items)
    return f"""
    <!-- ══════════════ REVIEWS ══════════════ -->
    <section class="reviews section">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Wat klanten zeggen</span>
          <h2>5,0 sterren op Google, 20 reviews</h2>
        </div>

        <div class="grid">
{figs}
        </div>
      </div>
    </section>
"""


def formulier(slug: str, type_werk: str, kop: str, tekst: str, knop: str) -> str:
    assure = "\n".join(f'              <span>{ICO_CHECK.format(s=16)} {t}</span>' for t in [
        "Wij bellen u maximaal één keer terug, geen spam",
        "Uw gegevens gaan nooit naar derden",
        "Vrijblijvend, u zit nergens aan vast",
    ])
    return f"""
    <!-- ══════════════ FORMULIER ══════════════ -->
    <section class="formsec section" id="aanvraag">
      <div class="wrap grid">
        <div class="intro">
          <span class="eyebrow">Liever teruggebeld</span>
          <h2 style="margin-top:14px">{kop}</h2>
          <p>{tekst}</p>
          <p class="alt">
            Haast? Bel dan direct
            <a href="{TEL_HREF}" data-cta="formsec-phone">{TEL_TXT}</a>.
          </p>
        </div>

        <div class="formcard">
          <form id="lead-form" novalidate>
            <input type="hidden" name="bron_pagina" value="{slug}">
            <input type="hidden" name="type_werk" value="{type_werk}">
            <div class="hp" aria-hidden="true">
              <label>Laat dit veld leeg <input type="text" name="company_url" tabindex="-1" autocomplete="off"></label>
            </div>

            <label class="field">
              <span>Uw naam</span>
              <input type="text" name="naam" required autocomplete="name" placeholder="Jan Jansen">
            </label>

            <div class="field-row">
              <label class="field">
                <span>Telefoonnummer</span>
                <input type="tel" name="telefoon" required autocomplete="tel" inputmode="tel" placeholder="06 12 34 56 78">
              </label>
              <label class="field">
                <span>Postcode</span>
                <input type="text" name="postcode" required autocomplete="postal-code" placeholder="1781 AA" maxlength="8">
              </label>
            </div>

            <div class="assure">
{assure}
            </div>

            <button type="submit" class="btn btn-call btn-block">{knop}</button>
            <p class="privacy-note">Door te verzenden gaat u akkoord met onze <a href="/privacy">privacyverklaring</a>.</p>
            <div class="form-error" id="form-error" role="alert"></div>
          </form>
        </div>
      </div>
    </section>
"""


def area(titel: str, tekst: str, kern: list[str], rest: list[str]) -> str:
    chips = "".join(f'<li class="core">{esc(p)}</li>' for p in kern) + "".join(f"<li>{esc(p)}</li>" for p in rest)
    return f"""
    <!-- ══════════════ WERKGEBIED ══════════════ -->
    <section class="area section">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Werkgebied</span>
          <h2>{titel}</h2>
          <p>{tekst}</p>
        </div>
        <ul class="chips">
          {chips}
        </ul>
      </div>
    </section>
"""


def faq(vragen: list[tuple[str, str]]) -> str:
    items = "\n".join(f"""          <details>
            <summary>{q}</summary>
            <div class="answer">{a}</div>
          </details>""" for q, a in vragen)
    return f"""
    <!-- ══════════════ FAQ ══════════════ -->
    <section class="faq section">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Veelgestelde vragen</span>
          <h2>Goed om te weten</h2>
        </div>

        <div class="list">
{items}
        </div>
      </div>
    </section>
"""


def slot(kop: str, tekst: str, wa: str) -> str:
    return f"""
    <!-- ══════════════ SLOT ══════════════ -->
    <section class="dark finalcta section">
      <div class="wrap">
        <div class="inner">
          <h2>{kop}</h2>
          <p>{tekst}</p>
          <div class="cta-row">
            <a href="{TEL_HREF}" class="btn btn-call" data-cta="final-phone">
              {ICO_PHONE.format(s=19)}
              {TEL_TXT}
            </a>
            <a href="{wa}" target="_blank" rel="noopener" class="btn btn-ghost-dark" data-cta="final-whatsapp">
              {ICO_WA.format(s=19)}
              Foto sturen via WhatsApp
            </a>
          </div>
        </div>
      </div>
    </section>
  </main>
"""


def footer(wa: str) -> str:
    return f"""
  <footer class="foot">
    <div class="wrap row">
      <div>
        <b>JS Techniek</b> &middot; Specialist platte daken Noord-Holland<br>
        KvK 70974306 &middot; <a href="{TEL_HREF}" data-cta="footer-phone">{TEL_TXT}</a> &middot;
        <a href="mailto:info@jschoutentechniek.com">info@jschoutentechniek.com</a>
      </div>
      <div class="links">
        <a href="/">Website</a>
        <a href="/privacy">Privacy</a>
        <a href="/voorwaarden">Voorwaarden</a>
      </div>
    </div>
  </footer>

  <nav class="mobilebar" aria-label="Snel contact">
    <a href="{TEL_HREF}" class="call" data-cta="mobilebar-phone">
      {ICO_PHONE.format(s=18)}
      Bel direct
    </a>
    <a href="{wa}" target="_blank" rel="noopener" class="wa" data-cta="mobilebar-whatsapp">
      {ICO_WA.format(s=18)}
      WhatsApp
    </a>
  </nav>

  <script src="/assets/lp-lekkage.js" defer></script>
</body>
</html>
"""


def stappen(kop: str, intro: str, stappen_: list[tuple[str, str]], eerlijk: str) -> str:
    st = "\n".join(f"""          <div class="step">
            <span class="n">{i}</span>
            <h3>{t}</h3>
            <p>{p}</p>
          </div>""" for i, (t, p) in enumerate(stappen_, 1))
    return f"""
    <!-- ══════════════ ZO WERKT HET ══════════════ -->
    <section class="dark section">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow on-dark">Zo werkt het</span>
          <h2>{kop}</h2>
          <p class="lead">{intro}</p>
        </div>

        <div class="steps">
{st}
        </div>

        <div class="honest">
          <p>{eerlijk}</p>
        </div>
      </div>
    </section>
"""


def hero(pill_open: str, h1: str, lead: str, checks_: list[str], img: str, img_alt: str,
         tag_b: str, tag_s: str) -> str:
    return f"""
  <main>
    <!-- ══════════════ HERO ══════════════ -->
    <section class="hero">
      <div class="wrap hero-grid">
        <div>
          {pill(pill_open)}

          <h1>{h1}</h1>

          <p class="lead">
            {lead}
          </p>

          <div class="cta-row">
            <a href="{TEL_HREF}" class="btn btn-call" data-cta="hero-phone">
              {ICO_PHONE.format(s=19)}
              Bel {TEL_TXT}
            </a>
            <a href="#aanvraag" class="btn btn-ghost" data-cta="hero-form">Liever teruggebeld worden</a>
          </div>

          {proof()}

          {checks(checks_)}
        </div>

        <div class="shot">
          <div class="frame">
            <img src="{img}" alt="{esc(img_alt)}" width="900" height="710" fetchpriority="high">
          </div>
          <div class="tag">
            <span class="ic">
              {ICO_CLOCK}
            </span>
            <span>
              <b>{tag_b}</b>
              <span>{tag_s}</span>
            </span>
          </div>
        </div>
      </div>
    </section>
"""


EERLIJK = ("<strong>Wat wij bewust niet beloven:</strong> dat elk lek binnen 24 uur verholpen is. "
           "Soms is een kleine reparatie genoeg, soms blijkt de dakbedekking op. Wat wij wel beloven: "
           "binnen 24 uur staan we op uw dak, brengen we het probleem in beeld en krijgt u een diagnose, "
           "een prijs en de doorlooptijd.")

FAQ_BEREIKBAAR = ("Zijn jullie 's nachts ook bereikbaar?",
                  "Nee, en dat zeggen we liever eerlijk. Overdag, 's avonds en in het weekend nemen we gewoon op. "
                  "'s Nachts staat de telefoon uit. Stuur dan een WhatsApp of vul het formulier in, dan bellen "
                  "we u 's ochtends als eerste terug.")
FAQ_KOSTEN = ("Wat kost het?",
              "Dat verschilt per dak, daarom staan er online geen bedragen. Het hangt af van de grootte, de "
              "staat van de ondergrond en wat er precies mis is. Jonathan komt eerst kijken en u krijgt vooraf "
              "een vaste prijs. Wij beginnen nooit aan werk zonder dat u de prijs kent.")
FAQ_PLAT = ("Ik weet niet zeker of ik een plat dak heb. Wat nu?",
            "Bel even, dan is dat binnen een minuut duidelijk. Wij werken uitsluitend aan platte daken. Heeft u "
            "pannen, leien of riet, dan zeggen we dat meteen en bent u geen tijd kwijt.")
FAQ_GARANTIE = ("Geven jullie garantie?",
                "Ja. Op nieuw aangebrachte bitumen dakbedekking krijgt u 10 jaar garantie op materiaal en "
                "uitvoering, schriftelijk vastgelegd. Op noodreparaties 1 jaar.")


# ---------------------------------------------------------------------------
# Plaatspagina
# ---------------------------------------------------------------------------
def plaatspagina(p: dict) -> str:
    naam, in_naam, slug, dorpen = p["naam"], p["in_naam"], p["slug"], p["dorpen"]
    is_regio = naam.startswith("Kop van")
    # Dorpen zonder de plaats zelf, voor in de lopende tekst
    dorpen_tekst = opsomming(dorpen)
    wa = wa_link(f"Hallo, ik heb een vraag over mijn platte dak in {naam if not is_regio else 'de Kop van Noord-Holland'}. Mijn adres: ")
    snel = ("Rond Den Helder en Schagen lukt het vaak nog dezelfde dag."
            if p["kern"] else "Wij plannen u in zodra u belt.")

    title = f"Dakdekker {naam} en omgeving | Platte daken | JS Techniek"
    description = (f"Dakdekker voor platte daken in {in_naam} en omgeving. Lekkage of reparatie? "
                   f"Jonathan komt zelf kijken, binnen 24 uur op uw dak met diagnose, prijs en doorlooptijd. "
                   f"5,0 sterren op Google.")
    og_desc = (f"Binnen 24 uur op uw dak in {in_naam} en omgeving, met diagnose, prijs en doorlooptijd. "
               f"Specialist platte daken.")

    plek = (f"in Den Helder, Schagen of een van de dorpen eromheen" if is_regio
            else f"in {in_naam}, {dorpen[0]} of {dorpen[1]}")
    lead = (f"Lekkage of een ander probleem met uw platte dak {plek}? "
            f"Jonathan komt zelf kijken en staat binnen 24 uur op uw dak. U krijgt een diagnose, een prijs "
            f"en de doorlooptijd.")

    out = head(slug, title, description, f"Dakdekker {naam} en omgeving | JS Techniek", og_desc)
    out += hero(
        pill_open=f"Nu bereikbaar voor {in_naam} en omgeving",
        h1=f"Dakdekker {esc(naam)} en omgeving",
        lead=lead,
        checks_=[
            "<strong>Binnen 24 uur op uw dak</strong> met diagnose, prijs en doorlooptijd",
            "Ook <strong>'s avonds en in het weekend</strong> bereikbaar",
            "U weet de prijs <strong>vooraf</strong>, zonder verrassingen",
        ],
        img="/images/noodreparaties-1.jpeg",
        img_alt=f"Dakdekker van JS Techniek aan het werk op een plat dak in de regio {naam}",
        tag_b="Binnen 24 uur op uw dak",
        tag_s=("In het kerngebied vaak nog dezelfde dag" if p["kern"] else "Met diagnose, prijs en doorlooptijd"),
    )
    out += trustbar()
    out += stappen(
        kop="U belt, Jonathan komt kijken",
        intro=("Bij een probleem met uw dak wilt u vooral weten hoe erg het is en wat het kost. "
               "Die duidelijkheid krijgt u binnen een dag."),
        stappen_=[
            ("U belt of laat uw nummer achter",
             "Jonathan stelt een paar korte vragen en plant meteen een moment in. Een foto via WhatsApp mag ook, dat scheelt tijd."),
            ("Binnen 24 uur op uw dak",
             (f"Ook in Callantsoog, Hippolytushoef en de andere dorpen in de Kop van Noord-Holland. " if is_regio
              else f"Ook in {dorpen[0]}, {dorpen[1]} en de andere dorpen rond {naam}. ") +
             "We zoeken uit waar het probleem echt zit, op het dak zelf."),
            ("U hoort wat er nodig is",
             "Een diagnose, een vaste prijs en de doorlooptijd. Daarna beslist u, zonder druk."),
        ],
        eerlijk=EERLIJK,
    )
    out += scope_block(
        "Uitsluitend platte daken",
        ("Daar zijn we in gespecialiseerd, en daarom zijn we snel en scherp. Heeft u pannen, leien of riet "
         "op uw dak, dan zijn wij niet de juiste partij. Dat zeggen we liever meteen."),
    )
    if is_regio:
        area_titel = "De hele Kop van Noord-Holland en omgeving"
        area_tekst = (f"Wij komen in {dorpen_tekst}, en ook verder tot Alkmaar en Hoorn. Woont u in een "
                      f"klein dorp dat hier niet staat? Bel gerust, dan kijken we of we het redden.")
        kern = [d for d in dorpen if d in WERKGEBIED_KERN]
        rest = [d for d in dorpen if d not in WERKGEBIED_KERN]
    else:
        area_titel = f"{esc(naam)} en de dorpen eromheen"
        area_tekst = (f"Wij werken in {in_naam} en in de dorpen eromheen, zoals {dorpen_tekst}. "
                      f"{snel} Woont u in een klein dorp dat hier niet staat? Bel gerust, dan kijken we of we het redden.")
        kern = [naam]
        rest = dorpen
    out += area(area_titel, area_tekst, kern, rest)
    out += reviews()
    out += formulier(
        slug, "plaats",
        kop="Laat uw nummer achter, Jonathan belt u terug",
        tekst=("Kunt u nu niet bellen? Vul deze drie velden in. Jonathan belt u zo snel mogelijk terug "
               "tijdens onze bereikbare uren en plant direct een moment in om te komen kijken."),
        knop="Bel mij terug over mijn dak",
    )
    out += faq([
        ("Hoe snel kunnen jullie er zijn?",
         f"Binnen 24 uur staan we bij u op het dak in {in_naam} en omgeving, met een diagnose, een prijs en "
         f"de doorlooptijd. {snel} Of de reparatie dan ook meteen klaar is, hangt af van wat we aantreffen. "
         f"Dat beloven we dus niet vooraf."),
        FAQ_BEREIKBAAR,
        (f"Komen jullie ook in de dorpen rond {naam if not is_regio else 'Den Helder en Schagen'}?",
         f"Ja. Wij werken in {in_naam} en in de dorpen eromheen, zoals {dorpen_tekst}. Ons werkgebied loopt "
         f"van Den Helder tot Alkmaar en Hoorn. Twijfelt u, bel dan even."),
        FAQ_KOSTEN,
        FAQ_PLAT,
        FAQ_GARANTIE,
    ])
    out += slot(
        kop=f"Probleem met uw platte dak in {esc(in_naam)}? Bel nu.",
        tekst="Hoe eerder we kijken, hoe kleiner de schade blijft. Binnen 24 uur op uw dak, met diagnose, prijs en doorlooptijd.",
        wa=wa,
    )
    out += footer(wa)
    return out


# ---------------------------------------------------------------------------
# Plat dak laten vervangen
# ---------------------------------------------------------------------------
def vervangpagina() -> str:
    slug = "plat-dak-laten-vervangen"
    wa = wa_link("Hallo, ik wil mijn platte dak laten vervangen. Mijn adres: ")
    title = "Plat dak laten vervangen in Den Helder en omgeving | JS Techniek"
    description = ("Plat dak laten vervangen? Nieuwe bitumen, dakleer of EPDM op uw woning, dakkapel, aanbouw "
                   "of garage, ook met isolatie. Jonathan komt zelf kijken en u krijgt vooraf een vaste prijs. "
                   "5,0 sterren op Google.")
    out = head(slug, title, description, "Plat dak laten vervangen | JS Techniek",
               "Nieuwe dakbedekking op uw platte dak, met vaste prijs vooraf. Den Helder tot Alkmaar en Hoorn.")
    out += hero(
        pill_open="Nu bereikbaar voor een afspraak",
        h1="Plat dak laten vervangen in Den Helder en omgeving",
        lead=("Is uw bitumen of dakleer op, of blijft het lekken na elke reparatie? Jonathan komt zelf kijken, "
              "zegt eerlijk of vervangen echt nodig is en geeft u vooraf een vaste prijs."),
        checks_=[
            "Bitumen, dakleer, EPDM of PVC, <strong>afgestemd op uw dak</strong>",
            "Ook op een <strong>dakkapel, aanbouw, uitbouw, garage of schuur</strong>",
            "U weet de prijs <strong>vooraf</strong>, zonder verrassingen",
        ],
        img="/images/dakwerk-bitumen-aanleg.jpeg",
        img_alt="JS Techniek legt nieuwe bitumen dakbedekking op een plat dak",
        tag_b="Eerst kijken, dan een vaste prijs",
        tag_s="Binnen 24 uur op uw dak voor de inspectie",
    )
    out += trustbar()

    # Waarom vervangen + isolatie
    out += f"""
    <!-- ══════════════ REPAREREN OF VERVANGEN ══════════════ -->
    <section class="signs section">
      <div class="wrap">
        <div class="section-head">
          <span class="eyebrow">Repareren of vervangen?</span>
          <h2>Wij zeggen het eerlijk als repareren nog volstaat</h2>
          <p>
            Een nieuw dak is een flinke stap. Is uw dak verder nog goed en zit het probleem op één plek, dan
            raden we een reparatie aan. Vervangen adviseren we pas als de dakbedekking echt op is.
          </p>
        </div>

        <div class="grid">
          <article class="sign">
            <h3>Het lekt steeds opnieuw</h3>
            <p>Telkens een nieuwe plek of een reparatie die het niet houdt. Dan zit het probleem meestal in de hele bedekking.</p>
          </article>
          <article class="sign">
            <h3>Scheuren, blazen of uitgedroogd bitumen</h3>
            <p>Een toplaag die opbolt, scheurt of bros is geworden, heeft zijn tijd gehad.</p>
          </article>
          <article class="sign">
            <h3>Water dat blijft staan</h3>
            <p>Plassen die dagen blijven liggen wijzen vaak op een doorgezakte ondergrond of een slecht afschot.</p>
          </article>
          <article class="sign">
            <h3>Natte of slappe isolatie</h3>
            <p>Voelt het dak zacht aan of ruikt het muf binnen? Dan is er vaak al langer vocht onder de bedekking.</p>
          </article>
          <article class="sign">
            <h3>U wilt het warmer onder het dak</h3>
            <p>Bij een nieuw plat dak is dit hét moment om te isoleren. Het dak ligt dan toch al open.</p>
          </article>
          <article class="sign">
            <h3>Losse dakranden of oude lichtkoepel</h3>
            <p>Dakranden, daktrim, lichtkoepels en dakdoorvoeren nemen we bij het vervangen meteen mee.</p>
          </article>
        </div>
      </div>
    </section>
"""
    out += stappen(
        kop="Zo vervangen wij uw platte dak",
        intro="Geen gedoe en geen verrassingen. U weet vooraf wat er gebeurt, wat het kost en hoe lang het duurt.",
        stappen_=[
            ("Jonathan komt kijken",
             "Binnen 24 uur staan we op uw dak. We bekijken de bedekking, de ondergrond, de randen en de afvoer."),
            ("Vaste prijs en planning",
             "U krijgt een vaste prijs en de doorlooptijd. Met of zonder isolatie, u kiest. Daarna plannen we samen een datum."),
            ("Nieuw dak, netjes opgeleverd",
             "De oude bedekking gaat eraf, de ondergrond wordt gecontroleerd en de nieuwe bedekking gaat erop, inclusief randen en afwerking."),
        ],
        eerlijk=("<strong>Eerlijk advies voorop:</strong> blijkt bij de inspectie dat een reparatie genoeg is, "
                 "dan zeggen we dat. U betaalt nooit voor een nieuw dak dat u niet nodig heeft."),
    )
    out += scope_block(
        "Uitsluitend platte daken",
        ("Wij vervangen de dakbedekking op platte daken van woningen, dakkapellen, aanbouwen, uitbouwen, "
         "garages en schuren. Een dakkapel of aanbouw zelf bouwen doen wij niet, en aan pannendaken werken we niet."),
    )
    out += area(
        "Den Helder en omgeving, tot 45 kilometer",
        "Van de Kop van Noord-Holland tot Alkmaar en Hoorn. Staat uw plaats er niet bij maar woont u in de buurt? Bel gerust.",
        WERKGEBIED_KERN, WERKGEBIED_REST,
    )
    out += reviews()
    out += formulier(
        slug, "vervangen",
        kop="Laat uw nummer achter voor een afspraak",
        tekst=("Vul deze drie velden in. Jonathan belt u zo snel mogelijk terug tijdens onze bereikbare uren "
               "en plant een moment in om uw dak te bekijken."),
        knop="Bel mij terug over een nieuw dak",
    )
    out += faq([
        ("Wat kost het om een plat dak te laten vervangen?",
         "Dat verschilt per dak, daarom noemen we online geen bedragen. De prijs hangt af van de oppervlakte, "
         "de staat van de ondergrond, het materiaal en of u wilt isoleren. Na de inspectie krijgt u een vaste "
         "prijs. Wij beginnen nooit zonder dat u de prijs kent."),
        ("Welk materiaal is het beste voor mijn dak?",
         "Dat hangt af van uw dak en wat u belangrijk vindt. Wij werken met bitumen, dakleer, EPDM en PVC. "
         "Jonathan legt bij de inspectie uit wat bij uw dak past en waarom."),
        ("Kan ik het dak meteen laten isoleren?",
         "Ja. Bij een nieuw plat dak is dat het handigste moment, want de oude bedekking gaat er toch al af. "
         "U krijgt de prijs met en zonder isolatie, zodat u zelf kunt kiezen."),
        ("Doen jullie ook het dak van mijn dakkapel, aanbouw of garage?",
         "Ja, de dakbedekking op een dakkapel, aanbouw, uitbouw, garage of schuur vervangen we ook. "
         "Het bouwen van een dakkapel of aanbouw zelf doen wij niet."),
        ("Hoe lang duurt het?",
         "Dat hangt af van de grootte van het dak en het weer. U hoort de doorlooptijd samen met de prijs, "
         "voordat u ergens aan vastzit."),
        FAQ_GARANTIE,
        FAQ_BEREIKBAAR,
    ])
    out += slot(
        kop="Toe aan een nieuw plat dak? Bel Jonathan.",
        tekst="Eerst kijken, dan een vaste prijs. U weet vooraf wat het kost en hoe lang het duurt.",
        wa=wa,
    )
    out += footer(wa)
    return out


# ---------------------------------------------------------------------------
# Controle: dezelfde regels die we bij elke pagina willen afdwingen
# ---------------------------------------------------------------------------
VERBODEN = [r"24/7", r"dag en nacht", r"24 uur per dag", r"binnen het uur", r"€", r"&euro;",
            r"\bvanaf\b", r"per m²", r"per m&sup2;", "—", "–", r"4,9",
            r"(?<!\w)(m'n|z'n|'t|'m)(?!\w)"]


def controleer(slug: str, s: str) -> list[str]:
    fouten = []
    eisen = {
        "GTM": "GTM-NN4SJRXV" in s and "googletagmanager.com/ns.html" in s,
        "lp-lekkage.js": '<script src="/assets/lp-lekkage.js" defer></script>' in s,
        "data-lp": f'<body data-lp="{slug}">' in s,
        "bron_pagina": f'name="bron_pagina" value="{slug}"' in s,
        "type_werk": 'name="type_werk" value="' in s,
        "form": '<form id="lead-form"' in s,
        "naam": 'name="naam" required' in s,
        "telefoon": 'name="telefoon" required' in s,
        "postcode": 'name="postcode" required' in s,
        "honeypot": 'name="company_url"' in s,
        "noindex": '<meta name="robots" content="noindex, follow">' in s,
        "canonical": f'<link rel="canonical" href="{SITE}/{slug}">' in s,
        "bereikbaar-label": "data-bereikbaar" in s and "nu bereikbaar" not in re.sub(r'data-open="[^"]*"', "", s).lower(),
    }
    fouten += [f"ontbreekt: {k}" for k, ok in eisen.items() if not ok]
    for a in re.findall(r'<a [^>]*href="(?:tel:|https://wa\.me)[^"]*"[^>]*>', s):
        if "data-cta=" not in a:
            fouten.append(f"link zonder data-cta: {a[:80]}")
    # Alleen zichtbare tekst en attributen controleren, niet de SVG-paden
    tekst = re.sub(r"<svg.*?</svg>", "", s, flags=re.S)
    for pat in VERBODEN:
        if re.search(pat, tekst, flags=re.I):
            fouten.append(f"verboden tekst: {pat}")
    return fouten


def main() -> int:
    paginas = {p["slug"]: plaatspagina(p) for p in PLAATSEN}
    paginas["plat-dak-laten-vervangen"] = vervangpagina()
    fout = False
    for slug, s in paginas.items():
        problemen = controleer(slug, s)
        if problemen:
            fout = True
            print(f"FOUT {slug}: " + "; ".join(problemen))
            continue
        (ROOT / f"{slug}.html").write_text(s, encoding="utf-8")
        print(f"ok  /{slug}")
    return 1 if fout else 0


if __name__ == "__main__":
    sys.exit(main())
