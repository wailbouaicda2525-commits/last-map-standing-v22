"""
scriptwriter_v22.py — 5-Tier Resilient Scriptwriter for Last Map Standing (Long-Form 10-14m + Shorts 45-55s).
Fallback Chain (Zero Single Point of Failure for 5+ Years):
  1. Groq: qwen/qwen3.8-27b
  2. Groq: openai/gpt-oss-120b
  3. Groq: llama-3.3-70b-versatile
  4. Gemini: gemini-2.5-flash
  5. Deterministic High-Craft Data-Documentary Generator (100% offline-proof!)
"""
import json
import os
import re
import urllib.request


def _clean_narration(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\*\*|\*|#+\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _call_groq(prompt, model, max_tokens=3200):
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an elite YouTube documentary scriptwriter in the style of Wendover Productions and RealLifeLore. Output ONLY clean spoken narration text — zero stage directions, zero markdown, zero brackets, zero timestamps."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.72,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "LastMapStandingV22/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    txt = data["choices"][0]["message"]["content"]
    return _clean_narration(txt)


def _call_gemini(prompt):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.72, "maxOutputTokens": 3200},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    txt = data["candidates"][0]["content"]["parts"][0]["text"]
    return _clean_narration(txt)


def _llm_generate(prompt, min_words=80, max_tokens=3200):
    groq_models = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
    ]
    for m in groq_models:
        try:
            out = _call_groq(prompt, m, max_tokens=max_tokens)
            if out and len(out.split()) >= min_words:
                print(f"  [SCRIPT OK] Groq {m} ({len(out.split())} words)")
                return out
        except Exception as e:
            print(f"  [GROQ FALLBACK {m}] {e}")
    try:
        out = _call_gemini(prompt)
        if out and len(out.split()) >= min_words:
            print(f"  [SCRIPT OK] Gemini 2.5 Flash ({len(out.split())} words)")
            return out
    except Exception as e:
        print(f"  [GEMINI FALLBACK] {e}")
    return None


def _offline_short_script(sim):
    sc = sim["scenario"]
    total = sim["total"]
    f1 = sim["first_out"][0]["name"].replace("United States of America", "the United States")
    f2 = sim["first_out"][1]["name"].replace("United States of America", "the United States")
    f3 = sim["first_out"][2]["name"].replace("United States of America", "the United States")
    mid_idx = total // 2
    mid_name = sim["entities"][mid_idx]["name"].replace("United States of America", "the United States")
    ru = sim["runner_up"]["name"].replace("United States of America", "the United States")
    win = sim["winner"]["name"].replace("United States of America", "the United States")
    win_m = sim["winner"]["metrics"]
    unit = "states" if sc["arena"] == "us_states" else "countries"
    max_d = sc["max_day"]

    return (
        f"{sc['premise']} Out of {total} {unit}, only one can survive to Day {max_d}. "
        f"Almost immediately, the most vulnerable territories collapse first: {f1}, {f2}, and {f3} are eliminated before the first wave even ends. "
        f"By the halfway mark, more than half the map has gone completely dark, dragging down major economies like {mid_name}. "
        f"Only the most resilient regions remain standing as the countdown tightens toward the final two: {ru} versus {win}. "
        f"In the final stretch, {ru} runs into severe resource bottlenecks while {win} holds an energy score of {win_m['energy']} and a food index of {win_m['food']}. "
        f"At Day {max_d}, only one remains on the map: {win}. Would your home survive this simulation?"
    )


def _offline_longform_acts(sim):
    """High-craft deterministic 6-act documentary script (~1,500 words = ~10 minutes) — 100% offline-proof."""
    sc = sim["scenario"]
    total = sim["total"]
    unit = "U.S. states" if sc["arena"] == "us_states" else "nations"
    unit_s = "state" if sc["arena"] == "us_states" else "country"
    ents = sim["entities"]
    w1 = [e["name"].replace("United States of America", "the United States") for e in ents[:6]]
    w2 = [e["name"].replace("United States of America", "the United States") for e in ents[total // 4 : total // 4 + 6]]
    w3 = [e["name"].replace("United States of America", "the United States") for e in ents[total // 2 : total // 2 + 6]]
    top5 = [e["name"].replace("United States of America", "the United States") for e in sim["top5"]]
    ru = sim["runner_up"]
    win = sim["winner"]
    ru_n = ru["name"].replace("United States of America", "the United States")
    win_n = win["name"].replace("United States of America", "the United States")
    c1 = sim["chart1"]
    c2 = sim["chart2"]
    max_d = sc["max_day"]

    acts = [
        {
            "act_id": 0,
            "label": "ACT I — THE SIMULATION BEGINS",
            "scene_type": "map",
            "text": (
                f"Right now, all {total} {unit} sit connected inside an invisible web of energy grids, supply chains, food corridors, and financial flows. "
                f"Now imagine pulling the plug on that balance all at once. {sc['premise']} "
                f"Starting at Day Zero and running all the way to Day {max_d}, we modeled every single {unit_s} using real public data on domestic energy, food output, freshwater reserves, population pressure, and geography. "
                f"Every time a territory crosses its breaking point, it turns dark and disappears from the board. Watch the leaderboard on the right carefully, because some of the wealthiest places on the map are about to fall faster than anyone expects. "
                f"Only one {unit_s} can remain standing at the end. Let us start the clock."
            ),
        },
        {
            "act_id": 1,
            "label": "ACT II — FIRST WAVE COLLAPSE",
            "scene_type": "map",
            "text": (
                f"The first shock hits almost immediately. On paper, dense urban centers look unstoppable because they command massive financial output and global trade hubs. "
                f"Yet in a survival simulation, extreme population density becomes a mathematical liability within hours. "
                f"The earliest eliminations strike {w1[0]}, {w1[1]}, and {w1[2]}. Without constant external replenishment, local inventories deplete rapidly and reserve margins drop below critical thresholds. "
                f"Right behind them, {w1[3]}, {w1[4]}, and {w1[5]} cross the red line and drop off the map. "
                f"Look at the pattern spreading across the map: geography punishes territories that rely heavily on distant producers. "
                f"What takes decades to build in modern infrastructure can unravel in just a handful of days once redundancy disappears. "
                f"Already, more than a quarter of our starting {total} {unit} have gone completely offline."
            ),
        },
        {
            "act_id": 2,
            "label": f"ACT III — DATA BREAKDOWN: {c1['title']}",
            "scene_type": "chart1",
            "text": (
                f"To understand why the collapse is accelerating so unevenly, pause the map and look directly at the numbers behind {c1['title'].lower()}. "
                f"At the very top of our chart, {c1['rows'][0]['name']} posts a massive score of {c1['rows'][0]['value']}, closely followed by {c1['rows'][1]['name']} at {c1['rows'][1]['value']} and {c1['rows'][2]['name']} at {c1['rows'][2]['value']}. "
                f"Now drop your eyes to the bottom of the exact same chart. Early casualties like {c1['rows'][-1]['name']} sit all the way down at {c1['rows'][-1]['value']}. "
                f"That gap is not a minor statistical detail — it is the entire difference between lasting a week and lasting an entire year. "
                f"When reserves are thin, every single day multiplies the strain on distribution systems, transport corridors, and essential utilities. "
                f"With the data locked in, let us jump back to the live map as the second major wave sweeps through."
            ),
        },
        {
            "act_id": 3,
            "label": "ACT IV — THE HALFWAY TIPPING POINT",
            "scene_type": "map_and_chart2",
            "text": (
                f"By the midpoint of the simulation, the easy cushions are gone. Second-wave pressure overtakes {w2[0]}, {w2[1]}, and {w2[2]}, turning huge stretches of territory dark charcoal. "
                f"Even medium-sized powerhouses such as {w2[3]}, {w2[4]}, and {w2[5]} begin flashing warning ochre as their backup capacity shrinks week after week. "
                f"Soon after, the third collapse sweeps across {w3[0]}, {w3[1]}, and {w3[2]}, wiping out the middle tier of the board. "
                f"Look closely at our second major indicator: {c2['title'].lower()}. "
                f"Here again, leaders like {c2['rows'][0]['name']} at {c2['rows'][0]['value']} and {c2['rows'][1]['name']} at {c2['rows'][1]['value']} separate cleanly from the pack. "
                f"Whenever a territory carries tens of millions of residents without matching domestic output, the math eventually catches up. "
                f"Three quarters of the entire map is now eliminated, leaving only the toughest geographic fortresses still in Prussian blue."
            ),
        },
        {
            "act_id": 4,
            "label": "ACT V — THE FINAL FIVE STANDING",
            "scene_type": "map",
            "text": (
                f"We have officially entered the endgame. Out of {total} starting {unit}, only five remain standing on the board: "
                f"{top5[4]}, {top5[3]}, {top5[2]}, {top5[1]}, and {top5[0]}. "
                f"Every single one of these five survivors earned its place through rare geographic fortune: abundant local energy, strong domestic agricultural surplus, reliable freshwater basins, and manageable demand. "
                f"Yet as the clock pushes into the final quarter toward Day {max_d}, even elite contenders start to fracture under sustained stress. "
                f"First, {top5[4]} drops out as seasonal swings erode its buffer. Weeks later, {top5[3]} and {top5[2]} hit their structural limits and turn dark. "
                f"Across the entire map, forty-eight or more territories have vanished into silence — leaving only two giants standing head to head: {ru_n} versus {win_n}."
            ),
        },
        {
            "act_id": 5,
            "label": f"ACT VI — FINAL VS SHOWDOWN: {ru_n.upper()} VS {win_n.upper()}",
            "scene_type": "vs_and_winner",
            "text": (
                f"This is the ultimate head-to-head showdown: {ru_n} against {win_n}. "
                f"Let us stack them side by side across all four survival pillars. "
                f"In domestic energy capacity, {ru_n} scores {ru['metrics']['energy']} while {win_n} stands at {win['metrics']['energy']}. "
                f"In food surplus per capita, {ru_n} registers {ru['metrics']['food']} compared to {win_n} at {win['metrics']['food']}. "
                f"In freshwater security, {ru_n} holds {ru['metrics']['water']} while {win_n} commands {win['metrics']['water']}. "
                f"And in overall self-reliance with zero outside help, {ru_n} reaches {ru['metrics']['trade_indep']} against {win_n} at {win['metrics']['trade_indep']}. "
                f"In the final stretch before Day {max_d}, {ru_n} finally bends under cumulative pressure, leaving only one territory left standing across the entire atlas: {win_n}. "
                f"With balanced domestic energy, deep food reserves, and geographic resilience, {win_n} claims the title of Last Map Standing. "
                f"Tell us in the comments where you live, whether it survived this simulation, and which scenario we should run next."
            ),
        },
    ]
    return acts


NARRATIVE_STYLES = [
    (
        "cold_open_fact",
        "Open with a surprising real-world infrastructure or geography fact that makes viewers rethink how fragile modern supply chains are, then smoothly launch the simulation.",
        "Ask viewers which territory surprised them most in the data.",
    ),
    (
        "day_one_dispatch",
        "Open inside the very first 24 hours of the scenario like a calm, gripping logistics analyst tracking cascading failures on a live operations map.",
        "Ask viewers how many days they think their own hometown would last.",
    ),
    (
        "counterintuitive_twist",
        "Open by immediately challenging conventional wisdom — point out that the largest or wealthiest economies are often the first to break under this specific stress test.",
        "Ask viewers whether they agree with the winner or think the runner-up had the stronger real-world edge.",
    ),
    (
        "geographic_paradox",
        "Open by framing the hidden geographic paradox at the heart of the map — why coastlines, elevation, aquifers, or local power grids decide everything before politics ever matters.",
        "Ask viewers what stress test scenario they want mapped next.",
    ),
]


def _pick_narrative_style(scenario):
    sid = scenario.get("id", "lms")
    h = sum(ord(c) * (i + 3) for i, c in enumerate(sid))
    return NARRATIVE_STYLES[h % len(NARRATIVE_STYLES)]


def generate_short_script(sim):
    sc = sim["scenario"]
    f3 = ", ".join(e["name"].replace("United States of America", "USA") for e in sim["first_out"][:3])
    top3 = ", ".join(e["name"].replace("United States of America", "USA") for e in sim["top5"][:3])
    win = sim["winner"]["name"].replace("United States of America", "USA")
    ru = sim["runner_up"]["name"].replace("United States of America", "USA")
    style_name, opening_dir, closing_dir = _pick_narrative_style(sc)

    prompt = (
        f"Write a gripping 115-to-135-word YouTube Short voiceover script for a data map simulation channel named 'Last Map Standing'.\n"
        f"Title: {sc['title_short']}\n"
        f"Premise: {sc['premise']}\n"
        f"Total regions: {sim['total']} | Timeline: Day 0 to Day {sc['max_day']}\n"
        f"First 3 eliminated: {f3}\n"
        f"Final 3 standing: {top3}\n"
        f"Runner-up (falls right at the end): {ru}\n"
        f"Last Survivor (Winner): {win}\n"
        f"Narrative Style ({style_name}): {opening_dir}\n"
        f"Closing Question: {closing_dir}\n"
        f"Rules: 100% factual adult tone (Wendover / RealLifeLore style), zero wars/violence/politics, punchy short sentences, "
        f"cover early drop-offs, halfway collapse, final two ({ru} vs {win}), and reveal {win} as the lone survivor. "
        f"Plain spoken words ONLY."
    )
    txt = _llm_generate(prompt, min_words=85, max_tokens=450)
    return txt if txt else _offline_short_script(sim)


def compute_adaptive_minutes(sim):
    """Pick a natural, topic-matched documentary duration (9–18 min) so every episode fits its exact depth."""
    sc = sim["scenario"]
    arena = sc.get("arena", "us_states")
    mech = sc.get("mechanic", "collapse")
    total_ents = len(sim["entities"])

    # Base natural runtime by geographical scale & analytical complexity
    if arena == "world" or total_ents >= 120:
        base = 14.5
    elif arena == "us_states":
        base = 12.0
    else:
        base = 10.5

    # Compound / dual-shock or long-horizon crises naturally deserve deeper analysis; fast visual mechanics run tighter
    if "dual_" in sc.get("id", "") or sc.get("max_day", 365) >= 730:
        base += 2.0
    elif mech in ("laser_line", "shrinking_zone"):
        base -= 1.2

    # Deterministic per-scenario natural variance (-1.0 to +1.5 min) so no two episodes have identical robotic length
    h = sum(ord(c) * (i + 1) for i, c in enumerate(sc.get("id", "lms")))
    jitter = ((h % 11) - 4) * 0.25  # -1.0 .. +1.5 min
    return round(max(9.0, min(18.0, base + jitter)), 1)


def generate_longform_acts(sim, target_minutes=None):
    """Generate 6 structured acts with adaptive natural duration (9–18 min) and varied documentary framing."""
    sc = sim["scenario"]
    if target_minutes is None:
        target_minutes = compute_adaptive_minutes(sim)
    offline = _offline_longform_acts(sim)
    if not (os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        return offline

    style_name, opening_dir, closing_dir = _pick_narrative_style(sc)
    acts = []
    words_per_act = int((target_minutes * 162) / len(offline))
    for base_act in offline:
        extra_dir = ""
        if base_act["act_id"] == 0:
            extra_dir = f"Opening Direction ({style_name}): {opening_dir}\n"
        elif base_act["act_id"] == len(offline) - 1:
            extra_dir = f"Closing Direction: {closing_dir}\n"

        prompt = (
            f"Rewrite and expand this documentary chapter into approximately {words_per_act} words of captivating, "
            f"intelligent narration in the style of RealLifeLore & Wendover Productions.\n"
            f"Episode: {sc['title_long']}\n"
            f"Chapter: {base_act['label']}\n"
            f"{extra_dir}"
            f"MANDATORY FACTS & NAMES TO KEEP ACCURATELY:\n{base_act['text']}\n\n"
            f"Rules: Keep ALL entity names, numbers, and outcome order 100% faithful. Explain real geographic, infrastructure, and economic causes vividly with fresh phrasing. "
            f"100% clean/halal, zero wars/politics/crime. Output plain spoken English prose ONLY (no headings, no bullets, no brackets)."
        )
        llm_txt = _llm_generate(prompt, min_words=max(120, words_per_act - 85), max_tokens=1400)
        act_copy = dict(base_act)
        if llm_txt:
            act_copy["text"] = llm_txt
        acts.append(act_copy)
    return acts
