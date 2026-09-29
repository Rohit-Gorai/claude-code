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
| **Reads itself** | Under the photo: one 15-25 word gist in 35px type and one "**Why it matters:**" line. Lots of space, no boxes | Short lines in big type are read without effort, the way you read a caption, not an article. |
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
│ Sensex Slides Again: ▇Over ₹5 Lakh▇      │  headline · Poppins 800 · 68px · white on the photo
│ ▇Crore Gone▇ in 30 Minutes               │  highlight = red marker
├──────────────────────────────────────────┤
│ The Sensex fell 595 points by 9:46 AM    │  gist · 15-25 words · Poppins 500 · 35px
│ as Brent crude rose past $106.           │
│                                          │
│ Why it matters: Costlier oil stokes      │  ≤12 words · 31px · label in red
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

## 3. Photo quality

Every photo goes through `brief/photos.py`:

1. **Find the biggest version.** News sites serve small copies (`photo-1200x675.jpg`, `?w=640`,
   Wikimedia `800px-` thumbnails). For each URL the renderer also tries the full-size original the
   same server usually has, and it reads the larger lead photos some articles list in their
   page metadata.
2. **Pick the sharpest.** Each photo is scored by how much it would be stretched to fill its space.
   The cover is the hardest: a landscape photo needs to be ~2600px wide to fill 1080×1440 without
   stretching. The editor's first choice wins unless a later photo is clearly sharper.
3. **Never lose quality.** Original files are used as-is (no second JPEG compression). If a photo
   must be stretched, it is enlarged once with Lanczos resampling and a light sharpen. Slides are
   captured losslessly and saved as maximum-quality JPEGs with full colour detail (4:4:4), so red
   text stays crisp after Instagram re-compresses them.
4. **Say so when it's not good enough.** `render` prints each photo's size and verdict (`sharp`,
   `fine`, `soft`) and the width a replacement needs, so the editor can find a bigger one.

## 4. Details that keep it working every day

- **Self-fitting text.** Headlines, the gist, stats and the last-slide copy shrink to fit. The
  photo never gets smaller than 700px tall (620px at 4:5).
- **No photo? A designed card.** A dark card with a red glow and the category in giant outline
  letters, so a missing photo still looks deliberate and carries no copyright risk.
- **White logo on photos, dark logo on the light slide.** `assets/logo-white.png` is generated
  from `assets/logo.png` (red dot kept). Replace both if you change the logo.
- **One font family.** Poppins 500-900 (OFL licence, bundled).

## 5. Changing the look

- `config.yaml` → `brand`: name, logos, handle, tagline, posting `schedule`, `colors`
  (`paper` reading panel, `ink` text, `accent` red, `dark` numbers slide and last card).
- `config.yaml` → `format`: size, number of stories, JPEG quality.
- `templates/style.css` for sizes and spacing; `templates/*.html.j2` for each slide's structure
  (`cover`, `story`, `numbers`, `wrap`; `base` holds the progress bar, logo and auto-fit script).

**3:4 or 4:5?** 1080×1440 (3:4) fills Instagram's profile grid edge to edge when you post by hand,
but scheduling tools reject it. If you schedule posts, set `format.height: 1350` (4:5): the photo
area shrinks and everything else stays the same.
