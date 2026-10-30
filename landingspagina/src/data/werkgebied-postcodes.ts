// Werkgebied JS Techniek voor /plat-dak-probleem
// Basis: Den Helder (1780-1789) en omgeving tot ongeveer 35 km, op de
// eerste 4 cijfers van de postcode. Texel valt er altijd buiten.
//
// Toegestaan (inclusief grenzen):
//   1700-1729  Heerhugowaard, Obdam/Hensbroek/Spanbroek, Langedijk
//              (rand van de straal, ca. 30-38 km)
//   1730-1739  Niedorp, Winkel, 't Veld
//   1740-1749  Schagen, Sint Maarten, Dirkshorn, Tuitjenhorn, Warmenhuizen
//   1750-1759  Schagerbrug, Sint Maartensbrug/-vlotbrug/-zee, Burgerbrug,
//              Petten, 't Zand, Oudesluis, Callantsoog
//   1760-1769  Anna Paulowna, Breezand, Wieringerwaard, Kolhorn
//   1770-1779  Wieringen en Wieringermeer: Wieringerwerf, Slootdorp,
//              Middenmeer, Kreileroord, Hippolytushoef, Westerland, Den Oever
//   1780-1789  Den Helder, Julianadorp
//   1860-1879  Bergen, Schoorl, Groet, Camperduin (rand)
//   1650-1699  West-Friesland noord: Medemblik, Twisk, Abbekerk, Wognum,
//              Wervershoof, Onderdijk (rand, ca. 30-40 km)
//
// Uitgesloten:
//   1790-1797  Texel (eiland)
//   1798-1799  niet toegewezen / geen woonadressen, voor de zekerheid uit
//   alle andere postcodes (o.a. Alkmaar 18xx behalve Bergen/Schoorl, Hoorn
//   en Enkhuizen 16xx onder 1650)
//
// Aanpassen? Wijzig deze lijst EN de kopie in api/_lib/plat-dak-probleem.js
// (de server controleert de kwalificatie opnieuw voordat er een Lead naar
// Meta gaat). Laat Jonathan de randgebieden bevestigen.

export const WERKGEBIED_RANGES: ReadonlyArray<readonly [number, number]> = [
  [1700, 1789],
  [1860, 1879],
  [1650, 1699],
];

export const UITGESLOTEN_RANGES: ReadonlyArray<readonly [number, number]> = [
  [1790, 1799], // Texel
];

export const POSTCODE_REGEX = /^\s*([1-9]\d{3})\s?([A-Za-z]{2})\s*$/;

export function normalizePostcode(raw: string): string | null {
  const m = POSTCODE_REGEX.exec(raw || '');
  if (!m) return null;
  const letters = m[2].toUpperCase();
  // SA, SD en SS worden in NL niet uitgegeven
  if (['SA', 'SD', 'SS'].includes(letters)) return null;
  return `${m[1]} ${letters}`;
}

export function isTexel(postcode: string): boolean {
  const n = parseInt(postcode.slice(0, 4), 10);
  return n >= 1790 && n <= 1797;
}

export function inWerkgebied(postcode: string): boolean {
  const n = parseInt(postcode.slice(0, 4), 10);
  if (Number.isNaN(n)) return false;
  if (UITGESLOTEN_RANGES.some(([a, b]) => n >= a && n <= b)) return false;
  return WERKGEBIED_RANGES.some(([a, b]) => n >= a && n <= b);
}
