# Measurement and Default Design Research Notes

Date verified: 2026-10-07

## Scope and evidence boundary

This note records the source review behind measurement-history deletion and the
default design presets for the four existing seeded garment families. It does
not authorize or seed customer measurements, garment dimensions, grading
tables, finished-garment ease, or regional sizing values.

## Primary sizing references

- ISO 8559-1:2017, *Size designation of clothes — Part 1: Anthropometric
  definitions for body measurement*, is published and was confirmed current in
  2026. ISO describes anthropometric definitions and measurement procedures for
  physical and digital body-measurement databases. Source:
  https://www.iso.org/standard/61686.html
- ISO 8559-2:2025, *Size designation of clothes — Part 2: Primary and secondary
  dimension indicators*, is the current published edition. It establishes size
  designation from body dimensions defined by ISO 8559-1. Source:
  https://www.iso.org/standard/85590.html
- ASTM Subcommittee D13.55 lists the currently active apparel body-measurement
  standards, including D5219-25 terminology, D5585-21 adult female body tables,
  and D6240/D6240M-24a adult male body tables. Source:
  https://www.astm.org/membership-participation/technical-committees/committee-d13/subcommittee-d13/jurisdiction-d1355
- ASTM D5219-25 is specifically terminology for body dimensions used in apparel
  sizing; it is not a finished-garment construction table. Source:
  https://store.astm.org/d5219-25.html

## Body measurements are not finished-garment measurements

ISO 8559-2 explicitly bases size designation on the wearer's body measurements.
The earlier ISO 8559-2:2017 abstract also states the important design boundary:
garment measurements are chosen by designers/manufacturers with allowances for
wear position, style, cut, and fashion. ASTM body tables likewise describe body
measurements as a baseline and call out fabric, movement ease, styling, and fit
as separate design considerations.

Therefore SGTP keeps these concepts separate:

- `MeasurementSet` stores a person's explicit body-measurement values and units.
- Seeded `Design` presets store categorical style selections only.
- No preset contains numerical body measurements, finished-garment dimensions,
  ease allowances, grading increments, or claimed fit ranges.

## Regional garment evidence and limitations

The Metropolitan Museum of Art identifies the abaya as a cloak and documents
examples using silk, cotton, metal-wrapped thread, and embroidery. This supports
offering optional embellishment as a design descriptor, but does not provide a
modern regional sizing chart or tailoring range. Source:
https://www.metmuseum.org/art/collection/search/86275

No openly verifiable primary source reviewed here provides authoritative,
current numerical tailoring ranges for Kuwaiti Dishdasha, Abaya, or Darraa /
Long Dress across SGTP's intended customer population. Those values are a
documented research/data gap. The migration deliberately seeds no numerical
measurement data for these families.

## Implemented preset policy

The existing Men’s Shirt migration remains unchanged. A new additive migration
adds three published global, style-only presets to the default active global
variant of each remaining seeded family:

- Kuwaiti Dishdasha: everyday, minimal, and tonal-detail configurations.
- Abaya: classic closed, everyday open, and embroidered occasion configurations.
- Darraa / Long Dress: everyday, neckline-embroidered, and flowing occasion
  configurations.

Preset names and choices are practical catalog starting points, not claims that
one style is culturally universal or a sizing standard. Shops may create their
own variants and designs. Runtime design creation validates only the chosen
family/variant and available style options; it does not assume a global preset
or global option group exists.

## Data and migration safeguards

- The seed resolves the active global default variant first, with the first
  active global variant as a deterministic fallback.
- Missing families or variants are skipped rather than creating garment or
  measurement records.
- No `MeasurementProfile`, `MeasurementSet`, or `MeasurementValue` is created.
- The migration is repeat-safe by family, variant, locale, and preset name.
- Reverse migration removes only the seeded preset designs, not customer/shop
  designs or immutable measurement history.
