# What makes a b.rief post travel — and what we changed because of it

Research done on 29 Sep 2026. Instagram doesn't publish its ranking formula: the platform
statements below (Meta, Adam Mosseri) are reported, and the percentages come from industry
studies and marketing blogs. Treat them as strong hints, not laws. Sources are at the bottom.

## 1. What the research says

### How Instagram decides who sees a post
- **Sends matter most for reaching strangers.** Mosseri names three top signals: time spent,
  **sends per reach** (DM shares) and likes per reach. Sends are reported to weigh about **3-5x
  more than likes** and are "one of the biggest signals" for reaching non-followers. Saves and
  shares outweigh follower count and likes. [1][2]
- **Carousels are the best feed format for engagement.** Social Insider measured carousels at
  ~0.5% engagement in 2026, the highest of any format (Reels ~0.48%, single images ~0.33%).
  Carousels are saved ~35% more than single images. [1][3][4]
- **8-10 slides is the sweet spot.** Carousels with fewer than 4 slides do barely better than a
  single image. [3]
- **Slide 2 gets a second chance.** If a follower scrolls past slide 1, Instagram can re-show the
  carousel later starting on slide 2. The slide 1 → 2 swipe is the most important moment. [5]
- **Originality is enforced on carousels now.** Since **30 April 2026**, photos and carousels
  follow the same originality rules as Reels: accounts that mostly repost content they didn't
  create, or haven't meaningfully transformed, stop being recommended to non-followers.
  Aggregators reported 60-80% reach drops; original creators 40-60% gains. [6][7][8]
- **Engagement bait is demoted.** "Comment YES", "tag 3 friends" and "like if you agree" count as
  engagement bait under Meta's recommendation guidelines. A detailed comment carries far more signal
  than "yes". [9][10]
- **Political content isn't recommended to non-followers.** Since 2024 Instagram doesn't
  proactively recommend political posts in Explore, Reels, in-feed suggestions or Suggested Users.
  Followers still see them. [11][12]
- **Search is a second front door.** The first sentence of the caption, the name field and alt text
  are read by Instagram search. Since 10 July 2025, public posts from professional accounts can be
  indexed by Google. 3-5 specific hashtags beat many generic ones. [13][14]

### What makes people share news (the science)
- **Berger & Milkman (2012)** studied every *New York Times* article over three months and which
  ones readers emailed. Content that triggers **high-arousal emotions spreads more: awe (positive),
  anger and anxiety (negative)**. Sadness, a low-arousal emotion, spreads *less*. Positive content
  beats negative overall, and **surprising, interesting and practically useful** content is shared
  more. [15][16]

### India
- India is Instagram's largest market (~534M monthly users, April 2026). Finance tips and exam
  prep are among the fastest-growing niches, and educational carousels get shared. [17]
- Evenings are the strongest window for Indian audiences (roughly 6-9 PM IST); b.rief's 6 PM and
  10 PM editions sit in or next to it. [18]

### Cover design
- A strong cover = a **5-8 word hook** (the biggest text on the slide), a **pattern interrupt**
  (an expressive face, high contrast) and a **curiosity gap** that only the swipe closes. [19]

## 2. What changed in b.rief

| Finding | Change |
|---|---|
| Sends + time spent rank posts | Every story ends on a "Next: …" line that teases the next one; each slide reads at a glance (headline, 15-25 word gist, one "Why it matters" line); the last slide names who to send the post to. |
| 8-10 slides win | Carousels are now **8 slides**: cover, 5 stories, **Today in numbers**, quick hits. |
| Slide 2 is re-shown | Story slides open with the photo and headline, so story #1 works as a second cover. The editor must put the most shareable, non-political story first. |
| Cover must stop the scroll | Full-bleed photo (ideally a face, the sharpest version the renderer can find), 5-8 word hook on a red marker, round previews of the other stories, **Swipe →** button. |
| Originality | A new, original design (no copy of another page's layout). The editor re-tells every story in its own words with original "why it matters" and stats, and the numbers slide is fully original. |
| Saves | The edition's key numbers are collected on the saveable **Today in numbers** slide. |
| Awe, anger, anxiety spread; sadness doesn't | Each story gets an `emotion`. `check` warns if the edition has more than one SAD story, leads with one, or has no AWE / JOY / PRIDE high point (ideally last). |
| Useful + surprising content spreads | **New ranking signal** (`brief/virality.py`): candidates about money, records/space/science, India pride, famous names, surprises and scams move up; political and grim stories move down. Each candidate carries `viral` and `flags` for the editor. |
| Bait is demoted | The question must invite an opinion *and* a reason. `check` flags "comment YES", "tag a friend", "like if" in the question, share line and caption. |
| Politics isn't recommended | Political stories are flagged, penalised in ranking and kept off the cover and slide 2. |
| Search | The caption's first line names the #1 story's key name/keyword; every slide has keyword-rich alt text; 3-5 specific hashtags. |
| 3:4 vs 4:5 | 1080×1440 stays the default (fills the grid when posted by hand). Use 1350 (4:5) for schedulers. |

## 3. How the ranking works now

```
rank = score + 1.0 × viral
score = 1.5 × outlets + 0.5 × related headlines + freshness (0-2) + 1 if a top story + 0.3 if it has photos
viral = sum of matched signals, capped to [-2, +3]
        money +1.2 · wow +1.0 · pride +0.8 · stars +0.6 · surprise +0.6 · outrage +0.4
        numbers +0.4 · alert +0.3 · grim −0.8 · political −1.2
```

A story covered by one more outlet (+1.5) still beats a small shareable one, so big news stays in.
Tune `VIRAL_WEIGHT` in `brief/fetch.py` and the keyword lists in `brief/virality.py`.

## Sources

1. [Instagram Algorithm 2026: 5 Ranking Signals Mosseri Confirmed — Dataslayer](https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers)
2. [The Instagram Algorithm 2026: What Mosseri Says vs What's Measured — Creator Lane](https://creatorlanehq.com/blog/instagram-algorithm-2026-mosseri-vs-measured)
3. [Instagram Carousel Engagement: Stats, Benchmarks and What Works in 2026 — Carouselli](https://carouselli.com/blog/instagram-carousel-engagement)
4. [Instagram Carousel Strategy 2026 — TrueFuture Media](https://www.truefuturemedia.com/articles/instagram-carousel-strategy-2026)
5. [Instagram Carousel Algorithm 2026: How to Maximize Swipes — TryMyPost](https://www.trymypost.com/blog/instagram-carousel-algorithm-strategy-2026)
6. [New Instagram Policies Target Reposted Content — PetaPixel (30 Apr 2026)](https://petapixel.com/2026/04/30/new-instagram-policies-target-reposted-content/)
7. [Instagram's Original Content Algorithm Update — ALM Corp](https://almcorp.com/blog/instagram-original-content-algorithm-update/)
8. [Instagram Now Penalizes Reposted Content Across Every Format — Launchvibes](https://www.launchvibes.tech/articles/instagram-original-content-algorithm)
9. [Engagement Bait — Meta Transparency Center](https://transparency.meta.com/features/approach-to-ranking/content-distribution-guidelines/engagement-bait/)
10. [How to Avoid Posting Engagement Bait — Meta Business Help Center](https://www.facebook.com/business/help/259911614709806)
11. [Instagram, Threads no longer recommending political content — The Hill](https://thehill.com/policy/technology/4459198-instagram-threads-no-longer-recommending-political-content/)
12. [Instagram's Political Content Limit: Everything to Know — TIME](https://time.com/6960587/meta-instagram-political-content-limit-off-setting-default/)
13. [Instagram SEO — Metricool](https://metricool.com/instagram-seo/)
14. [Instagram SEO 2026: keywords, captions, alt text — Outfame](https://www.outfame.com/blog/instagram-seo-2026-how-to-rank-in-search-keywords-captions-alt-text)
15. [Berger & Milkman, "What Makes Online Content Viral?", Journal of Marketing Research (2012)](https://journals.sagepub.com/doi/10.1509/jmr.10.0353) · [PDF](http://jonahberger.com/wp-content/uploads/2013/02/ViralityB.pdf)
16. [The Secret to Online Success: What Makes Content Go Viral — Scientific American](https://www.scientificamerican.com/article/the-secret-to-online-success-what-makes-content-go-viral/)
17. [Instagram Statistics 2026 — Digital Applied](https://www.digitalapplied.com/blog/instagram-statistics-2026-facts-data-trends) · [Complete Instagram Growth Guide India 2026 — SocialRob](https://socialrob.com/growth/guides/complete-instagram-growth-guide-india)
18. [Best Time to Post on Instagram in India (2026) — WsCube Tech](https://www.wscubetech.com/blog/instagram-post-time/) · [Buffer: data from 9.6M posts](https://buffer.com/resources/when-is-the-best-time-to-post-on-instagram/)
19. [Instagram Carousel Best Practices (2026): Slide-by-Slide Design — Adpicto](https://www.adpicto.com/en/blog/instagram-carousel-best-practices-2026)
