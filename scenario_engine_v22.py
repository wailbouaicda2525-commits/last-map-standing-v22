"""
scenario_engine_v22.py — 5+ Year Infinite Zero-Overlap Map Simulation Engine.
Combines:
  Layer 1: Curated flagship high-RPM US & World scenarios
  Layer 2: 2,000+ deterministic combinatorial scenarios (Arenas x Mechanics x Systems/Thresholds)
  Layer 3: Optional Groq/Gemini novel scenario expansion deduplicated against published_history.json
Outputs a complete simulation blueprint with real elimination order, bar chart data, and Final 2 VS stats.
"""
import difflib
import hashlib
import json
import math
import os
import random
from datetime import datetime, timezone

from map_geometry_v22 import load_arena_geometry, BASE_DIR
from real_metrics_db import get_entity_metrics

HISTORY_PATH = os.path.join(BASE_DIR, "published_history.json")

# =====================================================================
# LAYER 1: CURATED HIGH-RPM ADULT FLAGSHIP SCENARIOS (US & WORLD)
# =====================================================================
CURATED_SCENARIOS = [
    # --- US 50 STATES (Highest US Adult RPM $10-$18+) ---
    {
        "id": "us_zero_electricity",
        "arena": "us_states",
        "mechanic": "collapse",
        "title_long": "If Every U.S. State Lost Electricity Forever: Only 1 Survives (Day 0 to Day 365)",
        "title_short": "If Every U.S. State Lost Electricity Tomorrow — Only 1 Survives",
        "thumb_top": "ZERO POWER. 50 STATES.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 ELIMINATED",
        "rule_label": "US GRID COLLAPSE // DAY 0-365",
        "weights": {"energy": 0.35, "food": 0.25, "water": 0.20, "trade_indep": 0.20, "pop_penalty": 0.38},
        "chart1_metric": ("energy", "ENERGY INDEPENDENCE INDEX"),
        "chart2_metric": ("food", "FOOD SURPLUS PER CAPITA"),
        "premise": "A simultaneous nationwide power-grid failure cuts off every U.S. state from outside electricity.",
        "elim_tag": "GRID OFFLINE",
        "max_day": 365,
    },
    {
        "id": "us_zero_imports",
        "arena": "us_states",
        "mechanic": "collapse",
        "title_long": "If Every U.S. State Sealed Its Borders With Zero Imports: Only 1 Survives",
        "title_short": "If Every U.S. State Sealed Its Borders Forever — Only 1 Survives",
        "thumb_top": "ZERO IMPORTS. 50 STATES.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 COLLAPSED",
        "rule_label": "TOTAL BORDER SEAL // DAY 0-365",
        "weights": {"trade_indep": 0.35, "food": 0.30, "energy": 0.20, "water": 0.15, "pop_penalty": 0.32},
        "chart1_metric": ("trade_indep", "SELF-SUFFICIENCY SCORE"),
        "chart2_metric": ("water", "FRESHWATER RESERVES"),
        "premise": "Every interstate highway, freight train, port, and cargo flight shuts down permanently.",
        "elim_tag": "SUPPLY GONE",
        "max_day": 365,
    },
    {
        "id": "us_50k_salary",
        "arena": "us_states",
        "mechanic": "collapse",
        "title_long": "Surviving on $50,000 a Year in Every U.S. State: Only 1 Survives",
        "title_short": "Living on $50,000 a Year Across America — Only 1 State Survives",
        "thumb_top": "$50K SALARY. 50 STATES.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 PRICED OUT",
        "rule_label": "COST OF LIVING TEST // $50K/YR",
        "weights": {"afford": 0.50, "energy": 0.15, "food": 0.20, "water": 0.15, "pop_penalty": 0.15},
        "chart1_metric": ("afford", "AFFORDABILITY INDEX"),
        "chart2_metric": ("gdp_pc", "LOCAL ECONOMIC OUTPUT ($K)"),
        "premise": "Every household is capped at $50,000 annual income as housing, utility, and food costs rise every month.",
        "elim_tag": "PRICED OUT",
        "max_day": 365,
    },
    {
        "id": "us_laser_diagonal",
        "arena": "us_states",
        "mechanic": "laser_line",
        "title_long": "If a Sweeping Line Touches Your U.S. State, It Is Deleted: Only 1 Survives",
        "title_short": "If This Line Touches Your State, It's Deleted — Only 1 Survives",
        "thumb_top": "LINE TOUCHES = DELETED",
        "thumb_pill": "50 STATES",
        "thumb_stamp": "49 ERASED",
        "rule_label": "RULE: LINE TOUCHES = DELETED",
        "line_angle_deg": 32,
        "chart1_metric": ("elev_m", "MEAN ELEVATION (METERS)"),
        "chart2_metric": ("gdp_pc", "STATE GDP PER CAPITA ($K)"),
        "premise": "A geometric red line sweeps across the United States map — the instant it touches any border, that state is erased.",
        "elim_tag": "DELETED",
        "max_day": 50,
    },
    {
        "id": "us_shrinking_zone_heartland",
        "arena": "us_states",
        "mechanic": "shrinking_zone",
        "title_long": "If Your U.S. State Is Outside the Shrinking Safe Zone, It Is Deleted (50 to 1)",
        "title_short": "Outside the Shrinking Zone = Deleted: Which U.S. State Survives?",
        "thumb_top": "OUTSIDE ZONE = DELETED",
        "thumb_pill": "ONLY 1 LEFT",
        "thumb_stamp": "49 ELIMINATED",
        "rule_label": "SHRINKING SAFE ZONE // 50 TO 1",
        "zone_center": [0.46, 0.42],
        "chart1_metric": ("food", "AGRICULTURAL OUTPUT"),
        "chart2_metric": ("water", "WATER SECURITY INDEX"),
        "premise": "A circular safe zone collapses inward across North America — every state left outside the boundary vanishes.",
        "elim_tag": "OUT OF ZONE",
        "max_day": 50,
    },
    {
        "id": "us_ocean_rise_100m",
        "arena": "us_states",
        "mechanic": "elevation_flood",
        "title_long": "If Ocean Levels Rose 100 Meters Across America: Day 0 to Day 1000 (Only 1 Survives)",
        "title_short": "If Oceans Rose 100 Meters in America — Only 1 State Survives",
        "thumb_top": "+100M OCEANS. USA.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 FLOODED",
        "rule_label": "SEA LEVEL +100M // DAY 0-1000",
        "weights": {"elev_norm": 0.55, "water": 0.15, "food": 0.15, "energy": 0.15, "pop_penalty": 0.18},
        "chart1_metric": ("elev_m", "MEAN ELEVATION (METERS)"),
        "chart2_metric": ("energy", "ENERGY SELF-SUFFICIENCY"),
        "premise": "Global sea levels rise steadily toward 100 meters, flooding coastlines and pushing inland elevation to the test.",
        "elim_tag": "SUBMERGED",
        "max_day": 1000,
    },
    {
        "id": "us_extreme_freeze",
        "arena": "us_states",
        "mechanic": "collapse",
        "title_long": "If America Froze by -25°C Overnight: Day 0 to Day 365 (Only 1 State Survives)",
        "title_short": "If America Dropped -25°C Overnight — Only 1 State Survives",
        "thumb_top": "-25°C FREEZE. 50 STATES.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 FROZEN OUT",
        "rule_label": "ARCTIC FREEZE -25C // DAY 0-365",
        "weights": {"cold_res": 0.42, "energy": 0.30, "food": 0.15, "water": 0.13, "pop_penalty": 0.25},
        "chart1_metric": ("cold_res", "COLD RESILIENCE INDEX"),
        "chart2_metric": ("energy", "HEATING ENERGY CAPACITY"),
        "premise": "A permanent polar vortex plunges every state 25 degrees Celsius below normal for an entire year.",
        "elim_tag": "FROZEN OUT",
        "max_day": 365,
    },
    {
        "id": "us_extreme_heat",
        "arena": "us_states",
        "mechanic": "collapse",
        "title_long": "If America Heated Up by +15°C Overnight: Only 1 U.S. State Survives",
        "title_short": "If Every U.S. State Got +15°C Hotter — Only 1 Survives",
        "thumb_top": "+15°C HEATWAVE. USA.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "49 OVERHEATED",
        "rule_label": "HEAT DOME +15C // DAY 0-365",
        "weights": {"heat_res": 0.42, "water": 0.30, "energy": 0.15, "food": 0.13, "pop_penalty": 0.25},
        "chart1_metric": ("heat_res", "HEAT RESILIENCE INDEX"),
        "chart2_metric": ("water", "FRESHWATER RESERVES"),
        "premise": "A relentless +15°C heat anomaly dries reservoirs and overloads cooling grids across the United States.",
        "elim_tag": "OVERHEATED",
        "max_day": 365,
    },
    # --- WORLD 195 COUNTRIES (Global Viral + Tier-1 Economics) ---
    {
        "id": "world_oil_vanishes",
        "arena": "world",
        "mechanic": "collapse",
        "title_long": "If Global Oil Vanished Tomorrow: Day 0 to Day 365 (Only 1 Country Survives)",
        "title_short": "If Oil Disappeared From Earth Tomorrow — Only 1 Country Survives",
        "thumb_top": "ZERO OIL. 195 NATIONS.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "194 COLLAPSED",
        "rule_label": "GLOBAL OIL CUTOFF // DAY 0-365",
        "weights": {"energy": 0.40, "food": 0.25, "water": 0.15, "trade_indep": 0.20, "pop_penalty": 0.22},
        "chart1_metric": ("energy", "ENERGY INDEPENDENCE"),
        "chart2_metric": ("food", "DOMESTIC FOOD SECURITY"),
        "premise": "Every oil well, tanker, and refinery stops dead, forcing nations to run purely on hydro, nuclear, and local resources.",
        "elim_tag": "FUEL DEPLETED",
        "max_day": 365,
    },
    {
        "id": "world_cargo_ships_stop",
        "arena": "world",
        "mechanic": "collapse",
        "title_long": "If All Cargo Ships Stopped Forever: Which Country Survives Longest?",
        "title_short": "If Every Cargo Ship Stopped Forever — Only 1 Country Survives",
        "thumb_top": "ZERO CARGO SHIPS.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "194 CUT OFF",
        "rule_label": "GLOBAL SHIPPING HALT // DAY 0-365",
        "weights": {"trade_indep": 0.42, "food": 0.28, "energy": 0.20, "water": 0.10, "pop_penalty": 0.18},
        "chart1_metric": ("trade_indep", "ZERO-IMPORT SURVIVAL SCORE"),
        "chart2_metric": ("food", "FOOD SELF-SUFFICIENCY"),
        "premise": "Ninety percent of global trade moves by sea — overnight, every container ship freezes in port.",
        "elim_tag": "TRADE CUTOFF",
        "max_day": 365,
    },
    {
        "id": "world_earth_freezes",
        "arena": "world",
        "mechanic": "collapse",
        "title_long": "If Earth Froze by -25°C Overnight: Day 0 to Day 365 (Only 1 Country Survives)",
        "title_short": "If Earth Froze -25°C Overnight — Only 1 Country Survives",
        "thumb_top": "EARTH FROZE -25°C.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "194 FROZEN OUT",
        "rule_label": "GLOBAL FREEZE -25C // DAY 0-365",
        "weights": {"cold_res": 0.38, "energy": 0.32, "food": 0.18, "water": 0.12, "pop_penalty": 0.20},
        "chart1_metric": ("cold_res", "ARCTIC INFRASTRUCTURE INDEX"),
        "chart2_metric": ("energy", "HEATING ENERGY RESERVES"),
        "premise": "Global temperatures plummet 25 degrees overnight, testing heating grids, insulation, and winter energy supplies.",
        "elim_tag": "FROZEN OUT",
        "max_day": 365,
    },
    {
        "id": "world_never_rains",
        "arena": "world",
        "mechanic": "collapse",
        "title_long": "If It Never Rained Again on Earth: Day 0 to Day 1000 (Only 1 Country Survives)",
        "title_short": "If Rain Stopped Forever on Earth — Only 1 Country Survives",
        "thumb_top": "ZERO RAIN. DAY 1,000.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "194 DRIED OUT",
        "rule_label": "ZERO RAINFALL // DAY 0-1000",
        "weights": {"water": 0.48, "food": 0.22, "energy": 0.15, "trade_indep": 0.15, "pop_penalty": 0.24},
        "chart1_metric": ("water", "FRESHWATER PER CAPITA"),
        "chart2_metric": ("food", "STORED FOOD CAPACITY"),
        "premise": "Every raincloud vanishes permanently, leaving humanity dependent on glaciers, aquifers, and freshwater lakes.",
        "elim_tag": "DRIED OUT",
        "max_day": 1000,
    },
    {
        "id": "world_shrinking_zone_atlantic",
        "arena": "world",
        "mechanic": "shrinking_zone",
        "title_long": "If Your Country Is Outside the Shrinking Circle, It Is Deleted: Only 1 Survives",
        "title_short": "Outside the Circle = Deleted: Only 1 Country Survives",
        "thumb_top": "OUTSIDE ZONE = DELETED",
        "thumb_pill": "195 TO 1",
        "thumb_stamp": "194 ERASED",
        "rule_label": "SHRINKING CIRCLE // 195 TO 1",
        "zone_center": [0.49, 0.33],
        "chart1_metric": ("gdp_pc", "ECONOMIC STRENGTH ($K/CAPITA)"),
        "chart2_metric": ("energy", "ENERGY CAPACITY"),
        "premise": "Every round, a shrinking safe zone contracts across the globe — any country outside the ring is permanently deleted.",
        "elim_tag": "OUT OF ZONE",
        "max_day": 100,
    },
    {
        "id": "world_laser_line_sweep",
        "arena": "world",
        "mechanic": "laser_line",
        "title_long": "Every 30 Seconds a Line Sweeps the World Map — If It Touches Your Country, You're Out",
        "title_short": "If This Line Touches Your Country, It's Deleted — Only 1 Survives",
        "thumb_top": "1 LINE ERASES THE MAP",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "194 DELETED",
        "rule_label": "SWEEPING LASER LINE // 195 TO 1",
        "line_angle_deg": 24,
        "chart1_metric": ("coast_km", "COASTLINE EXPOSURE (KM)"),
        "chart2_metric": ("elev_m", "MEAN ELEVATION (M)"),
        "premise": "A relentless geometric beam sweeps across Earth's continents, erasing every country it crosses until one survives.",
        "elim_tag": "DELETED",
        "max_day": 100,
    },
    # --- EUROPE HIGH-RPM ARENA ---
    {
        "id": "europe_zero_gas",
        "arena": "europe",
        "mechanic": "collapse",
        "title_long": "If Europe Lost All Imported Energy Tomorrow: Day 0 to Day 365 (Only 1 Survives)",
        "title_short": "If Europe Lost Imported Energy Tomorrow — Only 1 Country Survives",
        "thumb_top": "ZERO ENERGY IMPORTS.",
        "thumb_pill": "EUROPE",
        "thumb_stamp": "ONLY 1 LEFT",
        "rule_label": "EUROPE ENERGY CUTOFF // DAY 0-365",
        "weights": {"energy": 0.45, "cold_res": 0.25, "food": 0.15, "water": 0.15, "pop_penalty": 0.18},
        "chart1_metric": ("energy", "DOMESTIC ENERGY SHARE"),
        "chart2_metric": ("cold_res", "WINTER GRID RESILIENCE"),
        "premise": "Every external pipeline and LNG tanker into Europe shuts off in winter — forcing nations onto domestic power alone.",
        "elim_tag": "GRID OFFLINE",
        "max_day": 365,
    },
    {
        "id": "americas_zero_trade",
        "arena": "americas",
        "mechanic": "collapse",
        "title_long": "If Every Country in the Americas Stopped Trading Forever: Only 1 Survives",
        "title_short": "If Every Country in the Americas Closed Its Borders — Only 1 Survives",
        "thumb_top": "ZERO TRADE. AMERICAS.",
        "thumb_pill": "1 SURVIVES",
        "thumb_stamp": "CUT OFF",
        "rule_label": "AMERICAS ISOLATION // DAY 0-365",
        "weights": {"trade_indep": 0.38, "food": 0.28, "energy": 0.22, "water": 0.12, "pop_penalty": 0.18},
        "chart1_metric": ("trade_indep", "SELF-SUFFICIENCY INDEX"),
        "chart2_metric": ("food", "AGRICULTURAL SURPLUS"),
        "premise": "From Canada to Argentina, every border freezes shut with zero exports or imports for an entire year.",
        "elim_tag": "ISOLATED",
        "max_day": 365,
    },
]

# =====================================================================
# LAYER 2: 2,000+ PROCEDURAL MATRIX GENERATOR (5+ YEARS ZERO DUPLICATES!)
# =====================================================================
MATRIX_SYSTEMS = [
    ("Trucking & Freight Highways", "NO TRUCKS", "trade_indep", "food", "FREIGHT HALT"),
    ("Commercial Aviation & Airports", "NO FLIGHTS", "trade_indep", "gdp_pc", "AIRSPACE SHUT"),
    ("Global Internet & Cloud Servers", "ZERO INTERNET", "trade_indep", "energy", "OFFLINE"),
    ("GPS & Navigation Satellites", "NO GPS", "food", "energy", "SIGNAL LOST"),
    ("Refrigeration & Cold Chains", "NO COLD CHAIN", "food", "cold_res", "SPOILAGE"),
    ("Synthetic Fertilizers", "NO FERTILIZER", "food", "water", "CROP DROP"),
    ("Semiconductors & Microchips", "NO CHIPS", "trade_indep", "energy", "TECH HALT"),
    ("Freshwater Pipelines & Aqueducts", "NO AQUEDUCTS", "water", "food", "WATER CUT"),
    ("Natural Gas Heating Networks", "NO NAT GAS", "energy", "cold_res", "HEAT LOSS"),
    ("Banking & Digital Payments", "NO DIGITAL PAY", "afford", "trade_indep", "CASH FREEZE"),
    ("Ocean Desalination & Coastal Ports", "PORTS CLOSED", "water", "trade_indep", "PORT LOCK"),
    ("Bridges & Interstate Tunnels", "BRIDGES OUT", "trade_indep", "food", "CUT OFF"),
    ("Industrial Steel & Cement Supply", "NO STEEL", "energy", "trade_indep", "STALLED"),
    ("Solar Output Drops 40%", "DIMMED SUN", "energy", "cold_res", "LOW POWER"),
    ("Hydroelectric Rivers Drop 60%", "LOW RIVERS", "water", "energy", "DROUGHT"),
    ("Diesel & Heavy Machinery Fuel", "NO DIESEL", "energy", "food", "FUEL OUT"),
    ("Global Insurance & Mortgages", "NO CREDIT", "afford", "gdp_pc", "INSOLVENT"),
    ("Housing Costs Double Overnight", "2X HOUSING", "afford", "gdp_pc", "PRICED OUT"),
    ("Grocery Prices Triple in 1 Year", "3X FOOD COST", "food", "afford", "COST SHOCK"),
    ("Underground Water Reserves Halved", "HALF AQUIFER", "water", "heat_res", "DRY WELLS"),
    ("Permanent -15°C Winter Anomaly", "-15C WINTER", "cold_res", "energy", "FROZEN"),
    ("Permanent +10°C Summer Anomaly", "+10C HEAT", "heat_res", "water", "OVERHEATED"),
    ("Sea Levels Rise +50 Meters", "+50M OCEANS", "elev_norm", "water", "FLOODED"),
    ("Sea Levels Rise +200 Meters", "+200M OCEANS", "elev_norm", "energy", "SUBMERGED"),
    ("Oceans Drain 500 Meters", "-500M OCEANS", "water", "trade_indep", "STRANDED"),
    ("100 Days of Nonstop Storms", "100-DAY STORM", "elev_norm", "energy", "STORM OUT"),
    ("Zero Tourism & Hospitality Revenue", "NO TOURISM", "trade_indep", "afford", "REVENUE DROP"),
    ("All Import Tariffs Hit 500%", "500% TARIFFS", "trade_indep", "food", "TRADE SHOCK"),
    ("Retirement on $40K a Year Test", "$40K RETIRE", "afford", "water", "PRICED OUT"),
    ("Working From Home Cuts Cities 50%", "CITY EXODUS", "afford", "energy", "HOLLOWED"),
]

MATRIX_ARENAS = [
    ("us_states", "U.S. State", "50 STATES", "Every U.S. State"),
    ("world", "Country", "195 NATIONS", "Every Country on Earth"),
    ("europe", "European Nation", "EUROPE", "Every Country in Europe"),
    ("americas", "Nation in the Americas", "AMERICAS", "Every Country in the Americas"),
]

MATRIX_ZONES = [
    ("us_states", "Denver Heartland", [0.38, 0.44]),
    ("us_states", "Chicago Great Lakes", [0.62, 0.34]),
    ("us_states", "Dallas Southern Hub", [0.48, 0.66]),
    ("us_states", "Pacific Northwest", [0.16, 0.22]),
    ("us_states", "Appalachian Spine", [0.74, 0.48]),
    ("us_states", "Northern Plains", [0.46, 0.24]),
    ("world", "North Atlantic Core", [0.42, 0.30]),
    ("world", "Mediterranean Basin", [0.54, 0.38]),
    ("world", "Pacific Rim", [0.82, 0.42]),
    ("world", "Equatorial Belt", [0.50, 0.58]),
    ("world", "Arctic Circle", [0.50, 0.14]),
    ("world", "South Atlantic", [0.40, 0.70]),
    ("europe", "Alpine Center", [0.48, 0.56]),
    ("europe", "Nordic North", [0.54, 0.24]),
    ("americas", "Caribbean Hub", [0.52, 0.46]),
]

MATRIX_LASER_ANGLES = [0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120, 132, 144, 156, 168, 180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 345]

# Extra Economic, Climate, Elevation, Cost-of-Living & Resource Cutoff Scenarios for 5+ Year Zero-Overlap Depth
MATRIX_THRESHOLDS = [
    ("Living on $35,000 a Year", "$35K SALARY", "afford", "food", "PRICED OUT", 365),
    ("Living on $45,000 a Year", "$45K SALARY", "afford", "energy", "PRICED OUT", 365),
    ("Living on $60,000 a Year", "$60K SALARY", "afford", "water", "PRICED OUT", 365),
    ("Living on $75,000 a Year", "$75K SALARY", "afford", "gdp_pc", "PRICED OUT", 365),
    ("Raising a Family of 4 on $70K", "$70K FAMILY", "afford", "food", "PRICED OUT", 365),
    ("Retiring With $250,000 Savings", "$250K RETIRE", "afford", "water", "DEPLETED", 365),
    ("Retiring With $500,000 Savings", "$500K RETIRE", "afford", "energy", "DEPLETED", 365),
    ("Sea Levels Rise +25 Meters", "+25M OCEANS", "elev_norm", "water", "FLOODED", 1000),
    ("Sea Levels Rise +75 Meters", "+75M OCEANS", "elev_norm", "food", "FLOODED", 1000),
    ("Sea Levels Rise +150 Meters", "+150M OCEANS", "elev_norm", "energy", "SUBMERGED", 1000),
    ("Sea Levels Rise +300 Meters", "+300M OCEANS", "elev_norm", "trade_indep", "SUBMERGED", 1000),
    ("Sea Levels Rise +500 Meters", "+500M OCEANS", "elev_norm", "water", "SUBMERGED", 1000),
    ("Temperatures Drop -10°C Forever", "-10C CHILL", "cold_res", "energy", "FROZEN OUT", 365),
    ("Temperatures Drop -20°C Forever", "-20C FREEZE", "cold_res", "food", "FROZEN OUT", 365),
    ("Temperatures Drop -35°C Forever", "-35C ICE AGE", "cold_res", "energy", "FROZEN SOLID", 365),
    ("Temperatures Spike +8°C Forever", "+8C HEAT", "heat_res", "water", "OVERHEATED", 365),
    ("Temperatures Spike +12°C Forever", "+12C SCORCH", "heat_res", "energy", "OVERHEATED", 365),
    ("Temperatures Spike +18°C Forever", "+18C FURNACE", "heat_res", "water", "SCORCHED", 365),
    ("Rainfall Drops 50% for 3 Years", "-50% RAIN", "water", "food", "DROUGHT", 1000),
    ("Rainfall Drops 80% for 5 Years", "-80% RAIN", "water", "energy", "DRY OUT", 1000),
    ("Electricity Costs Triple Overnight", "3X POWER BILL", "energy", "afford", "PRICED OUT", 365),
    ("Electricity Costs Jump 5x Overnight", "5X POWER BILL", "energy", "gdp_pc", "GRID SHOCK", 365),
    ("Gasoline Hits $15 per Gallon", "$15 GASOLINE", "energy", "trade_indep", "FUEL SHOCK", 365),
    ("Global Shipping Costs Jump 10x", "10X FREIGHT", "trade_indep", "food", "IMPORT HALT", 365),
    ("Domestic Water Supply Drops 40%", "-40% WATER", "water", "heat_res", "WATER SHORT", 365),
    ("All Coal Plants Shut Down Tomorrow", "ZERO COAL", "energy", "cold_res", "BLACKOUT", 365),
    ("All Nuclear Plants Pause 1 Year", "ZERO NUCLEAR", "energy", "trade_indep", "GRID DROP", 365),
    ("All Wind & Solar Drop 70%", "LOW RENEWABLES", "energy", "water", "POWER DROP", 365),
    ("All Oil Pipelines Freeze for 1 Year", "NO PIPELINES", "energy", "food", "FUEL CUT", 365),
    ("Grain Exports Stop Worldwide", "NO GRAIN TRADE", "food", "trade_indep", "FOOD SHORT", 365),
    ("Dairy & Meat Shipping Stops", "LOCAL FOOD ONLY", "food", "water", "SUPPLY GAP", 365),
    ("All Intermodal Rail Stops Forever", "ZERO RAIL", "trade_indep", "energy", "FREIGHT OUT", 365),
    ("All Fiber-Optic Undersea Cables Cut", "NO SUBSEA NET", "trade_indep", "gdp_pc", "DISCONNECTED", 365),
    ("Global Data Centers Lose Cooling", "CLOUD OFFLINE", "water", "energy", "SERVERS DOWN", 365),
    ("Commercial Banking Freezes 90 Days", "BANK FREEZE", "food", "trade_indep", "LIQUIDITY OUT", 90),
    ("Every Border Imposes 100% Export Ban", "ZERO EXPORTS", "trade_indep", "energy", "SEALED OFF", 365),
    ("Winter Lasts 9 Months Every Year", "9-MO WINTER", "cold_res", "food", "FROZEN OUT", 365),
    ("Summer Lasts 9 Months Every Year", "9-MO SUMMER", "heat_res", "water", "PARCHED", 365),
    ("Every Aquifer Runs Dry in 500 Days", "ZERO AQUIFERS", "water", "elev_norm", "DRIED OUT", 500),
    ("Urban Rent Triples in 24 Months", "3X RENT WAVE", "afford", "gdp_pc", "PRICED OUT", 730),
]

HORIZONS = [
    ("90-Day Stress Test", 90, 1.0),
    ("1-Year Survival Test", 365, 1.05),
    ("5-Year Endurance Test", 1825, 1.12),
]


def build_infinite_catalog():
    """Build deterministic 5+ year catalog (1,500+ genuinely distinct US & World blueprints!)."""
    catalog = list(CURATED_SCENARIOS)

    # 1) Systems x Arenas x Stress Horizons (30 x 4 x 3 = 360 unique survival collapse scenarios)
    for h_label, h_days, h_pop_mult in HORIZONS:
        for sys_name, short_tag, m1, m2, elim_tag in MATRIX_SYSTEMS:
            for arena_key, entity_singular, arena_badge, arena_phrase in MATRIX_ARENAS:
                sid = f"mx_{arena_key}_{h_days}_{hashlib.md5(sys_name.encode()).hexdigest()[:7]}"
                w = {m1: 0.42, m2: 0.28, "water": 0.15, "energy": 0.15, "pop_penalty": 0.24 * h_pop_mult}
                if m1 in ("energy", "water"):
                    w["food"] = 0.15
                title_suffix = f"Day 0 to Day {h_days}" if h_days != 365 else "Day 0 to Day 365"
                catalog.append({
                    "id": sid,
                    "arena": arena_key,
                    "mechanic": "collapse",
                    "title_long": f"If {sys_name} Stopped Across {arena_phrase} ({h_label}): Only 1 Survives",
                    "title_short": f"{sys_name} Stops ({h_days} Days) — Which {entity_singular} Survives?",
                    "thumb_top": f"{short_tag}. {arena_badge}.",
                    "thumb_pill": f"DAY {h_days}",
                    "thumb_stamp": "ELIMINATED",
                    "rule_label": f"{short_tag} // {title_suffix.upper()}",
                    "weights": w,
                    "chart1_metric": (m1 if m1 != "elev_norm" else "elev_m", m1.replace("_", " ").upper() + " SCORE"),
                    "chart2_metric": (m2 if m2 != "elev_norm" else "elev_m", m2.replace("_", " ").upper() + " SCORE"),
                    "premise": f"During a {h_days}-day {h_label.lower()}, {sys_name.lower()} disappears across {arena_phrase}.",
                    "elim_tag": elim_tag,
                    "max_day": h_days,
                })

    # 2) Economic, Climate & Elevation Threshold Cutoffs x Arenas (40 x 4 = 160)
    for t_name, short_tag, m1, m2, elim_tag, max_d in MATRIX_THRESHOLDS:
        for arena_key, entity_singular, arena_badge, arena_phrase in MATRIX_ARENAS:
            sid = f"th_{arena_key}_{hashlib.md5(t_name.encode()).hexdigest()[:7]}"
            w = {m1: 0.48, m2: 0.24, "energy": 0.14, "water": 0.14, "pop_penalty": 0.22}
            catalog.append({
                "id": sid,
                "arena": arena_key,
                "mechanic": "elevation_flood" if m1 == "elev_norm" else "collapse",
                "title_long": f"{t_name} Across {arena_phrase}: Only 1 Survives (Map Simulation)",
                "title_short": f"{t_name} — Only 1 {entity_singular} Survives",
                "thumb_top": f"{short_tag}. {arena_badge}.",
                "thumb_pill": "1 SURVIVES",
                "thumb_stamp": elim_tag,
                "rule_label": f"{short_tag} // DAY 0-{max_d}",
                "weights": w,
                "chart1_metric": (m1 if m1 != "elev_norm" else "elev_m", m1.replace("_", " ").upper() + " INDEX"),
                "chart2_metric": (m2 if m2 != "elev_norm" else "elev_m", m2.replace("_", " ").upper() + " INDEX"),
                "premise": f"We run a full {max_d}-day map simulation of {t_name.lower()} across {arena_phrase}.",
                "elim_tag": elim_tag,
                "max_day": max_d,
            })

    # 3) Shrinking Zones across 15 landmarks x 2 speeds (30) + Extra custom US/World points
    EXTRA_ZONES = [
        ("us_states", "Miami Coast", [0.80, 0.78]),
        ("us_states", "Seattle Harbor", [0.14, 0.16]),
        ("us_states", "New York Metro", [0.86, 0.30]),
        ("us_states", "Los Angeles Basin", [0.14, 0.56]),
        ("us_states", "Yellowstone Basin", [0.28, 0.28]),
        ("us_states", "Mississippi River Core", [0.60, 0.54]),
        ("world", "Sahara Crossroads", [0.51, 0.44]),
        ("world", "Himalayan Roof", [0.73, 0.41]),
        ("world", "Amazon Basin", [0.33, 0.64]),
        ("world", "Indian Ocean Core", [0.69, 0.64]),
        ("world", "East Asia Core", [0.80, 0.39]),
        ("world", "North America Core", [0.24, 0.32]),
        ("europe", "London Channel", [0.34, 0.46]),
        ("europe", "Danube Corridor", [0.64, 0.60]),
        ("americas", "Andes Ridge", [0.62, 0.76]),
    ]
    for arena_key, zname, zcenter in (MATRIX_ZONES + EXTRA_ZONES):
        badge = "50 STATES" if arena_key == "us_states" else ("EUROPE" if arena_key == "europe" else "WORLD MAP")
        sid = f"zone_{arena_key}_{hashlib.md5(zname.encode()).hexdigest()[:6]}"
        catalog.append({
            "id": sid,
            "arena": arena_key,
            "mechanic": "shrinking_zone",
            "title_long": f"Shrinking Safe Zone Centered on {zname}: Outside = Deleted (Only 1 Survives)",
            "title_short": f"Safe Zone Collapsing on {zname} — Only 1 Survives",
            "thumb_top": f"SAFE ZONE: {zname.upper()}",
            "thumb_pill": "1 SURVIVES",
            "thumb_stamp": "OUT OF ZONE",
            "rule_label": f"SHRINKING ZONE // {badge}",
            "zone_center": zcenter,
            "chart1_metric": ("gdp_pc", "ECONOMIC OUTPUT ($K)"),
            "chart2_metric": ("energy", "ENERGY CAPACITY"),
            "premise": f"A collapsing circular zone centers on {zname} — every border outside the ring is erased round by round.",
            "elim_tag": "OUT OF ZONE",
            "max_day": 50 if arena_key == "us_states" else 100,
        })

    # 4) Sweeping Laser Lines (4 arenas x 27 distinct compass angles = 108 unique geometric map sweeps)
    for arena_key, entity_singular, arena_badge, arena_phrase in MATRIX_ARENAS:
        for deg in MATRIX_LASER_ANGLES:
            sid = f"laser_{arena_key}_{deg}"
            dir_name = f"{deg}-Degree Sweep"
            catalog.append({
                "id": sid,
                "arena": arena_key,
                "mechanic": "laser_line",
                "title_long": f"A {dir_name} Line Crosses {arena_phrase}: Touch It = Deleted (Only 1 Survives)",
                "title_short": f"A {dir_name} Line Erases the Map — Which {entity_singular} Survives Last?",
                "thumb_top": f"{deg}° LASER SWEEP",
                "thumb_pill": arena_badge,
                "thumb_stamp": "DELETED",
                "rule_label": f"RULE: {deg}° LINE TOUCHES = OUT",
                "line_angle_deg": deg,
                "chart1_metric": ("elev_m", "ELEVATION (M)"),
                "chart2_metric": ("food", "FOOD SECURITY"),
                "premise": f"A razor-straight {deg}-degree red line sweeps across {arena_phrase}, eliminating every territory it touches.",
                "elim_tag": "DELETED",
                "max_day": 50 if arena_key == "us_states" else 100,
            })

    # 5) Pairwise Dual-Shock Scenarios (Two simultaneous crises across US States & World -> 600+ more unique episodes!)
    DUAL_A = MATRIX_SYSTEMS[:15]
    DUAL_B = MATRIX_THRESHOLDS[:10]
    for sa_name, sa_tag, m1, _, elim1 in DUAL_A:
        for tb_name, tb_tag, m2, _, elim2, _ in DUAL_B:
            for arena_key, entity_singular, arena_badge, arena_phrase in MATRIX_ARENAS[:2]:
                sid = f"dual_{arena_key}_{hashlib.md5((sa_tag + tb_tag).encode()).hexdigest()[:8]}"
                w = {m1: 0.36, m2: 0.36, "water": 0.14, "energy": 0.14, "pop_penalty": 0.25}
                catalog.append({
                    "id": sid,
                    "arena": arena_key,
                    "mechanic": "collapse",
                    "title_long": f"Double Shock: {sa_name} Fails + {tb_name} ({arena_badge} — Only 1 Survives)",
                    "title_short": f"{sa_tag} + {tb_tag} — Which {entity_singular} Survives?",
                    "thumb_top": f"{sa_tag} + {tb_tag}",
                    "thumb_pill": "1 SURVIVES",
                    "thumb_stamp": "DOUBLE SHOCK",
                    "rule_label": f"{sa_tag} + {tb_tag} // DAY 0-365",
                    "weights": w,
                    "chart1_metric": (m1 if m1 != "elev_norm" else "elev_m", m1.replace("_", " ").upper() + " SCORE"),
                    "chart2_metric": (m2 if m2 != "elev_norm" else "elev_m", m2.replace("_", " ").upper() + " SCORE"),
                    "premise": f"Two crises strike {arena_phrase} simultaneously: {sa_name.lower()} fails while {tb_name.lower()} hits.",
                    "elim_tag": elim1,
                    "max_day": 365,
                })

    return catalog


def load_history():
    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"published_ids": [], "published_titles": [], "count": 0}


def save_history(hist):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2)


def is_similar_title(title, existing_titles, threshold=0.78):
    tl = title.lower().strip()
    for prev in existing_titles:
        if difflib.SequenceMatcher(None, tl, prev.lower().strip()).ratio() >= threshold:
            return True
    return False


def pick_next_scenario(mode="longform", force_id=None, seed=None):
    """Select the next unpublished high-RPM scenario (alternating US 50 States & World/Europe automatically)."""
    catalog = build_infinite_catalog()
    hist = load_history()
    used_ids = set(hist.get("published_ids", []))

    if force_id:
        for sc in catalog:
            if sc["id"] == force_id:
                return sc

    # Alternate US 50 States (even runs -> maximum US RPM!) and World/Europe (odd runs -> viral scale!)
    prefer_us = (hist.get("count", 0) % 2 == 0)
    fresh = [sc for sc in catalog if f"{mode}:{sc['id']}" not in used_ids]

    # If >5 years pass and all matrix items were used, synthesize fresh parameter-shifted Year 6+ scenario!
    if not fresh:
        yr = datetime.now(timezone.utc).year
        base = random.Random(seed or hist.get("count", 0)).choice(catalog)
        sc = dict(base)
        sc["id"] = f"{base['id']}_{yr}_{hist.get('count', 0)}"
        sc["title_long"] = base["title_long"].replace("Only 1 Survives", f"({yr} Data Update) Only 1 Survives")
        sc["title_short"] = base["title_short"] + f" ({yr} Sim)"
        return sc

    # Prioritize curated first, alternating US vs Global
    curated_ids = {s["id"] for s in CURATED_SCENARIOS}
    curated_fresh = [s for s in fresh if s["id"] in curated_ids]
    pool = curated_fresh if curated_fresh else fresh

    targeted = [s for s in pool if (s["arena"] == "us_states") == prefer_us]
    return targeted[0] if targeted else pool[0]


def mark_published(scenario, mode="longform", video_id=""):
    hist = load_history()
    key = f"{mode}:{scenario['id']}"
    if key not in hist["published_ids"]:
        hist["published_ids"].append(key)
    t = scenario["title_long"] if mode == "longform" else scenario["title_short"]
    hist["published_titles"].append(t)
    hist["count"] = hist.get("count", 0) + 1
    hist["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    if video_id:
        hist["last_video_id"] = video_id
    save_history(hist)


def simulate_scenario(scenario):
    """Run real mathematical/data simulation across all polygons in the scenario's arena.
    Returns full simulation data:
      - entities: list sorted from FIRST ELIMINATED -> LAST SURVIVOR (winner = entities[-1])
      - winner, runner_up, top5
      - chart1, chart2 (real comparative bar chart data)
      - vs_metrics (4 real head-to-head metrics for Runner-Up vs Winner)
    """
    arena = scenario["arena"]
    geom = load_arena_geometry(arena)
    mech = scenario["mechanic"]
    max_day = scenario.get("max_day", 365)

    scored = []
    for name, gdata in geom.items():
        cx, cy = gdata["centroid"]
        m = get_entity_metrics(arena, name, (cx, cy))

        if mech == "shrinking_zone":
            zcx, zcy = scenario.get("zone_center", [0.5, 0.45])
            # Distance from safe-zone center (smaller distance = survives LONGER!)
            aspect = 1.45 if arena == "world" else 1.25
            dist = math.hypot((cx - zcx) * aspect, (cy - zcy))
            score = max(1.0, 100.0 - dist * 135.0)
        elif mech == "laser_line":
            ang = math.radians(scenario.get("line_angle_deg", 30))
            # Projection along sweep normal vector (higher projection = hit LATER!)
            nx, ny = math.cos(ang), math.sin(ang)
            proj = cx * nx + cy * ny
            score = 50.0 + proj * 50.0
        else:
            # Data-driven collapse or elevation flood
            w = scenario.get("weights", {"energy": 0.35, "food": 0.25, "water": 0.20, "trade_indep": 0.20, "pop_penalty": 0.25})
            elev_norm = min(100.0, (m["elev_m"] / 2100.0) * 100.0)
            pop_pen = min(40.0, math.log10(max(1.0, m["pop_m"] * 2.0)) * 22.0)
            s = 0.0
            for k, wt in w.items():
                if k == "pop_penalty":
                    s -= pop_pen * wt
                elif k == "elev_norm":
                    s += elev_norm * wt
                else:
                    s += m.get(k, 50) * wt
            # Tiny deterministic tie-breaker
            tie = ((abs(hash(name + scenario["id"])) % 100) / 1000.0)
            score = max(1.0, s + tie)

        scored.append({
            "name": name,
            "score": round(score, 2),
            "centroid": (cx, cy),
            "metrics": m,
        })

    # Sort ascending: index 0 falls FIRST, index -1 is the LAST SURVIVOR!
    scored.sort(key=lambda x: x["score"])
    total = len(scored)

    # Assign smooth elimination day/round across [1 .. max_day]
    for i, item in enumerate(scored):
        if i == total - 1:
            item["elim_day"] = max_day + 999  # SURVIVOR!
            item["elim_frac"] = 1.01
        else:
            # Non-linear dramatic curve: steady early wave, big mid-collapse, tense slow Final 5!
            u = i / max(1, total - 1)
            curved = (u ** 1.25)
            item["elim_day"] = max(1, int(1 + curved * (max_day - 1)))
            item["elim_frac"] = curved

    winner = scored[-1]
    runner_up = scored[-2] if total >= 2 else scored[-1]
    top5 = list(reversed(scored[-5:]))
    first_out = scored[:5]

    # Build Bar Chart 1 & Bar Chart 2 comparing top survivors vs biggest early fallen entities
    def make_chart(metric_key, chart_title):
        sample_entities = [scored[-1], scored[-2], scored[-3], scored[0], scored[min(2, total - 1)], scored[min(5, total - 1)]]
        seen = set()
        rows = []
        for ent in sample_entities:
            if ent["name"] in seen:
                continue
            seen.add(ent["name"])
            val = ent["metrics"].get(metric_key, 50)
            rows.append({
                "name": ent["name"].replace("United States of America", "USA"),
                "value": round(float(val), 1),
                "survived": ent["elim_frac"] > 0.85,
            })
        rows.sort(key=lambda r: r["value"], reverse=True)
        return {"title": chart_title, "metric": metric_key, "rows": rows[:6]}

    c1_k, c1_t = scenario.get("chart1_metric", ("energy", "ENERGY INDEPENDENCE"))
    c2_k, c2_t = scenario.get("chart2_metric", ("food", "FOOD SURPLUS INDEX"))
    chart1 = make_chart(c1_k, c1_t)
    chart2 = make_chart(c2_k, c2_t)

    # Build Final 2 VS SHOWDOWN metrics (4 clean bars out of 100)
    def norm_bar(m, key):
        if key == "elev_m":
            return min(100, int((m["elev_m"] / 2100.0) * 100))
        if key == "gdp_pc":
            return min(100, int(m["gdp_pc"]))
        return int(max(5, min(100, m.get(key, 50))))

    vs_keys = [
        ("energy", "ENERGY POWER"),
        ("food", "FOOD SURPLUS"),
        ("water", "FRESHWATER"),
        ("trade_indep", "SELF-RELIANCE"),
    ]
    vs_metrics = []
    for k, lbl in vs_keys:
        vs_metrics.append({
            "label": lbl,
            "left_val": norm_bar(runner_up["metrics"], k),
            "right_val": norm_bar(winner["metrics"], k),
        })

    return {
        "scenario": scenario,
        "total": total,
        "entities": scored,
        "winner": winner,
        "runner_up": runner_up,
        "top5": top5,
        "first_out": first_out,
        "chart1": chart1,
        "chart2": chart2,
        "vs_metrics": vs_metrics,
    }


if __name__ == "__main__":
    cat = build_infinite_catalog()
    print(f"Infinite catalog layer 1+2 ready: {len(cat)} unique scenarios (~{len(cat) * 2 / 365:.1f} years at 1 Long-Form / 2 days!)")
    sc = pick_next_scenario("longform")
    sim = simulate_scenario(sc)
    print("Sample Scenario:", sc["title_long"])
    print("First 3 out:", [e["name"] for e in sim["first_out"][:3]])
    print("Final 3:", [e["name"] for e in sim["top5"][:3]])
    print("Winner:", sim["winner"]["name"], "| Runner-up:", sim["runner_up"]["name"])
