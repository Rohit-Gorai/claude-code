"""How shareable is a story on Instagram? A keyword-based hint for ranking candidates.

`score` in fetch.py measures how *big* a story is (outlets covering it, freshness). This module
adds `viral`: how often stories on that topic get sent, saved and swiped on Instagram, following
the research in VIRALITY.md:
  - useful "your money" news, awe (records, firsts, space), pride and famous names get shared;
  - high-arousal anger (scams, overcharging) and anxiety people can act on (alerts) spread too;
  - numbers make a story saveable and feed the "Today in numbers" slide;
  - sad, low-arousal news (deaths, obituaries) spreads least (Berger & Milkman 2012);
  - political posts are not recommended to non-followers at all.
It is a hint, not a verdict: the editor still reads every candidate and decides.
"""

from __future__ import annotations

import re

# tag → (weight, pattern). Each tag counts once per story.
SIGNALS: dict[str, tuple[float, str]] = {
    "money": (1.2, r"prices?|cost(?:s|lier)?|cheaper|hike[sd]?|repo|rbi|emis?|loans?|tax(?:es)?|gst|itr|salar(?:y|ies)|"
                   r"pensions?|epfo?|petrol|diesel|lpg|cng|fuel|gold|silver|sensex|nifty|ipo|upi|banks?|fares?|tickets?|"
                   r"refunds?|deadline|new rules?|rules? change|jobs?|hiring|layoffs?|recruitment|exams?|admit card|"
                   r"(?:exam|board|cbse|neet|jee|upsc) results?|scholarships?|iphone|smartphones?|sale|discounts?|budget|inflation|rupee|tariffs?|fees?"),
    "wow": (1.0, r"records?|all-time|first[- ]ever|for the first time|historic|world'?s (?:largest|biggest|first|fastest|tallest|oldest)|"
                 r"breakthrough|discover(?:s|ed|y)|scientists?|space|isro|nasa|spacex|rocket|moon|mars|satellites?|telescope|"
                 r"robots?|fossils?|species|galaxy|asteroid"),
    "pride": (0.8, r"wins?|won|beat|beats|medals?|gold medal|champions?|championship|title|trophy|century|hat-trick|"
                   r"world cup|olympics?|qualif(?:y|ies|ied)|india'?s first|clinch(?:es|ed)?"),
    "stars": (0.6, r"bollywood|box office|films?|movies?|trailer|actor|actress|singer|netflix|ott|celebrit(?:y|ies)|"
                   r"kohli|dhoni|rohit sharma|bumrah|neeraj chopra|shah rukh|salman|deepika|alia|ranbir|taylor swift|musk|ambani|adani"),
    "surprise": (0.6, r"bizarre|weird|unusual|rare|unexpected|surpris(?:e|es|ing)|stuns?|mystery|shock(?:s|ed|ing)?"),
    "outrage": (0.4, r"scams?|fraud|fined|penalt(?:y|ies)|overcharg\w*|banned|cheat(?:ing|ed)?|backlash|outrage"),
    "alert": (0.3, r"alerts?|warning|heatwave|cyclone|floods?|outbreak|virus|recall(?:s|ed)?|advisory"),
    "political": (-1.2, r"bjp|congress|aap|tmc|dmk|aiadmk|shiv sena|ncp|rjd|jd\(u\)|bsp|elections?|polls?|bypolls?|assembly|"
                        r"lok sabha|rajya sabha|parliament|mps?|mlas?|ministers?|chief minister|modi|rahul gandhi|kejriwal|"
                        r"opposition|campaign|manifesto|rally|protests?|trump|white house|kremlin|senate"),
    "grim": (-0.8, r"dies|died|dead|deaths?|killed|kills|funeral|mourns?|tragedy|tragic|passes away|passed away|"
                   r"condolences?|suicide|murder(?:ed)?|body found|obituary"),
}
_COMPILED = {tag: (w, re.compile(rf"\b(?:{pat})\b", re.I)) for tag, (w, pat) in SIGNALS.items()}
_NUMBER = re.compile(r"₹\s?\d|\$\s?\d|\b\d[\d,.]*\s?(?:%|per ?cent|crore|cr|lakh|billion|bn|million|mn|trillion|bps|basis points)(?!\w)", re.I)
NUMBERS_WEIGHT = 0.4


def signals(text: str) -> tuple[float, list[str]]:
    """Return (viral score, flags) for a story's text (title + other titles + summary)."""
    score, flags = 0.0, []
    for tag, (weight, rx) in _COMPILED.items():
        if rx.search(text):
            score += weight
            flags.append(tag)
    if _NUMBER.search(text):
        score += NUMBERS_WEIGHT
        flags.append("numbers")
    return round(max(-2.0, min(3.0, score)), 2), flags


def story_text(title: str, other_titles: list[str], summary: str) -> str:
    return " ".join([title, *other_titles[:4], summary[:400]])
