// Server-side kwalificatie voor /plat-dak-probleem.
// KOPIE van landingspagina/src/data/werkgebied-postcodes.ts: wijzig beide.
// De server vertrouwt de kwalificatie van de browser niet blind, zodat er
// alleen een Lead naar Meta gaat als de antwoorden het echt rechtvaardigen.

export const WERKGEBIED_RANGES = [
  [1700, 1789], // Den Helder, Julianadorp, Schagen, Zijpe, Wieringen, Wieringermeer, Niedorp, Langedijk
  [1860, 1879], // Bergen, Schoorl, Groet, Camperduin
  [1650, 1699], // Medemblik en West-Friesland noord
];
export const UITGESLOTEN_RANGES = [
  [1790, 1799], // Texel
];

export function inWerkgebied(postcode) {
  const n = parseInt(String(postcode || '').slice(0, 4), 10);
  if (Number.isNaN(n)) return false;
  if (UITGESLOTEN_RANGES.some(([a, b]) => n >= a && n <= b)) return false;
  return WERKGEBIED_RANGES.some(([a, b]) => n >= a && n <= b);
}

export const PROBLEEM_WAARDEN = ['lekt_nu', 'lekkage_vocht', 'oud_dak', 'slecht_werk', 'anders'];
export const TERMIJN_WAARDEN = ['zsm', '1_3_maanden', 'orienteren'];
export const BEREIKBAAR_WAARDEN = ['ochtend', 'middag', 'avond'];

/** 'gekwalificeerd' | 'orienterend' | null (null = geen lead: huurder of buiten gebied) */
export function bepaalKwalificatie({ eigenaar, postcode, termijn }) {
  if (eigenaar !== 'ja') return null;
  if (!inWerkgebied(postcode)) return null;
  if (termijn === 'orienteren') return 'orienterend';
  if (TERMIJN_WAARDEN.includes(termijn)) return 'gekwalificeerd';
  return null;
}
