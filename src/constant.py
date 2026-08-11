SECTOR_ETFS = {"XLC","XLP","XLY","XLE","XLF","XLV","XLI","XLB","XLRE","XLK","XLU","XLSR"} # not ishare, spdr
ISHARE_SECTOR1_ETF = {"IBB","IHI","IYW","IGV","IXN","SOXX","IGF","ITA","IGM","IYH","IXJ","ITB","IYG","IYF","IXC","IYC",
                      "IHF","IYJ","IYT","IDU","EUFN","IYK","KXI","RING","IYE","IGE","MXI","IYZ","IHE","IYM","IXP"}
ISHARE_SECTOR2_ETF = {"PICK","IEO","RXI","IXG","SLVP","WOOD","IAT","EXI","IDNA","JXI","IEZ","IHAK","IAI","IETC","IAK",
                      "FILL","VEGI","IFRA","IEDI","EMIF"}
INDUSTRY_ETFS = {"KBE","KRE","KCE","KIE","XAR","XTN","XBI","XPH","XHE","XHS",
                 "XOP","XES","XME","XRT","XHB","XSD","XSW","XNTK","XITK","XTL"} # not isare

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
