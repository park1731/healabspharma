#!/usr/bin/env python3
"""
Heal Labs Pharma — static site generator.

Reads  : healabspharma/data/{site,products}.json
Writes : index.html, 404.html, healabspharma/frontend/html/**.html,
         sitemap.xml, robots.txt

No third-party dependencies — plain Python 3. Run after editing any data file:

    python3 healabspharma/build/build.py

Edit content in the JSON files, never in the generated HTML.
"""

import hashlib
import html
import json
import os
import re
from datetime import date
from urllib.parse import quote

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "healabspharma", "data")

CSS = "/healabspharma/frontend/css/site.css"
JS = "/healabspharma/frontend/scripts/site.js"
IMG = "/healabspharma/images"
PRODUCT_DIR = "/healabspharma/frontend/html/products"

SITE = json.load(open(os.path.join(DATA, "site.json"), encoding="utf-8"))
PRODUCTS = sorted(
    json.load(open(os.path.join(DATA, "products.json"), encoding="utf-8")),
    key=lambda p: p.get("order", 0),
)

CO = SITE["company"]
CONTACT = SITE["contact"]
ADDR = CONTACT["address"]
BASE = CO["baseUrl"].rstrip("/")

PAGES = {
    "home":     "/index.html",
    "about":    "/healabspharma/frontend/html/aboutus.html",
    "products": "/healabspharma/frontend/html/products.html",
    "contact":  "/healabspharma/frontend/html/contact.html",
}
NAV = [("home", "Home"), ("about", "About"), ("products", "Products"), ("contact", "Contact")]

TEL = CONTACT["phones"][0]
TEL_RAW = TEL.replace(" ", "")
WA = "https://wa.me/%s" % CONTACT["whatsapp"]


def e(t):
    """Escape for HTML text/attribute context."""
    return html.escape(str(t), quote=True)


def href(key):
    return "/" if key == "home" else PAGES[key]


def canonical(key):
    """`key` is a PAGES name, or a literal path for generated product pages."""
    if key in PAGES:
        return BASE + ("/" if key == "home" else PAGES[key])
    return BASE + key


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("&", "and")).strip("-")


def product_url(p):
    return "%s/%s.html" % (PRODUCT_DIR, p["slug"])


def area_url(name):
    return "%s?area=%s" % (PAGES["products"], slug(name))


# ------------------------------------------------------- catalogue facts ---
def _ordered_unique(seq):
    out = []
    for x in seq:
        if x not in out:
            out.append(x)
    return out


CAT_META = {c["name"]: c for c in SITE.get("categories", [])}
CATEGORIES = _ordered_unique([c["name"] for c in SITE.get("categories", [])] +
                             [p["category"] for p in PRODUCTS])
CATEGORIES = [c for c in CATEGORIES if any(p["category"] == c for p in PRODUCTS)]
FORM_ORDER = ["Tablet", "Capsule", "Suspension", "Syrup", "Drops", "Injection"]
FORMS = sorted(set(p["form"] for p in PRODUCTS),
               key=lambda f: (FORM_ORDER.index(f) if f in FORM_ORDER else 99, f))

# Only molecules that actually appear in a product description make the
# ticker — so it can never advertise something the range does not contain.
_ALL_DESC = " ".join(p["description"] for p in PRODUCTS).lower()
MOLECULES = [m for m in SITE.get("molecules", []) if m.lower() in _ALL_DESC]


def in_cat(cat):
    return [p for p in PRODUCTS if p["category"] == cat]


def count_in(cat):
    return len(in_cat(cat))


def forms_in(cat):
    return [f for f in FORMS if any(p["category"] == cat and p["form"] == f for p in PRODUCTS)]


def picks(cat, n):
    """Featured products of a category first, then catalogue order."""
    ps = in_cat(cat)
    return (sorted(ps, key=lambda p: not p.get("featured")))[:n]


# ---------------------------------------------------------------- icons ----
ICONS = {
    "shield":   '<path d="M12 2 4 5v6c0 5 3.4 9.1 8 11 4.6-1.9 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    "truck":    '<path d="M1 4h13v12H1z"/><path d="M14 8h4l3 3v5h-7V8Z"/><circle cx="5.5" cy="18.5" r="2"/><circle cx="17.5" cy="18.5" r="2"/>',
    "flask":    '<path d="M9 2v6L4 18a2 2 0 0 0 1.8 3h12.4A2 2 0 0 0 20 18L15 8V2"/><path d="M8 2h8"/><path d="M6.5 14h11"/>',
    "headset":  '<path d="M3 14v-3a9 9 0 0 1 18 0v3"/><path d="M21 15a2 2 0 0 1-2 2h-1v-6h1a2 2 0 0 1 2 2v2Z"/><path d="M3 15a2 2 0 0 0 2 2h1v-6H5a2 2 0 0 0-2 2v2Z"/><path d="M21 17v1a4 4 0 0 1-4 4h-3"/>',
    "heart":    '<path d="M20.8 5.6a5.5 5.5 0 0 0-7.8 0L12 6.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8Z"/><path d="M3.5 12h4l2-3 3 6 2-3h6"/>',
    "handshake": '<path d="m11 17 2 2a1.4 1.4 0 0 0 2-2"/><path d="m14 16 2.5 2.5a1.4 1.4 0 0 0 2-2l-4-4"/><path d="m8 13 2-2 4 4"/><path d="M3 11 7 7h4l3 3"/><path d="m21 11-4-4h-3l-2 2"/>',
    "leaf":     '<path d="M11 20A7 7 0 0 1 4 13c0-6 5-10 16-10 0 10-5 14-9 14Z"/><path d="M4 21c2-6 6-9 11-10"/>',
    "check":    '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "tick":     '<path d="m5 12 5 5 9-10"/>',
    "mail":     '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/>',
    "phone":    '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
    "pin":      '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "clock":    '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "whatsapp": '<path d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Z"/><path d="M8.5 7.5c.3 0 .6.2.8.6l.7 1.5c.1.3 0 .6-.2.8l-.5.5a7 7 0 0 0 3.3 3.3l.5-.5c.2-.2.5-.3.8-.2l1.5.7c.4.2.6.5.6.8 0 1-.8 1.8-1.8 1.8A8.2 8.2 0 0 1 6.7 9.3c0-1 .8-1.8 1.8-1.8Z"/>',
    "search":   '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "zoom":     '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/>',
    "chevright": '<path d="m9 6 6 6-6 6"/>',
    "chevup":   '<path d="m18 15-6-6-6 6"/>',
    "chevdown": '<path d="m6 9 6 6 6-6"/>',
    "close":    '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "arrow":    '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrowup":  '<path d="M7 17 17 7"/><path d="M8 7h9v9"/>',
    "alert":    '<circle cx="12" cy="12" r="10"/><path d="M12 8v5"/><path d="M12 16h.01"/>',
    "target":   '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "eye":      '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    "send":     '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "spark":    '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
    "microbe":  '<circle cx="12" cy="12" r="5.5"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.9 4.9 2.8 2.8"/><path d="m16.3 16.3 2.8 2.8"/><path d="m4.9 19.1 2.8-2.8"/><path d="m16.3 7.7 2.8-2.8"/><circle cx="10.5" cy="11" r=".8" fill="currentColor"/><circle cx="13.5" cy="13.5" r=".8" fill="currentColor"/>',
    "lungs":    '<path d="M12 3v9"/><path d="m12 11-2.5 2.5"/><path d="m12 11 2.5 2.5"/><path d="M8.5 7.5C6 7.5 3.5 11 3.5 15.5c0 2.6 1.2 4.5 3.3 4.5 2 0 3.2-1.5 3.2-3.5V9c0-.8-.6-1.5-1.5-1.5Z"/><path d="M15.5 7.5c2.5 0 5 3.5 5 8 0 2.6-1.2 4.5-3.3 4.5-2 0-3.2-1.5-3.2-3.5V9c0-.8.6-1.5 1.5-1.5Z"/>',
    "thermo":   '<path d="M14 14.8V4.5a2 2 0 0 0-4 0v10.3a4 4 0 1 0 4 0Z"/><path d="M12 10v7"/><path d="M17.5 5h3"/><path d="M17.5 9h3"/>',
    "stomach":  '<path d="M10 2.5v3.2c0 1.8-1.4 3-3.2 3.4C4.6 9.6 3.4 11.6 3.8 14c.7 4.3 4.4 7.5 9 7.5 4.3 0 7.4-3.4 7.4-7.7 0-4-2.7-6.8-6.4-6.4-.9.1-1.6-.6-1.6-1.5V2.5"/><path d="M8 15c1.5 1.5 4 2 6 1"/>',
    "capsule":  '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
    "f-tablet":   '<circle cx="12" cy="12" r="8.5"/><path d="m6 18 12-12"/>',
    "f-bottle":   '<path d="M9 2.5h6v3H9z"/><path d="M8 5.5h8l1.2 3V20a1.5 1.5 0 0 1-1.5 1.5H8.3A1.5 1.5 0 0 1 6.8 20V8.5Z"/><path d="M6.8 12.5h10.4"/><path d="M6.8 17h10.4"/>',
    "f-syringe":  '<path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3a2.4 2.4 0 0 1-3.4 0l-.6-.6a2.4 2.4 0 0 1 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/><path d="m14 4 6 6"/>',
    "f-capsule":  '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/>',
    "f-drop":     '<path d="M12 2.7 6.3 9.6a7 7 0 1 0 11.4 0L12 2.7Z"/>',
}

FORM_ICON = {
    "Tablet": "f-tablet", "Capsule": "f-capsule", "Suspension": "f-bottle",
    "Syrup": "f-bottle", "Injection": "f-syringe", "Drops": "f-drop",
}


def icon(name, cls=""):
    body = ICONS.get(name, "")
    c = ' class="%s"' % cls if cls else ""
    return (
        '<svg%s viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">%s</svg>'
        % (c, body)
    )


def cat_icon(cat):
    return icon(CAT_META.get(cat, {}).get("icon", "flask"))


def form_badge(form):
    return '<span class="form">%s%s</span>' % (icon(FORM_ICON.get(form, "f-tablet")), e(form))


# ---------------------------------------------------------------- media ----
_VER_CACHE = {}


def ver(path):
    """Append a content hash so a replaced file reaches returning visitors."""
    if path in _VER_CACHE:
        return _VER_CACHE[path]
    disk = os.path.join(ROOT, path.lstrip("/"))
    try:
        with open(disk, "rb") as fh:
            out = "%s?v=%s" % (path, hashlib.md5(fh.read()).hexdigest()[:8])
    except OSError:
        out = path
    _VER_CACHE[path] = out
    return out


def picture(jpg_path, alt, cls="", loading="lazy", sizes=None, fetchpriority=None):
    """<picture> with a WebP source when the sibling .webp exists on disk."""
    webp = re.sub(r"\.(jpe?g|png)$", ".webp", jpg_path, flags=re.I)
    has_webp = os.path.exists(os.path.join(ROOT, webp.lstrip("/")))
    attrs = ' class="%s"' % cls if cls else ""
    attrs += ' loading="%s" decoding="async"' % loading
    if fetchpriority:
        attrs += ' fetchpriority="%s"' % fetchpriority
    if sizes:
        attrs += ' sizes="%s"' % sizes
    img = '<img src="%s" alt="%s"%s>' % (e(ver(jpg_path)), e(alt), attrs)
    if has_webp:
        return '<picture><source srcset="%s" type="image/webp">%s</picture>' % (e(ver(webp)), img)
    return img


def product_img(p):
    return "%s/product-images/%s" % (IMG, p["image"])


def product_pic(p, **kw):
    return picture(product_img(p), "%s %s pack by %s" % (p["name"], p["form"].lower(), CO["name"]), **kw)


# ------------------------------------------------------------ text motion --
def split(text, start=0, accent=False):
    """Wrap each word so CSS can slide it up out of a mask, one after another.

    Words stay real text separated by real spaces, so screen readers, search
    engines and copy-paste see an ordinary sentence.
    """
    out = []
    for i, w in enumerate(text.split()):
        out.append('<span class="w"><span style="--i:%d">%s</span></span>' % (start + i, e(w)))
    html_ = " ".join(out)
    return ('<em class="accent">%s</em>' % html_) if accent else html_


def headline(text, accent=""):
    words = len(text.split())
    return split(text) + ((" " + split(accent, words, accent=True)) if accent else "")


# Background effects shared by every dark band: drifting aurora, a faint
# lab grid, and (optionally) the live molecule canvas.
def fx(canvas=True, density=""):
    return """<div class="fx" aria-hidden="true">
      <div class="fx__aurora"><span></span><span></span><span></span></div>
      <div class="fx__grid"></div>
      {canvas}
    </div>""".format(canvas=('<canvas class="fx__molecules" data-molecules%s></canvas>' % (
        ' data-density="%s"' % density if density else "")) if canvas else "")


ECG = """<svg class="ecg" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true" focusable="false">
  <path class="ecg__base" d="M0 60h330l18-26 22 52 26-92 30 118 22-70 16 18h176l14-14 14 14h170l18-26 22 52 26-92 30 118 22-70 16 18h250"/>
  <path class="ecg__pulse" pathLength="1000" d="M0 60h330l18-26 22 52 26-92 30 118 22-70 16 18h176l14-14 14 14h170l18-26 22 52 26-92 30 118 22-70 16 18h250"/>
</svg>"""


# ----------------------------------------------------------------- head ----
def org_ld():
    address = {
        "@type": "PostalAddress",
        "streetAddress": ADDR["street"],
        "addressLocality": ADDR["city"],
        "addressRegion": ADDR["region"],
        "postalCode": ADDR["postalCode"],
        "addressCountry": ADDR["country"],
    }
    ld = [{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": CO["legal"],
        "alternateName": CO["name"],
        "url": BASE + "/",
        "logo": BASE + IMG + "/logo.png",
        "description": CO["blurb"],
        "email": CONTACT["email"],
        "telephone": CONTACT["phones"],
        "address": address,
    }]
    geo = CONTACT.get("geo")
    if geo:
        local = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "@id": BASE + "/#business",
            "name": CO["legal"],
            "image": BASE + IMG + "/logo.png",
            "url": BASE + "/",
            "telephone": TEL,
            "email": CONTACT["email"],
            "address": address,
            "geo": {"@type": "GeoCoordinates", "latitude": geo["lat"], "longitude": geo["lng"]},
        }
        hours = CONTACT.get("openingHours") or []
        if hours:
            local["openingHoursSpecification"] = [
                {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"],
                 "opens": h["opens"], "closes": h["closes"]}
                for h in hours
            ]
        ld.append(local)
    return ld


def head(title, description, page_key, extra_ld=None, og_image=None, robots="index, follow"):
    og = og_image or (IMG + "/banners/banner.jpeg")
    ld = org_ld() + (extra_ld or [])
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#061736">
<meta name="robots" content="{robots}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="{co}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:image" content="{ogimg}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{ogimg}">

<link rel="icon" href="{img}/favicon.ico" sizes="any">
<link rel="icon" href="{img}/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="{img}/favicon.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=DM+Sans:opsz,wght@9..40,400..600&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="{css}">

<script type="application/ld+json">{ld}</script>
{verify}{analytics}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><span></span></div>
""".format(
        title=e(title), desc=e(description), canon=e(canonical(page_key)), robots=robots,
        co=e(CO["name"]), ogimg=e(BASE + og), img=IMG, css=ver(CSS),
        ld=json.dumps(ld if len(ld) > 1 else ld[0], ensure_ascii=False).replace("</", "<\\/"),
        verify=verification_tag(), analytics=analytics_tag(),
    )


def verification_tag():
    code = (SITE.get("analytics") or {}).get("googleSiteVerification", "")
    return '<meta name="google-site-verification" content="%s">\n' % e(code) if code else ""


def analytics_tag():
    """GA4, emitted only once a measurement id is filled in in site.json."""
    mid = (SITE.get("analytics") or {}).get("ga4MeasurementId", "")
    if not mid:
        return ""
    return (
        '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}"
        "gtag('js',new Date());gtag('config','%s');</script>\n" % (e(mid), e(mid))
    )


# --------------------------------------------------------------- chrome ----
def header(current):
    links = "".join(
        '<li><a class="nav__link" href="{h}"{cur}>{l}</a></li>'.format(
            h=e(href(k)), l=e(l), cur=' aria-current="page"' if k == current else "")
        for k, l in NAV
    )
    hours = " · ".join("%s %s" % (h["days"], h["time"]) for h in SITE["hours"] if h["time"] != "Closed")
    return """<header class="header" data-header>
  <div class="wrap header__row">
    <a class="header__brand" href="/" aria-label="{co} home">
      <img class="logo logo--light" src="{logo_w}" alt="{co} — {tag}" width="378" height="175">
      <img class="logo logo--dark" src="{logo}" alt="" width="378" height="175" aria-hidden="true">
    </a>
    <nav class="nav" aria-label="Main">
      <ul class="nav__menu" id="nav-menu">
        {links}
        <li class="nav__drawer">
          <a class="btn btn--glow btn--block" href="{contact}">Send an enquiry{arrow}</a>
          <a class="nav__drawer-link" href="tel:{tel_raw}">{ph_i}{tel}</a>
          <a class="nav__drawer-link" href="mailto:{mail}">{mail_i}{mail}</a>
          <p class="nav__drawer-hours">{clock}{hours}</p>
        </li>
      </ul>
    </nav>
    <div class="header__actions">
      <a class="header__call" href="tel:{tel_raw}" aria-label="Call {tel}">{ph_i}<span>{tel}</span></a>
      <a class="btn btn--glow btn--sm" href="{contact}">Enquire</a>
    </div>
    <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-menu" aria-label="Open menu">
      <span></span><span></span>
    </button>
  </div>
</header>
""".format(
        co=e(CO["name"]), tag=e(CO["tagline"]), logo=ver(IMG + "/logo.png"), logo_w=ver(IMG + "/logo-white.png"),
        links=links, contact=e(PAGES["contact"]), arrow=icon("arrow"), tel=e(TEL), tel_raw=e(TEL_RAW),
        ph_i=icon("phone"), mail=e(CONTACT["email"]), mail_i=icon("mail"), clock=icon("clock"), hours=e(hours),
    )


def floating():
    return """<a class="fab" href="{wa}" target="_blank" rel="noopener" aria-label="Chat with us on WhatsApp">{wa_i}</a>
<button class="totop" type="button" aria-label="Back to top">{up}</button>
<nav class="mobilebar" aria-label="Quick contact">
  <a class="mobilebar__btn" href="tel:{tel_raw}">{ph}<span>Call</span></a>
  <a class="mobilebar__btn" href="{wa}" target="_blank" rel="noopener">{wa_i}<span>WhatsApp</span></a>
  <a class="mobilebar__btn mobilebar__btn--cta" href="{contact}">{send}<span>Enquire</span></a>
</nav>
""".format(wa=e(WA), wa_i=icon("whatsapp"), up=icon("chevup"), tel_raw=e(TEL_RAW),
           ph=icon("phone"), send=icon("send"), contact=e(PAGES["contact"]))


def lightbox():
    return """<div class="lightbox" role="dialog" aria-modal="true" aria-label="Product image" aria-hidden="true">
  <div class="lightbox__stage">
    <button class="lightbox__close" type="button" aria-label="Close">{close}</button>
    <img class="lightbox__img" alt="">
    <p class="lightbox__caption"></p>
  </div>
</div>
""".format(close=icon("close"))


def footer(with_lightbox=False):
    areas = "".join('<li><a href="{h}">{n}</a></li>'.format(h=e(area_url(c)), n=e(c)) for c in CATEGORIES)
    quick = "".join('<li><a href="{h}">{l}</a></li>'.format(h=e(href(k)), l=e(l)) for k, l in NAV)
    phones = "".join('<a href="tel:{r}">{p}</a>'.format(r=e(p.replace(" ", "")), p=e(p)) for p in CONTACT["phones"])
    hours = "".join("<div><dt>{d}</dt><dd>{t}</dd></div>".format(d=e(h["days"]), t=e(h["time"])) for h in SITE["hours"])
    addr = "{s}, {l}, {c}, {r} {p}".format(s=ADDR["street"], l=ADDR["locality"], c=ADDR["city"],
                                            r=ADDR["region"], p=ADDR["postalCode"])
    return """<footer class="footer">
  {fx}
  <div class="wrap footer__inner">
    <div class="footer__top">
      <div class="footer__brand">
        <img src="{logo}" alt="{co}" width="378" height="175" loading="lazy">
        <p>{blurb}</p>
      </div>
      <form class="newsletter" action="/healabspharma/backend/signup_newsletter.php" method="POST">
        <label for="nl-email">Product updates for partners</label>
        <p>New launches and availability notes — occasional, never spam.</p>
        <div class="hp" aria-hidden="true">
          <label for="nl-website">Leave this field empty</label>
          <input id="nl-website" type="text" name="website" tabindex="-1" autocomplete="off">
        </div>
        <div class="newsletter__row">
          <input id="nl-email" type="email" name="email" placeholder="you@pharmacy.in" autocomplete="email" required>
          <button class="btn btn--glow" type="submit">Subscribe</button>
        </div>
      </form>
    </div>

    <div class="footer__grid">
      <div>
        <h2 class="footer__h">Company</h2>
        <ul class="footer__list">{quick}</ul>
      </div>
      <div>
        <h2 class="footer__h">Therapeutic areas</h2>
        <ul class="footer__list">{areas}</ul>
      </div>
      <div>
        <h2 class="footer__h">Contact</h2>
        <div class="footer__contact">
          <p>{pin}<span>{addr}</span></p>
          <p>{ph_i}<span class="footer__stack">{phones}</span></p>
          <p>{mail_i}<a href="mailto:{mail}">{mail}</a></p>
        </div>
      </div>
      <div>
        <h2 class="footer__h">Office hours</h2>
        <dl class="hours hours--dark">{hours}</dl>
      </div>
    </div>

    <p class="footer__word" aria-hidden="true">Caring <em>for</em> Wellness</p>

    <p class="footer__disclaimer"><strong>Medical disclaimer.</strong> Product information on this site
    is intended for healthcare professionals and general reference. It is not medical advice. Always
    consult a qualified physician before starting, stopping or changing any medication.</p>

    <div class="footer__bottom">
      <p>&copy; <span data-year>{year}</span> {legal}. All rights reserved.</p>
      <p>Made in Bengaluru</p>
    </div>
  </div>
</footer>
{floating}{lightbox}<script src="{js}" defer></script>
</body>
</html>
""".format(
        fx=fx(canvas=False), logo=ver(IMG + "/logo-white.png"), co=e(CO["name"]), blurb=e(CO["blurb"]),
        quick=quick, areas=areas, pin=icon("pin"), addr=e(addr), ph_i=icon("phone"), phones=phones,
        mail_i=icon("mail"), mail=e(CONTACT["email"]), hours=hours, year=date.today().year,
        legal=e(CO["legal"]), floating=floating(),
        lightbox=lightbox() if with_lightbox else "", js=ver(JS),
    )


def crumbs(trail):
    parts = []
    for label, h in trail:
        if h:
            parts.append('<a href="%s">%s</a>' % (e(h), e(label)))
        else:
            parts.append('<span aria-current="page">%s</span>' % e(label))
    return '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>' % icon("chevright").join(parts)


def pill(text):
    return '<p class="pill"><span class="pill__dot"></span>%s</p>' % e(text)


def pagehead(eyebrow, title, accent, lead, crumb_label, aside=""):
    return """<header class="pagehead dark">
  {fx}
  <div class="wrap pagehead__grid">
    <div class="pagehead__copy">
      {crumbs}
      {pill}
      <h1 class="display">{h}</h1>
      <p class="pagehead__lead">{lead}</p>
    </div>
    {aside}
  </div>
</header>
""".format(fx=fx(density="low"), crumbs=crumbs([("Home", "/"), (crumb_label, None)]), pill=pill(eyebrow),
           h=headline(title, accent), lead=e(lead), aside=aside)


def sec_head(eyebrow, title, lead="", center=False, action="", light=False, accent=""):
    return """<div class="sec-head{c}{l}">
        <div class="sec-head__copy reveal">
          <p class="eyebrow">{eb}</p>
          <h2 class="split-in">{t}</h2>
          {lead}
        </div>
        {action}
      </div>""".format(c=" sec-head--center" if center else "", l=" sec-head--light" if light else "",
                       eb=e(eyebrow), t=headline(title, accent),
                       lead="<p>%s</p>" % e(lead) if lead else "",
                       action=('<div class="sec-head__action reveal" data-delay="2">%s</div>' % action) if action else "")


# ----------------------------------------------------- shared components ---
def product_card(p, idx=0):
    return """<article class="pcard reveal" data-delay="{d}" data-area="{area}" data-form="{form_s}" data-tilt>
  <div class="pcard__media">{pic}<span class="pcard__glow" aria-hidden="true"></span></div>
  <div class="pcard__body">
    <p class="pcard__cat">{cat_i}<span>{cat}</span></p>
    <h3 class="pcard__name"><a href="{h}">{name}</a></h3>
    <p class="pcard__desc">{desc}</p>
    <div class="pcard__foot">{badge}<span class="pcard__go" aria-hidden="true">{arrow}</span></div>
  </div>
</article>
""".format(
        d=(idx % 4) + 1, area=e(slug(p["category"])), form_s=e(slug(p["form"])),
        pic=product_pic(p, sizes="(max-width: 640px) 92vw, (max-width: 1100px) 45vw, 300px"),
        cat_i=cat_icon(p["category"]), cat=e(p["category"]), h=e(product_url(p)),
        name=e(p["name"]), desc=e(p["description"]), badge=form_badge(p["form"]), arrow=icon("arrowup"),
    )


def product_ld(p):
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["name"],
        "category": p["category"],
        "description": p["description"][:300],
        "image": BASE + product_img(p),
        "brand": {"@type": "Brand", "name": CO["name"]},
        "manufacturer": {"@type": "Organization", "name": CO["legal"]},
    }


def initial(name):
    parts = [p for p in name.split() if p.rstrip(".").lower() not in ("dr", "mr", "mrs", "ms", "prof")]
    return (parts[0] if parts else name)[0].upper()


def ticker():
    if not MOLECULES:
        return ""
    items = "".join('<li>%s<span>%s</span></li>' % (icon("spark"), e(m)) for m in MOLECULES)
    return """<section class="ticker" aria-label="Active ingredients across our range">
    <div class="ticker__label">In our formulations</div>
    <div class="ticker__viewport">
      <ul class="ticker__track">{items}</ul>
      <ul class="ticker__track" aria-hidden="true">{items}</ul>
    </div>
  </section>""".format(items=items)


def process_section():
    n = len(SITE["process"])
    steps = "".join(
        """<li class="step" data-step="{k}">
          <span class="step__node"><span>{num:02d}</span></span>
          <h3>{t}</h3>
          <p>{x}</p>
        </li>""".format(k=i, num=i + 1, t=e(s["title"]), x=e(s["text"]))
        for i, s in enumerate(SITE["process"])
    )
    stats = "".join(
        '<div class="stat reveal" data-delay="{d}"><span class="stat__n" data-count="{n}" data-suffix="{s}">{n}{s}</span>'
        '<span class="stat__label">{l}</span></div>'.format(d=i + 1, n=s["n"], s=e(s["suffix"]), l=e(s["label"]))
        for i, s in enumerate(SITE["stats"])
    )
    return """<section class="section dark process">
    {fx}
    <div class="wrap">
      {head}
      <ol class="timeline" data-timeline style="--steps:{n}">
        <li class="timeline__rail" aria-hidden="true"><span></span></li>
        {steps}
      </ol>
      {ecg}
      <div class="process__band">
        <div class="process__photo reveal"><div data-parallax="0.06">{pic}</div></div>
        <div class="stats">{stats}</div>
      </div>
    </div>
  </section>""".format(
        fx=fx(density="low"), n=n, steps=steps, stats=stats, ecg=ECG,
        head=sec_head("Quality, start to finish", "From formulation", accent="to pharmacy shelf",
                      lead="Every product follows the same four-step path before it reaches a patient.", light=True),
        pic=picture(IMG + "/banners/banner3.jpeg", "Operators in cleanroom suits working on a sterile production floor",
                    sizes="(max-width: 900px) 92vw, 600px"),
    )


def cta_panel(title, accent, lead):
    return """<section class="section section--tight">
    <div class="wrap">
      <div class="cta dark reveal">
        {fx}
        {ecg}
        <div class="cta__copy">
          {pill}
          <h2 class="split-in">{h}</h2>
          <p>{l}</p>
        </div>
        <div class="cta__actions">
          <a class="btn btn--glow btn--lg" href="{contact}">Send an enquiry{arrow}</a>
          <a class="btn btn--glass btn--lg" href="{wa}" target="_blank" rel="noopener">{wa_i}WhatsApp us</a>
          <a class="cta__tel" href="tel:{tel_raw}">{ph}<span><small>or call directly</small>{tel}</span></a>
        </div>
      </div>
    </div>
  </section>""".format(fx=fx(canvas=False), ecg=ECG, pill=pill("We reply the same working day"),
                       h=headline(title, accent), l=e(lead), contact=e(PAGES["contact"]), arrow=icon("arrow"),
                       wa=e(WA), wa_i=icon("whatsapp"), tel_raw=e(TEL_RAW), ph=icon("phone"), tel=e(TEL))


# ----------------------------------------------------------------- home ----
def about_heading():
    year = CO.get("founded")
    return ("Caring for wellness,", "since %s" % year) if year else ("Caring for wellness,", "every single day")


def build_home():
    h = SITE["hero"]
    total = len(PRODUCTS)
    featured = [p for p in PRODUCTS if p.get("featured")] or PRODUCTS[:6]

    deck = "".join(
        """<a class="deck__card" href="{h}" data-pos="{k}"{hid}>
          <span class="deck__img">{pic}</span>
          <span class="deck__meta">
            <span class="deck__cat">{cat_i}{cat}</span>
            <strong>{name}</strong>
            {badge}
          </span>
        </a>""".format(h=e(product_url(p)), k=k, hid=' tabindex="-1"' if k else "",
                       pic=product_pic(p, loading="eager" if k == 0 else "lazy", sizes="340px",
                                       fetchpriority="high" if k == 0 else None),
                       cat_i=cat_icon(p["category"]), cat=e(p["category"]), name=e(p["name"]), badge=form_badge(p["form"]))
        for k, p in enumerate(featured[:4])
    )

    tiles = []
    for k, c in enumerate(CATEGORIES):
        thumbs = ""
        if k == 0:
            thumbs = '<span class="tile__thumbs">%s</span>' % "".join(
                '<span>%s</span>' % product_pic(p, sizes="120px") for p in picks(c, 3))
        tiles.append("""<a class="tile{big} reveal" data-delay="{d}" href="{h}" data-tilt>
          <span class="tile__top"><span class="tile__icon">{i}</span><span class="tile__count"><b>{n}</b> products</span></span>
          <h3>{name}</h3>
          <p>{blurb}</p>
          {thumbs}
          <span class="tile__foot"><span class="tile__forms">{forms}</span><span class="tile__go">{arrow}</span></span>
        </a>""".format(big=" tile--big" if k == 0 else "", d=(k % 4) + 1, h=e(area_url(c)), i=cat_icon(c),
                       n=count_in(c), name=e(c), blurb=e(CAT_META.get(c, {}).get("blurb", "")), thumbs=thumbs,
                       forms=e(" · ".join(forms_in(c))), arrow=icon("arrowup")))

    tabs = "".join(
        '<button class="tabs__btn" type="button" role="tab" id="tab-{s}" aria-controls="panel-{s}" '
        'aria-selected="{sel}" tabindex="{ti}">{i}<span>{c}</span><span class="tabs__n">{n}</span></button>'.format(
            s=slug(c), sel="true" if k == 0 else "false", ti="0" if k == 0 else "-1", i=cat_icon(c), c=e(c), n=count_in(c))
        for k, c in enumerate(CATEGORIES)
    )
    panels = "".join(
        """<div class="panel" role="tabpanel" id="panel-{s}" aria-labelledby="tab-{s}">
          <div class="pgrid pgrid--4">{cards}</div>
          <p class="panel__more"><a class="link-arrow" href="{h}">All {n} {c} products{arrow}</a></p>
        </div>""".format(s=slug(c), cards="".join(product_card(p, i) for i, p in enumerate(picks(c, 4))),
                         h=e(area_url(c)), n=count_in(c), c=e(c), arrow=icon("arrow"))
        for c in CATEGORIES
    )

    quotes = "".join(
        """<figure class="quote reveal" data-delay="{d}">
          <svg class="quote__mark" viewBox="0 0 32 24" aria-hidden="true"><path d="M0 24V14C0 6 4 1 12 0v5c-4 1-6 4-6 8h6v11Zm20 0V14c0-8 4-13 12-14v5c-4 1-6 4-6 8h6v11Z" fill="currentColor"/></svg>
          <blockquote><p>{q}</p></blockquote>
          <figcaption><span class="quote__avatar" aria-hidden="true">{ini}</span>
            <span><strong>{n}</strong><small>{r}</small></span></figcaption>
        </figure>""".format(d=i + 1, q=e(t["quote"]), ini=e(initial(t["name"])), n=e(t["name"]), r=e(t["role"]))
        for i, t in enumerate(SITE["testimonials"])
    )
    ah = about_heading()

    return """{head}{header}
<main id="main">
  <section class="hero dark">
    {fx}
    <div class="wrap hero__grid">
      <div class="hero__copy">
        {pill}
        <h1 class="display">{h1}</h1>
        <p class="hero__lead">{lead}</p>
        <div class="hero__actions">
          <a class="btn btn--glow btn--lg" href="{products}">Explore {total} products{arrow}</a>
          <a class="btn btn--glass btn--lg" href="{contact}">Become a partner</a>
        </div>
        <dl class="hero__stats">
          <div><dt data-count="{total}">{total}</dt><dd>Formulations</dd></div>
          <div><dt data-count="{ncat}">{ncat}</dt><dd>Therapeutic areas</dd></div>
          <div><dt data-count="{nform}">{nform}</dt><dd>Dosage forms</dd></div>
        </dl>
      </div>

      <div class="hero__stage">
        <svg class="orbit" viewBox="0 0 400 400" aria-hidden="true" focusable="false">
          <circle cx="200" cy="200" r="190"/><circle cx="200" cy="200" r="140"/>
          <g class="orbit__dots"><circle cx="200" cy="10" r="5"/><circle cx="390" cy="200" r="3.5"/><circle cx="60" cy="200" r="4"/></g>
        </svg>
        <span class="pill3d pill3d--a" aria-hidden="true"></span>
        <span class="pill3d pill3d--b" aria-hidden="true"></span>
        <span class="pill3d pill3d--c" aria-hidden="true"></span>
        <div class="deck" data-deck role="group" aria-label="Featured products">{deck}</div>
        <div class="hero__chip">
          <span class="hero__chip-icon">{shield}</span>
          <span><strong>Batch-level checks</strong><small>before every dispatch</small></span>
        </div>
      </div>
    </div>
    <a class="scroll-cue" href="#areas" aria-label="Scroll to therapeutic areas"><span></span></a>
  </section>

  {ticker}

  <section class="section" id="areas">
    <div class="wrap">
      {areas_head}
      <div class="bento">{tiles}</div>
    </div>
  </section>

  <section class="section section--mist">
    <div class="wrap">
      {range_head}
      <div class="tabs" role="tablist" aria-label="Therapeutic areas" data-tabs>{tabs}</div>
      <div class="panels">{panels}</div>
    </div>
  </section>

  {process}

  <section class="section">
    <div class="wrap split">
      <div class="collage reveal">
        <div class="collage__main"><div data-parallax="0.05">{about_a}</div></div>
        <div class="collage__inset" data-parallax="-0.08">{about_b}</div>
        <div class="collage__badge">{pin}Bengaluru, Karnataka</div>
      </div>
      <div class="split__copy">
        <div class="reveal"><p class="eyebrow">About {co}</p></div>
        <h2 class="split-in reveal">{about_h}</h2>
        <p class="lead reveal" data-delay="1">{intro}</p>
        <ul class="checklist reveal" data-delay="2">
          <li>{tick}<span>Quality-assured manufacturing at certified facilities</span></li>
          <li>{tick}<span>Paediatric-friendly suspensions, syrups and drops</span></li>
          <li>{tick}<span>Consistent supply for pharmacies and distributors</span></li>
        </ul>
        <div class="reveal" data-delay="3"><a class="btn btn--line" href="{about}">Our story{arrow}</a></div>
      </div>
    </div>
  </section>

  <section class="section section--mist">
    <div class="wrap">
      {quotes_head}
      <div class="quotes">{quotes}</div>
    </div>
  </section>

  {cta}
</main>
{footer}""".format(
        head=head("{co} — {tag} | Pharmaceutical Company in Bengaluru".format(co=CO["name"], tag=CO["tagline"]),
                  CO["blurb"], "home"),
        header=header("home"), fx=fx(), pill=pill(h["eyebrow"]),
        h1=headline(h["title"], h.get("titleAccent", "")), lead=e(h["lead"]),
        products=e(PAGES["products"]), contact=e(PAGES["contact"]), about=e(PAGES["about"]),
        total=total, ncat=len(CATEGORIES), nform=len(FORMS), arrow=icon("arrow"),
        deck=deck, shield=icon("shield"), ticker=ticker(),
        areas_head=sec_head("Therapeutic areas", "Focused care across", accent="%d areas" % len(CATEGORIES),
                            lead="A deliberately focused portfolio — the formulations general physicians, paediatricians and pharmacies reach for every day.",
                            action='<a class="link-arrow" href="%s">Full catalogue%s</a>' % (e(PAGES["products"]), icon("arrow"))),
        tiles="".join(tiles),
        range_head=sec_head("Explore the range", "Formulations", accent="clinicians trust",
                            lead="Pick a therapeutic area — or search all %d products by brand or molecule in the catalogue." % total,
                            action='<a class="btn btn--dark" href="%s">All %d products%s</a>' % (e(PAGES["products"]), total, icon("arrow"))),
        tabs=tabs, panels=panels, process=process_section(),
        about_a=picture(IMG + "/about.jpeg", "A pharmacist selecting a medication box from a dispensary shelf",
                        sizes="(max-width: 900px) 92vw, 560px"),
        about_b=picture(IMG + "/title-image.jpeg", "Close-up of tablets in blister packs", sizes="260px"),
        pin=icon("pin"), co=e(CO["name"]), about_h=headline(ah[0], ah[1]), intro=e(SITE["about"]["intro"]),
        tick=icon("tick"),
        quotes_head=sec_head("Partners", "Trusted by clinicians,", accent="pharmacies & distributors", center=True),
        quotes=quotes,
        cta=cta_panel("Looking for a reliable", "supply partner?",
                      "Send us your requirement — product list, quantities, location — and we will come back with stock and rates."),
        footer=footer(),
    )


# ---------------------------------------------------------------- about ----
def build_about():
    values = "".join(
        """<div class="value reveal" data-delay="{d}" data-tilt>
          <span class="value__n">{n:02d}</span>
          <span class="value__icon">{i}</span>
          <h3>{t}</h3>
          <p>{x}</p>
        </div>""".format(d=(i % 4) + 1, n=i + 1, i=icon(v["icon"]), t=e(v["title"]), x=e(v["text"]))
        for i, v in enumerate(SITE["values"])
    )
    aside = '<div class="pagehead__art reveal">%s</div>' % picture(
        IMG + "/about2.jpeg", "A scientist pipetting samples into test tubes in a laboratory",
        loading="eager", sizes="(max-width: 900px) 92vw, 480px")
    return """{head}{header}
<main id="main">
  {ph}

  <section class="section">
    <div class="wrap split">
      <div class="collage reveal">
        <div class="collage__main"><div data-parallax="0.05">{img1}</div></div>
        <div class="collage__inset" data-parallax="-0.08">{img2}</div>
      </div>
      <div class="split__copy">
        <div class="reveal"><p class="eyebrow">Who we are</p></div>
        <h2 class="split-in reveal">{who}</h2>
        <p class="lead reveal" data-delay="1">{intro}</p>
        <ul class="checklist reveal" data-delay="2">
          <li>{tick}<span>{n} formulations across {c} therapeutic areas</span></li>
          <li>{tick}<span>Based in Bengaluru, supplying across India</span></li>
          <li>{tick}<span>Direct support for clinicians, pharmacies and distributors</span></li>
        </ul>
      </div>
    </div>
  </section>

  {ticker}

  <section class="section section--mist">
    <div class="wrap">
      <div class="mv">
        <article class="mv__card reveal" data-tilt>
          <span class="mv__icon">{target}</span>
          <p class="eyebrow">Our mission</p>
          <h2>Closing the gap between <em class="accent">patient and medicine</em></h2>
          <p>{mission}</p>
        </article>
        <article class="mv__card mv__card--dark dark reveal" data-delay="1" data-tilt>
          {fx}
          <span class="mv__icon">{eye}</span>
          <p class="eyebrow">Our vision</p>
          <h2>Healthcare that <em class="accent">reaches everyone</em></h2>
          <p>{vision}</p>
        </article>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      {values_head}
      <div class="values">{values}</div>
    </div>
  </section>

  {process}

  {cta}
</main>
{footer}""".format(
        head=head("About Us — {co} | {legal}".format(co=CO["name"], legal=CO["legal"]),
                  "Heal Labs is a Bengaluru-based pharmaceutical company supplying quality-assured medicines across five therapeutic areas. Read about our mission, vision and values.",
                  "about", og_image=IMG + "/about.jpeg"),
        header=header("about"),
        ph=pagehead("About Heal Labs", "Caring for", "wellness",
                    "A Bengaluru pharmaceutical company — how we work, what we make and what we stand for.",
                    "About", aside),
        img1=picture(IMG + "/about.jpeg", "A pharmacist selecting a medication box from a dispensary shelf",
                     sizes="(max-width: 900px) 92vw, 560px"),
        img2=picture(IMG + "/about1.jpeg", "Shelves stocked with a wide range of packaged medicines", sizes="260px"),
        who=headline("A pharmaceutical company", "built on trust"),
        intro=e(SITE["about"]["intro"]), tick=icon("tick"), n=len(PRODUCTS), c=len(CATEGORIES),
        ticker=ticker(), target=icon("target"), eye=icon("eye"), fx=fx(canvas=False),
        mission=e(SITE["about"]["mission"]), vision=e(SITE["about"]["vision"]),
        values_head=sec_head("What guides us", "Our", accent="values", center=True), values=values,
        process=process_section(),
        cta=cta_panel("Work with", "Heal Labs", "Distributors, pharmacies and clinicians — we would like to hear from you."),
        footer=footer(),
    )


# ------------------------------------------------------------- products ----
def build_products():
    def opt(facet, value, label, n, pressed=False, ic=""):
        return ('<button class="facet__opt" type="button" data-facet="{f}" data-value="{v}" aria-pressed="{p}">'
                '{ic}<span class="facet__label">{l}</span><span class="facet__n">{n}</span></button>').format(
            f=facet, v=e(value), p="true" if pressed else "false", ic=ic, l=e(label), n=n)

    area_opts = opt("area", "all", "All areas", len(PRODUCTS), True) + "".join(
        opt("area", slug(c), c, count_in(c), ic=cat_icon(c)) for c in CATEGORIES)
    form_opts = opt("form", "all", "All forms", len(PRODUCTS), True) + "".join(
        opt("form", slug(f), f, sum(1 for p in PRODUCTS if p["form"] == f), ic=icon(FORM_ICON.get(f, "f-tablet")))
        for f in FORMS)
    cards = "".join(product_card(p, i) for i, p in enumerate(PRODUCTS))

    ld = [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Heal Labs product range",
        "numberOfItems": len(PRODUCTS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": BASE + product_url(p), "name": p["name"]}
            for i, p in enumerate(PRODUCTS)
        ],
    }]

    aside = """<dl class="glass-stats reveal">
      <div><dt data-count="{n}">{n}</dt><dd>Formulations</dd></div>
      <div><dt data-count="{c}">{c}</dt><dd>Therapeutic areas</dd></div>
      <div><dt data-count="{f}">{f}</dt><dd>Dosage forms</dd></div>
    </dl>""".format(n=len(PRODUCTS), c=len(CATEGORIES), f=len(FORMS))

    return """{head}{header}
<main id="main">
  {ph}

  <section class="section section--catalog">
    <div class="wrap catalog">
      <aside class="catalog__side" aria-label="Filter products">
        <div class="search">
          {si}
          <label class="sr-only" for="product-search">Search products</label>
          <input id="product-search" type="search" data-search placeholder="Brand or molecule…" autocomplete="off">
          <kbd class="search__kbd" aria-hidden="true">/</kbd>
        </div>
        <div class="facet">
          <h2 class="facet__title">Therapeutic area</h2>
          <div class="facet__opts">{area_opts}</div>
        </div>
        <div class="facet">
          <h2 class="facet__title">Dosage form</h2>
          <div class="facet__opts">{form_opts}</div>
        </div>
        <div class="side-help dark">
          {fx}
          <p><strong>Need pricing or stock?</strong> Send your list and we will come back with rates and availability.</p>
          <a class="btn btn--glow btn--sm btn--block" href="{contact}">Request a quote</a>
          <a class="side-help__wa" href="{wa}" target="_blank" rel="noopener">{wa_i}WhatsApp {tel}</a>
        </div>
      </aside>

      <div class="catalog__main">
        <div class="catalog__bar">
          <p aria-live="polite">Showing <strong data-result-count>{n}</strong> of {n} products</p>
          <button class="link-btn" type="button" data-reset hidden>Clear filters</button>
        </div>
        <div class="pgrid pgrid--catalog" data-catalogue>
          {cards}
        </div>
        <div class="empty" data-empty hidden>
          {si}
          <p><strong>No products match.</strong> Try a different brand or molecule name, or clear the filters.</p>
        </div>
      </div>
    </div>
  </section>

  {cta}
</main>
{footer}""".format(
        head=head("Products — {n} Pharmaceutical Formulations | {co}".format(n=len(PRODUCTS), co=CO["name"]),
                  "Browse the full Heal Labs range: {n} formulations across anti-infectives, pain and fever, respiratory and allergy, gastro and nutraceuticals.".format(n=len(PRODUCTS)),
                  "products", extra_ld=ld),
        header=header("products"),
        ph=pagehead("Product catalogue", "Our", "products",
                    "Tablets, suspensions, syrups, drops and injections — search by brand name or active molecule.",
                    "Products", aside),
        si=icon("search"), area_opts=area_opts, form_opts=form_opts, n=len(PRODUCTS), cards=cards,
        fx=fx(canvas=False), contact=e(PAGES["contact"]), wa=e(WA), wa_i=icon("whatsapp"), tel=e(TEL),
        cta=cta_panel("Need pricing", "or availability?", "Send us the list — we will come back to you with stock and rates."),
        footer=footer(),
    )


def build_product(p):
    img = product_img(p)
    url = product_url(p)
    related = [r for r in PRODUCTS if r["category"] == p["category"] and r["slug"] != p["slug"]][:4]
    rel_cards = "".join(product_card(r, i) for i, r in enumerate(related))
    wa_href = "%s?text=%s" % (WA, quote("Hello Heal Labs, I would like to enquire about %s (%s)." % (p["name"], p["form"])))
    ld = [
        product_ld(p),
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products", "item": BASE + PAGES["products"]},
                {"@type": "ListItem", "position": 3, "name": p["category"], "item": BASE + area_url(p["category"])},
                {"@type": "ListItem", "position": 4, "name": p["name"], "item": BASE + url},
            ],
        },
    ]
    desc = p["description"]
    meta = (desc[:150].rsplit(" ", 1)[0] + "…") if len(desc) > 155 else desc
    found = [m for m in MOLECULES if re.search(r"\b%s\b" % re.escape(m), desc, re.I)]
    mol_row = ('<tr><th scope="row">Key actives</th><td>%s</td></tr>' % e(", ".join(found))) if found else ""

    related_block = ""
    if related:
        related_block = """<section class="section section--mist">
    <div class="wrap">
      {head}
      <div class="pgrid pgrid--4">{cards}</div>
    </div>
  </section>""".format(
            head=sec_head("Same therapeutic area", "More in", accent=p["category"],
                          action='<a class="link-arrow" href="%s">View all %d%s</a>' % (
                              e(area_url(p["category"])), count_in(p["category"]), icon("arrow"))),
            cards=rel_cards)

    return """{head}{header}
<main id="main">
  <section class="pd-hero dark">
    {fx}
    <div class="wrap">
      {crumbs}
      <div class="pd">
        <div class="pd__media reveal">
          <button class="pd__zoom" type="button" data-lightbox="{img_v}" data-caption="{name}"
                  aria-label="View larger image of {name}" data-tilt>
            {pic}
            <span class="pd__zoom-hint">{zoom}Enlarge</span>
          </button>
        </div>
        <div class="pd__body">
          <a class="pd__cat" href="{area_h}">{cat_i}<span>{cat}</span></a>
          <h1 class="display display--md">{h1}</h1>
          <div class="pd__badges">{badge}</div>
          <p class="pd__lead">{desc}</p>

          <table class="spec">
            <caption class="sr-only">Product details</caption>
            <tbody>
              <tr><th scope="row">Brand name</th><td>{name}</td></tr>
              <tr><th scope="row">Dosage form</th><td>{form}</td></tr>
              {mol_row}
              <tr><th scope="row">Therapeutic area</th><td><a href="{area_h}">{cat}</a></td></tr>
              <tr><th scope="row">Marketed by</th><td>{legal}</td></tr>
            </tbody>
          </table>

          <div class="pd__actions">
            <a class="btn btn--glow btn--lg" href="{contact}">Request pricing{arrow}</a>
            <a class="btn btn--glass btn--lg" href="{wa}" target="_blank" rel="noopener">{wa_i}Ask on WhatsApp</a>
          </div>

          <p class="pd__note">{alert}<span>For healthcare professionals and general reference only — not
             medical advice. Use only as directed by a qualified physician.</span></p>
        </div>
      </div>
    </div>
  </section>

  {related_block}
</main>
{footer}""".format(
        head=head("{n} — {form} | {co}".format(n=p["name"], form=p["form"], co=CO["name"]),
                  meta, url, extra_ld=ld, og_image=img),
        header=header("products"), fx=fx(density="low"),
        crumbs=crumbs([("Home", "/"), ("Products", PAGES["products"]),
                       (p["category"], area_url(p["category"])), (p["name"], None)]),
        img_v=e(ver(img)),
        pic=product_pic(p, loading="eager", fetchpriority="high", sizes="(max-width: 900px) 92vw, 540px"),
        zoom=icon("zoom"), area_h=e(area_url(p["category"])), cat_i=cat_icon(p["category"]),
        cat=e(p["category"]), name=e(p["name"]), h1=split(p["name"]), form=e(p["form"]), badge=form_badge(p["form"]),
        desc=e(desc), mol_row=mol_row, legal=e(CO["legal"]), contact=e(PAGES["contact"]), arrow=icon("arrow"),
        wa=e(wa_href), wa_i=icon("whatsapp"), alert=icon("alert"), related_block=related_block,
        footer=footer(with_lightbox=True),
    )


# -------------------------------------------------------------- contact ----
def build_contact():
    phones = "".join('<a href="tel:{r}">{p}</a>'.format(r=e(p.replace(" ", "")), p=e(p)) for p in CONTACT["phones"])
    addr = "{s}<br>{l}<br>{c}, {r} {p}".format(s=e(ADDR["street"]), l=e(ADDR["locality"]), c=e(ADDR["city"]),
                                               r=e(ADDR["region"]), p=e(ADDR["postalCode"]))
    hours = "".join("<div><dt>{d}</dt><dd>{t}</dd></div>".format(d=e(h["days"]), t=e(h["time"])) for h in SITE["hours"])
    aside = """<div class="quick reveal">
      <a class="quick__btn" href="tel:{tel_raw}">{ph}<span><small>Call</small>{tel}</span></a>
      <a class="quick__btn quick__btn--wa" href="{wa}" target="_blank" rel="noopener">{wa_i}<span><small>WhatsApp</small>Chat with the team</span></a>
      <a class="quick__btn" href="mailto:{mail}">{mail_i}<span><small>Email</small>{mail}</span></a>
    </div>""".format(tel_raw=e(TEL_RAW), ph=icon("phone"), tel=e(TEL), wa=e(WA), wa_i=icon("whatsapp"),
                     mail=e(CONTACT["email"]), mail_i=icon("mail"))
    return """{head}{header}
<main id="main">
  {ph}

  <section class="section">
    <div class="wrap contact">
      <form class="form-card reveal" action="/healabspharma/backend/submit_contact.php" method="POST" novalidate>
        <p class="eyebrow">Enquiry form</p>
        <h2>Send us a <em class="accent">message</em></h2>
        <p class="form-card__lead">Clinician, pharmacy or distributor — tell us what you need. Fields marked <span class="req">*</span> are required.</p>

        <div class="field-row">
          <div class="field">
            <label for="c-name">Your name <span class="req">*</span></label>
            <input id="c-name" name="name" type="text" required autocomplete="name" placeholder="Full name">
          </div>
          <div class="field">
            <label for="c-phone">Phone number</label>
            <input id="c-phone" name="phone" type="tel" autocomplete="tel" placeholder="+91 00000 00000"
                   pattern="[0-9+()\\s-]{{7,20}}">
          </div>
        </div>
        <div class="field">
          <label for="c-email">Email address <span class="req">*</span></label>
          <input id="c-email" name="email" type="email" required autocomplete="email" placeholder="you@example.com">
        </div>
        <div class="field">
          <label for="c-message">How can we help? <span class="req">*</span></label>
          <textarea id="c-message" name="message" required rows="5" placeholder="Products you are interested in, quantities, your city…"></textarea>
        </div>
        <div class="hp" aria-hidden="true">
          <label for="c-website">Leave this field empty</label>
          <input id="c-website" type="text" name="website" tabindex="-1" autocomplete="off">
        </div>
        <button class="btn btn--glow btn--lg btn--block" type="submit">Send enquiry{arrow}</button>
        <p class="form-card__fine">We use your details only to answer your enquiry.</p>
      </form>

      <div class="contact__info">
        <div class="ccard reveal" data-delay="1">
          <span class="ccard__icon">{ph_i}</span>
          <div><h2>Call us</h2><div class="ccard__stack">{phones}</div></div>
        </div>
        <div class="ccard reveal" data-delay="2">
          <span class="ccard__icon">{pin}</span>
          <div><h2>Visit</h2><p>{addr}</p></div>
        </div>
        <div class="ccard reveal" data-delay="3">
          <span class="ccard__icon">{clock}</span>
          <div class="ccard__grow"><h2>Office hours</h2><dl class="hours">{hours}</dl></div>
        </div>
        <div class="map reveal" data-delay="4">
          <iframe src="{map}" title="Map showing the Heal Labs office in Bengaluru"
                  loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
        </div>
      </div>
    </div>
  </section>
</main>
{footer}""".format(
        head=head("Contact Us — {co} | Bengaluru".format(co=CO["name"]),
                  "Get in touch with Heal Labs Pharmaceutical, Bengaluru. Call {t}, email {m}, or send an enquiry for pricing and availability.".format(
                      t=TEL, m=CONTACT["email"]),
                  "contact"),
        header=header("contact"),
        ph=pagehead("Contact", "Talk to", "our team",
                    "Enquiries, pricing and supply — reach us Monday to Saturday. We usually reply the same working day.",
                    "Contact", aside),
        ph_i=icon("phone"), phones=phones, pin=icon("pin"), addr=addr, clock=icon("clock"), hours=hours,
        arrow=icon("arrow"), map=e(CONTACT["mapEmbed"]),
        footer=footer(),
    )


# ------------------------------------------------------- status pages -----
def status_page(kind_cls, icon_name, eyebrow, title, accent, lead, primary, secondary, head_html):
    return """{head}{header}
<main id="main">
  <section class="status dark">
    {fx}
    <div class="wrap status__inner">
      <span class="status__icon status__icon--{cls}">{i}</span>
      {eyebrow}
      <h1 class="display display--md">{h}</h1>
      <p class="status__lead">{lead}</p>
      <p class="status__actions">{primary}{secondary}</p>
    </div>
  </section>
</main>
{footer}""".format(head=head_html, header=header(""), fx=fx(), cls=kind_cls, i=icon(icon_name),
                   eyebrow=pill(eyebrow) if eyebrow else "", h=headline(title, accent), lead=e(lead),
                   primary=primary, secondary=secondary, footer=footer())


def build_status(kind):
    ok = kind == "success"
    lead = ("Your enquiry has reached us. A member of the team will get back to you shortly, "
            "usually within one working day.") if ok else \
           ("We could not submit your message. Please try again, or reach us directly by phone "
            "or WhatsApp and we will pick it up right away.")
    return status_page(
        "ok" if ok else "err", "check" if ok else "alert", "Enquiry received" if ok else "Not sent",
        "Thank you —" if ok else "Something", "message received" if ok else "went wrong", lead,
        '<a class="btn btn--glow btn--lg" href="/">Back to home%s</a>' % icon("arrow"),
        '<a class="btn btn--glass btn--lg" href="%s">%s</a>' % (
            e(PAGES["products"] if ok else PAGES["contact"]), "Browse products" if ok else "Try again"),
        head(("Thank You" if ok else "Submission Failed") + " — " + CO["name"], lead, "contact",
             robots="noindex, follow"),
    )


def build_404():
    return status_page(
        "err", "search", "Error 404", "We cannot find", "that page",
        "The link may be out of date, or the page may have moved. Our product range and contact details are a click away.",
        '<a class="btn btn--glow btn--lg" href="/">Back to home%s</a>' % icon("arrow"),
        '<a class="btn btn--glass btn--lg" href="%s">Browse products</a>' % e(PAGES["products"]),
        head("Page Not Found — " + CO["name"],
             "The page you were looking for is not here. Browse the Heal Labs product range or get in touch.",
             "home", robots="noindex, follow"),
    )


def build_legacy_home_redirect():
    """The old homepage URL — keep it alive, point search engines at '/'."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{co} — {tag}</title>
<link rel="canonical" href="{base}/">
<meta http-equiv="refresh" content="0; url=/">
<meta name="robots" content="noindex, follow">
<script>window.location.replace("/");</script>
</head>
<body>
<p>This page has moved. <a href="/">Continue to the {co} home page</a>.</p>
</body>
</html>
""".format(co=e(CO["name"]), tag=e(CO["tagline"]), base=e(BASE))


# -------------------------------------------------------------- sitemap ----
def build_sitemap():
    today = date.today().isoformat()
    entries = [("/", "1.0", "weekly"),
               (PAGES["products"], "0.9", "weekly"),
               (PAGES["about"], "0.7", "monthly"),
               (PAGES["contact"], "0.7", "monthly")]
    entries += [(product_url(p), "0.8", "monthly") for p in PRODUCTS]
    urls = "".join(
        "  <url><loc>{b}{l}</loc><lastmod>{d}</lastmod><changefreq>{cf}</changefreq>"
        "<priority>{p}</priority></url>\n".format(b=BASE, l=loc, d=today, cf=cf, p=pr)
        for loc, pr, cf in entries
    )
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")


def build_robots():
    return """User-agent: *
Allow: /
Disallow: /healabspharma/backend/
Disallow: /healabspharma/build/
Disallow: /healabspharma/data/

Sitemap: {base}/sitemap.xml
""".format(base=BASE)


# ----------------------------------------------------------------- main ----
def write(path, content, quiet=False):
    full = os.path.join(ROOT, path.lstrip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)
    if not quiet:
        print("  %-52s %6.1f KB" % (path, len(content.encode("utf-8")) / 1024))


def main():
    print("Building %s (%d products)…" % (CO["name"], len(PRODUCTS)))
    write("/index.html", build_home())
    write(PAGES["about"], build_about())
    write(PAGES["products"], build_products())
    write(PAGES["contact"], build_contact())
    for prod in PRODUCTS:
        write(product_url(prod), build_product(prod), quiet=True)
    print("  %-52s %d pages" % (PRODUCT_DIR + "/<slug>.html", len(PRODUCTS)))
    write("/healabspharma/frontend/html/success.html", build_status("success"))
    write("/healabspharma/frontend/html/reject.html", build_status("reject"))
    write("/healabspharma/frontend/html/healab.html", build_legacy_home_redirect())
    write("/404.html", build_404())
    write("/sitemap.xml", build_sitemap())
    write("/robots.txt", build_robots())
    print("Done.")


if __name__ == "__main__":
    main()
