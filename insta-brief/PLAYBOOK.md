# Growth playbook: running a news page people actually follow

The tool makes the posts. This page is about everything around them. The short version:
**be useful every single day, be right, and make every post easy to save and send.**

---

## 1. Positioning: one sentence people remember

> **"India's news in 60 seconds. Every morning, 8 AM."**

People follow pages that make a clear promise and keep it. Yours: *I'll catch you up faster than
anyone, and I won't waste your time or mislead you.*

**Name:** **b.rief**. It's short and easy to say, and the name itself promises what the page does.
Grab the same handle on Instagram, Threads and WhatsApp Channels so people find you everywhere.

**Bio** (4 lines, no fluff):

```
📰 The day's biggest news in 60 seconds
🗞️ New edition every morning · 8 AM
✅ Sourced. Simple. No spin.
👇 Get it on WhatsApp
```

**Profile picture:** use `assets/profile_picture.jpg`, your **b.** monogram with the red dot on the paper background. It matches every post.
**Story highlights:** `Money` · `Tech` · `Sports` · `Explained` · `Corrections`.

**Before launch:** post 6–9 editions *before* you tell anyone about the page. A new visitor who sees a
full, consistent grid of red mastheads assumes you're established and follows. An empty grid looks
like a page that won't last.

---

## 2. Weekly content system

| When | What | Why |
|---|---|---|
| **Daily 8:00 AM IST** | The Morning Brief carousel (`python -m brief run`) | Your core product. The same time every day builds a habit. |
| **Daily, Stories** | 1 quiz sticker from today's brief ("What did RBI cut today?"), 1 poll, reshare the post | Stickers are easy interactions that keep you at the front of the Stories bar |
| **Evenings, when big news breaks** | One single-story post (`format.stories: 1`) or a Reel | Speed on big moments is how pages get discovered |
| **Sunday** | "The week in 10 headlines" (`format.stories: 10`) | Very saveable, and a good way to catch up anyone who missed the week |
| **Weekly** | One "Explained" carousel on a topic people are confused about | These get saved and shared the most |
| **Weekly** | A Reel version of the brief: slides + trending audio | Reels reach non-followers, while carousels deepen engagement with followers |

Consistency beats volume. One excellent post every morning for 90 days does more than three
rushed posts a day for two weeks.

---

## 3. What Instagram rewards, and how the template uses it

- **Sends (shares by DM) and saves** are the strongest signals. That's why the editor picks stories
  with a *send test* (would you forward this to a friend or the family group?), why every story has a
  *Why it matters* line, why the caption names exactly who to send it to, and why the last slide asks
  one easy question and for Save · Share · Follow.
- **Reach to non-followers comes mostly from Reels.** Every edition also comes as `reel.mp4`. Post
  it as a **Trial Reel** (shown only to non-followers first) with a trending song, alongside the
  carousel.
- **Politics isn't recommended.** Instagram doesn't show posts about politics, governments,
  elections or protests to people who don't follow you (unless they change their settings). So the
  cover and story #1 are always non-political; political stories go further back in the carousel.
- **Time spent.** Carousels hold attention longer than single images. Seven slides of real content is the sweet spot.
- **The second chance.** If someone scrolls past, Instagram may show the carousel again starting on
  slide 2. So story #1 (slide 2) is always the most shareable story.
- **Search, not hashtags.** Instagram search reads captions and alt text. Keep captions keyword-rich
  (the tool lists every headline), fill in alt text, and use only 3–5 relevant hashtags. Instagram
  now caps posts at 5.
- **Music on carousels.** Adding a trending track makes the carousel eligible for more surfaces.
  Add it in the app when posting.
- **3:4 format** fills the new profile grid and the feed completely, so there are no bars or crops.

---

## 4. Covers and hooks that get the swipe

The cover's two lines have one job: make the reader swipe. Formulas that work:

| Formula | Red line | Charcoal line |
|---|---|---|
| Promise | *Today's biggest headlines* | *in 60 seconds* |
| Stakes | *Your EMI* | *is about to change* |
| Curiosity | *India did something* | *no one expected* |
| Number | *5 stories* | *you can't miss today* |
| Event | *Budget 2027* | *in 6 slides* |

Rules: at most 9 words, never lie about what's inside, and rotate formulas so the grid doesn't feel
repetitive. Look at which covers bring the most **reach from non-followers** and do more of those.

---

## 5. Your first 1,000 followers

1. **Show up daily for 30 days, no gaps.** Algorithms and people both reward reliability.
2. **Reply to every comment in the first hour.** It doubles the conversation and signals a live page.
   End captions with the engagement question the tool writes.
3. **Collab posts.** Instagram's Collab feature puts one post on two profiles. Offer niche creators
   (finance, tech, cricket, campus pages) a co-branded edition on their topic.
4. **Be first, but only after you've verified.** On big breaking news, a clean single-story slide within 30
   minutes can travel far. A wrong one can sink the page.
5. **Share everywhere you already are.** Post each edition to a WhatsApp Channel, Threads and your own
   Status. "Forward this to your family group" is how news spreads in India.
6. **Leave useful comments** on big news pages and creators' posts, not "follow me" spam. Curious
   people click good commenters.
7. **Pin your 3 best posts** (most saves) so new visitors immediately see your best work.
8. **Turn one edition a week into a Reel.** Use Instagram's own editor or the Edits app with trending audio.

---

## 6. Trust: the moat no one can copy

A news page lives or dies on credibility. Make these non-negotiable:

- **Accuracy over speed.** The editor only writes from source material. You still read every slide
  before it goes out. If a number looks surprising, check it.
- **Corrections policy.** When you get something wrong, post a correction in Stories and add it to
  the `Corrections` highlight. Owning mistakes earns more trust than it costs.
- **Neutral on politics.** Report what happened and what each side says. Your audience spans every party.
- **Careful wording.** Use "alleged" and "accused" for charges that haven't been proven, and attribute
  claims ("police said").
- **Tragedies:** no puns, no gore, no victims' photos from social media, and no highlighting victims' names.
- **Photo rights.** See the *Photos and copyright* section in the README. Copyright strikes are the
  most common way small news pages get restricted. When in doubt, use the typographic card.

---

## 7. Measure weekly and double down

Every Sunday, open Insights for the week's posts and note these for each one:

| Metric | What it tells you |
|---|---|
| Reach from **non-followers** | Is the cover and hook pulling in new people? |
| **Saves + shares ÷ reach** | Is the content worth keeping and sending? This is the number to grow |
| Follows from post | Did it convert? |
| Profile visits | Is the brand intriguing? |

Then change one thing at a time: cover formula, posting time (try 7:30 vs 8:30), story mix (more
money? more tech?), or summary length. Keep what moves saves and shares.

---

## 8. The 30-day launch plan

| Week | Focus |
|---|---|
| **0 (before launch)** | Pick name + handle, set `config.yaml`, post 6–9 editions quietly, set bio, highlights and profile picture |
| **1** | Go public. Daily 8 AM brief plus daily Stories quiz. Send it to 50 friends and ask them to share it with one person |
| **2** | Add the Sunday "week in 10 headlines". Reply to every comment. Start leaving thoughtful comments on bigger pages |
| **3** | First Collab post. First Reel version of the brief. Launch a WhatsApp Channel |
| **4** | First weekly review (section 7). Pin the top 3 posts. Adjust the story mix toward what gets saved |

After that: an "Explained" carousel every week, a newsletter or WhatsApp list for superfans, and,
once you have steady reach, brand partnerships like the ones the reference page runs.
