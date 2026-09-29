# The template, dissected

b.rief's look is its own: a photo-first **story card**, designed around how Instagram ranks
carousels (see [VIRALITY.md](VIRALITY.md)). It no longer borrows the newspaper layout of the page
that inspired the project: no masthead, dateline bar, double rules or crumpled paper.

![Sample carousel](samples/preview/contact_sheet.jpg)

## 1. Design principles

| Principle | How the template does it | Why |
|---|---|---|
| **Stop the scroll** | Cover = story #1's photo edge to edge, a 5-8 word hook in 100px type, the key words on a red marker | The cover is judged in under a second in a busy feed. Big type on a face or a strong photo is the pattern that makes people stop. |
| **Promise more** | Story-style progress bar + `1/8` counter on every slide; "Also inside" thumbnails of stories 2-5 on the cover; a red **Swipe →** button | People swipe when they can see there is more, and what it is. Swipes and time spent are what Instagram measures. |
| **Slide 2 stands alone** | Every story slide opens with the photo and a white headline on it, with its own number and category | Instagram re-shows slide 2 to people who skipped the cover, so story #1 is a second cover. |
| **Readable in 5 seconds** | 2-3 bullet points (the summary's sentences), then a white **Why it matters to you** card | Bullets are faster to scan than a paragraph. The "why it matters" line is what people save and forward. |
| **Always an open loop** | A dark **Next** bar at the bottom of each story teases the next one ("Next: why your portfolio is red again") | A question the next slide answers is the strongest swipe cue there is. |
| **Numbers are the sticker** | A tilted white sticker with the story's key number on the photo (`₹5L cr / wiped out in 30 min`) | Numbers stop the eye, and they are what people quote when they share. |
| **Something worth saving** | A dark **Today in numbers** slide lists the edition's stats | A recap people screenshot or save. Saves are a ranking signal. |
| **End with a job** | A quick-hits list, then a dark card: a real question, who to send it to, **Follow** and the posting times | The last slide asks for comments with a reason, sends and the follow at the moment readers are most satisfied. |
| **Branded, every slide** | Logo top left, @handle in the footer | Screenshots and forwards keep the brand attached, and the look is recognisable in the grid. |

## 2. The slides

```
┌──────────────────────────────────────────┐  1080 × 1440 (3:4)
│ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬                 │  progress bar: done / current (red) / to come
│ b.rief                              2/8  │  white logo · counter
│                          ┌────────────┐  │
│                          │ ₹5L cr     │  │  stat sticker (optional)
│         photo            │ wiped out… │  │
│      (flexes, ≥600px)    └────────────┘  │
│ [02] [MONEY]                             │  rank + category
│ Sensex Slides Again: ▇Over ₹5 Lakh▇      │  headline · Poppins 800 · 66px · white on the photo
│ ▇Crore Gone▇ in 30 Minutes               │  highlight = red marker
├──────────────────────────────────────────┤
│ ■ By 9:46 AM the Sensex was down 595…    │  bullets · Poppins 500 · 30px · one per sentence
│ ■ Listed firms lost over ₹5 lakh crore.  │
│ ■ The rupee opened at 96 a dollar.       │
│ ┃ WHY IT MATTERS TO YOU                  │  white card, red edge
│ ┃ Costlier oil is dragging your portfolio│
│ @b.rief · Source: … · Image: …           │  watermark + credit
│ [NEXT] Why your younger cousin…       →  │  dark "Next" bar
└──────────────────────────────────────────┘
```

**Carousel order (8 slides by default):**

1. **Cover.** Story #1's photo, a kicker pill (`29 SEP · 5 STORIES · 60 SEC`), the hook with a red
   marker, "Also inside" thumbnails for stories 2-5, `@b.rief` and a red **Swipe →** button.
2. **Story #1.** The most shareable story. Works as a second cover.
3. **Stories #2-#5.** Same layout every time, so the page trains the reader's eye. The last story's
   Next bar points to the numbers slide.
4. **Today in numbers.** Built automatically when at least 3 stories have a `stat`: each number
   big (alternating red and white), with its category and label.
5. **Quick hits + your take.** Five numbered one-liners, then the question, the share line,
   **Follow @b.rief** and "New brief daily · 10 AM · 2 PM · 6 PM · 10 PM".

With fewer than 3 stats the numbers slide is skipped (7 slides) and `check` says so.

## 3. Details that keep it working every day

- **Self-fitting text.** Headlines, bullets, stats and the last-slide copy shrink to fit. The photo
  never gets smaller than 600px (540px at 4:5), and bullets on one slide always share one size.
- **No photo? A designed card.** A dark card with a red glow and the category in giant outline
  letters, so a missing photo still looks deliberate and carries no copyright risk.
- **White logo on photos, dark logo on the light slide.** `assets/logo-white.png` is generated
  from `assets/logo.png` (red dot kept). Replace both if you change the logo.
- **One font family.** Poppins 500-900 (OFL licence, bundled), so the page looks consistent in the grid.

## 4. Changing the look

- `config.yaml` → `brand`: name, logos, handle, tagline, posting `schedule`, `colors`
  (`paper` reading panel, `ink` text, `accent` red, `dark` bars and cards).
- `config.yaml` → `format`: size and number of stories.
- `templates/style.css` for sizes and spacing; `templates/*.html.j2` for each slide's structure
  (`cover`, `story`, `numbers`, `wrap`; `base` holds the progress bar, logo and auto-fit script).

**3:4 or 4:5?** 1080×1440 (3:4) fills Instagram's profile grid edge to edge when you post by hand,
but scheduling tools reject it. If you schedule posts, set `format.height: 1350` (4:5): the photo
area shrinks and everything else stays the same.
