# dcsketchfest.com

The DC Sketchfest website — a plain static site (HTML + CSS + a little vanilla
JS), rebuilt off Webflow. No build step, no framework, no dependencies. Whatever
is on the `main` branch is what's live.

**Current state: 2027 is announced, applications are open, tickets are not.**
The festival runs **31 March – 3 April 2027** at MILKCRATE (Wed/Thu) and Sitar
Arts Center (Fri/Sat). Performer applications are open and close **13 December**,
taking real money through Stripe — see [The application system](#the-application-system).
There is no 2027 lineup yet and no tickets on sale; the Crowdwork calendar is
still commented out in `index.html`. The 2026, 2025 and 2024 lineups stay up as
an archive. See [Remaining to turn ticketing on](#remaining-to-turn-ticketing-on).

```
index.html                  home page
apply/index.html            performer application (talks to the Worker)
volunteer/index.html        volunteer signup
photos/index.html           photo album (generated — see below)
performers-<year>/index.html  lineup pages (generated — see below)
404.html                    not-found page
admin/, donate/,            meta-refresh redirect stubs — no nav, no footer,
  past-performers/          no analytics, nothing shared
assets/css/style.css        all site styles (the only site-wide stylesheet)
assets/css/apply.css        extra styles for the apply + volunteer forms
assets/js/main.js           mobile nav, sliders, scroll reveals, signup form
assets/js/apply.js          the whole application form — and its CONFIG block,
                            which OVERWRITES copy in apply/index.html at runtime
assets/js/volunteer.js      volunteer form (its confirmation screen lives here,
                            not in the HTML)
assets/img/                 all images (nothing loads from Webflow's CDN)
assets/lineups/<year>.json  lineup data, one file per festival
assets/lineups/gallery.json photo manifest for the album and carousel
assets/img/gallery/<year>/  festival photos (800px thumbs + 1800px full)
tools/build-lineup.py       regenerates the lineup pages from that JSON
tools/build-gallery.py      regenerates the album and the homepage carousel
tools/mailing-list.gs       Apps Script for the signup form (deploy separately)
CNAME                       custom domain for GitHub Pages
```

## Working on it locally

```bash
python3 -m http.server 4322
```

Then open <http://localhost:4322>. Edit a file, refresh. That's the whole loop.

## Deploying

Push to `main`. GitHub Pages redeploys in about a minute. There is no build
step and no CI — the committed HTML is what ships.

---

# How everything is set up

Six moving parts:

1. **GitHub** hosts the files and serves them over HTTPS.
2. **Squarespace** answers DNS for the domain.
3. **A Google Sheet** collects mailing-list signups.
4. **Google Analytics** counts visits.
5. **Crowdwork** sells the tickets.
6. **A Cloudflare Worker** runs the performer application, takes the fee, and
   can commit back into this repo.

Only the first two are needed to keep the *site* up. The sixth is the only one
that stores anything or costs real money to get wrong — it is a separate repo
and is documented at [The application system](#the-application-system).

## 1. Hosting — GitHub Pages

Three separate repos, each publishing itself to its own subdomain from `main`,
folder `/ (root)`. Each repo's `CNAME` file is what claims its hostname.

| Site | Repo | Serves |
|------|------|--------|
| Live site | [`walkergreen/dcsketchfest`](https://github.com/walkergreen/dcsketchfest) | `dcsketchfest.com` |
| Frozen 2026-brand archive | [`walkergreen/dcsketchfest-2026`](https://github.com/walkergreen/dcsketchfest-2026) | `2026.dcsketchfest.com` |
| Rebrand scratchpad | [`walkergreen/dcsketchfest-staging`](https://github.com/walkergreen/dcsketchfest-staging) | `staging.dcsketchfest.com` |

All three have a Let's Encrypt certificate issued and **Enforce HTTPS** on.
The archive and staging sites are `noindex` with a `robots.txt` disallow, so
they can't compete with the live site in search results.

Settings live at **Settings → Pages** in each repo. The certificate is issued
automatically once DNS resolves; if it never appears (the domain shows a
"not secure" warning and HTTPS serves a `*.github.io` certificate), remove the
custom domain, save, then re-add it — that re-triggers provisioning. That is
the fix, not a DNS change.

## 2. DNS — Squarespace Domains

`dcsketchfest.com` is registered at **Squarespace Domains** (inherited from
Google Domains) and uses Google's nameservers. The zone is *not* in any GCP
project, so records must be edited in the Squarespace panel — there is no API
path to it.

Current records:

| Type  | Name      | Value                   | Why |
|-------|-----------|-------------------------|-----|
| A     | `@`       | `185.199.108.153`       | GitHub Pages |
| A     | `@`       | `185.199.109.153`       | GitHub Pages |
| A     | `@`       | `185.199.110.153`       | GitHub Pages |
| A     | `@`       | `185.199.111.153`       | GitHub Pages |
| CNAME | `www`     | `walkergreen.github.io` | redirects to the bare domain |
| CNAME | `2026`    | `walkergreen.github.io` | archive site |
| CNAME | `staging` | `walkergreen.github.io` | staging site |

Every hostname points at `walkergreen.github.io`; GitHub decides which repo to
serve by matching the requested hostname against each repo's `CNAME` file. That
is why adding a new subdomain is two steps: a CNAME here, and a `CNAME` file in
the repo that should answer it.

> **Never touch the MX or TXT records.** `admin@dcsketchfest.com` is Google
> Workspace, and its 5 MX records plus the SPF (`v=spf1 include:_spf.google.com
> ~all`) and DMARC entries live in this same zone. Deleting them takes down
> festival email, which is a far worse outage than the website being down.

### Canonical host

The bare domain is canonical — that's what `CNAME` holds, and `www` redirects
to it. Every absolute URL in the site (canonical tags, `og:url`, `sitemap.xml`,
`robots.txt`) points at the bare domain to match. If the custom domain is ever
switched to `www`, those all need updating too, or search engines get
contradictory signals.

## 3. Email marketing — Google Sheet + Apps Script

The signup form on the homepage posts to a Google Apps Script web app, which
appends a row to a Google Sheet. No Mailchimp, no third-party account, no
monthly fee, and the list stays in the festival's own Drive.

**This is already wired up and collecting.** The pieces:

| Piece | Where |
|-------|-------|
| The form | `index.html`, `<form class="signup">`, its `data-endpoint` holds the `/exec` URL |
| The script | `tools/mailing-list.gs` — the copy of record; the running copy is pasted into Apps Script |
| The Sheet | ID `1Ie3SdfTFCmJSqegK4n_zG5mf26puzopWpDWgP-ISiXQ`, tab `Signups` |

Columns are `Timestamp, Email, Name, Source, User agent`. The script validates
the address, skips duplicates case-insensitively, and takes a lock so two
simultaneous signups can't overwrite each other. The form carries a honeypot
field that bots fill and humans never see; those submissions are accepted in
the UI and silently dropped.

**To send an actual email blast**, export the Sheet (File → Download → CSV) and
import it into whatever sends the mail. Nothing in this repo sends email.

### If you change the script

Edit `tools/mailing-list.gs` here *and* in Apps Script, then **Deploy → Manage
deployments → edit → New version**. Without a new version the live URL keeps
running the old code — the single most common way this quietly stops working.

### If you ever rebuild it from scratch

1. Create a Sheet in the DCSF Google account.
2. **Extensions → Apps Script**, paste in `tools/mailing-list.gs`, and set
   `SHEET_ID` to that Sheet's id.
3. **Deploy → New deployment → Web app**, *Execute as:* **Me**,
   *Who has access:* **Anyone** — it must be "Anyone", not "Anyone with a
   Google account", or the form gets a 401 and every signup fails silently.
4. Authorise it (the "unverified app" warning is expected for your own script:
   *Advanced → Go to … (unsafe)*).
5. Put the `/exec` URL into the form's `data-endpoint` in `index.html`.

If `data-endpoint` is ever emptied, the form degrades gracefully: it still
renders and tells people to email `admin@dcsketchfest.com`.

## 4. Analytics — Google Analytics 4

Measurement ID **`G-5WTXCDDHMK`** (GA4). Reports are in the GA dashboard under
the DCSF Google account; nothing is stored in this repo.

The tag is on **four pages, not every page**:

| Page | Tag? |
|------|------|
| `index.html` | yes |
| `404.html` | yes |
| `apply/index.html` | yes |
| `photos/index.html` | yes — generated from `GA_TAG` in `build-gallery.py` |
| `performers-2024/2025/2026` | **no** — `build-lineup.py` has no slot for one |
| `volunteer/index.html` | **no** |
| `admin/`, `donate/`, `past-performers/` | no — redirect stubs, correctly excluded |

So the lineup pages and the volunteer page are **not** being measured. To put a
tag on the lineup pages, add it to the `PAGE` template in `build-lineup.py`
before the `<title>` and rerun — one edit covers all three.

**To change the measurement ID**, edit these four and rerun `build-gallery.py`:

```
index.html:7-15
404.html:7-15
apply/index.html:7-15
tools/build-gallery.py:38-47     (the GA_TAG constant → regenerates photos/)
```

`assets/js/apply.js` also fires `gtag('event', …)` in four places, but it is
guarded by `if (window.gtag)` and reads no ID, so an ID change needs no edit
there. **Swapping to a different analytics provider does**, making it a fifth
place.

To verify it is really reporting (rather than just present in the HTML), open
the site with devtools on the Network tab and look for a request to
`analytics.google.com/g/collect` carrying `tid=G-5WTXCDDHMK`. The tag being in
the page source is not proof it fires.

## 5. Ticketing — Crowdwork

Tickets are **not** sold by this site. They are sold by
[Crowdwork](https://crowdwork.com), under the theatre handle
`dcsketchfest`. The homepage embeds Crowdwork's calendar, which pulls shows
straight from that account:

```html
<script id="fw_script" src="https://crowdwork.com/embed.js?v=6"
        data-theatre="dcsketchfest" data-type="shows" data-view="calendar"
        data-start-date="2027-03-01"></script>
```

**Shows, prices, and on-sale dates are managed in the Crowdwork account, not
here.** Publish a show there and it appears on the site by itself; nothing in
this repo needs a commit for a lineup or on-sale change.

Between festivals that embed is **commented out** in `index.html` and a
"2027 is coming" panel stands in its place, because an empty calendar looks
broken. To turn ticketing back on, follow step 1 of
[Remaining to turn ticketing on](#remaining-to-turn-ticketing-on): delete the
`.coming-soon` panel and uncomment the block marked `<!-- TICKETS:`.

Donations are separate and go through Givebutter
(`givebutter.com/dcsketchfest2027`), linked from the Donate button in the nav.

## The application system

The performer application is **not** part of this repo. `apply/index.html` and
`assets/js/apply.js` are just the front end; everything behind them is a single
Cloudflare Worker in a separate private repo,
[`walkergreen/dcsketchfest-judges-app`](https://github.com/walkergreen/dcsketchfest-judges-app).

| Piece | Where |
|-------|-------|
| Worker | `dcsketchfest-app.walker-df2.workers.dev` (Cloudflare) |
| Database | Cloudflare D1, `dcsketchfest` — the source of truth |
| Payments | **Stripe, live mode.** $25 + 6% DC tax + card fee = **$27.61** |
| Email | Resend, from `admin@send.dcsketchfest.com` (the apex is *not* verified) |
| Mirrors | an Airtable base and a Google Sheet, both best-effort copies |
| Alerts | Slack `#applicants`, on submission only |

**The fee is pinned when an application is submitted**, not when it is paid, so
changing the price does not re-bill anyone who already submitted.

### Three places hold the same festival facts

Dates, venues, deadlines and the fee appear on `/apply/` three times over, and
they must agree:

1. **`assets/js/apply.js`**, the `CONFIG` block (~lines 26–63). This is the
   source of truth for what a visitor *sees* — it overwrites the five
   `data-cfg` elements, the `<title>`, the deadlines panel and the availability
   checkboxes at runtime. **Editing `apply/index.html` alone changes nothing.**
2. **`apply/index.html`**'s meta tags (`description`, `og:title`,
   `og:description`, `og:image`). JS never touches these, so they are
   authoritative — they drive every share card and search result.
3. **The Worker's D1 settings.** The Worker is what actually enforces the fee
   and the open/closed phase. The other two only *describe* it.

Get 1 and 3 out of step and the page advertises one price while the card is
charged another.

### The Worker can commit into this repo

The Worker's admin has a small CMS at `/admin/site/publish` that rewrites
**7 shared values** across **11 files here** (9 HTML files plus both
generators) and commits the result via the GitHub API, which redeploys Pages.
The values are things like the contact address, the donate URL, the festival
dates and the December 13 close date.

Three things to know before trusting it:

- **It cannot reach `assets/js/apply.js` or `assets/js/main.js`.** Those hold
  ~14 more copies of the contact address and 5 more of "December 13", so a
  publish leaves them stale.
- **Exact-string replacement can't catch the dates**, which are spelled at
  least six different ways across the repo (`March 31 - April 3, 2027`,
  `March 31&ndash;April 3, 2027`, `March 31–April 3, 2027`, and prose forms).
- **A publish that matches nothing still reports success.** It records the new
  value and prints "Published to 0 file(s)" — after which the old string it was
  searching for is gone from the database and the value can no longer be fixed
  through the UI. If you see "0 file(s)", treat it as a failure.

**Do not hand-edit a CMS-managed value in a generated page.** The edit survives
the next publish, then the next generator run reverts it, and at that point the
value is permanently out of reach of the CMS.

## Where a change has to be made

There is no include system, so shared markup is copied. **How many places a
change touches depends entirely on what kind of change it is** — anywhere from
one file to six. Check this table before editing anything shared.

| Change | Places | Where |
|--------|--------|-------|
| **Colours, type, spacing, any CSS rule** | **1** | `assets/css/style.css` — nothing else, no rebuild |
| **Shared JS behaviour** (nav drawer, sliders, reveals) | **1–2** | `assets/js/main.js`, usually plus `style.css` (main.js only flips classes; the visible behaviour is the CSS) |
| **Nav link, hamburger, brand** | **5–6** | `index.html`, `apply/index.html`, `volunteer/index.html`, `tools/build-lineup.py`, `tools/build-gallery.py` — which has *two* copies, a `NAV` const and its own `WORDMARK` const |
| **Footer** | **5** | the same five. They have already drifted — see below |
| **Analytics tag** | **4** | `index.html`, `404.html`, `apply/index.html`, `tools/build-gallery.py` |
| **Lineup page markup** | **1** | `tools/build-lineup.py`, then rerun |
| **Photo album / Fest Pics carousel** | **1** | `tools/build-gallery.py`, then rerun |
| **Festival copy on `/apply/`** | **3 surfaces** | `assets/js/apply.js` CONFIG, the page's own meta tags, **and** the Worker's D1 settings — see [The application system](#the-application-system) |

`404.html` has no nav and no footer, so it is **not** one of the five for those.
`admin/`, `donate/` and `past-performers/` are meta-refresh redirect stubs — no
nav, no footer, no analytics, nothing shared.

After editing either generator, rerun it and commit the output:

```bash
python3 tools/build-lineup.py && python3 tools/build-gallery.py
```

Both are idempotent — rerunning with no source change produces byte-identical
output, so it is always safe to run them to check.

### Which files are generated

Only four files are generated, and they must never be hand-edited:

| Generated file | Written by |
|----------------|-----------|
| `performers-2024/index.html` | `tools/build-lineup.py` (whole file) |
| `performers-2025/index.html` | `tools/build-lineup.py` (whole file) |
| `performers-2026/index.html` | `tools/build-lineup.py` (whole file) |
| `photos/index.html` | `tools/build-gallery.py` (whole file) |

Plus one *region* of a hand-maintained file: `index.html` lines between
`<!-- GALLERY:start -->` and `<!-- GALLERY:end -->` are rewritten by
`build-gallery.py`. The rest of `index.html` — including its `<head>` and its
analytics tag — is hand-maintained and safe to edit.

Everything else is hand-maintained: `index.html`, `404.html`, `apply/index.html`,
`volunteer/index.html`, and the three redirect stubs.

### Known drift

The copied blocks are no longer identical, because they were edited separately:

- The design credit reads **"Design by"** in `index.html` and `build-gallery.py`,
  **"Designed by"** in `apply/` and `volunteer/`, and is **missing entirely** from
  `build-lineup.py` — so the three performers pages have no credit line.
- The footer logo is an inline SVG wordmark in `index.html` and `build-gallery.py`,
  but an `<img>` of `logo-2027-light.png` in `build-lineup.py`, `apply/` and
  `volunteer/`.
- **The three performers pages carry no analytics at all.** They are the only
  real pages with no tag, because `build-lineup.py` has no slot for one.

Fixing any of these means touching all five places, which is the point of the
table above.

> **Watch the braces.** `build-lineup.py`'s page template is a `.format()`
> string and `build-gallery.py`'s is an f-string. Any snippet containing a
> literal `{` or `}` — the Google Analytics tag, most JavaScript — will be
> mangled or throw if pasted inline. Define it as a module-level constant and
> pass it through a placeholder, the way `GA_TAG` is wired.

## Common edits

**Change dates, venue, FAQ answers, testimonials** — edit `index.html`. Each
section is marked with a comment banner (`<!-- ==== faq ==== -->` and so on).

**Change a lineup, or add a year** — lineups live in `assets/lineups/<year>.json`,
one file per festival (2026, 2025, 2024). Edit one, or drop in a new
`2027.json`, then:

```bash
python3 tools/build-lineup.py
```

That rewrites every `performers-<year>/index.html` and rebuilds the year
switcher from whatever files exist, so a new year needs no template edits — just
add its dates and venue to the `YEARS` dict at the top of the script. Commit the
JSON and the generated HTML together.

Performer images live in `assets/img/performers-<year>/`; the `local` field in
each entry points at one. `city` and `link` are optional — cards drop the line
when they're empty.

**Change the photos** — the album at `/photos/` and the homepage Fest Pics
carousel are both generated from `assets/lineups/gallery.json`:

```bash
python3 tools/build-gallery.py
```

Each entry holds a team name, a date, and paths to a thumbnail (800px) and a
full-size image (1800px) under `assets/img/gallery/<year>/`. To swap what the
homepage carousel shows, edit the `CAROUSEL` list at the top of
`tools/build-gallery.py` — it names photos by team, so reprocessing the images
can't silently reshuffle the front page. To add a year, add its photos, add an
entry to `YEARS` in the same script, and rerun it. Commit the JSON, the images,
and the generated `photos/index.html` together.

Photos are by Mikail Faalasli; the originals live in the festival's Google
Drive (roughly 32 GB of raw JPEGs across 2025 and 2026, plus a 2024 folder) and
are deliberately not in this repo — only the resized web copies are.

**Change colors or type** — the palette is a block of CSS variables at the top of
`assets/css/style.css`:

| Variable   | Value     | Used for                                     |
|------------|-----------|----------------------------------------------|
| `--blue`   | `#2b3fbf` | hero, fest pics, Mumbie, lineup page heroes  |
| `--pink`   | `#ef4d8e` | press + FAQ backgrounds, accents, shadows    |
| `--yellow` | `#ffc933` | ticker, testimonials, buttons                |
| `--paper`  | `#f6efe1` | paper backgrounds, navbar, light text        |
| `--ink`    | `#211b3a` | text, borders, newsletter + footer           |

The pre-2027 names (`--red`, `--cream`, `--teal`, `--purple`, `--dark`) are
aliased onto these inks so older inline styles and generated pages keep
working — change the new variables, not the aliases.

Fonts are Anton (display) and Space Grotesk (body), loaded from Google Fonts.

### The logo

In the header and footer the logo is **not an image** — it is live text set in
Anton plus an inline SVG of the DC flag (three stars over two bars), assembled
by `.wordmark` / `.wordmark-flag` in the stylesheet. That keeps it crisp at any
size and recolourable per background, which is why the footer version is cream
and the header version is ink.

For anywhere outside the website — posters, socials, a partner asking for "your
logo" — use the standalone files, which carry the same lockup with the type
converted to outlines so they need no font installed:

| File | Use on |
|------|--------|
| `assets/img/brand/logo-wordmark.svg` | light backgrounds (ink type) |
| `assets/img/brand/logo-wordmark-light.svg` | dark backgrounds (cream type) |

The flag is `--pink` in both. They were generated from the live CSS lockup and
match the desktop header to within half a percent.

Two caveats. The CSS gap between the flag and the words is a fixed `7.2px`
rather than an em value, so the on-site lockup is slightly tighter at large
sizes than at small ones; the SVG files use a fixed `0.30em`, matching the
desktop header. And the old 2026 PNG logos (`logo-wide.png`, `logo-stacked.png`)
are still in `assets/img/brand/` — nothing on the site renders them, but the
`Organization` JSON-LD block in `index.html` still points `logo` at
`logo-stacked.png`, so that needs a new raster export before it is accurate. The 2026-brand site is archived at
[2026.dcsketchfest.com](https://2026.dcsketchfest.com)
(github.com/walkergreen/dcsketchfest-2026).

## Remaining to turn ticketing on

Most of the 2027 rollover is **already done**: the hero, the ticker, the FAQ,
the venue cards with both addresses, the `Festival` JSON-LD with `startDate`/
`endDate` and two `Place` entries, and the nav's Past Lineups pointing at
`/performers-2026/`.

What is left:

1. **Ticket calendar** — in `#about-section` in `index.html`, delete the
   `<div class="coming-soon">` panel and uncomment the block marked
   `<!-- TICKETS:` just below it. `data-start-date` is already `2027-03-01`.
   The calendar pulls shows straight from Crowdwork, so it fills in on its own
   once shows are published there. Nothing else needs a commit for a ticket change.

   Note that uncommenting this adds a **third** runtime-overwritten region to
   the site: the placeholder copy inside that container is not in any HTML file,
   it is `assets/css/style.css` (`.crowdwork-embed:empty::after`).

2. **2027 lineup** — add `assets/lineups/2027.json`, add a `"2027"` entry to the
   `YEARS` dict in `tools/build-lineup.py`, and run it. The page and the year
   switcher build themselves. Then drop the `.archive-note` paragraph from the
   template (`build-lineup.py:109`) once 2027 is current.

3. **sitemap.xml** — it currently lists only `/`, `/photos/` and the three
   lineup pages. **`/apply/` and `/volunteer/` are live and linked from the nav
   but missing from it**, and the 2027 lineup URL will need adding too.

4. **Analytics on the pages that have none** — the three lineup pages and
   `/volunteer/` are unmeasured. See [4. Analytics](#4-analytics--google-analytics-4).

## Third-party pieces at a glance

Everything the site talks to, and where it is documented:

| Piece | Account | Details |
|-------|---------|---------|
| Hosting | GitHub | [1. Hosting](#1-hosting--github-pages) |
| DNS | Squarespace Domains | [2. DNS](#2-dns--squarespace-domains) |
| Mailing list | Google Sheet + Apps Script | [3. Email marketing](#3-email-marketing--google-sheet--apps-script) |
| Analytics | Google Analytics 4, `G-5WTXCDDHMK` | [4. Analytics](#4-analytics--google-analytics-4) |
| Tickets | Crowdwork, `dcsketchfest` | [5. Ticketing](#5-ticketing--crowdwork) |
| Applications | Cloudflare Worker + D1 | [The application system](#the-application-system) |
| Application fees | **Stripe, live mode** | $27.61 all-in; separate repo |
| Transactional email | Resend | sends from `send.dcsketchfest.com`, *not* the apex |
| Applicant mirrors | Airtable + a Google Sheet | best-effort copies of D1 |
| Applicant alerts | Slack `#applicants` | on submission only |
| Donations | Givebutter, `dcsketchfest2027` | Donate button in the nav of every real page |
| Fonts | Google Fonts | Anton + Space Grotesk, loaded per page |
| Email | Google Workspace | `admin@dcsketchfest.com` — **MX records live in the same DNS zone** |

**Legacy note:** the pre-rebuild signup list lived in the Webflow dashboard
under Forms and was never in this repo. Export it before that account lapses if
it hasn't been exported already — those addresses are not in the Sheet.

## Notes

- Images were pulled from Webflow's CDN and resized for the web (5 MB total, down
  from 21 MB of originals). Nothing on the site depends on Webflow staying up.
- The sliders are CSS scroll-snap with arrow buttons — they work with touch,
  trackpad, and keyboard, and degrade to a plain scroller if JS fails.
- Scroll-reveal animations respect `prefers-reduced-motion`.
