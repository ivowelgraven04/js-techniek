// Single source of truth for all repeated content across LP's.
// Update here once, propagates everywhere.

export const company = {
  name: 'JS Techniek',
  legalName: 'JS Techniek',
  kvk: '70974306',
  phone: '+31 6 12602082',
  phoneRaw: '+31612602082',          // for tel: href
  phoneDisplay: '06 12 60 20 82',    // formatted for display
  whatsappRaw: '31612602082',        // for wa.me/ href
  email: 'info@jschoutentechniek.com',
  domain: 'jschoutentechniek.com',
  reviewsRating: '4,9',
  reviewsCount: 50,
  yearsActive: 25,
  projectsCount: 2500,
  warrantyYearsBitumen: 10,
  emergencyResponseMinutes: 30,
} as const;

export const serviceArea = {
  tier1: [
    'Den Helder',
    'Anna Paulowna',
    'Breezand',
    'Julianadorp',
    'Callantsoog',
    "'t Zand",
    'Oudesluis',
    'Wieringerwaard',
  ],
  tier2: [
    'Sint Maartensvlotbrug',
    'Sint Maartensbrug',
    'Sint Maartenszee',
    'Schagerbrug',
    'Kolhorn',
    'Hippolytushoef',
    'Den Oever',
    'Westerland',
    'Slootdorp',
    'Middenmeer',
    'Wieringerwerf',
    'Kreileroord',
    'Schagen',
    'Petten',
    'Burgerbrug',
    'Warmenhuizen',
    'Tuitjenhorn',
    'Dirkshorn',
  ],
} as const;

export const allServiceAreaCities = [...serviceArea.tier1, ...serviceArea.tier2];

export type Testimonial = {
  quote: string;
  name: string;
  location: string;
  date?: string;
};

// Echte Google Reviews (bron: MoF/_ad-copy.md reviews-carousel).
// TODO (klant levert): plaats + datum verifiëren voor elke review.
export const testimonialsLekkage: Testimonial[] = [
  {
    quote: 'Toppers, vooral bij calamiteiten. Snelle reactie en goede prijs-kwaliteit.',
    name: 'Sylvia Z.',
    location: 'Noord-Holland',
    date: 'Google review',
  },
  {
    quote: 'Snel, deskundig en nog aardig ook.',
    name: 'Ruud D.',
    location: 'Noord-Holland',
    date: 'Google review',
  },
  {
    quote: 'Ineens was alles van A tot Z duidelijk. 24 uur later stond er iemand op m\'n dak.',
    name: 'Joris V.',
    location: 'Alkmaar',
    date: 'Google review',
  },
];

export const testimonialsPlatDak: Testimonial[] = [
  {
    quote: 'Gewoon één woord: VAKMANNEN. Eerlijk advies en duidelijke kennis van zaken.',
    name: 'S. Kramer',
    location: 'Noord-Holland',
    date: 'Google review',
  },
  {
    quote: 'Toppers, vooral bij calamiteiten. Snelle reactie en goede prijs-kwaliteit.',
    name: 'Sylvia Z.',
    location: 'Noord-Holland',
    date: 'Google review',
  },
  {
    quote: 'Snel, deskundig en nog aardig ook.',
    name: 'Ruud D.',
    location: 'Noord-Holland',
    date: 'Google review',
  },
];

export type FaqItem = { q: string; a: string };

export const faqLekkage: FaqItem[] = [
  {
    q: 'Hoe snel kunnen jullie ter plaatse zijn?',
    a: `Bij acute lekkage bellen we u binnen ${company.emergencyResponseMinutes} minuten terug en zijn we in het werkgebied Den Helder/Schagen vaak nog dezelfde dag op locatie. Buiten kantooruren? Bel direct het mobiele nummer.`,
  },
  {
    q: 'Wat kost een noodreparatie?',
    a: 'Een noodreparatie begint bij €150,- (excl. btw) voor kleine lekken. Bij grotere schades maken we eerst een gratis inspectie en een vaste prijsopgave voordat we beginnen. Geen verrassingen achteraf.',
  },
  {
    q: 'Werken jullie ook in het weekend?',
    a: 'Bij echte spoed (water binnen, schade aan inboedel) zijn we ook in het weekend bereikbaar. Reguliere offertes en grote werkzaamheden plannen we doordeweeks.',
  },
  {
    q: 'Wat als ik niet thuis ben tijdens het werk?',
    a: 'Geen probleem als het werk volledig buiten op het dak plaatsvindt. We sturen u foto\'s van de uitgevoerde reparatie en bellen na afloop.',
  },
  {
    q: 'Geven jullie garantie op de reparatie?',
    a: `Op noodreparaties geven we 1 jaar garantie. Op nieuwe bitumen dakbedekking ${company.warrantyYearsBitumen} jaar garantie op materiaal en uitvoering.`,
  },
];

export const faqPlatDak: FaqItem[] = [
  {
    q: 'Hoe lang gaat een nieuw bitumen plat dak mee?',
    a: 'Een vakkundig aangebrachte bitumen toplaag (SBS gemodificeerd, met leislag) gaat 25-30 jaar mee. Onze garantie is 10 jaar op materiaal en uitvoering.',
  },
  {
    q: 'Wat is de gemiddelde prijs voor een plat dak vervangen?',
    a: 'De prijs hangt af van oppervlakte, isolatie en bestaande staat. Een eengezinswoning-aanbouw ligt vaak tussen €80-€140 per m² (incl. isolatie en afwerking). U krijgt altijd een vaste prijsopgave na gratis inspectie op locatie.',
  },
  {
    q: 'Werken jullie met onderaannemers?',
    a: 'Nee. Alle werkzaamheden voeren we uit met onze eigen vakmensen. Daardoor staan we volledig in voor kwaliteit en garantie.',
  },
  {
    q: 'Welke garantie krijg ik?',
    a: `${company.warrantyYearsBitumen} jaar garantie op nieuw aangebrachte bitumen dakbedekking (materiaal + uitvoering). Op zinkwerk en loodwerk 5 jaar garantie. Alles schriftelijk vastgelegd.`,
  },
  {
    q: 'Hoe snel kunnen jullie starten?',
    a: 'Reguliere vervangings- en renovatieprojecten plannen we meestal binnen 2-4 weken na opdracht. Spoedwerk en kleine reparaties vaak binnen een week.',
  },
  {
    q: 'Werken jullie ook op zaterdag?',
    a: 'Standaard werken we maandag t/m vrijdag. Bij grotere projecten op verzoek ook zaterdag. Vraag dat tijdens de offerte.',
  },
];

export const seo = {
  lekkage: {
    title: 'Lekkage plat dak Noord-Holland | JS Techniek',
    description: `Daklekkage in uw platte dak? JS Techniek staat 24/7 paraat in Den Helder en Noord-Holland. ${company.reviewsRating} ★ op Google, ${company.reviewsCount}+ reviews. Bel direct: ${company.phoneDisplay}.`,
  },
  platDak: {
    title: 'Plat dak vervangen Noord-Holland | JS Techniek',
    description: `Plat dak vervangen of repareren? Vakwerk door bitumen-specialist met ${company.warrantyYearsBitumen} jaar garantie. ${company.reviewsRating} ★ op Google. Vraag een gratis dakinspectie.`,
  },
} as const;
