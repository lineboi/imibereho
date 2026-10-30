# District staple-price and checklist evidence (#13 and #21)

> **Status:** research record, 2026-10-27. **Nothing in this document is served by the API.** It records which sources were checked for `GET /api/v1/districts/{code}/basket-details` (#13: `staplePriceIndex`, `primaryMarketHub`) and `GET /api/v1/market/shopping-checklist` (#21), what they actually contain, and the candidate values that would need an owner decision before use. Until a decision is recorded, the responses keep `null` and `awaiting_validated_data` (contract §11.7).

## 1. What the endpoints need

| Endpoint | Field | Needed per district |
|---|---|---|
| #13 | `staplePriceIndex.irishPotatoesPerKg` | retail RWF per kg, Irish potatoes |
| #13 | `staplePriceIndex.sweetPotatoesPerKg` | retail RWF per kg, sweet potatoes |
| #13 | `staplePriceIndex.redBeansPerKg` | retail RWF per kg, red beans |
| #13 | `primaryMarketHub` | the district's main market, by a stated criterion |
| #21 | `items`, totals | item list, quantities and prices for a household basket; a definition of `unoptimizedBasket` |

## 2. Sources checked

| # | Source | Publisher | What it is | Retrieved | File and SHA-256 | Usable? |
|---|---|---|---|---|---|---|
| S1 | "Rwanda - Food Prices", `wfp_food_prices_rwa.csv` ([HDX dataset](https://data.humdata.org/dataset/wfp-food-prices-for-rwanda)) | World Food Programme, via OCHA HDX; licence CC BY-IGO | Monthly market prices, 2000-01-15 to 2026-08-15, by market with district (`admin2`), commodity, unit, retail or wholesale, RWF. Dataset sources: FPMA, Face2Face, MINAGRI, RATIN via FAO GIEWS, WFP RWA Market Database, WFP mVAM. HDX metadata last modified 2026-10-19. | 2026-10-27 | 153,205 lines; `3880fb6d2a11aec08a6e34e3caa1494c8d5003d2c35b42933e8416bba3b296e2` | Partly: see §3 |
| S2 | "Rwanda - Markets", `wfp_markets_rwa.csv` (same dataset) | WFP via HDX | Market list with district and coordinates; 320 markets | 2026-10-27 | `95ef480b6807a708cbc8f626bfc88c37aeb9c0bcc30243badd4bbd6116169a60` | Locations only; no "primary market" attribute |
| S3 | Consumer Price Index, September 2026, `CPI_time_series_September_2026.xls` ([NISR page](https://statistics.gov.rw/index%2Ephp/node/1836); files updated 10 Oct 2026) | NISR | Price **indices** by Urban, Rural and All Rwanda (and province in the data sheet), by COICOP group, with weights | 2026-10-27 | `2e5ebfe1b867b81ae0ebb325cd6ffe19ab00a2373142b26d68ff26171a4d03a2` | No: indices, not RWF prices; no district or product prices |
| S4 | MINAGRI e-Soko (cited by IFPRI as 66 markets, about 90 items) | MINAGRI | Market information system | — | — | No public download found; S1 lists MINAGRI as one of its sources |
| S5 | News and aggregator pages (for example a 17 Oct 2026 report of Kinigi potatoes at 1,000–1,200 RWF/kg in Musanze; Selina Wamucii price pages) | various | Single quotes or unexplained estimates | — | — | No: no method or traceable underlying data |

The files were downloaded to a scratch folder and are not committed. Re-download them from the URLs above and compare the hashes to check this record; HDX replaces the file when WFP updates it, so the hash changes.

## 3. What S1 actually contains (retail, RWF per kg)

**Coverage since 2025: five districts only.** Recent rows are for markets in Gatsibo, Gisagara, Karongi, Kirehe and Nyamagabe, which are mostly markets around refugee camps (camp markets are flagged "(Camp)"). The other 25 districts have no Irish-potato or bean price after 2015, except Gicumbi (last 2021-10) and Nyarugenge (Irish potatoes 2025-10, beans 2024-09). **Gasabo has no rows at all.**

**Field-by-field fit:**
- **Sweet potatoes:** the last row in any district is 2015-12-15. No current value exists for any district.
- **Red beans:** S1 has "Beans (dry)", with no variety. Serving it as `redBeansPerKg` would mislabel it. Recent bean rows are mostly flagged `aggregate` (WFP-computed from higher-frequency data), not `actual`.
- **Irish potatoes:** S1 has both "Potatoes (Irish)" and "Potatoes" in the same markets and months, at very different prices (for example Karongi market, July 2026: 750 and 350). The dataset does not say how they differ, so which one matches the field is unconfirmed.
- **Market hub:** S2 lists the markets WFP monitors; it does not say which is a district's primary market. The "Kimironko" market in S2 is placed in Gatsibo (Eastern Province, -1.75, 30.34), not Gasabo, and has no data after 2015-12, so S1 neither confirms nor contradicts the PDF's "Kimironko Market" for Gasabo.

**Candidate values (not implemented).** Latest month, non-camp markets, retail. "Median" is a calculation by this project, not a published figure.

| District | Irish potatoes, 2026-07-15 ("Potatoes (Irish)", `actual`) | Candidate median | Beans (dry), 2026-08-15 (`aggregate`) | Candidate median | Sweet potatoes |
|---|---|---|---|---|---|
| Gatsibo | Bubare 600; Mugera 550; Ntungaruze 550 | 550 | Mugera 800; Nyagahanga 800 | 800 | none since 2015-12 |
| Gisagara | Kibirizi 550; Mugombwa 566.67 | 558.33 | Kabuga 800; Kibirizi 850; Mugombwa 833.33 | 833.33 | none since 2015-12 |
| Karongi | Karongi 750; Kivuruga 700; Mubuga 700 | 700 | Karongi 1,100; Kivuruga 1,200 | 1,150 | none since 2015-12 |
| Kirehe | Gatore 700; Kabeza 700; Nyamugari 750 | 700 | Kabeza 1,000; Kigufi 800; Kiyanzi 700 | 800 | none since 2015-12 |
| Nyamagabe | Gasarenda 500; Kabacuzi 580; Kigeme 525 | 525 | Gasarenda 900; Kigeme 938.89 | 919.44 | none since 2015-12 |

Limitations: one month; a handful of markets, mostly near refugee camps, so not representative of the district; beans of unstated variety; two unexplained potato series; no sweet potatoes; no market is identified as primary.

## 4. Conclusion

- **#13:** no checked source supports all three staple prices, or a primary market, for any district. The five districts above could at most have two of the three prices, and only with the owner decisions in §5. Nothing from S1 is served.
- **#21:** no checked source publishes a district household shopping basket (items, quantities, totals) or an "unoptimized" basket. The only checklist remains the PDF's Gasabo example; sizes other than 4 are now modelled from it by BR-24 (contract §11.5), and other districts stay `awaiting_validated_data`.
- **Gasabo:** no independent source validates the PDF's 750 / 800 / 850 or "Kimironko Market"; they stay labelled as the illustrative PDF example.

## 5. Decisions needed before any S1 value is used

1. Whether a district may show **some** staple prices with others `null` (today `staplePriceIndex` is reported as one unavailable field), and, if so, a per-field source in the response.
2. Whether "Beans (dry)" may be served, which needs `redBeansPerKg` to be renamed or relabelled, because S1 does not say "red".
3. Which potato series is "Irish potatoes": "Potatoes (Irish)" or "Potatoes". WFP's commodity definitions would settle this.
4. The aggregation rule: latest month or an average over months; median or mean; whether camp markets count; and how rows flagged `aggregate` are treated.
5. Whether five mostly camp-area districts are acceptable coverage, given the other 25 have no current data.
6. A criterion for `primaryMarketHub` (for example a MINAGRI or district designation), which no checked source provides.
