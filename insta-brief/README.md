# b.rief: an automatic Instagram news carousel

Every morning this tool reads 20 news feeds, finds the stories everyone is covering, has Claude write
catchy (but accurate) slide copy, and renders a ready-to-post 8-slide carousel in b.rief's own
photo-first design: cover, 5 stories, "Today in numbers", quick hits, a caption, and alt text.

![Sample carousel](samples/preview/contact_sheet.jpg)

*The sample above uses placeholder stories and illustrations. Real editions use today's news and photos.*

- **Design breakdown:** [TEMPLATE.md](TEMPLATE.md)
- **What makes posts travel (research + sources):** [VIRALITY.md](VIRALITY.md)
- **How to grow the page:** [PLAYBOOK.md](PLAYBOOK.md)

---

## Setup (once)

You need Python 3.10+.

```bash
cd insta-brief
pip install -r requirements.txt
python -m playwright install chromium          # headless browser that draws the slides
export ANTHROPIC_API_KEY=sk-ant-...            # for the Claude editor (or: ant auth login)
```

Then open `config.yaml` and set your page **name**, **handle**, and **first_edition_date**.
To see how your branding looks without fetching any news, render the sample edition:

```bash
python -m brief render --edition samples/sample_edition.json --out output/sample
```

## Every day

```bash
python -m brief run
```

The result goes to `output/<today>/`:

| File | What to do with it |
|---|---|
| `01_cover.jpg` … `07_quickhits.jpg` | Upload as one carousel, in this order |
| `caption.txt` | Paste as the caption |
| `alt_text.txt` | Instagram → Advanced settings → Accessibility → alt text per slide (helps search) |
| `candidates.json` | Every story found today, ranked (for your own reading) |
| `edition.json` | The copy Claude wrote. Edit it and run `python -m brief render` to redraw |

**Always read the slides before posting.** Claude is told to use only facts from the source
articles, but you are the editor-in-chief. If something looks off, fix `edition.json` and re-render.

## Three ways to run the editor

| Mode | Command | Needs | Best for |
|---|---|---|---|
| **claude** (default) | `python -m brief run` | `ANTHROPIC_API_KEY` | Fully automatic daily runs |
| **Claude Code** | type `/brief` in Claude Code, in this repo | Claude Code | Best quality: the agent can web-search to verify facts and looks at the rendered slides before handing them over |
| **basic** | `python -m brief run --mode basic` | nothing | Testing; uses raw feed headlines, no AI |

The Claude Code agent lives in `.claude/agents/brief-editor.md` and the command in
`.claude/commands/brief.md`. Themed editions work too: `/brief budget day special`,
`/brief tech only`, `/brief weekend recap`.

### Step by step (what `run` does)

```bash
python -m brief fetch     # feeds → ranked story clusters → candidates.json
python -m brief edit      # candidates.json → edition.json (Claude writes the copy)
python -m brief check     # validates edition.json, prints warnings
python -m brief render    # edition.json → slides + caption + alt text
python -m brief guide     # prints the editorial rules + edition.json schema
```

## How it picks "the biggest news"

1. **Fetch** Google News (India edition, 8 sections) plus 12 publisher feeds (The Hindu, Indian Express,
   NDTV, HT, Mint, ET, BBC, Al Jazeera, Guardian, TechCrunch, The Verge, ESPNcricinfo). Old items,
   opinion pieces, live blogs and horoscopes are dropped.
2. **Cluster** headlines about the same event, e.g. *"RBI cuts repo rate…"* from The Hindu and Mint
   become one story with 2 sources.
3. **Score** each story. The score goes up with how many outlets cover it, how many related articles
   Google groups with it, how fresh it is, whether it's in a top-stories feed, and whether it has a photo.
   A **virality signal** (`brief/virality.py`) then nudges shareable topics up (your money, records and
   space, India pride, famous names, surprises) and political or grim ones down. See [VIRALITY.md](VIRALITY.md).
4. **Enrich** the top 24 by opening the articles to get the lead photo and a few paragraphs of real text.
5. **Edit.** Claude picks 5 stories plus 5 quick hits with a category mix and puts the most shareable,
   non-political story on slide 2. It writes headline, red highlight, a 15-25 word gist, a short "why it
   matters", the key stat, a teaser for the next slide, caption hook, question, share line and hashtags,
   and tags each story's emotion so `check` can test the edition's arc.
6. **Render.** For each story it finds the largest version of the photo, picks the sharpest, and warns
   when one would look soft (see [TEMPLATE.md](TEMPLATE.md#3-photo-quality)).
   The rules it follows are in `brief/editor.py` (`GUIDE`). Tweak the voice there.

## Customise

- **Brand:** `config.yaml → brand` (name, logos, handle, tagline, posting schedule, colours).
  `assets/logo.png` is used on the light slide, `assets/logo-white.png` on photos;
  `assets/profile_picture.jpg` is a ready-made Instagram profile picture.
- **Size:** `format.height: 1440` (3:4, fills the grid when you post by hand) or `1350` (4:5, needed by
  scheduling tools).
- **Length:** `format.stories` (up to 18, since Instagram allows 20 slides), `format.quick_hits`.
- **Feeds:** add/remove under `news.feeds`. Any RSS/Atom URL works. `top: true` marks top-stories feeds.
  For a global page, swap `hl=en-IN&gl=IN&ceid=IN:en` for `hl=en-US&gl=US&ceid=US:en`.
- **Look:** `templates/style.css` and `templates/*.html.j2`.
- **Voice/rules:** `GUIDE` in `brief/editor.py`.

## Photos and copyright ⚠️

The tool uses each article's lead photo (in the largest size the site serves) and credits the site on
the slide. **A credit is not a licence.** Wire photos (Getty, Reuters, AP, PTI, ANI) are often copyrighted, and repeated
copyright claims can get an Instagram account restricted. Safer options:

- Official handouts, press-kit images, government/PIB, ISRO, team and company press photos.
- Wikimedia Commons / Unsplash / Pexels images that allow reuse (credit them).
- The built-in **designed card**: remove a story's `images` in `edition.json` (set it to `[]`)
  and re-render. It looks intentional (see slide 5 in the sample).

## Automate it

**Cron (your computer or a server):** run at 7:15 AM IST every day, review the output, and post by 8:

```cron
15 7 * * *  cd /path/to/insta-brief && /usr/bin/python3 -m brief run >> output/cron.log 2>&1
```

**Auto-posting** is possible later with the Instagram Graph API. It needs a Business/Creator account,
a Meta developer app, and the slide images hosted at public URLs. Get the page running manually first,
because a human review before posting is what keeps a news page trustworthy.

## Troubleshooting

- **"✗ feed … 403/timeout"**: that feed changed or blocked the request. One failing feed is fine. If
  most fail, check your internet connection.
- **Chromium not found**: run `python -m playwright install chromium`, or point
  `BRIEF_CHROMIUM=/path/to/chrome` at an existing Chrome/Chromium.
- **A photo crops someone's head off**: add `"image_position": "center 15%"` to that story in
  `edition.json` and re-render.
- **Tests:** `python -m unittest discover -s tests` (offline, uses fake feeds).
