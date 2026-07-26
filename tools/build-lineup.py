#!/usr/bin/env python3
"""Regenerate performers-2026/index.html from assets/performers.json.

The generated HTML is committed, so the site needs no build step to deploy.
Run this only when the lineup changes:

    python3 tools/build-lineup.py

Each entry in assets/performers.json looks like:

    {
      "name":  "Bad Medicine",
      "city":  "Washington, DC",
      "slug":  "bad-medicine",
      "blurb": "...",
      "local": "assets/img/performers/bad-medicine.avif"
    }
"""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "assets" / "performers.json"
OUT = ROOT / "performers-2026" / "index.html"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2026 Lineup - DC Sketchfest</title>
<meta name="description" content="The {count} sketch comedy teams who performed at DC Sketchfest 2026, March 25-28 at The DC Arts Center in Washington, DC. The 2027 lineup is announced after dates go public.">

<meta property="og:type" content="website">
<meta property="og:url" content="https://www.dcsketchfest.com/performers-2026/">
<meta property="og:title" content="2026 Lineup - DC Sketchfest">
<meta property="og:description" content="The {count} sketch comedy teams who performed at DC Sketchfest 2026, March 25-28 at The DC Arts Center.">
<meta property="og:image" content="https://www.dcsketchfest.com/assets/img/brand/og-image.avif">
<meta name="twitter:card" content="summary_large_image">

<link rel="canonical" href="https://www.dcsketchfest.com/performers-2026/">
<link rel="icon" href="/assets/img/brand/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/img/brand/favicon-256.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Londrina+Solid:wght@300;400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
<a class="skip-link" href="#lineup">Skip to the lineup</a>

<header class="navbar">
  <div class="nav-inner">
    <div class="nav-bar">
      <a href="/" class="brand" aria-label="DC Sketchfest home">
        <img src="/assets/img/brand/logo-wide.png" alt="DC Sketchfest" width="192" height="50">
      </a>

      <nav id="nav-links" class="nav-links" aria-label="Main">
        <a class="nav-link" href="/#about-section">2027</a>
        <a class="nav-link" href="/performers-2026/" aria-current="page">Past Lineup</a>
        <a class="nav-link" href="/#faq-section">FAQ</a>
        <a class="nav-link" href="mailto:admin@dcsketchfest.com?subject=Question">Contact</a>
      </nav>

      <a class="btn nav-donate-desktop" href="https://givebutter.com/dcsketchfest2026"><span>Donate</span></a>

      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav-links" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</header>

<main>
<section class="section lineup-hero">
  <div class="pad pad-sm">
    <div class="container">
      <h1 class="h-lg text-white">2026 <span class="text-yellow">Performers</span></h1>
      <p class="body-copy text-white" style="margin-top:1rem">{count} teams &middot; March 25&ndash;28, 2026 &middot; The DC Arts Center</p>
      <p class="archive-note">This is the lineup from the 2026 festival. DC Sketchfest returns in 2027 &mdash; dates are announced this fall, and the new lineup follows. <a href="/#newsletter-section">Get on the list</a> to hear first.</p>
    </div>
  </div>
</section>

<section id="lineup" class="section lineup-section">
  <div class="pad pad-md">
    <div class="container">
      <div class="performer-grid">
{cards}
      </div>
    </div>
  </div>
</section>

<section class="section section--teal">
  <div class="pad pad-sm">
    <div class="container text-center">
      <h2 class="h-sm text-white">Don&rsquo;t miss 2027</h2>
      <div class="btn-row" style="margin-top:1.5rem">
        <a class="btn btn--yellow" href="/#newsletter-section"><span>Get Updates</span></a>
      </div>
    </div>
  </div>
</section>
</main>

<footer class="footer">
  <div class="pad pad-sm">
    <div class="container footer-wrapper">
      <a class="footer-logo" href="/" title="Homepage">
        <img src="/assets/img/brand/logo-stacked.png" alt="DC Sketchfest" loading="lazy">
      </a>
      <div class="footer-social">
        <div class="join-us">Follow us on social media!</div>
        <div class="social-links">
          <a href="https://facebook.com/dcsketchfest" target="_blank" rel="noopener">fb</a>
          <a href="https://instagram.com/dcsketchfest" target="_blank" rel="noopener">insta</a>
        </div>
      </div>
    </div>
  </div>
</footer>

<script src="/assets/js/main.js" defer></script>
</body>
</html>
"""

CARD = """        <article class="performer-card">
          <img src="/{image}" alt="{alt}" loading="lazy" width="400" height="250">
          <div class="performer-card__body">
            <h2 class="performer-card__name">{name}</h2>
            <p class="performer-card__city">{city}</p>
            <p class="performer-card__blurb">{blurb}</p>
          </div>
        </article>"""


def main() -> None:
    performers = json.loads(DATA.read_text())
    performers.sort(key=lambda p: p["name"].lower())

    cards = "\n".join(
        CARD.format(
            image=p["local"],
            alt=html.escape("%s promotional image" % p["name"], quote=True),
            name=html.escape(p["name"]),
            city=html.escape(p["city"]),
            blurb=html.escape(p["blurb"]).replace("\n", "<br>"),
        )
        for p in performers
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(PAGE.format(count=len(performers), cards=cards))
    print("wrote %s (%d performers)" % (OUT.relative_to(ROOT), len(performers)))


if __name__ == "__main__":
    main()
