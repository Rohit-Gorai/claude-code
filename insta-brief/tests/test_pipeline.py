"""Offline tests: fake RSS feeds → clustering/ranking → basic edition → finalize.

Run:  python -m unittest discover -s tests
"""

import datetime as dt
import tempfile
import unittest
from email.utils import format_datetime
from pathlib import Path

from brief.config import load_config
from brief.editor import build_caption, edit_basic, finalize
from brief.fetch import cluster, fetch_all

NOW = dt.datetime.now(dt.timezone.utc)


def rss(title, items):
    body = ""
    for t, link, hours, extra in items:
        body += (
            f"<item><title>{t}</title><link>{link}</link>"
            f"<pubDate>{format_datetime(NOW - dt.timedelta(hours=hours))}</pubDate>{extra}</item>"
        )
    return (
        '<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">'
        f"<channel><title>{title}</title>{body}</channel></rss>"
    )


GOOGLE = rss("Top stories - Google News", [
    ("RBI cuts repo rate by 25 basis points to 5.25% - The Hindu", "https://news.google.com/rss/articles/a1", 2,
     '<source url="https://thehindu.com">The Hindu</source><description>&lt;ol&gt;&lt;li&gt;&lt;a href="x"&gt;RBI cuts repo rate, EMIs to fall&lt;/a&gt;&lt;font&gt;Mint&lt;/font&gt;&lt;/li&gt;&lt;li&gt;&lt;a href="y"&gt;Repo rate cut explained&lt;/a&gt;&lt;font&gt;NDTV&lt;/font&gt;&lt;/li&gt;&lt;/ol&gt;</description>'),
    ("India beat Australia by 6 wickets in series decider - ESPNcricinfo", "https://news.google.com/rss/articles/a2", 5,
     '<source url="https://espncricinfo.com">ESPNcricinfo</source>'),
    ("Daily horoscope for today - Astro Site", "https://news.google.com/rss/articles/a3", 1, '<source url="https://x.com">Astro Site</source>'),
    ("Old story from last week - Somewhere", "https://news.google.com/rss/articles/a4", 200, '<source url="https://x.com">Somewhere</source>'),
])
PUBLISHER = rss("Mint - Latest News", [
    ("RBI cuts repo rate by 25 bps, home loan EMIs set to fall", "https://www.livemint.com/rbi-cut", 3,
     '<description>The Reserve Bank of India cut its key lending rate by 25 basis points on Friday, the second cut this year.</description>'
     '<media:content url="https://img.example.com/rbi.jpg" medium="image"/>'),
    ("Apple launches new iPhone with bigger battery in India", "https://www.livemint.com/iphone", 4,
     "<description>The new phone goes on sale next week.</description>"),
])
SPORTS = rss("ESPNcricinfo", [
    ("India beat Australia by six wickets to clinch series", "https://www.espncricinfo.com/story/1", 6, "<description>A late charge sealed the chase.</description>"),
])


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        feeds = []
        for name, xml, cat, top in (("g", GOOGLE, "TOP", True), ("m", PUBLISHER, "MONEY", False), ("s", SPORTS, "SPORTS", False)):
            path = cls.tmp / f"{name}.xml"
            path.write_text(xml, encoding="utf-8")
            feeds.append({"url": str(path), "category": cat, "top": top})
        cls.items = fetch_all(feeds, max_age_hours=26, now=NOW, log=lambda m: None)
        cls.candidates = cluster(cls.items, now=NOW)
        cls.cfg = load_config()
        cls.cfg["format"]["stories"] = 2

    def test_filters_stale_and_junk(self):
        titles = [i["title"] for i in self.items]
        self.assertFalse(any("horoscope" in t.lower() for t in titles))
        self.assertFalse(any("Old story" in t for t in titles))

    def test_google_suffix_and_related(self):
        rbi = next(i for i in self.items if "news.google" in i["link"] and "RBI" in i["title"])
        self.assertEqual(rbi["source"], "The Hindu")
        self.assertFalse(rbi["title"].endswith("The Hindu"))
        self.assertEqual(len(rbi["related"]), 2)

    def test_clusters_same_story_across_outlets(self):
        top = self.candidates[0]
        self.assertIn("RBI", top["title"])
        self.assertEqual(set(top["sources"]), {"The Hindu", "Mint"})
        self.assertEqual(top["category"], "MONEY")
        self.assertEqual(top["images"], ["https://img.example.com/rbi.jpg"])
        cricket = [c for c in self.candidates if "Australia" in c["title"]]
        self.assertEqual(len(cricket), 1, "both cricket headlines should merge into one story")

    def test_dates_do_not_merge_unrelated_stories(self):
        from brief.fetch import _similar, _tokens

        a = _tokens("KOW vs USRC Cricket Scorecard, 1st Match at Kowloon, September 27, 2026")
        b = _tokens("HT morning news brief September 27: EC says all SIR calls unanimous")
        c = _tokens("Asian Games 2026: India wins gold medal in men's kabaddi after beating Iran")
        self.assertFalse(_similar(a, b))
        self.assertFalse(_similar(a, c))
        self.assertNotIn("2026", c)
        self.assertIn("25", _tokens("RBI cuts repo rate by 25 bps"))  # real numbers still count

    def test_watermarked_share_cards_are_skipped(self):
        from brief.photos import usable_image_url

        self.assertFalse(usable_image_url("https://i.guim.co.uk/img/x.jpg?width=1200&overlay-base64=L2ltZy9"))
        self.assertTrue(usable_image_url("https://images.indianexpress.com/2026/09/lng-train.jpg"))

    def test_basic_edition_finalizes(self):
        raw = edit_basic(self.candidates, self.cfg, NOW.date())
        edition, warnings = finalize(raw, self.candidates, self.cfg)
        self.assertEqual(len(edition["stories"]), 2)
        s = edition["stories"][0]
        self.assertEqual(s["hl_before"] + s["hl_text"] + s["hl_after"], s["headline"])
        self.assertIn("1️⃣", edition["caption"])
        self.assertIn(self.cfg["brand"]["handle"], edition["caption"])

    def test_finalize_repairs_bad_highlight_and_ids(self):
        raw = {
            "cover": {"hook_accent": "Big day", "hook_rest": "for your wallet"},
            "stories": [
                {"candidate_id": self.candidates[0]["id"], "category": "money", "headline": "RBI Cuts Repo Rate",
                 "highlight": "not in headline", "summary": "x", "why_it_matters": "", "alt_text": "a"},
                {"candidate_id": "c99", "category": "x", "headline": "Ghost", "highlight": "Ghost",
                 "summary": "x", "why_it_matters": "", "alt_text": "a"},
            ],
            "quick_hits": [{"candidate_id": self.candidates[0]["id"], "text": "dup of a story"}],
            "caption_hook": "hi", "engagement_question": "?", "hashtags": ["news", "#india"],
        }
        edition, warnings = finalize(raw, self.candidates, self.cfg)
        self.assertEqual(len(edition["stories"]), 1)
        self.assertEqual(edition["stories"][0]["hl_text"], "RBI Cuts")
        self.assertEqual(edition["stories"][0]["category"], "MONEY")
        self.assertEqual(edition["quick_hits"], [])
        self.assertEqual(edition["hashtags"], ["#news", "#india"])
        self.assertTrue(any("c99" in w for w in warnings))
        self.assertTrue(build_caption(edition, self.cfg).endswith("#news #india\n"))

    def test_quick_hits_must_be_grounded_and_unique(self):
        real = self.candidates[1]["id"]
        raw = {"stories": [], "quick_hits": [
            {"candidate_id": "c99", "text": "Invented claim"},
            {"candidate_id": real, "text": "Real one."},
            {"candidate_id": real, "text": "Real one again"},
            {"text": "No id at all"},
        ]}
        edition, warnings = finalize(raw, self.candidates, self.cfg)
        self.assertEqual(edition["quick_hits"], [{"text": "Real one", "candidate_id": real}])
        self.assertTrue(any("c99" in w for w in warnings))
        self.assertTrue(any("None" in w for w in warnings))
        self.assertTrue(any("repeats" in w for w in warnings))

    def test_quick_hits_without_candidates_are_kept(self):
        edition, warnings = finalize({"stories": [], "quick_hits": [{"text": "Sample hit"}]}, [], self.cfg)
        self.assertEqual([h["text"] for h in edition["quick_hits"]], ["Sample hit"])

    def test_custom_credit_passes_through(self):
        cid = self.candidates[0]["id"]
        raw = {"stories": [{"candidate_id": cid, "category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI",
                            "summary": "x", "why_it_matters": "", "alt_text": "a", "credit": "Image: PIB"}]}
        edition, _ = finalize(raw, self.candidates, self.cfg)
        self.assertEqual(edition["stories"][0]["credit"], "Image: PIB")

    def test_empty_images_forces_typographic_card(self):
        cid = self.candidates[0]["id"]
        base = {"candidate_id": cid, "category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI",
                "summary": "x", "why_it_matters": "", "alt_text": "a"}
        with_photo, _ = finalize({"stories": [base]}, self.candidates, self.cfg)
        no_photo, _ = finalize({"stories": [{**base, "images": []}]}, self.candidates, self.cfg)
        self.assertEqual(with_photo["stories"][0]["images"], self.candidates[0]["images"])
        self.assertEqual(no_photo["stories"][0]["images"], [])

    def test_share_line_and_all_sources_in_caption(self):
        cid = self.candidates[0]["id"]
        story = {"candidate_id": cid, "category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI",
                 "summary": "x", "why_it_matters": "", "alt_text": "a", "sources": [f"Outlet {i}" for i in range(10)]}
        edition, _ = finalize({"stories": [story], "share_line": "Send this to the friend with a home loan"}, self.candidates, self.cfg)
        self.assertIn("✈️ Send this to the friend with a home loan", edition["caption"])
        self.assertIn("Outlet 9", edition["caption"])
        generic, _ = finalize({"stories": [story]}, self.candidates, self.cfg)
        self.assertIn("✈️ Send it to someone who needs to know", generic["caption"])

    def test_political_lead_warns(self):
        cid = self.candidates[0]["id"]
        story = {"candidate_id": cid, "category": "politics", "headline": "Party Wins Vote", "highlight": "Party",
                 "summary": "x", "why_it_matters": "", "alt_text": "a"}
        _, warnings = finalize({"stories": [story]}, self.candidates, self.cfg)
        self.assertTrue(any("non-followers" in w for w in warnings))

    def test_formula_checks(self):
        ids = [c["id"] for c in self.candidates[:2]]
        base = {"category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI", "summary": "x",
                "why_it_matters": "", "alt_text": "a"}
        raw = {"cover": {"hook_accent": "Today's top stories", "hook_rest": "in 60 seconds"},
               "stories": [{**base, "candidate_id": ids[0]}, {**base, "candidate_id": ids[1]}],
               "engagement_question": "What do you think about all of the things that happened in the news today?"}
        _, warnings = finalize(raw, self.candidates, self.cfg)
        text = " | ".join(warnings)
        for part in ("STOP: cover hook", "story #2 has no tease", "engagement question is", "no share_line"):
            self.assertIn(part, text)

        good = {"cover": {"hook_accent": "Your EMI", "hook_rest": "just got cheaper"},
                "stories": [{**base, "candidate_id": ids[0]}, {**base, "candidate_id": ids[1], "tease": "The record nobody expected."}],
                "engagement_question": "Rate cut: good news or too late?",
                "share_line": "Send this to the friend with a home loan"}
        edition, warnings = finalize(good, self.candidates, self.cfg)
        self.assertFalse([w for w in warnings if w.split(":")[0] in ("STOP", "SWIPE", "SHARE")])
        self.assertEqual(edition["stories"][1]["tease"], "The record nobody expected")

    def test_virality_signals(self):
        from brief.virality import signals

        money, flags = signals("Petrol prices cut by ₹2 a litre from tomorrow")
        self.assertGreater(money, 1)
        self.assertIn("money", flags)
        self.assertIn("numbers", flags)
        politics, flags = signals("BJP and Congress trade barbs ahead of assembly elections")
        self.assertLess(politics, 0)
        self.assertIn("political", flags)
        grim, flags = signals("Veteran actor dies at 84, industry mourns")
        self.assertIn("grim", flags)
        self.assertLess(grim, money)
        wow, flags = signals("ISRO spots water on the Moon for the first time")
        self.assertIn("wow", flags)

    def test_candidates_carry_virality(self):
        rbi = self.candidates[0]
        self.assertIn("money", rbi["flags"])
        self.assertIn("numbers", rbi["flags"])
        self.assertGreater(rbi["viral"], 0)
        for c in self.candidates:
            self.assertIn("viral", c)

    def test_bigger_photo_variants(self):
        from brief.photos import Photo, bigger_variants

        self.assertEqual(
            bigger_variants("https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Kohli.jpg/800px-Kohli.jpg")[0],
            "https://upload.wikimedia.org/wikipedia/commons/a/ab/Kohli.jpg",
        )
        self.assertEqual(bigger_variants("https://x.com/wp-content/uploads/2026/09/pic-1200x675.jpeg")[0],
                         "https://x.com/wp-content/uploads/2026/09/pic.jpeg")
        self.assertEqual(bigger_variants("https://img.x.com/a.jpg?w=640&sig=abc")[0], "https://img.x.com/a.jpg?sig=abc")
        self.assertEqual(bigger_variants("https://dims.x.com/r/?url=https%3A%2F%2Fa.x.com%2Fb.jpg")[0], "https://a.x.com/b.jpg")
        # the original URL is always tried last, so nothing is lost
        self.assertEqual(bigger_variants("https://img.x.com/a.jpg?w=640")[-1], "https://img.x.com/a.jpg?w=640")
        cover = (1080, 1440)
        self.assertLessEqual(Photo(b"", "", 2400, 3200, "JPEG").stretch(cover), 1.0)
        self.assertAlmostEqual(Photo(b"", "", 1200, 675, "JPEG").stretch(cover), 1440 / 675)

    def test_small_photos_are_enlarged(self):
        from PIL import Image

        from brief import photos

        img = Image.effect_noise((80, 60), 40).convert("RGB")
        plain, how = photos.enlarge(img, 1.5, ai=False)
        self.assertEqual((plain.size, how), ((120, 90), "sharpened"))
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            self.skipTest("onnxruntime not installed")
        up, how = photos.enlarge(img, 1.5, ai=True)
        self.assertEqual((up.size, how), ((120, 90), "ai"))

    def test_story_visuals_are_validated(self):
        from brief.editor import clean_visual
        from brief.maps import contains, inset_svg

        w = []
        self.assertEqual(clean_visual({"type": "trend", "label": "sensex", "value": "595 pts", "direction": "down"}, "c1", w),
                         {"type": "trend", "label": "SENSEX", "value": "595 pts", "direction": "down"})
        self.assertEqual(clean_visual({"type": "stamp", "label": "Most wanted"}, "c1", w), {"type": "stamp", "label": "MOST WANTED"})
        self.assertEqual(clean_visual({"type": "none"}, "c1", w), {})
        self.assertEqual(clean_visual({"type": "stamp", "label": "a very long stamp label"}, "c1", w), {})
        # a pin must fall inside the named country: Mumbai is in India, not in Pakistan
        self.assertTrue(contains("IND", 19.07, 72.88))
        self.assertTrue(contains("IND", 34.08, 74.80))  # Srinagar: India's official map includes all of J&K
        self.assertFalse(contains("PAK", 19.07, 72.88))
        self.assertEqual(clean_visual({"type": "place", "place": "Mumbai", "country": "PAK", "lat": 19.07, "lon": 72.88}, "c2", w), {})
        self.assertTrue(any("not inside country" in x for x in w))
        self.assertIn("<svg", inset_svg("IND", 19.07, 72.88))

    def test_stats_feed_the_numbers_slide(self):
        from brief.render import plan_slides

        ids = [c["id"] for c in self.candidates[:2]]
        base = {"category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI", "summary": "x",
                "why_it_matters": "", "alt_text": "a", "tease": "Why it matters"}
        raw = {"stories": [{**base, "candidate_id": ids[0], "stat": "25 bps", "stat_label": "repo rate cut", "emotion": "useful"},
                           {**base, "candidate_id": ids[1], "stat": "much too long a stat", "stat_label": "x", "emotion": "SAD"}],
               "quick_hits": [{"candidate_id": self.candidates[2]["id"], "text": "Hit"}]}
        edition, warnings = finalize(raw, self.candidates, self.cfg)
        self.assertEqual(edition["stories"][0]["stat"], "25 bps")
        self.assertEqual(edition["stories"][0]["emotion"], "USEFUL")
        self.assertEqual(edition["stories"][1]["stat"], "")
        text = " | ".join(warnings)
        self.assertIn("max 8", text)
        self.assertIn("SAVE: only 1 stories have a stat", text)
        self.assertIn("FEEL: no AWE / JOY / PRIDE story", text)
        kinds = [k for k, _, _ in plan_slides(edition)]
        self.assertEqual(kinds, ["cover", "story1", "story2", "quickhits"])

        for s in edition["stories"]:
            s["stat"] = "3x"
        edition["stories"].append({**edition["stories"][0], "rank": 3})
        kinds = [k for k, _, _ in plan_slides(edition)]
        self.assertEqual(kinds, ["cover", "story1", "story2", "story3", "numbers", "quickhits"])
        last_story = plan_slides(edition)[3][2]
        self.assertEqual(last_story["next_text"], "Today in numbers")

    def test_engagement_bait_is_flagged(self):
        cid = self.candidates[0]["id"]
        story = {"candidate_id": cid, "category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI",
                 "summary": "x", "why_it_matters": "", "alt_text": "a"}
        _, warnings = finalize({"stories": [story], "engagement_question": "Comment YES if your EMI falls",
                                "share_line": "Tag a friend with a home loan"}, self.candidates, self.cfg)
        self.assertEqual(sum("engagement bait" in w for w in warnings), 2)
        _, warnings = finalize({"stories": [story], "engagement_question": "Rate cut: good news or too late? Why?",
                                "share_line": "Send this to the friend with a home loan"}, self.candidates, self.cfg)
        self.assertFalse(any("bait" in w for w in warnings))

    def test_long_copy_warns(self):
        cid = self.candidates[0]["id"]
        story = {"candidate_id": cid, "category": "MONEY", "headline": "RBI Cuts Rate", "highlight": "RBI",
                 "summary": " ".join(["word"] * 34) + ".", "why_it_matters": " ".join(["so"] * 16), "alt_text": "a"}
        _, warnings = finalize({"stories": [story]}, self.candidates, self.cfg)
        self.assertTrue(any("is 34 words" in w for w in warnings))
        self.assertTrue(any("why_it_matters" in w and "16 words" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
