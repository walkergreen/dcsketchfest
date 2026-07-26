# dcsketchfest.com

The DC Sketchfest website — a plain static site (HTML + CSS + a little vanilla
JS), rebuilt off Webflow. No build step, no framework, no dependencies. Whatever
is on the `main` branch is what's live.

**Current state: between festivals.** The site is framed around "back in 2027,
dates announced this fall." There are no tickets on sale and no 2027 lineup; the
2026 lineup stays up as an archive. See [Turning the festival back on](#turning-the-festival-back-on)
when dates are set.

```
index.html                  home page
performers-2026/index.html  the lineup (generated — see below)
404.html                    not-found page
assets/css/style.css        all styles
assets/js/main.js           mobile nav, sliders, scroll reveals
assets/img/                 all images (nothing loads from Webflow's CDN)
assets/performers.json      lineup data
tools/build-lineup.py       regenerates the lineup page from that JSON
CNAME                       custom domain for GitHub Pages
```

## Working on it locally

```bash
python3 -m http.server 4322
```

Then open <http://localhost:4322>. Edit a file, refresh. That's the whole loop.

## Deploying

Push to `main`. GitHub Pages redeploys in about a minute.

### First-time setup

1. Create a repo on GitHub and push this folder to it:

   ```bash
   git init && git add -A && git commit -m "Rebuild dcsketchfest.com off Webflow"
   git branch -M main
   git remote add origin git@github.com:YOUR-ORG/dcsketchfest.git
   git push -u origin main
   ```

2. In the repo: **Settings → Pages → Source: Deploy from a branch**, branch
   `main`, folder `/ (root)`.

3. Point DNS at GitHub. At your registrar, for `dcsketchfest.com`:

   | Type  | Name  | Value                    |
   |-------|-------|--------------------------|
   | CNAME | `www` | `YOUR-ORG.github.io`     |
   | A     | `@`   | `185.199.108.153`        |
   | A     | `@`   | `185.199.109.153`        |
   | A     | `@`   | `185.199.110.153`        |
   | A     | `@`   | `185.199.111.153`        |

   The `CNAME` file in this repo already claims `www.dcsketchfest.com`. Once DNS
   resolves, tick **Enforce HTTPS** in Settings → Pages.

4. Cancel the Webflow plan **after** the new site is confirmed live.

## Common edits

**Change dates, venue, FAQ answers, testimonials** — edit `index.html`. Each
section is marked with a comment banner (`<!-- ==== faq ==== -->` and so on).

**Change the lineup** — edit `assets/performers.json`, then:

```bash
python3 tools/build-lineup.py
```

That rewrites `performers-2026/index.html`. Commit both files. Performer images
live in `assets/img/performers/`; the `local` field in the JSON points at one.
(The 2026 page is an archive now — see [Turning the festival back on](#turning-the-festival-back-on)
for building a 2027 page alongside it.)

**Change colors or type** — the palette is a block of CSS variables at the top of
`assets/css/style.css`:

| Variable   | Value     | Used for                                  |
|------------|-----------|-------------------------------------------|
| `--red`    | `#df3d23` | hero, press, FAQ backgrounds              |
| `--cream`  | `#f6ede4` | tickets, venue backgrounds; button text   |
| `--teal`   | `#19647e` | buttons, fest pics, Mumbie, footer        |
| `--yellow` | `#f4d35e` | navbar pill, testimonials, accents        |
| `--purple` | `#5541ba` | secondary buttons, testimonial quotes     |
| `--dark`   | `#211509` | body text, borders                        |

Fonts are Londrina Solid (display) and Inter (body), loaded from Google Fonts.

## Turning the festival back on

When the 2027 dates are public, in order:

1. **Homepage hero** (`index.html`) — replace `Back in 2027 / Dates announced
   this fall` with the real dates and venue. Point the first button back at
   `#about-section` and relabel it `Get Tickets`.
2. **Ticket calendar** — in the `#about-section` block, delete the
   `<div class="coming-soon">` panel and uncomment the block below it marked
   `<!-- TICKETS:`. Set `data-start-date` to the new year (it's already
   `2027-03-01`). The calendar pulls shows straight from Crowdwork, so it fills
   in on its own once shows are published there.
3. **FAQ** — update "When is the 2027 festival?" and "Where do I get tickets?".
4. **Venue** — the `#where-section` copy currently says the 2027 venue is
   confirmed with the dates. Once it's locked, change the heading back to
   `We're back at`.
5. **Lineup** — put the new teams in `assets/performers.json`, change `OUT` in
   `tools/build-lineup.py` to `performers-2027/index.html`, drop the
   `.archive-note` paragraph from the template, and run it. Keep
   `performers-2026/` in place as the archive and relabel the nav link.
6. **Structured data** — swap the `Organization` JSON-LD block in `index.html`
   back to a `Festival` block with `startDate`/`endDate`/`location`. The old one
   is in git history.
7. **sitemap.xml** — add the new lineup URL.

## Third-party pieces

- **Tickets** — the Crowdwork calendar embed in `index.html`
  (`crowdwork.com/embed.js`, `data-theatre="dcsketchfest"`), currently commented
  out. Unchanged from the Webflow site; it pulls shows from the Crowdwork
  account, so the lineup and on-sale dates are managed there, not here.
- **Donate** — links to `givebutter.com/dcsketchfest2026`.
- **Map** — a keyless Google Maps embed iframe.

### Mailing list signup — not wired up yet

The Webflow form is gone (Webflow was collecting those submissions). The
newsletter section currently shows a placeholder pointing people at
`admin@dcsketchfest.com`.

To switch it to a Google Form:

1. Build the form in Google Forms (Name + Email). Responses land in a Sheet.
2. **Send → `<>` (embed)** and copy the `src` URL.
3. In `index.html`, find the `<!-- SIGNUP FORM` comment in the newsletter
   section, uncomment the `<iframe>`, paste your URL in, and delete the
   `<div class="form-fallback">` block below it.

**Before shutting Webflow down, export the existing signup list** — those
submissions live in the Webflow dashboard under Forms and are not in this repo.

## Notes

- Images were pulled from Webflow's CDN and resized for the web (5 MB total, down
  from 21 MB of originals). Nothing on the site depends on Webflow staying up.
- The sliders are CSS scroll-snap with arrow buttons — they work with touch,
  trackpad, and keyboard, and degrade to a plain scroller if JS fails.
- Scroll-reveal animations respect `prefers-reduced-motion`.
