"""EICV7 (2023/24): published headcount poverty and health-insurance estimates, with uncertainty.

OFFICIAL PUBLISHED STATISTICS from the National Institute of Statistics of Rwanda (NISR). Nothing
here is synthetic, derived, recomputed or rounded.

Source documents (both retrieved 2026-10-26 from the NISR publication page):
- Data: "EICV7_Tables_MainIndicatorReport.xlsx" (NISR, last updated 28 Apr 2025), 673,527 bytes,
  SHA-256 8a01ec05d851d9813a855e513eb0e74046a070ca0235df9e81730560028e350d. Sheets
  "Table A9.23" and "Table A3.7".
- Definitions, methodology and page references: "EICV7_Main Indicator Report.pdf" (NISR, 2025;
  111 PDF pages), SHA-256 6105321b6edaeac40df291d9b2450cec121cd0a0b7b750554aefabbfd5b2873c.
  Page numbers below are the report's printed page numbers (PDF page = printed page + 2).

Values are the workbook's stored cell text, verbatim (17 significant digits, e.g.
"27.362976067289672"), held as `Decimal`. The report prints the same tables to two decimals
(pp. 91 and 107). `python -m app.data.eicv7_workbook <xlsx>` re-reads the workbook and checks
every value here; the row tuples were produced by its `--literals` mode.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Final

from app.core.constants import (
    EICV7_HEALTH_INSURANCE_INDICATOR,
    EICV7_POVERTY_INDICATOR,
    EICV7_SOURCE_ID,
)
from app.data.reference import DISTRICT_CODES
from app.data.registry import Dataset, TableRows
from app.models import StatisticalSource, SurveyEstimate

SOURCE_ID: Final = EICV7_SOURCE_ID
SURVEY_ROUND: Final = "2023/24"
PRINTED_DECIMALS: Final = 2  # the annex tables print two decimals (pp. 91, 107)

POVERTY_LINE: Final = (
    "RWF 560,127 per adult equivalent per year in January 2024 prices (extreme poverty: "
    "RWF 356,432, the food poverty line) (pp. 17, 18, 79)"
)

SOURCE: Final = {
    "id": SOURCE_ID,
    "title": "Seventh Integrated Household Living Conditions Survey (EICV7): Main Indicators "
    "Report 2023/24",
    "publisher": "National Institute of Statistics of Rwanda (NISR)",
    "sponsors": None,
    "distributor": "National Institute of Statistics of Rwanda (NISR), statistics.gov.rw",
    "citation": "National Institute of Statistics of Rwanda (NISR) (2025) Seventh Integrated "
    "Household Living Conditions Survey (EICV7) Report: NISR",
    "publication_date": "2025",
    "survey_round": SURVEY_ROUND,
    "fieldwork_period": "October 2023 - October 2024 (12 months in nine cycles; pp. 11, 12, 15)",
    "population": "Household-based population of Rwanda; two-stage sample of 1,674 enumeration "
    "areas stratified by district, nine households per area (pp. 12, 15). Each estimate states "
    "its own denominator.",
    "sample_size": 15_054,
    "lowest_published_geography": "district",
    "document_file": "EICV7_Tables_MainIndicatorReport.xlsx",
    "document_url": "https://statistics.gov.rw/sites/default/files/documents/2025-04/"
    "EICV7_Tables_MainIndicatorReport.xlsx",
    "catalog_url": "https://statistics.gov.rw/statistical-publications/"
    "poverty-and-social-protection/eicv7-main-indicators-report-202324",
    "document_sha256": "8a01ec05d851d9813a855e513eb0e74046a070ca0235df9e81730560028e350d",
    "retrieved_on": date(2026, 10, 26),
    "notes": (
        "sampleSize counts households: 15,054 households (62,110 people) were surveyed (p. 78). "
        "The data file is NISR's annex workbook; definitions and page references come from the "
        "report PDF (https://statistics.gov.rw/sites/default/files/documents/2025-07/"
        "EICV7_Main%20Indicator%20Report.pdf, SHA-256 6105321b6edaeac40df291d9b2450cec121cd0a0b7b"
        "750554aefabbfd5b2873c). The report gives only the year 2025; the workbook is dated 28 "
        "April 2025 and the PDF 9-10 July 2025. "
        f"Poverty line: {POVERTY_LINE}. EICV7 revised how consumption and poverty are measured "
        "(fewer visits, a 7-day food recall, food away from home, January 2024 household-level "
        "Paasche deflators, a new adult-equivalence scale and a poverty line built on 2,400 "
        "kcal/adult equivalent/day valued at second-quintile consumption patterns; p. 13), so "
        "EICV7 poverty rates are not directly comparable with earlier EICV publications (pp. 11, "
        "13, 18). The report's comparison uses a modelled 2016/17 rate of 39.8% under the EICV7 "
        "method (Table 9.3, p. 82; 95% CI 37.7-41.4, model-dependent) against 27.4% in 2023/24, "
        "a fall of 12.4 percentage points; the originally published EICV5 rate was 38.2% (Table "
        "0.1 note, p. 19). Those trend figures are not served as records here. Estimates are "
        "descriptive survey estimates with sampling error; differences between districts whose "
        "confidence intervals overlap may not be meaningful."
    ),
}

# (dimension, category code, published row label, estimate, standard error, 95% CI lower,
#  95% CI upper, CV (%), design effect). Text exactly as stored in the workbook; None = blank.
Row = tuple[str, str, str, str, str | None, str | None, str | None, str | None, str | None]


@dataclass(frozen=True, slots=True)
class TableSpec:
    table_id: str
    sheet: str
    title: str  # the sheet's A1 text, exactly
    value_header: str  # the B2 header
    sections: dict[str, str]  # section-heading label -> dimension
    national_label: str
    indicator_code: str
    indicator_label: str
    definition: str
    population: str
    page: int


POVERTY_TABLE: Final = TableSpec(
    table_id="A9.23",
    sheet="Table A9.23",
    title="Table A9.23: Headcount Poverty rate(%) by area of residence, province and district",
    value_header="Total Poverty rate (%)",
    sections={"Area of residence": "area", "Province": "province", "District": "district"},
    national_label="Poverty Rate",
    indicator_code=EICV7_POVERTY_INDICATOR,
    indicator_label="Headcount poverty rate",
    definition="Percentage of people who are poor: consumption per adult equivalent below the "
    f"poverty line of {POVERTY_LINE}.",
    population="All individuals in the household-based population",
    page=107,
)
HEALTH_INSURANCE_TABLE: Final = TableSpec(
    table_id="A3.7",
    sheet="Table A3.7",
    title="Table A3.7: Percentage (%) of population with health insurance,by area of residence, "
    "province, consumption quintile and sex and district",
    value_header="% with health insurance",
    sections={
        "Sex": "sex",
        "Area of residence": "area",
        "Province": "province",
        "Quintile": "quintile",
        "District": "district",
    },
    national_label="Rwanda",
    indicator_code=EICV7_HEALTH_INSURANCE_INDICATOR,
    indicator_label="Population with health insurance",
    definition="Percentage of the population with any health insurance: community-based health "
    "insurance (Mutuelle), RSSB (former RAMA), employer or other insurance (Table 3.5, p. 33).",
    population="All individuals in the household-based population, all ages",
    page=91,
)
TABLES: Final = (POVERTY_TABLE, HEALTH_INSURANCE_TABLE)

_CODES: Final[dict[str, dict[str, str]]] = {
    "area": {"Urban": "urban", "Rural": "rural"},
    "province": {
        "City of Kigali": "city_of_kigali",
        "Southern": "southern",
        "Western": "western",
        "Northern": "northern",
        "Eastern": "eastern",
    },
    "sex": {"Male": "male", "Female": "female"},
    "quintile": {f"Q{n}": f"q{n}" for n in range(1, 6)},
}


def category_code(dimension: str, label: str) -> str:
    """The stable code for a published row label. Raises KeyError for an unknown label."""
    if dimension == "national":
        return "rwanda"
    if dimension == "district":
        code = label.strip().lower()
        if code not in DISTRICT_CODES:
            raise KeyError(f"unknown district {label!r}")
        return code
    try:
        return _CODES[dimension][label.strip()]
    except KeyError:
        raise KeyError(f"unknown {dimension} {label!r}") from None


# Table A9.23 (Table A9.23), rows 3-43, extracted by app.data.eicv7_workbook --literals.
POVERTY: Final[tuple[Row, ...]] = (
    ("national", "rwanda", "Poverty Rate",
     "27.362976067289672", "0.49624639004466625", "26.389621090104246",
     "28.336331044475099", "1.8135687756489709", "1.8650754691612403"),
    ("area", "urban", "Urban",
     "16.69437894637872", "0.90542229193848334", "14.918452084253564",
     "18.470305808503873", "5.4235158722983465", "2.515588670510791"),
    ("area", "rural", "Rural",
     "31.58433380322931", "0.5918960006737628", "30.423368343752415",
     "32.745299262706205", "1.8740176834543363", "1.7486404710788017"),
    ("province", "city_of_kigali", "City of Kigali",
     "9.0541946554448476", "1.0639082588138458", "6.9674078903221233",
     "11.140981420567572", "11.750446056227119", "2.8402670615812649"),
    ("province", "southern", "Southern",
     "34.666877826067051", "1.0138489724443434", "32.678279091163994",
     "36.655476560970108", "2.9245465297771935", "1.5276030300185433"),
    ("province", "western", "Western",
     "37.412058313592915", "1.1685376959257137", "35.120047721322997",
     "39.704068905862833", "3.1234253034967314", "1.8828246325074596"),
    ("province", "northern", "Northern",
     "20.15069027559494", "1.0775256723607776", "18.037193840602164",
     "22.264186710587715", "5.3473387642000469", "1.6828742922257685"),
    ("province", "eastern", "Eastern",
     "26.776883461120043", "1.0434394373166165", "24.730244956379938",
     "28.823521965860149", "3.8967919430642013", "2.2544635310103551"),
    ("district", "nyarugenge", "Nyarugenge",
     "6.7999300949706969", "1.2026866468360777", "4.4409385593607729",
     "9.1589216305806218", "17.68675015829351", "0.99491109990941295"),
    ("district", "gasabo", "Gasabo",
     "11.058701583614019", "1.8465393123645137", "7.4368349739712141",
     "14.680568193256823", "16.697614077050254", "3.7352112177928416"),
    ("district", "kicukiro", "Kicukiro",
     "6.925051391175594", "1.3370090751048411", "4.3025951599509256",
     "9.5475076224002624", "19.306846976017471", "1.5333250091539479"),
    ("district", "nyanza", "Nyanza",
     "43.27198723363891", "2.824219359930666", "37.73246487982486",
     "48.81150958745296", "6.5266689617969886", "1.3183532087921135"),
    ("district", "gisagara", "Gisagara",
     "45.591219752409472", "2.6859713436478279", "40.322861879455019",
     "50.859577625363926", "5.8914224235158255", "1.2922703704370215"),
    ("district", "nyaruguru", "Nyaruguru",
     "39.698549156944445", "2.5368787609271077", "34.722626675690435",
     "44.674471638198455", "6.3903563601223778", "1.0271191966308688"),
    ("district", "huye", "Huye",
     "24.190701339070184", "2.7011251672134309", "18.892620228049172",
     "29.488782450091197", "11.165964679374003", "1.6523186717078371"),
    ("district", "nyamagabe", "Nyamagabe",
     "51.39408818367712", "3.2140169282663194", "45.090003284228963",
     "57.698173083125276", "6.2536704937341385", "1.6701460450989005"),
    ("district", "ruhango", "Ruhango",
     "14.993299314885093", "2.4379187592341816", "10.211480432412767",
     "19.775118197357418", "16.260055295593663", "1.8406638560175697"),
    ("district", "muhanga", "Muhanga",
     "14.951667489644226", "2.1870259498815816", "10.661958513908766",
     "19.241376465379687", "14.627304622687417", "1.4451517785627757"),
    ("district", "kamonyi", "Kamonyi",
     "39.645735779695706", "3.333571462261705", "33.107152447525408",
     "46.184319111866003", "8.4083985243350465", "2.4881689805369689"),
    ("district", "karongi", "Karongi",
     "38.189393470274382", "3.3583435665523726", "31.60222126876338",
     "44.776565671785384", "8.7939170051664188", "1.9740058229790693"),
    ("district", "rutsiro", "Rutsiro",
     "40.777692709802139", "2.9913275270138673", "34.910398568783492",
     "46.644986850820786", "7.3356958872143645", "1.5128909364676328"),
    ("district", "rubavu", "Rubavu",
     "38.806887932963463", "3.0969092258838886", "32.732502165372829",
     "44.881273700554097", "7.9803081123990429", "2.4538094507259274"),
    ("district", "nyabihu", "Nyabihu",
     "20.406112287135535", "2.2291960759124554", "16.033689355421487",
     "24.778535218849584", "10.924158627303987", "1.0949006216202231"),
    ("district", "ngororero", "Ngororero",
     "30.244443741284549", "2.6947489535697704", "24.958869158089552",
     "35.530018324479542", "8.9098975554685413", "1.3489910985419171"),
    ("district", "rusizi", "Rusizi",
     "44.163106142354039", "3.4346451130299558", "37.426273426387269",
     "50.899938858320809", "7.7771819354345757", "2.6627466130885322"),
    ("district", "nyamasheke", "Nyamasheke",
     "42.671646918478494", "2.5729321753366268", "37.625008012754627",
     "47.718285824202361", "6.0296059822862063", "1.3348811311374287"),
    ("district", "rulindo", "Rulindo",
     "21.637385467650525", "2.0890506686497283", "17.539848625639973",
     "25.734922309661076", "9.6548202266535945", "1.0592813456674268"),
    ("district", "gakenke", "Gakenke",
     "24.473967753574655", "2.8944211035034182", "18.796749251467247",
     "30.151186255682063", "11.826529856731796", "1.8790575531421951"),
    ("district", "musanze", "Musanze",
     "20.980727500084797", "2.7026744674018137", "15.679607537638827",
     "26.281847462530767", "12.881700443375429", "2.455661436107841"),
    ("district", "burera", "Burera",
     "21.791509001940817", "1.8460629331252121", "18.170576779152817",
     "25.412441224728816", "8.4714781934596459", "0.85390356456546146"),
    ("district", "gicumbi", "Gicumbi",
     "13.311406162730469", "2.0990691059732951", "9.1942188083370731",
     "17.428593517123865", "15.768950930595965", "1.9917105443649805"),
    ("district", "rwamagana", "Rwamagana",
     "23.860447652227737", "2.5877848884479264", "18.784676116984308",
     "28.936219187471167", "10.845500160623841", "2.1058918868916723"),
    ("district", "nyagatare", "Nyagatare",
     "36.366405113317853", "2.7897853056270216", "30.894422914583032",
     "41.838387312052674", "7.6713254910240378", "2.5072735563719881"),
    ("district", "gatsibo", "Gatsibo",
     "18.406204261258939", "2.6318002540724179", "13.24409945274096",
     "23.568309069776916", "14.298440986074384", "2.7825514638846203"),
    ("district", "kayonza", "Kayonza",
     "36.554396761518568", "3.2311024819699306", "30.216799661137561",
     "42.891993861899579", "8.8391623668410979", "2.5728528984879149"),
    ("district", "kirehe", "Kirehe",
     "14.237073445161911", "2.1284905270000833", "10.062177889425804",
     "18.411969000898019", "14.950337477702583", "1.7623889867703879"),
    ("district", "ngoma", "Ngoma",
     "30.939048609497078", "2.6331095710571071", "25.774375660979842",
     "36.103721558014314", "8.5106352308740529", "1.4792247580558999"),
    ("district", "bugesera", "Bugesera",
     "23.698645176490345", "2.6259443355730441", "18.548026370755871",
     "28.849263982224819", "11.080567332085495", "2.4305877067424273"),
)  # fmt: skip

# Table A3.7 (Table A3.7), rows 3-52, extracted by app.data.eicv7_workbook --literals.
HEALTH_INSURANCE: Final[tuple[Row, ...]] = (
    ("national", "rwanda", "Rwanda",
     "85.310917075321285", "0.36316526070014143", "84.598592066747401",
     "86.02324208389517", "0.42569611621863312", "6.531306740603827"),
    ("sex", "male", "Male",
     "84.911713711824234", "0.38794569930050377", "84.150783486703929",
     "85.672643936944539", "0.45688125035036364", "3.4873094645318745"),
    ("sex", "female", "Female",
     "85.677015852419231", "0.38309664468282439", "84.925596732148151",
     "86.428434972690312", "0.44714050888830886", "3.8714253927839133"),
    ("area", "urban", "Urban",
     "85.075412999020287", "0.73118816797696617", "83.641235024455241",
     "86.509590973585333", "0.85945885209559469", "7.4085009345646071"),
    ("area", "rural", "Rural",
     "85.404110132167702", "0.41611776224604047", "84.587922240219527",
     "86.220298024115877", "0.48723388324294303", "6.1761302757580943"),
    ("province", "city_of_kigali", "City of Kigali",
     "84.188923338252579", "1.1412007977929388", "81.950532291418455",
     "86.427314385086703", "1.355523687133811", "8.339592452326869"),
    ("province", "southern", "Southern",
     "84.832555820541202", "0.70129882066532623", "83.457003854253998",
     "86.208107786828407", "0.82668595079097573", "5.3038071745506281"),
    ("province", "western", "Western",
     "82.888280836560199", "0.81237229718615178", "81.294865479478148",
     "84.48169619364225", "0.98008100661177211", "6.1939884658829722"),
    ("province", "northern", "Northern",
     "91.673941182269573", "0.65914072787819211", "90.381079569537008",
     "92.966802795002138", "0.71900555313495662", "5.4770894265419781"),
    ("province", "eastern", "Eastern",
     "84.546987271427028", "0.75563010492687688", "83.06486802925879",
     "86.029106513595266", "0.89373983546099101", "7.308368122613861"),
    ("quintile", "q1", "Q1",
     "76.018949867683503", "0.93849125667523137", "74.178160384766315",
     "77.859739350600691", "1.2345490937572059", "5.9935137246573733"),
    ("quintile", "q2", "Q2",
     "81.590887518140704", "0.76727562306792763", "80.085926350525966",
     "83.095848685755442", "0.94039376995051516", "4.8675694053211975"),
    ("quintile", "q3", "Q3",
     "86.03199428062328", "0.68807451029881772", "84.682380937917657",
     "87.381607623328904", "0.79978909712870683", "4.8915397269666521"),
    ("quintile", "q4", "Q4",
     "89.536552275440926", "0.55198221861795249", "88.45387510017467",
     "90.619229450707181", "0.61648813204231034", "4.0361808621563577"),
    ("quintile", "q5", "Q5",
     "93.377251056978139", "0.44230376593958776", "92.509701024087406",
     "94.244801089868872", "0.47367400617704747", "3.9246952775832904"),
    ("district", "nyarugenge", "Nyarugenge",
     "81.764627595840224", "1.7985448238992683", "78.236899049793024",
     "85.292356141887424", "2.1996612432327267", "3.9023197795873656"),
    ("district", "gasabo", "Gasabo",
     "86.25335754912301", "1.7964095232332549", "82.729817256275723",
     "89.776897841970296", "2.0827125740701327", "12.100523037825447"),
    ("district", "kicukiro", "Kicukiro",
     "82.0751116874155", "1.9890455485069236", "78.173728375965169",
     "85.976494998865832", "2.423445436275784", "6.1292100534747762"),
    ("district", "nyanza", "Nyanza",
     "82.320371636364953", "1.9411441196173846", "78.512943858212765",
     "86.127799414517142", "2.3580361471058837", "4.3200489321284117"),
    ("district", "gisagara", "Gisagara",
     "85.044907599385709", "1.7999131009882656", "81.51449526693429",
     "88.575319931837129", "2.1164266642124807", "4.6701081395229185"),
    ("district", "nyaruguru", "Nyaruguru",
     "90.095998670106837", "1.4784660208732325", "87.196083851810698",
     "92.995913488402977", "1.6409896584716768", "3.8601865948496368"),
    ("district", "huye", "Huye",
     "82.877097614804597", "1.7985735065232411", "79.349312809658372",
     "86.404882419950823", "2.1701695139984682", "3.9023405608267203"),
    ("district", "nyamagabe", "Nyamagabe",
     "86.002010122898611", "1.8262828697062536", "82.41987520637646",
     "89.584145039420761", "2.1235350977220864", "4.607714491627684"),
    ("district", "ruhango", "Ruhango",
     "83.820731783654239", "1.9299474435480093", "80.03526555645476",
     "87.606198010853717", "2.3024702868608999", "4.470692420612159"),
    ("district", "muhanga", "Muhanga",
     "89.834774303721375", "1.5866277843880121", "86.72270723007324",
     "92.946841377369509", "1.7661621534482852", "4.3678299489435917"),
    ("district", "kamonyi", "Kamonyi",
     "80.595062321028536", "2.5619698500102985", "75.569925302536433",
     "85.620199339520639", "3.1788173818954166", "9.2779612886779201"),
    ("district", "karongi", "Karongi",
     "85.06888802055596", "1.8470491015793189", "81.446021492567141",
     "88.691754548544779", "2.1712392680306341", "4.5788705080171619"),
    ("district", "rutsiro", "Rutsiro",
     "82.260360116491768", "2.3172178441407407", "77.715288218610027",
     "86.805432014373508", "2.8169313152279511", "6.1932594933890677"),
    ("district", "rubavu", "Rubavu",
     "79.492845592306935", "1.9038743386979466", "75.758520062320784",
     "83.227171122293086", "2.3950260234264373", "5.5670164259018788"),
    ("district", "nyabihu", "Nyabihu",
     "87.472057643703877", "1.5813924742446164", "84.370259289964665",
     "90.57385599744309", "1.80788301640969", "3.3681348597841638"),
    ("district", "ngororero", "Ngororero",
     "87.760787139439898", "1.8679324767365852", "84.096959231061149",
     "91.424615047818648", "2.1284363297342535", "5.2504606897566806"),
    ("district", "rusizi", "Rusizi",
     "78.094379954281791", "2.5168568250725176", "73.157729196324752",
     "83.031030712238831", "3.2228398849519544", "8.4970413853112117"),
    ("district", "nyamasheke", "Nyamasheke",
     "83.970274710237788", "2.1654519871136642", "79.722881657517661",
     "88.217667762957916", "2.5788316098597317", "7.0844821744962596"),
    ("district", "rulindo", "Rulindo",
     "90.408372550484742", "1.8458028270659022", "86.787950508793273",
     "94.028794592176212", "2.0416281976928534", "6.6720174860968147"),
    ("district", "gakenke", "Gakenke",
     "96.349709583879303", "0.77734109800031914", "94.825005642675237",
     "97.874413525083369", "0.80679132439271994", "2.9391623308704036"),
    ("district", "musanze", "Musanze",
     "88.926973276339979", "1.6836307015653023", "85.624641297737014",
     "92.229305254942943", "1.8932733675005795", "6.6204701979824625"),
    ("district", "burera", "Burera",
     "93.039828670848053", "1.1944927199005377", "90.696908989311837",
     "95.382748352384269", "1.2838509453046802", "3.8804526847171568"),
    ("district", "gicumbi", "Gicumbi",
     "90.773653708404396", "1.4046913983989755", "88.018443007691516",
     "93.528864409117276", "1.5474659672853075", "5.0709737012623037"),
    ("district", "rwamagana", "Rwamagana",
     "82.675537763256102", "1.8187623909530171", "79.10815377605482",
     "86.242921750457384", "2.1998797227797877", "5.4306028177800032"),
    ("district", "nyagatare", "Nyagatare",
     "81.557058328635009", "2.1334823512761383", "77.372371634662315",
     "85.741745022607702", "2.615938332007083", "9.2728983112280599"),
    ("district", "gatsibo", "Gatsibo",
     "84.471228191522357", "1.8792871137102036", "80.785128902164061",
     "88.157327480880653", "2.224765939769787", "6.6906197669087764"),
    ("district", "kayonza", "Kayonza",
     "83.04706690296041", "2.2566720626944692", "78.620751612482906",
     "87.473382193437914", "2.7173410775980393", "8.5193993727381372"),
    ("district", "kirehe", "Kirehe",
     "89.409711472159856", "1.6733302186795902", "86.127583219942323",
     "92.691839724377388", "1.8715307220297059", "5.7957534955449654"),
    ("district", "ngoma", "Ngoma",
     "89.808464272533485", "1.5370507697895077", "86.793639284433013",
     "92.823289260633956", "1.7114765097476348", "4.8552967643497018"),
    ("district", "bugesera", "Bugesera",
     "83.730538894482365", "2.0399101389240033", "79.729388001366587",
     "87.731689787598143", "2.4362797204669948", "8.0216274927834643"),
)  # fmt: skip

# Notes on individual records: (table id, category code) -> note.
ROW_NOTES: Final = {
    ("A9.23", "rwanda"): (
        "The workbook labels this row 'Poverty Rate'; the printed table (p. 107) labels it "
        "'Rwanda'."
    ),
    ("A9.23", "gisagara"): (
        "The report text (p. 80) gives Gisagara's poverty rate as 46.6%; this table and Figure "
        "9.1 give 45.59 (45.6). The table value is served."
    ),
}


def _optional(text: str | None) -> Decimal | None:
    return Decimal(text) if text is not None else None


def _rows(spec: TableSpec, rows: tuple[Row, ...], offset: int) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "source_id": SOURCE_ID,
            "table_id": spec.table_id,
            "indicator_code": spec.indicator_code,
            "dimension": dimension,
            "category_code": code,
            "district_code": code if dimension == "district" else None,
            "label": label,
            "indicator_label": spec.indicator_label,
            "definition": spec.definition,
            "population": spec.population,
            "unit": "percent",
            "survey_round": SURVEY_ROUND,
            "estimate_pct": Decimal(estimate),
            "standard_error_pct": _optional(se),
            "ci_lower_pct": _optional(lower),
            "ci_upper_pct": _optional(upper),
            "cv_pct": _optional(cv),
            "design_effect": _optional(deff),
            "printed_decimals": PRINTED_DECIMALS,
            "page": spec.page,
            "table_or_figure": spec.title,
            "notes": ROW_NOTES.get((spec.table_id, code)),
            "sort_order": offset + index,
        }
        for index, (dimension, code, label, estimate, se, lower, upper, cv, deff) in enumerate(
            rows, 1
        )
    )


def _eicv7() -> tuple[TableRows, ...]:
    estimates = _rows(POVERTY_TABLE, POVERTY, 0) + _rows(
        HEALTH_INSURANCE_TABLE, HEALTH_INSURANCE, 1000
    )
    return (
        TableRows(StatisticalSource, None, (SOURCE,), partition=("id", SOURCE_ID)),
        TableRows(SurveyEstimate, None, estimates, partition=("source_id", SOURCE_ID)),
    )


DATASETS: Final = (Dataset("eicv7_2023_24", _eicv7),)
