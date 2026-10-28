"""What the generated organisation looks like.

Everything tunable lives here so the shape of the data can be read in one
screen rather than reverse-engineered out of the generation code.

The numbers are invented but not arbitrary: a level pyramid rather than equal
counts, markets priced relative to the US, and salaries scattered around the
band midpoint. Uniform data would make every chart flat and leave nothing for
the band analysis to find.
"""

DEFAULT_SEED = 20260101
DEFAULT_HEADCOUNT = 10_000

# How far back hires go. Pay history can only be as deep as tenure.
HISTORY_YEARS = 10

# Merit review lands on the same date each year, as it tends to in reality.
MERIT_MONTH = 4
MERIT_DAY = 1

BASE_CURRENCY = "USD"

# country_code, name, currency, market factor vs the US, share of headcount
LOCATIONS = [
    ("US", "United States", "USD", 1.00, 0.34),
    ("IN", "India", "INR", 0.28, 0.26),
    ("GB", "United Kingdom", "GBP", 0.80, 0.12),
    ("DE", "Germany", "EUR", 0.78, 0.11),
    ("BR", "Brazil", "BRL", 0.35, 0.09),
    ("SG", "Singapore", "SGD", 0.72, 0.08),
]

# code, rank, US midpoint for a baseline family in whole dollars, share of staff
LEVELS = [
    ("L1", 1, 85_000, 0.10),
    ("L2", 2, 105_000, 0.18),
    ("L3", 3, 130_000, 0.22),
    ("L4", 4, 155_000, 0.19),
    ("L5", 5, 185_000, 0.14),
    ("L6", 6, 225_000, 0.09),
    ("L7", 7, 280_000, 0.05),
    ("L8", 8, 350_000, 0.03),
]

# name, pay relative to software at the same level
JOB_FAMILIES = [
    ("Software", 1.00),
    ("Data", 0.97),
    ("Product Management", 1.02),
    ("Design", 0.90),
    ("Sales", 0.95),
    ("Marketing", 0.84),
    ("Finance", 0.88),
    ("People Ops", 0.80),
    ("Support", 0.70),
]

# name, share of headcount, the families that department hires into
DEPARTMENTS = [
    ("Engineering", 0.36, ("Software", "Data")),
    ("Customer Support", 0.15, ("Support",)),
    ("Sales", 0.14, ("Sales",)),
    ("Finance", 0.09, ("Finance",)),
    ("People", 0.09, ("People Ops",)),
    ("Product", 0.09, ("Product Management", "Design")),
    ("Marketing", 0.08, ("Marketing",)),
]

BAND_MIN_FACTOR = 0.80
BAND_MAX_FACTOR = 1.20

# Where people sit in their band. Centred slightly under the midpoint, which is
# where a real organisation drifts. The tails are the point: at this spread
# roughly 5% land below their band and 2% above, so the outlier view has
# genuine cases to show without any being planted.
COMPA_MEAN = 0.98
COMPA_SD = 0.11
COMPA_FLOOR = 0.70
COMPA_CEILING = 1.38

MERIT_RAISE = (0.02, 0.05)
PROMOTION_RAISE = (0.10, 0.18)
MARKET_RAISE = (0.05, 0.09)

PROMOTION_CHANCE_PER_YEAR = 0.12
MARKET_CHANCE_PER_YEAR = 0.04

# Staff who have since left. They keep their history and drop out of headcount.
LEAVER_FRACTION = 0.08
MIN_TENURE_DAYS = 200

# Local currency per unit, against the base. Starting points for the quarterly
# series; see generate.fx_series for the drift applied from here.
FX_START = {
    "USD": "1.0",
    "GBP": "1.27",
    "EUR": "1.08",
    "SGD": "0.74",
    "BRL": "0.19",
    "INR": "0.0120",
}

# Quarter-on-quarter movement, as a fraction. Enough to make the snapshotted
# rate matter, not so much that old salaries look absurd.
FX_QUARTERLY_DRIFT = 0.025
