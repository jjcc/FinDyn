SECTOR_ETFS = {"XLC","XLP","XLY","XLE","XLF","XLV","XLI","XLB","XLRE","XLK","XLU","XLSR"} # not ishare, spdr
ISHARE_SECTOR1_ETF = {"IBB","IHI","IYW","IGV","IXN","SOXX","IGF","ITA","IGM","IYH","IXJ","ITB","IYG","IYF","IXC","IYC",
                      "IHF","IYJ","IYT","IDU","EUFN","IYK","KXI","RING","IYE","IGE","MXI","IYZ","IHE","IYM","IXP"}
ISHARE_SECTOR2_ETF = {"PICK","IEO","RXI","IXG","SLVP","WOOD","IAT","EXI","IDNA","JXI","IEZ","IHAK","IAI","IETC","IAK",
                      "FILL","VEGI","IFRA","IEDI","EMIF"}
INDUSTRY_ETFS = {"KBE","KRE","KCE","KIE","XAR","XTN","XBI","XPH","XHE","XHS",
                 "XOP","XES","XME","XRT","XHB","XSD","XSW","XNTK","XITK","XTL"} # not isare
THEMATIC_ETFS = {"KOMP", "SIMS", "HAIL", "FITE", "ROKT", "CNRG"}
SMART_BETA_ETFS = {
    "SPYD", "SDY", "WDIV", "DWX", "EDIV", "QUS", "QWLD", "QEFA", "QEMM",
    "ONEY", "ONEV", "ONEO", "LGLV", "SMLV", "MMTM", "VLU", "DWFI",
}

ETF_PRICE_GROUPS = (
    ("sector", SECTOR_ETFS),
    ("industry", INDUSTRY_ETFS),
    ("smart_beta", SMART_BETA_ETFS),
    ("thematic", THEMATIC_ETFS),
    ("ishares_sector1", ISHARE_SECTOR1_ETF),
    ("ishares_sector2", ISHARE_SECTOR2_ETF),
)
ETF_PRICE_SYMBOLS = frozenset().union(*(symbols for _, symbols in ETF_PRICE_GROUPS))

# Exact provider exchange labels accepted as US listings. Keep this centralized
# so the holdings updater and web routes apply the same rule.
US_EXCHANGES = {
    "cboe bzx",
    "nasdaq",
    "new york",
    "new york stock exchange inc.",
    "nyse",
    "nyse mkt llc",
}
