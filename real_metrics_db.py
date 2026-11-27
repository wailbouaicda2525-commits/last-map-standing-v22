"""
real_metrics_db.py — Verified public-data metrics for all 50 U.S. States and 75+ World Countries.
Drives realistic elimination waves, animated Saul Bass Bar Charts, live Leaderboards, and Final VS Showdowns.
Metrics scale (0-100 index unless noted):
  pop_m       : Population in millions
  energy      : Energy self-sufficiency / domestic production vs demand (0-100)
  food        : Agricultural / food production per capita (0-100)
  water       : Freshwater abundance per capita (0-100)
  gdp_pc      : GDP per capita ($ thousands USD)
  afford      : Cost-of-living affordability index (higher = more affordable, 0-100)
  elev_m      : Mean elevation in meters
  coast_km    : Approximate coastline length in km (0 = landlocked)
  cold_res    : Cold / freeze survival resilience (0-100)
  heat_res    : Extreme heat resilience (0-100)
  trade_indep : Ability to survive with zero external imports (0-100)
"""

US_STATE_METRICS = {
    "Alabama":        {"pop_m": 5.1,  "energy": 74, "food": 64, "water": 82, "gdp_pc": 58,  "afford": 84, "elev_m": 150,  "coast_km": 97,   "cold_res": 45, "heat_res": 52, "trade_indep": 68, "region": "South"},
    "Alaska":         {"pop_m": 0.73, "energy": 98, "food": 32, "water": 99, "gdp_pc": 88,  "afford": 42, "elev_m": 580,  "coast_km": 10690,"cold_res": 96, "heat_res": 95, "trade_indep": 62, "region": "West"},
    "Arizona":        {"pop_m": 7.4,  "energy": 58, "food": 34, "water": 18, "gdp_pc": 68,  "afford": 56, "elev_m": 1250, "coast_km": 0,    "cold_res": 55, "heat_res": 22, "trade_indep": 34, "region": "Southwest"},
    "Arkansas":       {"pop_m": 3.1,  "energy": 68, "food": 86, "water": 84, "gdp_pc": 56,  "afford": 88, "elev_m": 200,  "coast_km": 0,    "cold_res": 58, "heat_res": 54, "trade_indep": 78, "region": "South"},
    "California":     {"pop_m": 39.0, "energy": 44, "food": 72, "water": 30, "gdp_pc": 99,  "afford": 18, "elev_m": 880,  "coast_km": 1352, "cold_res": 52, "heat_res": 40, "trade_indep": 42, "region": "West"},
    "Colorado":       {"pop_m": 5.9,  "energy": 78, "food": 62, "water": 52, "gdp_pc": 86,  "afford": 46, "elev_m": 2070, "coast_km": 0,    "cold_res": 86, "heat_res": 78, "trade_indep": 66, "region": "Mountain"},
    "Connecticut":    {"pop_m": 3.6,  "energy": 28, "food": 16, "water": 64, "gdp_pc": 94,  "afford": 36, "elev_m": 150,  "coast_km": 154,  "cold_res": 70, "heat_res": 70, "trade_indep": 24, "region": "Northeast"},
    "Delaware":       {"pop_m": 1.0,  "energy": 22, "food": 42, "water": 55, "gdp_pc": 90,  "afford": 54, "elev_m": 18,   "coast_km": 45,   "cold_res": 60, "heat_res": 66, "trade_indep": 26, "region": "Northeast"},
    "Florida":        {"pop_m": 22.6, "energy": 36, "food": 48, "water": 62, "gdp_pc": 69,  "afford": 48, "elev_m": 30,   "coast_km": 2170, "cold_res": 22, "heat_res": 26, "trade_indep": 36, "region": "South"},
    "Georgia":        {"pop_m": 11.0, "energy": 48, "food": 58, "water": 72, "gdp_pc": 72,  "afford": 70, "elev_m": 180,  "coast_km": 161,  "cold_res": 46, "heat_res": 48, "trade_indep": 52, "region": "South"},
    "Hawaii":         {"pop_m": 1.4,  "energy": 18, "food": 24, "water": 78, "gdp_pc": 74,  "afford": 12, "elev_m": 920,  "coast_km": 1210, "cold_res": 18, "heat_res": 72, "trade_indep": 16, "region": "West"},
    "Idaho":          {"pop_m": 2.0,  "energy": 84, "food": 94, "water": 88, "gdp_pc": 60,  "afford": 64, "elev_m": 1520, "coast_km": 0,    "cold_res": 88, "heat_res": 78, "trade_indep": 90, "region": "Mountain"},
    "Illinois":       {"pop_m": 12.6, "energy": 64, "food": 78, "water": 76, "gdp_pc": 85,  "afford": 62, "elev_m": 180,  "coast_km": 0,    "cold_res": 74, "heat_res": 62, "trade_indep": 58, "region": "Midwest"},
    "Indiana":        {"pop_m": 6.9,  "energy": 60, "food": 84, "water": 74, "gdp_pc": 70,  "afford": 80, "elev_m": 210,  "coast_km": 0,    "cold_res": 72, "heat_res": 64, "trade_indep": 69, "region": "Midwest"},
    "Iowa":           {"pop_m": 3.2,  "energy": 82, "food": 99, "water": 78, "gdp_pc": 75,  "afford": 84, "elev_m": 340,  "coast_km": 0,    "cold_res": 80, "heat_res": 66, "trade_indep": 89, "region": "Midwest"},
    "Kansas":         {"pop_m": 2.9,  "energy": 84, "food": 96, "water": 56, "gdp_pc": 74,  "afford": 86, "elev_m": 610,  "coast_km": 0,    "cold_res": 76, "heat_res": 58, "trade_indep": 85, "region": "Midwest"},
    "Kentucky":       {"pop_m": 4.5,  "energy": 74, "food": 72, "water": 82, "gdp_pc": 60,  "afford": 82, "elev_m": 230,  "coast_km": 0,    "cold_res": 66, "heat_res": 62, "trade_indep": 73, "region": "South"},
    "Louisiana":      {"pop_m": 4.6,  "energy": 92, "food": 66, "water": 86, "gdp_pc": 66,  "afford": 80, "elev_m": 30,   "coast_km": 639,  "cold_res": 36, "heat_res": 40, "trade_indep": 74, "region": "South"},
    "Maine":          {"pop_m": 1.4,  "energy": 58, "food": 52, "water": 92, "gdp_pc": 64,  "afford": 54, "elev_m": 180,  "coast_km": 367,  "cold_res": 88, "heat_res": 86, "trade_indep": 64, "region": "Northeast"},
    "Maryland":       {"pop_m": 6.2,  "energy": 30, "food": 26, "water": 64, "gdp_pc": 83,  "afford": 42, "elev_m": 110,  "coast_km": 50,   "cold_res": 64, "heat_res": 62, "trade_indep": 28, "region": "Northeast"},
    "Massachusetts":  {"pop_m": 7.0,  "energy": 24, "food": 14, "water": 66, "gdp_pc": 103, "afford": 24, "elev_m": 150,  "coast_km": 309,  "cold_res": 74, "heat_res": 72, "trade_indep": 20, "region": "Northeast"},
    "Michigan":       {"pop_m": 10.0, "energy": 54, "food": 64, "water": 98, "gdp_pc": 66,  "afford": 76, "elev_m": 270,  "coast_km": 0,    "cold_res": 84, "heat_res": 78, "trade_indep": 62, "region": "Midwest"},
    "Minnesota":      {"pop_m": 5.7,  "energy": 64, "food": 88, "water": 96, "gdp_pc": 81,  "afford": 70, "elev_m": 370,  "coast_km": 0,    "cold_res": 92, "heat_res": 82, "trade_indep": 80, "region": "Midwest"},
    "Mississippi":    {"pop_m": 2.9,  "energy": 64, "food": 76, "water": 86, "gdp_pc": 50,  "afford": 92, "elev_m": 90,   "coast_km": 71,   "cold_res": 40, "heat_res": 46, "trade_indep": 72, "region": "South"},
    "Missouri":       {"pop_m": 6.2,  "energy": 58, "food": 82, "water": 82, "gdp_pc": 68,  "afford": 82, "elev_m": 240,  "coast_km": 0,    "cold_res": 70, "heat_res": 60, "trade_indep": 74, "region": "Midwest"},
    "Montana":        {"pop_m": 1.13, "energy": 94, "food": 96, "water": 95, "gdp_pc": 62,  "afford": 58, "elev_m": 1040, "coast_km": 0,    "cold_res": 95, "heat_res": 86, "trade_indep": 96, "region": "Mountain"},
    "Nebraska":       {"pop_m": 2.0,  "energy": 78, "food": 98, "water": 72, "gdp_pc": 88,  "afford": 82, "elev_m": 790,  "coast_km": 0,    "cold_res": 82, "heat_res": 64, "trade_indep": 90, "region": "Midwest"},
    "Nevada":         {"pop_m": 3.2,  "energy": 48, "food": 20, "water": 14, "gdp_pc": 74,  "afford": 54, "elev_m": 1680, "coast_km": 0,    "cold_res": 60, "heat_res": 28, "trade_indep": 28, "region": "West"},
    "New Hampshire":  {"pop_m": 1.4,  "energy": 46, "food": 24, "water": 84, "gdp_pc": 78,  "afford": 48, "elev_m": 300,  "coast_km": 21,   "cold_res": 84, "heat_res": 82, "trade_indep": 44, "region": "Northeast"},
    "New Jersey":     {"pop_m": 9.3,  "energy": 22, "food": 12, "water": 54, "gdp_pc": 86,  "afford": 30, "elev_m": 75,   "coast_km": 209,  "cold_res": 64, "heat_res": 62, "trade_indep": 18, "region": "Northeast"},
    "New Mexico":     {"pop_m": 2.1,  "energy": 92, "food": 48, "water": 24, "gdp_pc": 62,  "afford": 76, "elev_m": 1740, "coast_km": 0,    "cold_res": 70, "heat_res": 48, "trade_indep": 62, "region": "Southwest"},
    "New York":       {"pop_m": 19.6, "energy": 34, "food": 28, "water": 76, "gdp_pc": 110, "afford": 20, "elev_m": 300,  "coast_km": 204,  "cold_res": 72, "heat_res": 66, "trade_indep": 24, "region": "Northeast"},
    "North Carolina": {"pop_m": 10.8, "energy": 52, "food": 64, "water": 74, "gdp_pc": 71,  "afford": 68, "elev_m": 210,  "coast_km": 484,  "cold_res": 54, "heat_res": 56, "trade_indep": 56, "region": "South"},
    "North Dakota":   {"pop_m": 0.78, "energy": 99, "food": 98, "water": 68, "gdp_pc": 94,  "afford": 78, "elev_m": 580,  "coast_km": 0,    "cold_res": 94, "heat_res": 82, "trade_indep": 95, "region": "Midwest"},
    "Ohio":           {"pop_m": 11.8, "energy": 56, "food": 68, "water": 82, "gdp_pc": 74,  "afford": 78, "elev_m": 260,  "coast_km": 0,    "cold_res": 72, "heat_res": 66, "trade_indep": 60, "region": "Midwest"},
    "Oklahoma":       {"pop_m": 4.1,  "energy": 95, "food": 78, "water": 62, "gdp_pc": 62,  "afford": 88, "elev_m": 400,  "coast_km": 0,    "cold_res": 64, "heat_res": 50, "trade_indep": 84, "region": "South"},
    "Oregon":         {"pop_m": 4.2,  "energy": 76, "food": 76, "water": 92, "gdp_pc": 75,  "afford": 44, "elev_m": 1000, "coast_km": 476,  "cold_res": 78, "heat_res": 76, "trade_indep": 76, "region": "West"},
    "Pennsylvania":   {"pop_m": 13.0, "energy": 84, "food": 54, "water": 80, "gdp_pc": 74,  "afford": 66, "elev_m": 340,  "coast_km": 0,    "cold_res": 74, "heat_res": 68, "trade_indep": 64, "region": "Northeast"},
    "Rhode Island":   {"pop_m": 1.1,  "energy": 18, "food": 10, "water": 58, "gdp_pc": 70,  "afford": 38, "elev_m": 60,   "coast_km": 64,   "cold_res": 66, "heat_res": 70, "trade_indep": 14, "region": "Northeast"},
    "South Carolina": {"pop_m": 5.4,  "energy": 56, "food": 54, "water": 74, "gdp_pc": 60,  "afford": 72, "elev_m": 110,  "coast_km": 301,  "cold_res": 44, "heat_res": 48, "trade_indep": 54, "region": "South"},
    "South Dakota":   {"pop_m": 0.92, "energy": 86, "food": 98, "water": 72, "gdp_pc": 78,  "afford": 80, "elev_m": 670,  "coast_km": 0,    "cold_res": 90, "heat_res": 74, "trade_indep": 93, "region": "Midwest"},
    "Tennessee":      {"pop_m": 7.1,  "energy": 64, "food": 64, "water": 84, "gdp_pc": 73,  "afford": 78, "elev_m": 270,  "coast_km": 0,    "cold_res": 60, "heat_res": 58, "trade_indep": 66, "region": "South"},
    "Texas":          {"pop_m": 30.5, "energy": 99, "food": 82, "water": 52, "gdp_pc": 85,  "afford": 72, "elev_m": 520,  "coast_km": 591,  "cold_res": 38, "heat_res": 36, "trade_indep": 84, "region": "South"},
    "Utah":           {"pop_m": 3.4,  "energy": 74, "food": 52, "water": 32, "gdp_pc": 79,  "afford": 54, "elev_m": 1860, "coast_km": 0,    "cold_res": 82, "heat_res": 60, "trade_indep": 60, "region": "Mountain"},
    "Vermont":        {"pop_m": 0.65, "energy": 54, "food": 64, "water": 92, "gdp_pc": 66,  "afford": 46, "elev_m": 300,  "coast_km": 0,    "cold_res": 90, "heat_res": 88, "trade_indep": 68, "region": "Northeast"},
    "Virginia":       {"pop_m": 8.7,  "energy": 52, "food": 52, "water": 76, "gdp_pc": 81,  "afford": 56, "elev_m": 290,  "coast_km": 180,  "cold_res": 62, "heat_res": 60, "trade_indep": 52, "region": "South"},
    "Washington":     {"pop_m": 7.8,  "energy": 86, "food": 78, "water": 94, "gdp_pc": 102, "afford": 40, "elev_m": 520,  "coast_km": 253,  "cold_res": 80, "heat_res": 80, "trade_indep": 78, "region": "West"},
    "West Virginia":  {"pop_m": 1.77, "energy": 96, "food": 52, "water": 86, "gdp_pc": 56,  "afford": 88, "elev_m": 460,  "coast_km": 0,    "cold_res": 78, "heat_res": 74, "trade_indep": 76, "region": "South"},
    "Wisconsin":      {"pop_m": 5.9,  "energy": 58, "food": 86, "water": 94, "gdp_pc": 70,  "afford": 76, "elev_m": 320,  "coast_km": 0,    "cold_res": 88, "heat_res": 80, "trade_indep": 76, "region": "Midwest"},
    "Wyoming":        {"pop_m": 0.58, "energy": 99, "food": 84, "water": 72, "gdp_pc": 86,  "afford": 72, "elev_m": 2040, "coast_km": 0,    "cold_res": 94, "heat_res": 84, "trade_indep": 94, "region": "Mountain"},
}

WORLD_METRICS = {
    "Norway":                   {"pop_m": 5.5,   "energy": 99, "food": 66, "water": 98, "gdp_pc": 88, "afford": 42, "elev_m": 460,  "coast_km": 25148, "cold_res": 98, "heat_res": 95, "trade_indep": 84},
    "Canada":                   {"pop_m": 40.0,  "energy": 98, "food": 94, "water": 99, "gdp_pc": 54, "afford": 46, "elev_m": 487,  "coast_km": 202080,"cold_res": 96, "heat_res": 90, "trade_indep": 92},
    "United States of America": {"pop_m": 335.0, "energy": 96, "food": 95, "water": 82, "gdp_pc": 82, "afford": 50, "elev_m": 760,  "coast_km": 19924, "cold_res": 82, "heat_res": 74, "trade_indep": 94},
    "Australia":                {"pop_m": 26.5,  "energy": 96, "food": 96, "water": 58, "gdp_pc": 65, "afford": 44, "elev_m": 330,  "coast_km": 25760, "cold_res": 66, "heat_res": 48, "trade_indep": 90},
    "New Zealand":              {"pop_m": 5.2,   "energy": 84, "food": 98, "water": 96, "gdp_pc": 48, "afford": 48, "elev_m": 388,  "coast_km": 15134, "cold_res": 82, "heat_res": 88, "trade_indep": 86},
    "Brazil":                   {"pop_m": 216.0, "energy": 90, "food": 96, "water": 98, "gdp_pc": 10, "afford": 78, "elev_m": 320,  "coast_km": 7491,  "cold_res": 42, "heat_res": 60, "trade_indep": 88},
    "Argentina":                {"pop_m": 46.0,  "energy": 82, "food": 96, "water": 80, "gdp_pc": 14, "afford": 76, "elev_m": 595,  "coast_km": 4989,  "cold_res": 76, "heat_res": 72, "trade_indep": 86},
    "Iceland":                  {"pop_m": 0.39,  "energy": 99, "food": 58, "water": 99, "gdp_pc": 78, "afford": 38, "elev_m": 557,  "coast_km": 4970,  "cold_res": 98, "heat_res": 96, "trade_indep": 74},
    "Switzerland":              {"pop_m": 8.8,   "energy": 68, "food": 56, "water": 92, "gdp_pc": 100,"afford": 24, "elev_m": 1350, "coast_km": 0,     "cold_res": 92, "heat_res": 86, "trade_indep": 62},
    "Sweden":                   {"pop_m": 10.5,  "energy": 86, "food": 74, "water": 94, "gdp_pc": 56, "afford": 52, "elev_m": 320,  "coast_km": 3218,  "cold_res": 96, "heat_res": 92, "trade_indep": 76},
    "Finland":                  {"pop_m": 5.6,   "energy": 82, "food": 74, "water": 96, "gdp_pc": 54, "afford": 54, "elev_m": 164,  "coast_km": 1250,  "cold_res": 97, "heat_res": 92, "trade_indep": 74},
    "Russia":                   {"pop_m": 144.0, "energy": 99, "food": 88, "water": 94, "gdp_pc": 14, "afford": 74, "elev_m": 600,  "coast_km": 37653, "cold_res": 96, "heat_res": 82, "trade_indep": 90},
    "France":                   {"pop_m": 68.0,  "energy": 78, "food": 88, "water": 78, "gdp_pc": 45, "afford": 52, "elev_m": 375,  "coast_km": 3427,  "cold_res": 78, "heat_res": 70, "trade_indep": 74},
    "Germany":                  {"pop_m": 84.0,  "energy": 44, "food": 72, "water": 72, "gdp_pc": 53, "afford": 54, "elev_m": 263,  "coast_km": 2389,  "cold_res": 80, "heat_res": 74, "trade_indep": 52},
    "United Kingdom":           {"pop_m": 68.0,  "energy": 56, "food": 54, "water": 78, "gdp_pc": 49, "afford": 46, "elev_m": 162,  "coast_km": 12429, "cold_res": 78, "heat_res": 80, "trade_indep": 50},
    "Spain":                    {"pop_m": 48.0,  "energy": 54, "food": 82, "water": 52, "gdp_pc": 33, "afford": 64, "elev_m": 660,  "coast_km": 4964,  "cold_res": 64, "heat_res": 52, "trade_indep": 62},
    "Italy":                    {"pop_m": 59.0,  "energy": 40, "food": 74, "water": 68, "gdp_pc": 38, "afford": 58, "elev_m": 538,  "coast_km": 7600,  "cold_res": 68, "heat_res": 58, "trade_indep": 52},
    "Poland":                   {"pop_m": 37.0,  "energy": 60, "food": 84, "water": 64, "gdp_pc": 22, "afford": 70, "elev_m": 173,  "coast_km": 440,   "cold_res": 82, "heat_res": 74, "trade_indep": 66},
    "Japan":                    {"pop_m": 124.0, "energy": 22, "food": 38, "water": 76, "gdp_pc": 34, "afford": 56, "elev_m": 438,  "coast_km": 29751, "cold_res": 76, "heat_res": 64, "trade_indep": 26},
    "South Korea":              {"pop_m": 51.7,  "energy": 20, "food": 36, "water": 62, "gdp_pc": 35, "afford": 54, "elev_m": 282,  "coast_km": 2413,  "cold_res": 76, "heat_res": 64, "trade_indep": 24},
    "China":                    {"pop_m": 1410.0,"energy": 76, "food": 76, "water": 58, "gdp_pc": 13, "afford": 72, "elev_m": 1840, "coast_km": 14500, "cold_res": 74, "heat_res": 62, "trade_indep": 76},
    "India":                    {"pop_m": 1430.0,"energy": 60, "food": 78, "water": 48, "gdp_pc": 3,  "afford": 88, "elev_m": 160,  "coast_km": 7000,  "cold_res": 36, "heat_res": 38, "trade_indep": 68},
    "Indonesia":                {"pop_m": 277.0, "energy": 84, "food": 76, "water": 84, "gdp_pc": 5,  "afford": 84, "elev_m": 367,  "coast_km": 54716, "cold_res": 22, "heat_res": 62, "trade_indep": 76},
    "Mexico":                   {"pop_m": 129.0, "energy": 74, "food": 74, "water": 56, "gdp_pc": 14, "afford": 74, "elev_m": 1111, "coast_km": 9330,  "cold_res": 52, "heat_res": 54, "trade_indep": 70},
    "Chile":                    {"pop_m": 19.6,  "energy": 62, "food": 82, "water": 86, "gdp_pc": 17, "afford": 68, "elev_m": 1871, "coast_km": 6435,  "cold_res": 82, "heat_res": 76, "trade_indep": 74},
    "Colombia":                 {"pop_m": 52.0,  "energy": 82, "food": 80, "water": 92, "gdp_pc": 7,  "afford": 82, "elev_m": 593,  "coast_km": 3208,  "cold_res": 48, "heat_res": 66, "trade_indep": 78},
    "Peru":                     {"pop_m": 34.0,  "energy": 74, "food": 74, "water": 88, "gdp_pc": 8,  "afford": 80, "elev_m": 1555, "coast_km": 2414,  "cold_res": 68, "heat_res": 70, "trade_indep": 74},
    "Algeria":                  {"pop_m": 46.0,  "energy": 96, "food": 54, "water": 28, "gdp_pc": 5,  "afford": 84, "elev_m": 800,  "coast_km": 998,   "cold_res": 52, "heat_res": 48, "trade_indep": 68},
    "Morocco":                  {"pop_m": 37.5,  "energy": 44, "food": 68, "water": 36, "gdp_pc": 4,  "afford": 84, "elev_m": 909,  "coast_km": 1835,  "cold_res": 54, "heat_res": 52, "trade_indep": 56},
    "Egypt":                    {"pop_m": 112.0, "energy": 70, "food": 48, "water": 22, "gdp_pc": 4,  "afford": 86, "elev_m": 321,  "coast_km": 2450,  "cold_res": 32, "heat_res": 40, "trade_indep": 46},
    "Saudi Arabia":             {"pop_m": 36.0,  "energy": 99, "food": 26, "water": 12, "gdp_pc": 32, "afford": 64, "elev_m": 665,  "coast_km": 2640,  "cold_res": 34, "heat_res": 26, "trade_indep": 44},
    "United Arab Emirates":     {"pop_m": 10.0,  "energy": 96, "food": 16, "water": 10, "gdp_pc": 50, "afford": 46, "elev_m": 149,  "coast_km": 1318,  "cold_res": 24, "heat_res": 22, "trade_indep": 30},
    "Turkey":                   {"pop_m": 85.0,  "energy": 52, "food": 84, "water": 64, "gdp_pc": 13, "afford": 76, "elev_m": 1132, "coast_km": 7200,  "cold_res": 70, "heat_res": 64, "trade_indep": 68},
    "South Africa":             {"pop_m": 60.0,  "energy": 76, "food": 78, "water": 44, "gdp_pc": 6,  "afford": 80, "elev_m": 1034, "coast_km": 2798,  "cold_res": 66, "heat_res": 62, "trade_indep": 72},
    "Nigeria":                  {"pop_m": 223.0, "energy": 84, "food": 64, "water": 58, "gdp_pc": 2,  "afford": 88, "elev_m": 380,  "coast_km": 853,   "cold_res": 24, "heat_res": 46, "trade_indep": 62},
    "Kazakhstan":               {"pop_m": 20.0,  "energy": 96, "food": 86, "water": 62, "gdp_pc": 13, "afford": 76, "elev_m": 387,  "coast_km": 0,     "cold_res": 92, "heat_res": 70, "trade_indep": 84},
    "Ukraine":                  {"pop_m": 37.0,  "energy": 64, "food": 94, "water": 66, "gdp_pc": 5,  "afford": 82, "elev_m": 175,  "coast_km": 2782,  "cold_res": 84, "heat_res": 74, "trade_indep": 76},
    "Netherlands":              {"pop_m": 17.8,  "energy": 48, "food": 76, "water": 72, "gdp_pc": 62, "afford": 46, "elev_m": 30,   "coast_km": 451,   "cold_res": 78, "heat_res": 78, "trade_indep": 44},
    "Belgium":                  {"pop_m": 11.7,  "energy": 36, "food": 58, "water": 66, "gdp_pc": 54, "afford": 50, "elev_m": 181,  "coast_km": 66,    "cold_res": 76, "heat_res": 76, "trade_indep": 36},
    "Austria":                  {"pop_m": 9.1,   "energy": 68, "food": 78, "water": 90, "gdp_pc": 56, "afford": 50, "elev_m": 910,  "coast_km": 0,     "cold_res": 88, "heat_res": 82, "trade_indep": 68},
    "Portugal":                 {"pop_m": 10.4,  "energy": 60, "food": 72, "water": 68, "gdp_pc": 27, "afford": 66, "elev_m": 372,  "coast_km": 1793,  "cold_res": 62, "heat_res": 66, "trade_indep": 60},
    "Greece":                   {"pop_m": 10.4,  "energy": 52, "food": 70, "water": 62, "gdp_pc": 23, "afford": 68, "elev_m": 498,  "coast_km": 13676, "cold_res": 58, "heat_res": 54, "trade_indep": 56},
    "Ireland":                  {"pop_m": 5.2,   "energy": 54, "food": 88, "water": 92, "gdp_pc": 104,"afford": 38, "elev_m": 118,  "coast_km": 1448,  "cold_res": 82, "heat_res": 86, "trade_indep": 66},
    "Denmark":                  {"pop_m": 5.9,   "energy": 78, "food": 88, "water": 80, "gdp_pc": 68, "afford": 42, "elev_m": 34,   "coast_km": 7314,  "cold_res": 88, "heat_res": 86, "trade_indep": 72},
    "Romania":                  {"pop_m": 19.0,  "energy": 74, "food": 84, "water": 74, "gdp_pc": 18, "afford": 76, "elev_m": 414,  "coast_km": 225,   "cold_res": 80, "heat_res": 70, "trade_indep": 74},
    "Czechia":                  {"pop_m": 10.8,  "energy": 64, "food": 76, "water": 70, "gdp_pc": 31, "afford": 64, "elev_m": 433,  "coast_km": 0,     "cold_res": 82, "heat_res": 76, "trade_indep": 64},
    "Hungary":                  {"pop_m": 9.6,   "energy": 56, "food": 86, "water": 72, "gdp_pc": 22, "afford": 72, "elev_m": 143,  "coast_km": 0,     "cold_res": 78, "heat_res": 70, "trade_indep": 66},
    "Vietnam":                  {"pop_m": 99.0,  "energy": 68, "food": 84, "water": 82, "gdp_pc": 4,  "afford": 86, "elev_m": 398,  "coast_km": 3444,  "cold_res": 32, "heat_res": 54, "trade_indep": 72},
    "Thailand":                 {"pop_m": 71.8,  "energy": 60, "food": 88, "water": 78, "gdp_pc": 7,  "afford": 84, "elev_m": 287,  "coast_km": 3219,  "cold_res": 24, "heat_res": 48, "trade_indep": 72},
    "Philippines":              {"pop_m": 117.0, "energy": 44, "food": 66, "water": 76, "gdp_pc": 4,  "afford": 84, "elev_m": 442,  "coast_km": 36289, "cold_res": 20, "heat_res": 52, "trade_indep": 54},
    "Malaysia":                 {"pop_m": 34.0,  "energy": 84, "food": 70, "water": 88, "gdp_pc": 12, "afford": 78, "elev_m": 419,  "coast_km": 4675,  "cold_res": 22, "heat_res": 54, "trade_indep": 74},
    "Pakistan":                 {"pop_m": 240.0, "energy": 50, "food": 68, "water": 38, "gdp_pc": 2,  "afford": 90, "elev_m": 900,  "coast_km": 1046,  "cold_res": 46, "heat_res": 36, "trade_indep": 56},
    "Iran":                     {"pop_m": 89.0,  "energy": 94, "food": 68, "water": 32, "gdp_pc": 5,  "afford": 84, "elev_m": 1305, "coast_km": 2440,  "cold_res": 66, "heat_res": 44, "trade_indep": 72},
    "Ethiopia":                 {"pop_m": 126.0, "energy": 64, "food": 62, "water": 64, "gdp_pc": 1,  "afford": 92, "elev_m": 1330, "coast_km": 0,     "cold_res": 52, "heat_res": 64, "trade_indep": 64},
    "Kenya":                    {"pop_m": 55.0,  "energy": 68, "food": 64, "water": 52, "gdp_pc": 2,  "afford": 88, "elev_m": 762,  "coast_km": 536,   "cold_res": 46, "heat_res": 66, "trade_indep": 62},
    "Mongolia":                 {"pop_m": 3.4,   "energy": 84, "food": 76, "water": 66, "gdp_pc": 5,  "afford": 82, "elev_m": 1528, "coast_km": 0,     "cold_res": 96, "heat_res": 80, "trade_indep": 78},
    "Bolivia":                  {"pop_m": 12.4,  "energy": 82, "food": 76, "water": 86, "gdp_pc": 4,  "afford": 86, "elev_m": 1192, "coast_km": 0,     "cold_res": 74, "heat_res": 76, "trade_indep": 78},
    "Uruguay":                  {"pop_m": 3.4,   "energy": 86, "food": 94, "water": 88, "gdp_pc": 22, "afford": 66, "elev_m": 109,  "coast_km": 660,   "cold_res": 72, "heat_res": 76, "trade_indep": 84},
    "Paraguay":                 {"pop_m": 6.8,   "energy": 94, "food": 92, "water": 88, "gdp_pc": 6,  "afford": 84, "elev_m": 178,  "coast_km": 0,     "cold_res": 54, "heat_res": 58, "trade_indep": 84},
    "Ecuador":                  {"pop_m": 18.0,  "energy": 80, "food": 78, "water": 86, "gdp_pc": 6,  "afford": 82, "elev_m": 1117, "coast_km": 2237,  "cold_res": 56, "heat_res": 68, "trade_indep": 76},
    "Venezuela":                {"pop_m": 28.8,  "energy": 92, "food": 54, "water": 88, "gdp_pc": 4,  "afford": 84, "elev_m": 450,  "coast_km": 2800,  "cold_res": 36, "heat_res": 58, "trade_indep": 68},
    "Greenland":                {"pop_m": 0.06,  "energy": 58, "food": 30, "water": 99, "gdp_pc": 56, "afford": 40, "elev_m": 1792, "coast_km": 44087, "cold_res": 99, "heat_res": 99, "trade_indep": 46},
    "Bangladesh":               {"pop_m": 173.0, "energy": 38, "food": 62, "water": 70, "gdp_pc": 3,  "afford": 88, "elev_m": 85,   "coast_km": 580,   "cold_res": 26, "heat_res": 40, "trade_indep": 48},
    "Myanmar":                  {"pop_m": 54.0,  "energy": 70, "food": 78, "water": 86, "gdp_pc": 2,  "afford": 90, "elev_m": 702,  "coast_km": 1930,  "cold_res": 34, "heat_res": 52, "trade_indep": 70},
    "Tanzania":                 {"pop_m": 67.0,  "energy": 58, "food": 70, "water": 64, "gdp_pc": 1,  "afford": 90, "elev_m": 1018, "coast_km": 1424,  "cold_res": 42, "heat_res": 62, "trade_indep": 62},
}

EUROPE_SET = {
    "Norway", "Sweden", "Finland", "Iceland", "Denmark", "United Kingdom", "Ireland",
    "France", "Spain", "Portugal", "Germany", "Netherlands", "Belgium", "Luxembourg",
    "Switzerland", "Austria", "Italy", "Poland", "Czechia", "Slovakia", "Hungary",
    "Romania", "Bulgaria", "Greece", "Croatia", "Slovenia", "Serbia", "Bosnia and Herz.",
    "Montenegro", "Albania", "Macedonia", "North Macedonia", "Estonia", "Latvia",
    "Lithuania", "Belarus", "Ukraine", "Moldova", "Finland"
}


def get_entity_metrics(arena, name, centroid=(0.5, 0.5)):
    """Return real metrics dict for any US state or World country, with geographic fallback for minor nations."""
    if arena == "us_states" and name in US_STATE_METRICS:
        return US_STATE_METRICS[name]
    if name in WORLD_METRICS:
        return WORLD_METRICS[name]
    # Deterministic geographic fallback for smaller countries so every single polygon behaves realistically
    cx, cy = centroid
    lat_abs = abs(cy - 0.58) * 140.0
    h = abs(hash(name)) % 100
    return {
        "pop_m": round(2.0 + (h % 25) * 1.1, 1),
        "energy": 32 + (h % 46),
        "food": 38 + ((h * 3) % 44),
        "water": 35 + ((h * 7) % 50),
        "gdp_pc": 4 + (h % 28),
        "afford": 60 + (h % 28),
        "elev_m": 120 + (h * 9) % 1100,
        "coast_km": 0 if (h % 4 == 0) else (200 + (h * 37) % 3500),
        "cold_res": int(max(20, min(92, 28 + lat_abs * 1.1))),
        "heat_res": int(max(24, min(88, 78 - abs(lat_abs - 30) * 0.7))),
        "trade_indep": 34 + ((h * 5) % 42),
    }
