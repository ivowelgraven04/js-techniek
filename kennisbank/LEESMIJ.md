# Kennisbank JS Techniek

Live op https://jschoutentechniek.com/kennisbank. Elke werkdag (maandag tot en met
vrijdag) komt er een artikel bij via de geplande taak `jst-kennisbank`.

Doel: JS Techniek terug naar de top van Google voor platte daken in Noord-Holland,
en vaker genoemd worden in antwoorden van AI-assistenten. Elk artikel beantwoordt
precies een vraag die mensen echt stellen.

## Zo werkt het

- `artikelen/<slug>.md`: de artikelen, Markdown met een kop (zie hieronder).
- `bouw.py`: maakt er HTML van. Geen pakketten nodig.
- `sjabloon/pagina.html` en `sjabloon/stijl.css`: de opmaak. Menu, footer,
  knoppen en cookiemelding komen bij elke bouw uit `dakwerken.html`, zodat de
  kennisbank altijd gelijk loopt met de rest van de site.
- `prijzen.json`: de enige bron voor bedragen. Ranges aan de bovenkant van de markt.
- `ONDERWERPEN.md`: de wachtrij met vragen, in volgorde van prioriteit.

Uitvoer: `kennisbank.html` (overzicht), `kennisbank/<slug>.html` (artikelen),
`kennisbank/rubriek/<slug>.html` (rubrieken) en een bijgewerkte `sitemap.xml`.
Bron, sjablonen en json gaan niet mee naar Vercel (`.vercelignore`).

```
python3 kennisbank/bouw.py --nieuw <slug>   leeg artikel aanmaken
python3 kennisbank/bouw.py --controleer     alles controleren, niets schrijven
python3 kennisbank/bouw.py                  bouwen en sitemap bijwerken
```

Faalt een controle, dan schrijft het script niets weg. Een artikel met
`gepubliceerd` in de toekomst staat klaar en gaat pas mee op die datum.

## De kop van een artikel

```
---
titel: Wat kost een plat dak vervangen per m²?            (de vraag zelf, wordt de H1)
paginatitel: Wat kost een plat dak vervangen per m²? | JS Techniek   (max 65 tekens)
beschrijving: (105 tot 165 tekens, met het antwoord erin)
slug: wat-kost-een-plat-dak-vervangen-per-m2            (gelijk aan de bestandsnaam)
rubriek: kosten | bitumen-en-platte-daken | lekkage-en-schade | zinkwerk-en-goten
zoekwoord: kosten plat dak vervangen per m2
samenvatting: (een of twee zinnen voor de kaartjes en de hero)
dienst: dakwerken | zinkwerk | noodreparaties
gepubliceerd: 2026-11-10                                (nooit terugdateren)
bijgewerkt: 2026-11-10
foto: bestandsnaam uit images/web (optioneel, anders die van de rubriek)
foto_alt: beschrijving van de foto
vragen:                                                 (3 tot 6, worden FAQ-schema)
  - vraag: ...
    antwoord: ...
---
```

## Schrijfregels

1. **De eerste alinea is het antwoord**, in twee zinnen. Die wordt het kader
   "Kort antwoord" en is wat Google en AI-assistenten overnemen.
2. Daarna een H2 per vervolgvraag (minstens twee), met het antwoord in de eerste
   zin van de alinea. Tabellen en opsommingen waar dat helpt.
3. Een kopje "Wat wij zien in Den Helder en omgeving" of "in Noord-Holland":
   regionaal en vanuit de praktijk, zonder verzonnen projecten of klanten.
4. Minstens 500 woorden, liefst 800 tot 1.100.
5. Linken: minstens een dienstpagina (`/dakwerken`, `/zinkwerk`,
   `/noodreparaties`, `/contact`) en waar het past andere artikelen.
6. Aanspreken met **u**. Geen jij, je, jouw. Geen 't, 'n, z'n.
7. **Geen gedachtestreepjes** (— of –). Gebruik een komma, dubbele punt of punt.

## Wat nooit in een artikel staat

Het script blokkeert dit automatisch, maar ook zonder script geldt:

- **Pannen, pannendaken, schuine of hellende daken.** JS Techniek doet alleen platte daken.
  Ook geen foto's met dakpannen in beeld.
- **VvE's.** Daar wil Jonathan niets mee te maken hebben.
- **Loodgieterswerk en elektra.**
- **Andere bedekkingen als eigen dienst.** JS Techniek werkt uitsluitend met bitumen.
  EPDM en andere platte daken mogen alleen als vergelijking ("waarom bitumen
  vaak stabieler is dan EPDM"), nooit "wij leggen ook EPDM".
- **Vaste bedragen.** Altijd een range uit `prijzen.json`, geschreven als
  `€ 90 tot € 135`, inclusief btw. Ranges liggen bewust ruim aan de bovenkant
  van de markt.
- **Beloftes**: geen 24/7, geen "gegarandeerd", geen reactietijden ("binnen een uur").
  Wel toegestaan want bevestigd: 10 jaar garantie op een nieuw dak, 25 jaar in Noord-Holland.
- Verzonnen reviews, klanten, projecten of cijfers.
- Andere merken of sites (Wonera, Spoed Dak Techniek, LeadHuis en het netwerk).
  Teksten van die sites nooit overnemen; elk artikel is nieuw geschreven.
- Asbest.

## Na het bouwen

1. Bekijk het artikel lokaal of na de deploy op de live URL.
2. Commit alleen de eigen bestanden met expliciete paden (nooit `git add -A`):
   `kennisbank/artikelen/<slug>.md`, `kennisbank/ONDERWERPEN.md`, de gebouwde
   `kennisbank*.html`-bestanden en `sitemap.xml`.
3. Push naar `main`; Vercel zet het binnen een minuut live.
4. Controleer dat de nieuwe URL een 200 geeft en dien de sitemap in bij Search
   Console (`sc-domain:jschoutentechniek.com`).
