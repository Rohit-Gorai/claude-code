# The template, dissected

b.rief's look is its own: a photo-first **story card**, designed around how Instagram ranks
carousels (see [VIRALITY.md](VIRALITY.md)) and around one rule: **reading should feel effortless**.
Each slide has one focal point, the headline on the photo, and at most two short lines of text
under it. No boxes, badges, bullet lists or stickers compete for attention.

![Sample carousel](samples/preview/contact_sheet.jpg)

## 1. Design principles

| Principle | How the template does it | Why |
|---|---|---|
| **Stop the scroll** | Cover = story #1's photo edge to edge, a 5-8 word hook in 108px type, the key words on a red marker | The cover is judged in under a second in a busy feed. Big type on a face or a strong photo is the pattern that makes people stop. |
| **One thing to look at** | The photo fills ~⅔ of each story slide, with the headline on it | The eye lands on the photo, then the headline, with nothing else to decide between. |
| **Reads itself** | Under the photo: one 15-25 word gist in 42px Source Sans 3 (≈15pt on a phone) and one "**Why it matters:**" line. Lots of space, no boxes | Short lines in big, humanist type are read without effort, the way you read a caption, not an article (§3). |
| **Promise more, quietly** | A thin story-style progress bar at the top; small round previews of the other stories on the cover; a red **Swipe →** button | People swipe when they can see there's more. Swipes and time spent are what Instagram measures. |
| **Slide 2 stands alone** | Every story slide opens with the photo and its headline | Instagram re-shows slide 2 to people who skipped the cover, so story #1 is a second cover. |
| **Always an open loop** | A red "Next: …" line at the bottom of each story teases the next one | A question the next slide answers is the strongest swipe cue there is. |
| **Something worth saving** | A dark **Today in numbers** slide collects the edition's key numbers | A recap people save. Saves are a ranking signal. |
| **End with a job** | Quick hits, then a dark card: a real question, who to send it to, **Follow** and the posting times | Asks for comments, sends and the follow when readers are most satisfied. |
| **Sharp photos** | The renderer finds the largest version of every photo and says when one is too small (below) | A soft, stretched photo makes the whole page look cheap. |

## 2. The slides

```
┌──────────────────────────────────────────┐  1080 × 1440 (3:4)
│ ━━━━ ━━━━ ━━━━ ──── ──── ──── ──── ──── │  thin progress bar
│ b.rief          Business Standard · Photo│  white logo · tiny source/photo credit
│                                          │
│                                          │
│        photo (≈⅔ of the slide)           │
│                                          │
│ — MONEY                                  │  category, quiet
│ Sensex Slides Again: ▇Over ₹5 Lakh▇     ┊│  headline · Poppins 800 · 68px · white, soft shadow
                                            ┊   ┊ = photo credit, small and vertical along the edge
│ ▇Crore Gone▇ in 30 Minutes               │  highlight = red marker
├──────────────────────────────────────────┤
│ The Sensex fell 595 points by 9:46 AM    │  gist · 15-25 words · Source Sans 3 · 42px · 1.42 leading
│ as Brent crude rose past $106.           │
│                                          │
│ Why it matters: Costlier oil stokes      │  ≤12 words · Source Sans 3 · 36px · bold label in ink
│ inflation worries, dragging you down.    │
│                                          │
│ @b.rief      Next: Why your cousin… →    │  watermark · red swipe cue
└──────────────────────────────────────────┘
```

**Carousel order (8 slides by default):**

1. **Cover.** Story #1's photo, "Today's brief · 5 stories", the hook with a red marker, small
   round previews of the other stories ("+4 more inside") and a red **Swipe →** button.
2. **Story #1.** The most shareable story. Works as a second cover.
3. **Stories #2-#5.** Same layout every time, so the page trains the reader's eye.
4. **Today in numbers.** Built automatically when at least 3 stories have a `stat`.
5. **Quick hits.** Five numbered one-liners, then the question, the share line, **Follow @b.rief**
   and "New brief daily · 10 AM · 2 PM · 6 PM · 10 PM".

With fewer than 3 stats the numbers slide is skipped (7 slides) and `check` says so.

## 3. Easy on the eyes: the research behind the details

A slide is 1080px wide but shows ~390pt wide on a phone, so everything is seen at ~36% size.
Every size and colour below was chosen with that in mind.

| Finding | What the template does |
|---|---|
| Text that is easy to read is **liked more and believed more**. In Reber & Schwarz's experiments, the same statement was judged more likely true when it was easier to read ([Reber & Schwarz 1999](https://www.semanticscholar.org/paper/Effects-of-Perceptual-Fluency-on-Judgments-of-Truth-Reber-Schwarz/5a14c99cae5603943848d43273242a4c06e9e72c); [Schwarz, "Of fluency, beauty, and truth"](https://dornsife.usc.edu/norbert-schwarz/wp-content/uploads/sites/231/2023/12/18_ch_Schwarz_Fluency_beauty_truth.pdf)). | Readability is treated as a trust feature for a news page, not decoration. |
| Mobile body text should be **≥14-16pt**, with **1.3-1.6 line height** and **30-50 characters per line** ([UXPin](https://www.uxpin.com/studio/blog/optimal-line-length-for-readability/), [Baymard](https://baymard.com/blog/line-length-readability)). | Gist 42px (≈15pt on a phone), line height 1.42, ~45 characters per line; why-it-matters 36px; nothing under ~24px except the photo credit. |
| **Humanist sans-serifs are read faster at a glance** than grotesque/geometric ones (a ~12% difference in glance time, [UX Movement](https://uxmovement.com/content/how-sans-serif-typeface-styles-affect-readability/); open shapes don't blur, [Vision Australia](https://www.visionaustralia.org/business-consulting/digital-access/blog/typography-in-inclusive-design-part-2)). | Body text in **Source Sans 3** (humanist, has ₹). **Poppins** (geometric) is kept for headlines, numbers and buttons, where it is big and brand-defining. |
| **If everything stands out, nothing does** (the isolation / von Restorff effect, [Laws of UX](https://lawsofux.com/von-restorff-effect/)). | Red appears once per story slide: the headline marker, plus a small red arrow on "Next". Labels, stamps and the category line are now ink or white. |
| **Text over photos needs a scrim**: a dark gradient only where the text sits ([NN/g](https://www.nngroup.com/articles/text-over-images/), [Smashing](https://www.smashingmagazine.com/2023/08/designing-accessible-text-over-images-part1/)). | ~80-95% dark gradient behind the headline, plus a soft text shadow for very bright photos. |
| **Pure white and pure black strain the eyes** (glare, and halo on OLED screens) ([UX Movement](https://uxmovement.com/content/why-you-should-never-use-pure-black-for-text-or-backgrounds/)). | Warm off-white paper `#F6F2EA`, warm near-black ink `#1F1C18`, deep grey `#17161A` for dark slides with off-white `#EEEAE3` text. |
| **Small text needs ≥4.5:1 contrast** ([WebAIM](https://webaim.org/articles/contrast/)). The brand red on the paper is only 4.3:1. | Small red text uses a darker red `#C40F09` (5.5:1) on light slides and a brighter `#FF4B3E` (5.4:1) on dark slides. The big marker keeps the brand red. |
| **Instagram shows its own "1/8" counter in the top-right** of a carousel in the feed; keep key content 60-80px from the edges ([Veeso](https://veeso.ai/blog/instagram-carousel-safe-zone-guide)). | Nothing important top-right: the cover date moved into the kicker line, the photo credit runs vertically along the photo's edge, side margins are 72px. |

## 4. Photo quality

Every photo goes through `brief/photos.py`:

1. **Find the biggest version.** News sites serve small copies (`photo-1200x675.jpg`, `?w=640`,
   Wikimedia `800px-` thumbnails). For each URL the renderer also tries the full-size original the
   same server usually has, and it reads the larger lead photos some articles list in their
   page metadata.
2. **Pick the sharpest.** Each photo is scored by how much it would be stretched to fill its space.
   The cover is the hardest: a landscape photo needs to be ~2600px wide to fill 1080×1440 without
   stretching. The editor's first choice wins unless a later photo is clearly sharper.
3. **Never lose quality.** Original files are used as-is (no second JPEG compression). Slides are
   captured losslessly and saved as maximum-quality JPEGs with full colour detail (4:4:4), so red
   text stays crisp after Instagram re-compresses them.
4. **AI upscaling when a photo is too small.** Photos that would be stretched go through
   Real-ESRGAN's compact super-resolution model, run locally on the CPU (~10-15 s per photo,
   bundled in `assets/models/`, BSD-3 licence). It removes JPEG blockiness and restores edges.
   Because this is news, the AI result is blended 60/40 with a plain enlargement so it can't invent
   detail, and no face-restoration model is used: people keep their real features. Turn it off with
   `format.ai_upscale: false`; without `onnxruntime` it falls back to Lanczos + a light sharpen.
5. **Say so when it's not good enough.** `render` prints each photo's size and verdict (`sharp`,
   `fine`, `soft`) and the width a replacement needs. Upscaling helps, but a bigger original is
   always better, so the editor still looks for one.

## 5. Story graphics

Each story can carry one small graphic on its photo, chosen by the editor to fit that story and
built only from its facts (`visual` in `edition.json`):

| Type | Looks like | Use it for |
|---|---|---|
| `trend` | White chip: `SENSEX ▼ 595 pts` (red when down, green when up) | A number that rose or fell |
| `stamp` | Tilted white-outlined stamp: `MOST WANTED`, `WORLD FIRST`, `CANCELLED` | A 1-3 word label that is literally true |
| `versus` | Pill: `India vs Sri Lanka` | Matches, contests, disputes |
| `place` | Dark card with a map and a red pin: `📍 Bengaluru` | When where it happened matters |

- **Graphics, never photo edits.** The photo always shows what the camera captured. A graphic sits
  on top of it and is obviously a graphic.
- **Maps use India's official borders.** Borders come from Natural Earth's India point-of-view
  dataset (public domain, bundled in `assets/maps/`), and `check` drops any pin that doesn't fall
  inside the country it names.
- **One consistent colour grade** (a touch of contrast, saturation and warmth, tone only) on every
  photo, so the grid reads as one page.

## 6. Details that keep it working every day

- **Self-fitting text.** Headlines, the gist, stats and the last-slide copy shrink to fit. The
  photo never gets smaller than 700px tall (620px at 4:5).
- **No photo? A designed card.** A dark card with a red glow and the category in giant outline
  letters, so a missing photo still looks deliberate and carries no copyright risk.
- **White logo on photos, dark logo on the light slide.** `assets/logo-white.png` is generated
  from `assets/logo.png` (red dot kept). Replace both if you change the logo.
- **Two font families.** Poppins 500-900 for headlines, Source Sans 3 for reading (both OFL, bundled).

## 7. Changing the look

- `config.yaml` → `brand`: name, logos, handle, tagline, posting `schedule`, `colors`
  (`paper` reading panel, `ink` text, `accent` brand red, `accent_on_light` / `accent_on_dark` for
  small red text, `dark` + `on_dark` for the numbers slide and question card).
- `config.yaml` → `format`: size, number of stories, JPEG quality.
- `templates/style.css` for sizes and spacing; `templates/*.html.j2` for each slide's structure
  (`cover`, `story`, `numbers`, `wrap`; `base` holds the progress bar, logo and auto-fit script).

**3:4 or 4:5?** 1080×1440 (3:4) fills Instagram's profile grid edge to edge when you post by hand,
but scheduling tools reject it. If you schedule posts, set `format.height: 1350` (4:5): the photo
area shrinks and everything else stays the same.
