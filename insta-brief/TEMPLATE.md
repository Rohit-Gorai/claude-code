# The template, dissected

Your reference is *The Brand Bulletin* by @btswithbrands. Here is what makes it work, and how
**The Brief** keeps that DNA while being built for people who just want the headlines.

![Sample carousel](samples/preview/contact_sheet.jpg)

## 1. What the reference does

| Element | What it is | Why it works |
|---|---|---|
| **Canvas** | 3:4 portrait (1080×1440) on off-white crumpled paper | 3:4 fills Instagram's grid and feed with no cropping. The paper texture says "newspaper" before anyone reads a word. |
| **Masthead** | Bold serif title in deep red, centred | Same on every slide, so the brand is recognisable at thumbnail size and in the grid. |
| **Dateline bar** | Charcoal strip: page name left, date right | Borrowed from real newspapers. It makes the post feel *current* and official. |
| **Two-tone headline** | Heavy geometric sans. The hook words in red, the rest in charcoal | The eye lands on the red words first, which gives you the story in 2–3 words. |
| **Double rule** | Thick line plus thin line | Newspaper section divider. It separates "headline" from "picture". |
| **Picture block** | Cover: one big hero image plus two small ones. Story: one wide image | The cover collage teases several stories at once, which pushes people to swipe. |
| **`#1` badge** | White box, red number, pinned bottom-left of the image | Ranking makes it a countdown, and the number tells you where you are in the carousel. |
| **Italic serif body** | ~40 words, centred, under the image | Short enough to read in 5 seconds. The italic serif reads as "the story" in contrast to the loud headline. |
| **Swipe cue** | Italic caps `SWIPE TO KNOW  >>` under a double rule | An explicit call to action. Swipes are a strong engagement signal. |

## 2. The Brief's slide system

```
┌──────────────────────────────────────────┐  1080 × 1440  (3:4)
│               The Brief                  │  masthead · Playfair Display 800 · 76px · red
│ ▓ THE BRIEF · No. 012     27 SEPTEMBER ▓ │  dateline bar · 58px · Crimson Pro caps
│                                          │
│   Stock Markets Hit a Record             │  headline · Poppins 700 · 70px · ≤3 lines
│   High as Investors Pour Back In         │  (hook words in red, auto-shrinks to fit)
│ ┌──────────────────────────────────────┐ │
│ │ MONEY                                │ │  category chip
│ │                                      │ │
│ │            photo (flexes)            │ │  fills whatever space the text leaves
│ │                                      │ │  (typographic card if there's no photo)
│ │ #1                                   │ │  rank badge
│ └──────────────────────────────────────┘ │
│                  Source: The Hindu, Mint │  credit · builds trust
│   Share prices closed at an all-time     │  summary · Crimson Pro italic · 36px · ≤5 lines
│   high after three straight weeks...     │
│   WHY IT MATTERS Your SIPs are up.       │  the takeaway · Poppins 600 · red label
│ ════════════════════════════════════════ │  double rule
│ SWIPE FOR THE NEXT                    >> │  swipe cue
└──────────────────────────────────────────┘
```

**Carousel order (7 slides by default):**

1. **Cover.** Two-line hook (red + charcoal), a collage of stories #1–#3 with rank badges, and `SWIPE TO KNOW`.
2. **Story #1.** Your strongest story. Instagram re-shows a carousel's *second* slide to people who
   scrolled past the first, so this slide gets a second chance at every viewer.
3. **Stories #2–#5.** One story per slide, same layout every time, so the page trains the reader's eye.
4. **Quick hits + follow card.** Five one-line headlines for headline lovers, then a charcoal card
   with your handle and `SAVE · SHARE · FOLLOW`. Readers see it when they're most satisfied, which is
   the best moment to ask for the follow.

## 3. What was kept, and what was added

**Kept from the reference:** masthead, dateline bar, red/charcoal two-tone headlines, double rules,
white `#N` badge on the image, italic serif body, swipe cue, crumpled paper, 3:4.

**Added for a headlines page:**

- **Edition number** (`No. 012`) in the dateline. It builds a daily ritual, and people like to collect a numbered series.
- **Category chip** on every photo (MONEY, TECH, SPORTS…) so people can tell what a story is about at a glance.
- **"Why it matters" line.** The one-sentence takeaway is what makes people save and forward the post.
- **Source credit** under every image. On a news page, trust is what keeps followers.
- **Quick hits slide.** You get five more headlines without making the carousel longer.
- **Follow card** on the last slide, which turns satisfied readers into followers.
- **Typographic fallback card.** When there's no photo you can safely use, the story still looks
  designed (see slide #4 in the sample) and you take no copyright risk.
- **Self-fitting text.** Headlines and summaries shrink to fit, and the photo absorbs the leftover
  space, so no slide ever overflows.

## 4. Changing the look

Everything visual lives in two places:

- `config.yaml` → `brand` (name, handle, colours) and `format` (size, number of stories).
- `templates/style.css` for fonts, sizes and spacing. `templates/*.html.j2` hold the slide structures.

To switch to 4:5, set `format.height: 1350`. The photo area shrinks and everything else stays the same.
