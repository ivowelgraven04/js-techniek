#!/usr/bin/env python3
"""Bouwt de kennisbank van JS Techniek uit Markdown naar HTML.

Gebruik:
  python3 kennisbank/bouw.py               alles bouwen en de sitemap bijwerken
  python3 kennisbank/bouw.py --controleer  alleen controleren, niets wegschrijven
  python3 kennisbank/bouw.py --nieuw <slug> leeg artikel aanmaken om in te vullen

Bewust zonder externe pakketten: de site heeft geen bouwstap en een dagelijkse
routine mag niet omvallen omdat een bibliotheek verandert.

Menu, footer, knoppen en cookiemelding komen bij elke bouw uit dakwerken.html.
Zo lopen de kennisbankpagina's nooit achter op de rest van de site.

Er wordt niets weggeschreven als een van de controles faalt. Liever geen nieuwe
pagina dan een kapotte pagina, of een pagina met iets wat Jonathan niet doet.
"""
import html
import json
import math
import os
import re
import sys
from datetime import date

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(BASIS, "kennisbank")
ARTIKELEN = os.path.join(KB, "artikelen")
SJABLOON = os.path.join(KB, "sjabloon")
BRONPAGINA = os.path.join(BASIS, "dakwerken.html")
SITE = "https://jschoutentechniek.com"
MERK = "JS Techniek"
TELEFOON = "06 12 60 20 82"
TEL_LINK = "tel:+31612602082"
WHATSAPP = "https://wa.me/31612602082"
GEBOUWD = "<!-- gebouwd door kennisbank/bouw.py, niet met de hand aanpassen -->"

RUBRIEKEN = {
    "kosten": {
        "naam": "Kosten",
        "titel": "Wat kost werk aan een plat dak?",
        "intro": "Wat u ongeveer kwijt bent voor een nieuw plat dak, een reparatie of zinkwerk. "
                 "Altijd als bandbreedte, inclusief btw, materiaal en arbeid.",
        "beschrijving": "Wat kost een plat dak vervangen, een lekkage repareren of een zinken "
                        "dakgoot? Prijsindicaties inclusief btw, uitgelegd door JS Techniek.",
        "foto": "bitumen-plat-dak-naden-dakrand.jpg",
        "foto_alt": "Bitumen dakbedekking met strak afgewerkte naden bij de dakrand",
    },
    "bitumen-en-platte-daken": {
        "naam": "Bitumen en platte daken",
        "titel": "Bitumen en platte daken",
        "intro": "Hoe een bitumen dak is opgebouwd, hoe lang het meegaat en hoe het zich "
                 "verhoudt tot andere bedekkingen voor een plat dak.",
        "beschrijving": "Alles over bitumen dakbedekking: opbouw, levensduur, onderhoud en de "
                        "vergelijking met andere platte daken, uitgelegd door een dakdekker.",
        "foto": "bitumen-plat-dak-lichtkoepel-overzicht.jpg",
        "foto_alt": "Plat dak met nieuwe bitumen dakbedekking rond een lichtkoepel",
    },
    "lekkage-en-schade": {
        "naam": "Lekkage en schade",
        "titel": "Lekkage en schade aan een plat dak",
        "intro": "Waar het water vandaan komt, wat u meteen kunt doen en wat er bij een "
                 "reparatie van een plat dak komt kijken.",
        "beschrijving": "Daklekkage bij een plat dak: oorzaken, wat u zelf direct doet, wat "
                        "herstel kost en wanneer de verzekering betaalt. Uitleg van JS Techniek.",
        "foto": "plat-dak-waterplassen-lekkage.jpg",
        "foto_alt": "Plat dak met waterplassen, een bekende oorzaak van lekkage",
    },
    "zinkwerk-en-goten": {
        "naam": "Zinkwerk en goten",
        "titel": "Zinkwerk en dakgoten",
        "intro": "Zinken goten, dakranden en afvoeren: wat ze kosten, hoe lang ze meegaan "
                 "en wanneer repareren nog zin heeft.",
        "beschrijving": "Zinken dakgoten en zinkwerk: levensduur, kosten per meter, lekkende "
                        "naden en wanneer repareren of vervangen. Uitleg van JS Techniek.",
        "foto": "zinken-dakrand-plat-dak.jpg",
        "foto_alt": "Zinken dakrand langs een plat dak met bitumen bedekking",
    },
}

DIENSTEN = {
    "dakwerken": {
        "kop": "Uw platte dak laten bekijken?",
        "tekst": "JS Techniek legt en herstelt bitumen dakbedekking op platte daken, vanuit "
                 "Den Helder in heel Noord-Holland. We komen vrijblijvend kijken en u krijgt "
                 "een prijs op papier.",
        "knop": "Bekijk onze dakwerken",
    },
    "zinkwerk": {
        "kop": "Zinkwerk laten maken of herstellen?",
        "tekst": "Zinken goten, dakranden en afvoeren maken we op maat. We kijken eerst of "
                 "repareren nog kan, voordat we over vervangen praten.",
        "knop": "Bekijk ons zinkwerk",
    },
    "noodreparaties": {
        "kop": "Last van een lekkage?",
        "tekst": "Lekt uw platte dak of zinken goot, bel of app ons. We zoeken uit waar het "
                 "water vandaan komt en maken het dak weer dicht.",
        "knop": "Bekijk noodreparaties",
    },
}

MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]

VERPLICHT = ["titel", "paginatitel", "beschrijving", "rubriek", "zoekwoord",
             "samenvatting", "dienst", "gepubliceerd", "bijgewerkt"]

PRIJZEN = json.load(open(os.path.join(KB, "prijzen.json"), encoding="utf-8"))

fouten = []
waarschuwingen = []


def fout(bestand, tekst):
    fouten.append("%s: %s" % (bestand, tekst))


# ---------------------------------------------------------------- YAML-kop

def lees_kop(tekst, bestand):
    """Leest de YAML-kop. Kan: sleutel/waarde, lijst van tekst, lijst van
    vraag/antwoord-paren. Meer niet, en dat is genoeg."""
    if not tekst.startswith("---\n"):
        fout(bestand, "mist de kop tussen --- regels")
        return {}, tekst
    eind = tekst.find("\n---\n", 3)
    if eind == -1:
        fout(bestand, "de kop wordt niet afgesloten met ---")
        return {}, tekst
    kop_tekst, lijf = tekst[4:eind], tekst[eind + 5:]

    kop, lijst = {}, None
    for nr, regel in enumerate(kop_tekst.split("\n"), start=2):
        if not regel.strip() or regel.lstrip().startswith("#"):
            continue
        inspring = len(regel) - len(regel.lstrip())
        strip = regel.strip()

        if inspring == 0:
            m = re.match(r"^([a-z_]+):\s*(.*)$", strip)
            if not m:
                fout(bestand, "regel %d snap ik niet: %s" % (nr, strip))
                continue
            sleutel, waarde = m.group(1), m.group(2).strip()
            if waarde:
                kop[sleutel] = waarde.strip('"').strip("'")
                lijst = None
            else:
                lijst = []
                kop[sleutel] = lijst
        elif strip.startswith("- "):
            if lijst is None:
                fout(bestand, "regel %d: opsomming zonder sleutel erboven" % nr)
                continue
            rest = strip[2:].strip()
            m = re.match(r"^([a-z_]+):\s*(.*)$", rest)
            if m:
                lijst.append({m.group(1): m.group(2).strip().strip('"').strip("'")})
            else:
                lijst.append(rest.strip('"').strip("'"))
        else:
            m = re.match(r"^([a-z_]+):\s*(.*)$", strip)
            if m and lijst and isinstance(lijst[-1], dict):
                lijst[-1][m.group(1)] = m.group(2).strip().strip('"').strip("'")
            else:
                fout(bestand, "regel %d snap ik niet: %s" % (nr, strip))
    return kop, lijf


# ------------------------------------------------------------- Markdown

def inline(t):
    """Vet, cursief en links. De tekst wordt eerst ge-escaped, dus er kan geen
    HTML uit een artikel in de pagina lekken."""
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", t)
    return t


def naar_html(md, bestand):
    """Markdown naar HTML. Kan: H2, H3, alinea, opsomming (los en genummerd),
    tabel, citaat. De eerste alinea wordt het kader 'Kort antwoord'."""
    regels = md.split("\n")
    uit, i = [], 0
    koppen = []
    eerste = True

    while i < len(regels):
        strip = regels[i].strip()

        if not strip:
            i += 1
            continue

        if strip.startswith("[["):
            fout(bestand, "onbekende code %s. De kennisbank van JS Techniek kent geen "
                          "codes tussen [[ ]]." % strip)
            i += 1
            continue

        if strip.startswith("# "):
            fout(bestand, "een H1 in de tekst (regel met '# '). De H1 komt uit "
                          "'titel' in de kop, gebruik H2 of H3.")
            i += 1
            continue

        if strip.startswith("### "):
            uit.append("<h3>%s</h3>" % inline(strip[4:].strip()))
            i += 1
            continue

        if strip.startswith("## "):
            kop = strip[3:].strip()
            anker = maak_slug(kop)
            koppen.append((kop, anker))
            uit.append('<h2 id="%s">%s</h2>' % (anker, inline(kop)))
            i += 1
            continue

        if strip.startswith("> "):
            blok = []
            while i < len(regels) and regels[i].strip().startswith("> "):
                blok.append(regels[i].strip()[2:])
                i += 1
            uit.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(blok)))
            continue

        if strip.startswith("|"):
            tabel = []
            while i < len(regels) and regels[i].strip().startswith("|"):
                tabel.append(regels[i].strip())
                i += 1
            uit.append(maak_tabel(tabel))
            continue

        if re.match(r"^[-*] ", strip):
            items = []
            while i < len(regels) and re.match(r"^[-*] ", regels[i].strip()):
                items.append(inline(regels[i].strip()[2:]))
                i += 1
            uit.append("<ul>\n%s\n</ul>" % "\n".join("  <li>%s</li>" % x for x in items))
            continue

        if re.match(r"^\d+\. ", strip):
            items = []
            while i < len(regels) and re.match(r"^\d+\. ", regels[i].strip()):
                items.append(inline(re.sub(r"^\d+\.\s*", "", regels[i].strip())))
                i += 1
            uit.append("<ol>\n%s\n</ol>" % "\n".join("  <li>%s</li>" % x for x in items))
            continue

        alinea = []
        while i < len(regels) and regels[i].strip() and not re.match(
                r"^(#{1,3} |[-*] |\d+\. |\||> |\[\[)", regels[i].strip()):
            alinea.append(regels[i].strip())
            i += 1
        p = "<p>%s</p>" % inline(" ".join(alinea))
        if eerste and not koppen:
            p = ('<div class="kb-antwoord"><span class="kb-antwoord__label">'
                 '<i class="fa-solid fa-circle-check" aria-hidden="true"></i> Kort antwoord'
                 '</span>%s</div>' % p)
        eerste = False
        uit.append(p)

    if uit and 'kb-antwoord' not in uit[0]:
        fout(bestand, "de tekst begint niet met een alinea. Het antwoord op de "
                      "zoekvraag hoort in de eerste twee zinnen.")
    return "\n".join("        " + x for x in uit), koppen


def maak_tabel(regels):
    rijen = [[c.strip() for c in r.strip("|").split("|")] for r in regels]
    if len(rijen) >= 2 and all(re.fullmatch(r":?-{2,}:?", c) for c in rijen[1]):
        kop, lijf = rijen[0], rijen[2:]
    else:
        kop, lijf = rijen[0], rijen[1:]
    uit = ['<div class="kb-tabel"><table>', "  <thead><tr>"]
    uit += ["    <th>%s</th>" % inline(c) for c in kop]
    uit += ["  </tr></thead>", "  <tbody>"]
    for rij in lijf:
        uit.append("    <tr>%s</tr>" % "".join(
            '<td class="kb-prijs">%s</td>' % inline(c) if c.startswith("€") else
            "<td>%s</td>" % inline(c) for c in rij))
    uit += ["  </tbody>", "</table></div>"]
    return "\n".join(uit)


def maak_slug(t):
    t = t.lower()
    for van, naar in [("á", "a"), ("é", "e"), ("ë", "e"), ("í", "i"), ("ï", "i"),
                      ("ó", "o"), ("ö", "o"), ("ú", "u"), ("ü", "u"), ("²", "2")]:
        t = t.replace(van, naar)
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


# ------------------------------------------------------------ huisregels

# Wat Jonathan niet doet of niet op zijn site wil. Elk artikel en elke
# gegenereerde pagina gaat hier doorheen; een treffer blokkeert de bouw.
VERBODEN = [
    (r"\bpannen|\bdakpan|pannendak", "pannen en pannendaken: JS Techniek doet alleen platte daken"),
    (r"\b(schuin|hellend)e?\s+dak", "schuine of hellende daken: JS Techniek doet alleen platte daken"),
    (r"\bvve\b|\bvve'?s\b|\bvve-|vereniging(en)? van eigenaren", "VvE's: daar wil Jonathan niets mee"),
    (r"loodgiet", "loodgieterswerk: dat doet JS Techniek niet meer"),
    (r"\belektra\b|elektricien|\bmeterkast", "elektra: dat doet JS Techniek niet"),
    (r"\basbest", "asbest is geen onderwerp op deze site"),
    (r"24/7|24 uur per dag|dag en nacht", "de site belooft geen bereikbaarheid dag en nacht"),
    (r"\bgegarandeerd|\bgarandeer", "geen resultaat garanderen"),
    (r"binnen (een|1|2|twee|24) uur", "geen reactietijd beloven"),
    (r"(\bwij\b|\bwe\b|JS Techniek)\s+(leggen|plaatsen|verwerken|gebruiken|werken met|"
     r"bieden|doen)\s+(ook\s+)?(epdm|kunststof|pvc|tpo|rubber|sedum|groene? da)",
     "JS Techniek werkt zelf alleen met bitumen; andere bedekkingen alleen als vergelijking"),
    (r"Den Dungen|Spoed Dak Techniek|Wonera|lekkagegids|dakdekkerloket|spoedbijlekkage|"
     r"spoedcentrale|LeadHuis", "geen andere merken of sites noemen"),
]


def controleer_taal(tekst, bestand, waar):
    """De vaste schrijfregels, automatisch afgedwongen."""
    if "—" in tekst or "–" in tekst:
        fout(bestand, "%s bevat een gedachtestreepje. Gebruik een komma, "
                      "dubbele punt of punt." % waar)
    for m in re.finditer(r"(?:(?<=\s)|^)(['’](?:t|n|m)|[zmd]['’](?:n|r))\b", tekst, re.M):
        fout(bestand, "%s bevat de afkorting %s. Schrijf het voluit." % (waar, m.group(1)))
        break
    if re.search(r"\b(jij|jouw|jullie|je|jouwe)\b", tekst, re.I):
        fout(bestand, "%s spreekt de lezer aan met jij, je of jouw. De site gebruikt u." % waar)
    for verboden, waarom in VERBODEN:
        m = re.search(verboden, tekst, re.I)
        if m:
            fout(bestand, "%s bevat '%s': %s." % (waar, m.group(0), waarom))
    controleer_bedragen(tekst, bestand, waar)


def controleer_bedragen(tekst, bestand, waar):
    """Afspraak: prijzen altijd als range (€ X tot € Y), nooit een vast bedrag."""
    if re.search(r"\d\s*(euro|eur)\b", tekst, re.I):
        fout(bestand, "%s noemt een bedrag in 'euro'. Schrijf bedragen als € X tot € Y." % waar)
    for m in re.finditer(r"€\s?\d[\d.]*(,\d+)?", tekst):
        voor = tekst[max(0, m.start() - 6):m.start()]
        na = tekst[m.end():m.end() + 6]
        if re.search(r"\btot\s*$", voor) or re.match(r"\s*tot\b", na):
            continue
        fout(bestand, "%s noemt een los bedrag (%s). Prijzen altijd als range: "
                      "€ X tot € Y." % (waar, m.group(0)))


# -------------------------------------------------------------- artikel

def jpeg_maat(pad):
    """Breedte en hoogte uit een JPEG-kop, zonder pakketten."""
    data = open(pad, "rb").read()
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        mk = data[i + 1]
        if mk in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return (int.from_bytes(data[i + 7:i + 9], "big"),
                    int.from_bytes(data[i + 5:i + 7], "big"))
        if mk in (0xD8, 0x01, 0xFF) or 0xD0 <= mk <= 0xD7:
            i += 2 if mk != 0xFF else 1
            continue
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    return None


# Op deze foto's staan dakpannen in beeld (buren of achtergrond). Pannen horen
# niet bij JS Techniek, dus deze foto's niet in de kennisbank gebruiken.
FOTOS_MET_PANNEN = {"bitumen-plat-dak-dakkapel-aansluiting.jpg",
                    "zinkwerk-erker-afdekking-detail.jpg",
                    "zinkwerk-erker-afdekking-montage.jpg"}


def foto_info(naam, bestand):
    if naam in FOTOS_MET_PANNEN:
        fout(bestand, "foto %s heeft dakpannen in beeld, kies een andere" % naam)
    pad = os.path.join(BASIS, "images", "web", naam)
    if not os.path.exists(pad):
        fout(bestand, "foto images/web/%s bestaat niet" % naam)
        return None
    maat = jpeg_maat(pad) or (1400, 1050)
    return {"src": "/images/web/" + naam, "breed": maat[0], "hoog": maat[1]}


def lees_artikel(pad, vandaag):
    bestand = os.path.basename(pad)
    rauw = open(pad, encoding="utf-8").read()
    kop, lijf = lees_kop(rauw, bestand)
    if not kop:
        return None

    kop["slug"] = kop.get("slug") or bestand[:-3]
    if kop["slug"] != bestand[:-3]:
        fout(bestand, "slug '%s' moet gelijk zijn aan de bestandsnaam" % kop["slug"])

    for sleutel in VERPLICHT:
        if not kop.get(sleutel):
            fout(bestand, "mist '%s' in de kop" % sleutel)

    if kop.get("rubriek") and kop["rubriek"] not in RUBRIEKEN:
        fout(bestand, "rubriek '%s' bestaat niet. Kies uit: %s"
             % (kop["rubriek"], ", ".join(RUBRIEKEN)))
    if kop.get("dienst") and kop["dienst"] not in DIENSTEN:
        fout(bestand, "dienst '%s' bestaat niet. Kies uit: %s"
             % (kop["dienst"], ", ".join(DIENSTEN)))
    if not re.fullmatch(r"[a-z0-9-]+", kop["slug"]):
        fout(bestand, "slug '%s' mag alleen kleine letters, cijfers en streepjes" % kop["slug"])

    pt = kop.get("paginatitel", "")
    if len(pt) > 65:
        fout(bestand, "paginatitel is %d tekens, maximaal 65" % len(pt))
    if pt and not pt.endswith("| " + MERK):
        fout(bestand, "paginatitel eindigt op '| %s'" % MERK)
    be = kop.get("beschrijving", "")
    if be and not (105 <= len(be) <= 165):
        fout(bestand, "beschrijving is %d tekens, moet tussen 105 en 165" % len(be))

    vragen = kop.get("vragen") or []
    if not isinstance(vragen, list) or not (3 <= len(vragen) <= 6):
        fout(bestand, "er moeten 3 tot 6 vragen in de kop staan, nu %d"
             % (len(vragen) if isinstance(vragen, list) else 0))
        vragen = vragen if isinstance(vragen, list) else []
    for v in vragen:
        if not isinstance(v, dict) or not v.get("vraag") or not v.get("antwoord"):
            fout(bestand, "elke vraag heeft een 'vraag' en een 'antwoord'")

    for sleutel in ("gepubliceerd", "bijgewerkt"):
        if kop.get(sleutel) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(kop[sleutel])):
            fout(bestand, "%s moet JJJJ-MM-DD zijn" % sleutel)
    if kop.get("bijgewerkt", "") < kop.get("gepubliceerd", ""):
        fout(bestand, "bijgewerkt ligt voor gepubliceerd")
    if kop.get("bijgewerkt", "") > vandaag and kop.get("gepubliceerd", "") <= vandaag:
        fout(bestand, "bijgewerkt ligt in de toekomst")

    rubriek = RUBRIEKEN.get(kop.get("rubriek"), {})
    kop["foto"] = kop.get("foto") or rubriek.get("foto", "")
    kop["foto_alt"] = kop.get("foto_alt") or rubriek.get("foto_alt", "")
    kop["_foto"] = foto_info(kop["foto"], bestand) if kop["foto"] else None

    controleer_taal(rauw, bestand, "het artikel")

    inhoud, koppen = naar_html(lijf, bestand)
    if len(koppen) < 2:
        fout(bestand, "minder dan twee H2's. Elk artikel beantwoordt meerdere vervolgvragen.")

    woorden = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", inhoud)))
    if woorden < 500:
        fout(bestand, "maar %d woorden. Onder de 500 is het te dun om te ranken." % woorden)

    links = re.findall(r'href="(/[^"#?]*)', inhoud)
    if not any(not l.startswith("/kennisbank") for l in links):
        fout(bestand, "linkt niet naar een dienstpagina. Zet minstens een link naar "
                      "/dakwerken, /zinkwerk, /noodreparaties of /contact in de tekst.")

    tekst_laag = (kop.get("titel", "") + " " + lijf).lower().replace("²", "2")
    mist = [w for w in re.findall(r"\w+", (kop.get("zoekwoord") or "").lower())
            if w not in tekst_laag]
    if mist:
        waarschuwingen.append("%s: uit het zoekwoord '%s' ontbreekt %s in de tekst"
                              % (bestand, kop["zoekwoord"], " en ".join(mist)))

    kop["_inhoud"] = inhoud
    kop["_koppen"] = koppen
    kop["_vragen"] = vragen
    kop["_woorden"] = woorden
    return kop


# ------------------------------------------------------------- opbouwen

def nl_datum(iso):
    j, m, d = str(iso).split("-")
    return "%d %s %s" % (int(d), MAANDEN[int(m) - 1], j)


def euro(n):
    return "€ " + "{:,}".format(int(n)).replace(",", ".")


def sjabloon(naam):
    return open(os.path.join(SJABLOON, naam), encoding="utf-8").read()


def vul(tekst, waarden):
    """Vult {{sleutels}} in een keer in. Ingevoegde tekst wordt niet opnieuw
    doorzocht, dus een {{ in een artikel kan het sjabloon niet breken."""
    open_ = set(re.findall(r"\{\{([a-z_]+)\}\}", tekst)) - set(waarden)
    if open_:
        raise SystemExit("Sjabloon niet volledig ingevuld, nog open: %s" % open_)
    return re.sub(r"\{\{([a-z_]+)\}\}", lambda m: str(waarden[m.group(1)]), tekst)


_SCHIL = {}


def schil():
    """Menu (met tracking-noscript, knoppen en menuscript) en footer (met
    cookiemelding) uit dakwerken.html, met absolute paden."""
    if _SCHIL:
        return _SCHIL["menu"], _SCHIL["voet"]
    bron = open(BRONPAGINA, encoding="utf-8").read()
    try:
        a = bron.index("<!-- Google Tag Manager (noscript) -->")
        b = bron.index("<!-- ===== HERO ===== -->")
        c = bron.index("<!-- ===== FOOTER ===== -->")
        d = bron.rindex("</body>")
    except ValueError:
        raise SystemExit("dakwerken.html: menu of footer niet gevonden. Zijn de "
                         "markeringen (GTM noscript, HERO, FOOTER) veranderd?")

    def absoluut(t):
        return re.sub(r'\b(src|href)="(?![/#]|https?:|tel:|mailto:|data:)', r'\1="/', t)

    _SCHIL["menu"] = absoluut(bron[a:b]).rstrip() + "\n"
    _SCHIL["voet"] = absoluut(bron[c:d]).rstrip() + "\n"
    if 'href="/kennisbank"' not in _SCHIL["menu"]:
        waarschuwingen.append("het menu in dakwerken.html linkt nog niet naar /kennisbank")
    return _SCHIL["menu"], _SCHIL["voet"]


def schema_blok(obj):
    return ('  <script type="application/ld+json">\n  %s\n  </script>'
            % json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


UITGEVER = {"@type": "Organization", "@id": SITE + "/#business", "name": MERK,
            "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/images/logo.png"}}


def kruimel(stappen):
    """stappen: lijst van (naam, pad of None voor de huidige pagina)."""
    delen = []
    for naam, pad in stappen:
        if pad:
            delen.append('<a href="%s">%s</a>' % (pad, html.escape(naam)))
        else:
            delen.append('<span aria-current="page">%s</span>' % html.escape(naam))
    return ('<nav class="kb-kruimel" aria-label="Kruimelpad">%s</nav>'
            % '<span class="kb-kruimel__sep" aria-hidden="true">/</span>'.join(delen))


def kruimel_schema(stappen):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": n, "name": naam,
                                 "item": SITE + pad}
                                for n, (naam, pad) in enumerate(stappen, start=1)]}


def hero(foto, foto_alt, stappen, label, titel, intro, meta="", extra=""):
    img = ""
    if foto:
        img = ('<img class="kb-hero__foto" src="%s" alt="%s" width="%d" height="%d" '
               'fetchpriority="high">' % (foto["src"], html.escape(foto_alt, quote=True),
                                          foto["breed"], foto["hoog"]))
    return ('<section class="kb-hero">\n  %s\n  <div class="kb-hero__inner">\n'
            '    %s\n    <span class="kb-label">%s</span>\n    <h1>%s</h1>\n'
            '    <p class="kb-hero__intro">%s</p>\n%s%s  </div>\n</section>\n'
            % (img, kruimel(stappen), html.escape(label), html.escape(titel),
               html.escape(intro), meta, extra))


def kaart(a):
    return ('      <a class="kb-kaart" href="/kennisbank/%s">\n'
            '        <span class="kb-kaart__rubriek">%s</span>\n'
            '        <h3>%s</h3>\n'
            '        <p>%s</p>\n'
            '        <span class="kb-kaart__meer">Lees het antwoord '
            '<i class="fa-solid fa-arrow-right" aria-hidden="true"></i></span>\n'
            '      </a>' % (a["slug"], RUBRIEKEN[a["rubriek"]]["naam"],
                            html.escape(a["titel"]), html.escape(a["samenvatting"])))


def faq_sectie(vragen, kop="Veelgestelde vragen"):
    items = "\n".join(
        '      <div class="faq-item">\n'
        '        <h3 class="faq-kop"><button class="faq-question" type="button" '
        'aria-controls="faq-%d" aria-expanded="false">\n'
        '          <span>%s</span>\n'
        '          <i class="fa-solid fa-plus" aria-hidden="true"></i>\n'
        '        </button></h3>\n'
        '        <div class="faq-answer" id="faq-%d"><div><p>%s</p></div></div>\n'
        '      </div>' % (n, html.escape(v), n, html.escape(a))
        for n, (v, a) in enumerate(vragen, start=1))
    return ('<section class="kb-faq" aria-labelledby="faq-titel">\n'
            '  <div class="kb-container kb-container--smal">\n'
            '    <span class="kb-overline">Nog vragen?</span>\n'
            '    <h2 id="faq-titel">%s</h2>\n'
            '    <div class="faq-list">\n%s\n    </div>\n'
            '  </div>\n</section>\n' % (kop, items))


def faq_schema(vragen):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": v,
                            "acceptedAnswer": {"@type": "Answer", "text": a}}
                           for v, a in vragen]}


def cta_blok(kop="Wilt u weten wat uw dak nodig heeft?"):
    return ('<section class="kb-cta">\n  <div class="kb-container">\n'
            '    <div class="cta-box">\n'
            '      <p class="cta-text">%s</p>\n'
            '      <p class="cta-sub">Bel %s of stuur een WhatsApp. We komen vrijblijvend '
            'kijken en u krijgt een duidelijke prijs op papier.</p>\n'
            '      <div class="cta-knoppen">\n'
            '        <a href="%s" class="cta-button"><i class="fa-solid fa-phone" '
            'aria-hidden="true"></i> Bel %s</a>\n'
            '        <a href="/contact" class="cta-button cta-button--licht">'
            'Offerte aanvragen</a>\n'
            '      </div>\n    </div>\n  </div>\n</section>\n'
            % (html.escape(kop), TELEFOON, TEL_LINK, TELEFOON))


def pagina(waarden):
    menu, voet = schil()
    basis = {
        "stijl": sjabloon("stijl.css"), "menu": menu, "voet": voet,
        "gebouwd": GEBOUWD, "ogtype": "website", "extra_meta": "",
    }
    basis.update(waarden)
    return vul(sjabloon("pagina.html"), basis)


def bouw_artikel(a, alle):
    r = RUBRIEKEN[a["rubriek"]]
    pad = "/kennisbank/" + a["slug"]
    url = SITE + pad
    stappen = [("Home", "/"), ("Kennisbank", "/kennisbank"),
               (r["naam"], "/kennisbank/rubriek/" + a["rubriek"]), (a["titel"], pad)]
    minuten = max(2, int(math.ceil(a["_woorden"] / 200.0)))
    vragen = [(v["vraag"], v["antwoord"]) for v in a["_vragen"]]
    foto = a["_foto"]

    artikel_schema = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": a["titel"], "description": a["beschrijving"],
        "datePublished": a["gepubliceerd"], "dateModified": a["bijgewerkt"],
        "inLanguage": "nl-NL", "mainEntityOfPage": url,
        "author": {"@type": "Organization", "name": MERK, "url": SITE + "/"},
        "publisher": UITGEVER,
        "about": a["zoekwoord"],
    }
    if foto:
        artikel_schema["image"] = SITE + foto["src"]
    schema = "\n".join([schema_blok(artikel_schema), schema_blok(faq_schema(vragen)),
                        schema_blok(kruimel_schema(stappen[:3] + [(a["titel"], pad)]))])

    meta = ('    <p class="kb-meta">'
            '<span><i class="fa-regular fa-calendar" aria-hidden="true"></i> Bijgewerkt op '
            '<time datetime="%s">%s</time></span>'
            '<span><i class="fa-regular fa-clock" aria-hidden="true"></i> %d minuten lezen</span>'
            '<span><i class="fa-solid fa-helmet-safety" aria-hidden="true"></i> '
            'JS Techniek, Den Helder</span></p>\n'
            % (a["bijgewerkt"], nl_datum(a["bijgewerkt"]), minuten))

    inhoudsopgave = "\n".join(
        '          <li><a href="#%s">%s</a></li>' % (anker, inline(kop))
        for kop, anker in a["_koppen"])

    d = DIENSTEN[a["dienst"]]
    dienstblok = ('        <aside class="kb-dienst" aria-label="Dienst">\n'
                  '          <div class="kb-dienst__icoon"><i class="fa-solid fa-house-chimney-crack" '
                  'aria-hidden="true"></i></div>\n'
                  '          <div>\n'
                  '            <p class="kb-dienst__kop">%s</p>\n'
                  '            <p>%s</p>\n'
                  '            <a href="/%s" class="kb-dienst__link">%s '
                  '<i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a>\n'
                  '          </div>\n        </aside>' % (d["kop"], d["tekst"], a["dienst"], d["knop"]))

    zij = ('    <aside class="kb-zij">\n'
           '      <nav class="kb-inhoud" aria-label="In dit artikel">\n'
           '        <p class="kb-zij__kop">In dit artikel</p>\n'
           '        <ol>\n%s\n        </ol>\n      </nav>\n'
           '      <div class="kb-actie">\n'
           '        <p class="kb-actie__kop">Twijfelt u over uw dak?</p>\n'
           '        <p>We kijken vrijblijvend mee. Bel, app of vraag een offerte aan.</p>\n'
           '        <a href="%s" class="kb-knop"><i class="fa-solid fa-phone" aria-hidden="true">'
           '</i> %s</a>\n'
           '        <a href="%s" class="kb-knop kb-knop--whatsapp" target="_blank" rel="noopener">'
           '<i class="fa-brands fa-whatsapp" aria-hidden="true"></i> WhatsApp</a>\n'
           '        <a href="/contact" class="kb-actie__link">Offerte aanvragen</a>\n'
           '      </div>\n    </aside>\n' % (inhoudsopgave, TEL_LINK, TELEFOON, WHATSAPP))

    verwant = [x for x in alle if x["slug"] != a["slug"] and x["rubriek"] == a["rubriek"]]
    verwant += [x for x in alle if x["slug"] != a["slug"] and x["rubriek"] != a["rubriek"]]
    verder = ""
    if verwant:
        verder = ('<section class="kb-sectie kb-sectie--vlak" aria-labelledby="verder-titel">\n'
                  '  <div class="kb-container">\n'
                  '    <span class="kb-overline">Kennisbank</span>\n'
                  '    <h2 id="verder-titel">Verder lezen</h2>\n'
                  '    <div class="kb-raster">\n%s\n    </div>\n'
                  '  </div>\n</section>\n' % "\n".join(kaart(x) for x in verwant[:3]))

    inhoud = (hero(foto, a["foto_alt"], stappen[:3] + [(a["titel"], None)], r["naam"],
                   a["titel"], a["samenvatting"], meta)
              + '<div class="kb-wrap">\n'
              + '    <article class="kb-tekst">\n%s\n%s\n    </article>\n' % (a["_inhoud"], dienstblok)
              + zij + '</div>\n'
              + faq_sectie(vragen) + verder + cta_blok())

    ogbeeld = SITE + (foto["src"] if foto else "/images/og-image.png")
    return pagina({
        "paginatitel": html.escape(a["paginatitel"], quote=True),
        "beschrijving": html.escape(a["beschrijving"], quote=True),
        "canonical": url, "ogtitel": html.escape(a["titel"], quote=True),
        "ogbeeld": ogbeeld, "ogbeeld_alt": html.escape(a["foto_alt"], quote=True),
        "ogtype": "article",
        "extra_meta": ('  <meta property="article:published_time" content="%s">\n'
                       '  <meta property="article:modified_time" content="%s">\n'
                       % (a["gepubliceerd"], a["bijgewerkt"])),
        "schema": schema, "inhoud": inhoud,
    })


def bouw_hub(alle):
    pad = "/kennisbank"
    stappen = [("Home", "/"), ("Kennisbank", pad)]
    rubrieken = [(s, r, [a for a in alle if a["rubriek"] == s]) for s, r in RUBRIEKEN.items()]
    rubrieken = [x for x in rubrieken if x[2]]

    chips = ('    <ul class="kb-chips">\n%s\n    </ul>\n' % "\n".join(
        '      <li><a href="#r-%s">%s <span>%d</span></a></li>' % (s, r["naam"], len(lijst))
        for s, r, lijst in rubrieken)) if rubrieken else ""

    secties = []
    nieuw = alle[:3]
    if len(alle) > 6:
        secties.append(
            '<section class="kb-sectie" aria-labelledby="r-nieuw">\n'
            '  <div class="kb-container">\n'
            '    <span class="kb-overline">Net verschenen</span>\n'
            '    <h2 id="r-nieuw">Nieuwste artikelen</h2>\n'
            '    <div class="kb-raster">\n%s\n    </div>\n  </div>\n</section>\n'
            % "\n".join(kaart(a) for a in nieuw))
    for n, (s, r, lijst) in enumerate(rubrieken):
        vlak = " kb-sectie--vlak" if (n + len(secties)) % 2 else ""
        meer = ('    <p class="kb-meerlink"><a href="/kennisbank/rubriek/%s">Alle artikelen over '
                '%s <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></p>\n'
                % (s, r["naam"].lower()))
        secties.append(
            '<section class="kb-sectie%s" id="r-%s" aria-labelledby="r-%s-titel">\n'
            '  <div class="kb-container">\n'
            '    <span class="kb-overline">%d %s</span>\n'
            '    <h2 id="r-%s-titel">%s</h2>\n'
            '    <p class="kb-sectie__intro">%s</p>\n'
            '    <div class="kb-raster">\n%s\n    </div>\n%s'
            '  </div>\n</section>\n'
            % (vlak, s, s, len(lijst), "artikel" if len(lijst) == 1 else "artikelen",
               s, r["naam"], html.escape(r["intro"]),
               "\n".join(kaart(a) for a in lijst[:6]), meer))

    schema = "\n".join([
        schema_blok({"@context": "https://schema.org", "@type": "CollectionPage",
                     "name": "Kennisbank JS Techniek", "url": SITE + pad,
                     "description": "Antwoorden over platte daken, bitumen, lekkage, zinkwerk "
                                    "en kosten.",
                     "isPartOf": {"@type": "WebSite", "name": MERK, "url": SITE + "/"},
                     "publisher": UITGEVER}),
        schema_blok(kruimel_schema(stappen))])

    foto = foto_info("bitumen-plat-dak-lichtkoepel-naden.jpg", "kennisbank")
    inhoud = (hero(foto, "Nieuwe bitumen dakbedekking met strak gebrande naden op een plat dak",
                   [("Home", "/"), ("Kennisbank", None)], "Kennisbank",
                   "Kennisbank over platte daken, bitumen en zinkwerk",
                   "Eerlijke antwoorden op de vragen die we elke week horen: wat het kost, "
                   "hoe lang het meegaat en wat u bij een lekkage doet. Geschreven vanuit de "
                   "praktijk in Den Helder en de rest van Noord-Holland.", extra=chips)
              + "".join(secties) + cta_blok("Staat uw vraag er niet tussen?"))
    return pagina({
        "paginatitel": "Kennisbank platte daken en bitumen | JS Techniek",
        "beschrijving": "Antwoorden over platte daken, bitumen dakbedekking, lekkage, zinkwerk "
                        "en kosten. Uitgelegd door JS Techniek uit Den Helder.",
        "canonical": SITE + pad, "ogtitel": "Kennisbank JS Techniek",
        "ogbeeld": SITE + foto["src"], "ogbeeld_alt": "Bitumen dakbedekking op een plat dak",
        "schema": schema, "inhoud": inhoud,
    })


KOSTEN_VRAGEN = [
    ("Zijn deze bedragen inclusief btw?",
     "Ja. Alle bedragen in de kennisbank zijn inclusief 21% btw, materiaal en arbeid."),
    ("Waarom staat er een bandbreedte en geen vaste prijs?",
     "Omdat geen plat dak hetzelfde is. De staat van de ondergrond, de bereikbaarheid, het "
     "aantal aansluitingen en wat er onder de bedekking zit, maken samen het verschil. Een "
     "vaste prijs krijgt u nadat we het dak gezien hebben."),
    ("Kost langskomen iets?",
     "Nee. We komen vrijblijvend kijken en u krijgt daarna een prijs op papier. U zit nergens "
     "aan vast."),
]


def prijstabel():
    rijen = "\n".join(
        '      <tr><td>%s</td><td class="kb-prijs">%s tot %s<br><span class="kb-eenheid">per %s</span></td></tr>'
        % (html.escape(k["naam"]), euro(k["vanaf"]), euro(k["tot"]), k["eenheid"])
        for k in PRIJZEN["klussen"])
    return ('<section class="kb-sectie kb-sectie--vlak" aria-labelledby="prijzen-titel">\n'
            '  <div class="kb-container kb-container--smal kb-tekst">\n'
            '    <span class="kb-overline">Prijsindicaties</span>\n'
            '    <h2 id="prijzen-titel">Wat u ongeveer betaalt</h2>\n'
            '    <p>Een indicatie voor het werk dat JS Techniek doet, prijspeil %s. Alles '
            'inclusief %d%% btw, materiaal en arbeid. Wat u voor uw eigen dak betaalt, hoort u '
            'na een vrijblijvende inspectie.</p>\n'
            '    <div class="kb-tabel"><table>\n'
            '      <thead><tr><th>Klus</th><th>Indicatie inclusief btw</th></tr></thead>\n'
            '      <tbody>\n%s\n      </tbody>\n    </table></div>\n'
            '  </div>\n</section>\n' % (PRIJZEN["prijspeil"], PRIJZEN["btw"], rijen))


def bouw_rubriek(slug, alle):
    r = RUBRIEKEN[slug]
    pad = "/kennisbank/rubriek/" + slug
    stappen = [("Home", "/"), ("Kennisbank", "/kennisbank"), (r["naam"], pad)]
    inrub = [a for a in alle if a["rubriek"] == slug]

    artikelen = ('<section class="kb-sectie" aria-labelledby="artikelen-titel">\n'
                 '  <div class="kb-container">\n'
                 '    <span class="kb-overline">%d %s</span>\n'
                 '    <h2 id="artikelen-titel">Alle artikelen over %s</h2>\n'
                 '    <div class="kb-raster">\n%s\n    </div>\n'
                 '  </div>\n</section>\n'
                 % (len(inrub), "artikel" if len(inrub) == 1 else "artikelen",
                    r["naam"].lower(), "\n".join(kaart(a) for a in inrub)))

    schemas = [{"@context": "https://schema.org", "@type": "CollectionPage",
                "name": r["titel"], "url": SITE + pad, "description": r["beschrijving"],
                "isPartOf": {"@type": "WebSite", "name": MERK, "url": SITE + "/"}},
               kruimel_schema(stappen)]
    extra = ""
    if slug == "kosten":
        extra = prijstabel() + faq_sectie(KOSTEN_VRAGEN, "Vragen over prijzen")
        schemas.append(faq_schema(KOSTEN_VRAGEN))

    titel = "%s | %s" % (r["titel"], MERK)
    if len(titel) > 65:
        titel = "%s | %s" % (r["naam"], MERK)
    foto = foto_info(r["foto"], pad)
    inhoud = (hero(foto, r["foto_alt"], [("Home", "/"), ("Kennisbank", "/kennisbank"),
                                        (r["naam"], None)],
                   "Kennisbank", r["titel"], r["intro"])
              + artikelen + extra + cta_blok())
    return pagina({
        "paginatitel": html.escape(titel), "beschrijving": html.escape(r["beschrijving"], quote=True),
        "canonical": SITE + pad, "ogtitel": html.escape(r["titel"], quote=True),
        "ogbeeld": SITE + foto["src"], "ogbeeld_alt": html.escape(r["foto_alt"], quote=True),
        "schema": "\n".join(schema_blok(s) for s in schemas), "inhoud": inhoud,
    })


# -------------------------------------------------------------- sitemap

def lees_sitemap():
    """De bestaande sitemap, als lijst van (pad, lastmod, changefreq, priority)."""
    pad = os.path.join(BASIS, "sitemap.xml")
    if not os.path.exists(pad):
        return []
    uit = []
    for blok in re.findall(r"<url>(.*?)</url>", open(pad, encoding="utf-8").read(), re.S):
        veld = lambda n: (re.search(r"<%s>(.*?)</%s>" % (n, n), blok) or [None, ""])[1]
        loc = veld("loc").replace(SITE, "") or "/"
        uit.append((loc, veld("lastmod"), veld("changefreq") or "monthly",
                    veld("priority") or "0.5"))
    return uit


def bestaat(pad):
    if pad == "/":
        return True
    p = os.path.join(BASIS, pad.strip("/"))
    return os.path.exists(p + ".html") or os.path.exists(os.path.join(p, "index.html"))


def bouw_sitemap(alle, rubrieken):
    regels = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    def blok(pad, lastmod, freq, prio):
        return ("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n"
                "    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n  </url>"
                % (SITE, "/" if pad == "/" else pad, lastmod, freq, prio))

    # De vaste pagina's blijven zoals ze in de sitemap stonden. Wat niet (meer)
    # bestaat, gaat eruit: een sitemap met 404's kost vertrouwen bij Google.
    for pad, lastmod, freq, prio in lees_sitemap():
        if pad.startswith("/kennisbank"):
            continue
        if not bestaat(pad):
            waarschuwingen.append("sitemap: %s bestaat niet en is eruit gehaald" % pad)
            continue
        regels.append(blok(pad, lastmod, freq, prio))

    if alle:
        laatste = max(a["bijgewerkt"] for a in alle)
        regels.append(blok("/kennisbank", laatste, "daily", "0.8"))
        for s in rubrieken:
            lm = max(a["bijgewerkt"] for a in alle if a["rubriek"] == s)
            regels.append(blok("/kennisbank/rubriek/" + s, lm, "weekly", "0.6"))
        for a in alle:
            regels.append(blok("/kennisbank/" + a["slug"], a["bijgewerkt"], "monthly", "0.7"))

    regels.append("</urlset>")
    return "\n".join(regels) + "\n"


# ------------------------------------------------------------ controles

def controleer_uitvoer(paginas):
    """Laatste controle op wat we gaan wegschrijven: precies een H1, geldige
    JSON in elk schema-blok, geen link of afbeelding die nergens heen gaat, en
    de huisregels op de zichtbare tekst."""
    for pad, inhoud in paginas.items():
        n = inhoud.count("<h1")
        if n != 1:
            fout(pad, "%d keer een H1, moet er precies een zijn" % n)
        for blok in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                               inhoud, re.S):
            try:
                json.loads(blok)
            except ValueError as e:
                fout(pad, "ongeldige JSON in een schema-blok: %s" % e)
        for link in set(re.findall(r'href="(/[^"#?]*)', inhoud)):
            schoon = link.rstrip("/") or "/"
            if schoon in paginas or bestaat(schoon) or os.path.exists(
                    os.path.join(BASIS, schoon.lstrip("/"))):
                continue
            fout(pad, "interne link naar %s bestaat niet" % link)
        for src in set(re.findall(r'src="(/[^"?]+)', inhoud)):
            if not os.path.exists(os.path.join(BASIS, src.lstrip("/"))):
                fout(pad, "afbeelding of script %s bestaat niet" % src)
        titel = re.search(r"<title>(.*?)</title>", inhoud)
        if titel and len(html.unescape(titel.group(1))) > 65:
            fout(pad, "title is %d tekens, maximaal 65" % len(html.unescape(titel.group(1))))
        beschr = re.search(r'<meta name="description" content="(.*?)">', inhoud)
        if beschr and not 105 <= len(html.unescape(beschr.group(1))) <= 165:
            fout(pad, "beschrijving is %d tekens, moet tussen 105 en 165"
                 % len(html.unescape(beschr.group(1))))
        # Huisregels op de zichtbare tekst van het eigen deel van de pagina. Menu
        # en footer komen van de rest van de site en worden daar beheerd.
        hoofd = re.search(r"<main[^>]*>(.*)</main>", inhoud, re.S)
        zichtbaar = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", hoofd.group(1) if hoofd else "",
                           flags=re.S)
        zichtbaar = html.unescape(re.sub(r"<[^>]+>", " ", zichtbaar))
        controleer_taal(zichtbaar + " " + (titel.group(1) if titel else ""), pad, "de pagina")


# ----------------------------------------------------------------- main

def nieuw_artikel(slug):
    pad = os.path.join(ARTIKELEN, slug + ".md")
    if os.path.exists(pad):
        raise SystemExit("Bestaat al: " + pad)
    vandaag = date.today().isoformat()
    open(pad, "w", encoding="utf-8").write(
        "---\ntitel: \npaginatitel:  | JS Techniek\nbeschrijving: \nslug: %s\n"
        "rubriek: bitumen-en-platte-daken\nzoekwoord: \nsamenvatting: \ndienst: dakwerken\n"
        "gepubliceerd: %s\nbijgewerkt: %s\nvragen:\n  - vraag: \n    antwoord: \n"
        "  - vraag: \n    antwoord: \n  - vraag: \n    antwoord: \n---\n\n"
        "Het antwoord op de zoekvraag in de eerste twee zinnen.\n\n"
        "## Eerste vervolgvraag\n\nAntwoord in de eerste zin van de alinea.\n"
        % (slug, vandaag, vandaag))
    print("Aangemaakt: " + pad)


def opruimen(paginas):
    """Haalt oude, door dit script gebouwde pagina's weg die er niet meer horen
    (artikel verwijderd of hernoemd). Met de hand gemaakte bestanden blijven."""
    weg = []
    for map_ in (KB, os.path.join(KB, "rubriek")):
        if not os.path.isdir(map_):
            continue
        for f in os.listdir(map_):
            if not f.endswith(".html"):
                continue
            pad = "/" + os.path.relpath(os.path.join(map_, f), BASIS)[:-5]
            if pad in paginas:
                continue
            vol = os.path.join(map_, f)
            if GEBOUWD in open(vol, encoding="utf-8").read():
                os.remove(vol)
                weg.append(pad)
    return weg


def main():
    alleen_controle = "--controleer" in sys.argv
    if "--nieuw" in sys.argv:
        return nieuw_artikel(sys.argv[sys.argv.index("--nieuw") + 1])
    vandaag = date.today().isoformat()

    for k in PRIJZEN["klussen"] + PRIJZEN["voorbeelden_bitumen_vernieuwen"]:
        if not (0 < k["vanaf"] < k["tot"]):
            fout("prijzen.json", "%s: vanaf moet lager zijn dan tot" % k["naam"])

    bestanden = sorted(f for f in os.listdir(ARTIKELEN) if f.endswith(".md"))
    gelezen = [a for a in (lees_artikel(os.path.join(ARTIKELEN, f), vandaag)
                           for f in bestanden) if a]
    # Een artikel met een publicatiedatum in de toekomst staat klaar maar gaat
    # pas mee als die dag is aangebroken.
    artikelen = [a for a in gelezen if a.get("gepubliceerd", "") <= vandaag]
    ingepland = [a for a in gelezen if a.get("gepubliceerd", "") > vandaag]
    artikelen.sort(key=lambda a: (a.get("gepubliceerd", ""), a.get("bijgewerkt", "")),
                   reverse=True)

    slugs = [a["slug"] for a in gelezen]
    for s in set(slugs):
        if slugs.count(s) > 1:
            fout(s, "de slug komt %d keer voor" % slugs.count(s))

    rubrieken = [s for s in RUBRIEKEN if any(a["rubriek"] == s for a in artikelen)]
    paginas = {}
    if not fouten:
        paginas["/kennisbank"] = bouw_hub(artikelen)
        for slug in rubrieken:
            paginas["/kennisbank/rubriek/" + slug] = bouw_rubriek(slug, artikelen)
        for a in artikelen:
            paginas["/kennisbank/" + a["slug"]] = bouw_artikel(a, artikelen)
        controleer_uitvoer(paginas)

    print("Kennisbank JS Techniek")
    print("  artikelen live    : %d" % len(artikelen))
    print("  ingepland         : %d%s" % (len(ingepland), "".join(
        "\n    %s  %s" % (a["gepubliceerd"], a["slug"]) for a in
        sorted(ingepland, key=lambda a: a["gepubliceerd"]))))
    print("  pagina's klaar    : %d" % len(paginas))
    for w in waarschuwingen:
        print("  let op: " + w)

    if fouten:
        print("\n%d FOUT(EN), er is niets weggeschreven:" % len(fouten))
        for f in fouten:
            print("  - " + f)
        return 1

    al = len(waarschuwingen)
    sitemap = bouw_sitemap(artikelen, rubrieken)
    for w in waarschuwingen[al:]:
        print("  let op: " + w)

    if alleen_controle:
        print("\nAlles in orde. Niets weggeschreven (--controleer).")
        return 0

    for pad, inhoud in paginas.items():
        bestand = os.path.join(BASIS, pad.lstrip("/") + ".html")
        os.makedirs(os.path.dirname(bestand), exist_ok=True)
        open(bestand, "w", encoding="utf-8").write(inhoud)
    weg = opruimen(paginas)
    open(os.path.join(BASIS, "sitemap.xml"), "w", encoding="utf-8").write(sitemap)

    print("\nWeggeschreven:")
    for pad in sorted(paginas):
        print("  %s.html" % pad.lstrip("/"))
    for pad in weg:
        print("  verwijderd: %s.html" % pad.lstrip("/"))
    print("  sitemap.xml bijgewerkt (%d URL's)" % sitemap.count("<url>"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
