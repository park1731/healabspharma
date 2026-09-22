#!/usr/bin/env python3
"""
Heal Labs Pharma — static site generator.

Reads  : healabspharma/data/{site,products}.json
Writes : index.html, healabspharma/frontend/html/*.html, sitemap.xml, robots.txt

No third-party dependencies — plain Python 3. Run after editing any data file:

    python3 healabspharma/build/build.py

Edit content in the JSON files, never in the generated HTML.
"""

import hashlib
import json
import html
import os
import re
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "healabspharma", "data")
HTML_DIR = os.path.join(ROOT, "healabspharma", "frontend", "html")

CSS = "/healabspharma/frontend/css/site.css"
JS = "/healabspharma/frontend/scripts/site.js"
IMG = "/healabspharma/images"

SITE = json.load(open(os.path.join(DATA, "site.json"), encoding="utf-8"))
PRODUCTS = json.load(open(os.path.join(DATA, "products.json"), encoding="utf-8"))

CO = SITE["company"]
CONTACT = SITE["contact"]
ADDR = CONTACT["address"]
BASE = CO["baseUrl"].rstrip("/")

PRODUCT_DIR = "/healabspharma/frontend/html/products"


def product_url(p):
    return "%s/%s.html" % (PRODUCT_DIR, p["slug"])


PAGES = {
    "home":     "/index.html",
    "about":    "/healabspharma/frontend/html/aboutus.html",
    "products": "/healabspharma/frontend/html/products.html",
    "contact":  "/healabspharma/frontend/html/contact.html",
}

NAV = [("home", "Home"), ("about", "About Us"), ("products", "Products"), ("contact", "Contact")]


def e(t):
    """Escape for HTML text/attribute context."""
    return html.escape(str(t), quote=True)


def canonical(key):
    """`key` is a PAGES name, or a literal path for generated product pages."""
    if key in PAGES:
        return BASE + ("/" if key == "home" else PAGES[key])
    return BASE + key


# ---------------------------------------------------------------- icons ----
ICONS = {
    "shield":   '<path d="M12 2 4 5v6c0 5 3.4 9.1 8 11 4.6-1.9 8-6 8-11V5l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    "truck":    '<path d="M1 3h13v13H1z"/><path d="M14 8h4l3 3v5h-7V8Z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/>',
    "flask":    '<path d="M9 2v6L4 18a2 2 0 0 0 1.8 3h12.4A2 2 0 0 0 20 18L15 8V2"/><path d="M8 2h8"/><path d="M6.5 14h11"/>',
    "headset":  '<path d="M3 14v-3a9 9 0 0 1 18 0v3"/><path d="M21 15a2 2 0 0 1-2 2h-1v-6h1a2 2 0 0 1 2 2v2Z"/><path d="M3 15a2 2 0 0 0 2 2h1v-6H5a2 2 0 0 0-2 2v2Z"/><path d="M21 17v1a4 4 0 0 1-4 4h-3"/>',
    "heart":    '<path d="M20.8 5.6a5.5 5.5 0 0 0-7.8 0L12 6.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1 7.8 7.8 7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8Z"/>',
    "handshake":'<path d="m11 17 2 2a1.4 1.4 0 0 0 2-2"/><path d="m14 16 2.5 2.5a1.4 1.4 0 0 0 2-2l-4-4"/><path d="m8 13 2-2 4 4"/><path d="M3 11 7 7h4l3 3"/><path d="m21 11-4-4h-3l-2 2"/>',
    "leaf":     '<path d="M11 20A7 7 0 0 1 4 13c0-6 5-10 16-10 0 10-5 14-9 14Z"/><path d="M4 21c2-6 6-9 11-10"/>',
    "check":    '<circle cx="12" cy="12" r="10"/><path d="m8 12 3 3 5-6"/>',
    "mail":     '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/>',
    "phone":    '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
    "pin":      '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "clock":    '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "whatsapp": '<path d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Z"/><path d="M8.5 7.5c.3 0 .6.2.8.6l.7 1.5c.1.3 0 .6-.2.8l-.5.5a7 7 0 0 0 3.3 3.3l.5-.5c.2-.2.5-.3.8-.2l1.5.7c.4.2.6.5.6.8 0 1-.8 1.8-1.8 1.8A8.2 8.2 0 0 1 6.7 9.3c0-1 .8-1.8 1.8-1.8Z"/>',
    "search":   '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "zoom":     '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/>',
    "chevdown": '<path d="m6 9 6 6 6-6"/>',
    "chevright":'<path d="m9 6 6 6-6 6"/>',
    "chevleft": '<path d="m15 6-6 6 6 6"/>',
    "chevup":   '<path d="m18 15-6-6-6 6"/>',
    "close":    '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "arrow":    '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "alert":    '<circle cx="12" cy="12" r="10"/><path d="M12 8v5"/><path d="M12 16h.01"/>',
}


def icon(name, cls=""):
    body = ICONS.get(name, "")
    c = ' class="%s"' % cls if cls else ""
    return (
        '<svg%s viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">%s</svg>'
        % (c, body)
    )


_VER_CACHE = {}


def ver(path):
    """Append a content hash so a replaced image is picked up immediately.

    .htaccess serves images as immutable for a year, which is what we want
    for speed — but it also means swapping a file at the same name would
    leave returning visitors on the old one. The hash changes with the
    bytes, so the URL changes with them too.
    """
    if path in _VER_CACHE:
        return _VER_CACHE[path]
    disk = os.path.join(ROOT, path.lstrip("/"))
    try:
        with open(disk, "rb") as fh:
            digest = hashlib.md5(fh.read()).hexdigest()[:8]
        out = "%s?v=%s" % (path, digest)
    except OSError:
        out = path
    _VER_CACHE[path] = out
    return out


def picture(jpg_path, alt, cls="", loading="lazy", sizes=None, fetchpriority=None):
    """<picture> with a WebP source when the sibling .webp exists on disk."""
    disk = os.path.join(ROOT, jpg_path.lstrip("/"))
    webp = re.sub(r"\.(jpe?g|png)$", ".webp", jpg_path, flags=re.I)
    has_webp = os.path.exists(os.path.join(ROOT, webp.lstrip("/")))
    attrs = ' class="%s"' % cls if cls else ""
    attrs += ' loading="%s"' % loading
    attrs += ' decoding="async"'
    if fetchpriority:
        attrs += ' fetchpriority="%s"' % fetchpriority
    if sizes:
        attrs += ' sizes="%s"' % sizes
    dims = ""
    img = '<img src="%s" alt="%s"%s%s>' % (e(ver(jpg_path)), e(alt), attrs, dims)
    if has_webp:
        return '<picture><source srcset="%s" type="image/webp">%s</picture>' % (e(ver(webp)), img)
    return img


# ------------------------------------------------------------ chrome ------
def bg_image(jpg_path):
    """A background-image that prefers WebP but falls back to the JPEG.

    Hero and page headers are CSS backgrounds, so they cannot use <picture>.
    The plain url() comes first for browsers without image-set(); the second
    declaration wins wherever it is understood.
    """
    webp = re.sub(r"\.(jpe?g|png)$", ".webp", jpg_path, flags=re.I)
    jpg = ver(jpg_path)
    if not os.path.exists(os.path.join(ROOT, webp.lstrip("/"))):
        return "background-image:url('%s')" % jpg
    return (
        "background-image:url('%s');"
        "background-image:image-set(url('%s') type('image/webp'),url('%s') type('image/jpeg'))"
        % (jpg, ver(webp), jpg)
    )


def head(title, description, page_key, extra_ld=None, og_image=None):
    og = og_image or (IMG + "/banners/banner.jpeg")
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
        "address": {
            "@type": "PostalAddress",
            "streetAddress": ADDR["street"],
            "addressLocality": ADDR["city"],
            "addressRegion": ADDR["region"],
            "postalCode": ADDR["postalCode"],
            "addressCountry": ADDR["country"],
        },
    }]
    # A pharmaceutical company with one physical address benefits far more
    # from LocalBusiness than from Organization alone — it is what feeds the
    # map pack for searches like "pharma manufacturer Bengaluru".
    geo = CONTACT.get("geo")
    if geo:
        local = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "@id": BASE + "/#business",
            "name": CO["legal"],
            "image": BASE + IMG + "/logo.png",
            "url": BASE + "/",
            "telephone": CONTACT["phones"][0],
            "email": CONTACT["email"],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": ADDR["street"],
                "addressLocality": ADDR["city"],
                "addressRegion": ADDR["region"],
                "postalCode": ADDR["postalCode"],
                "addressCountry": ADDR["country"],
            },
            "geo": {"@type": "GeoCoordinates", "latitude": geo["lat"], "longitude": geo["lng"]},
        }
        hours = CONTACT.get("openingHours") or []
        if hours:
            local["openingHoursSpecification"] = [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": h["days"],
                    "opens": h["opens"],
                    "closes": h["closes"],
                }
                for h in hours
            ]
        ld.append(local)

    if extra_ld:
        ld.extend(extra_ld)

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta name="theme-color" content="#0b1533">
<meta name="robots" content="index, follow">

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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="{css}">

<script type="application/ld+json">{ld}</script>
{verify}{analytics}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
""".format(
        title=e(title),
        desc=e(description),
        canon=e(canonical(page_key)),
        co=e(CO["name"]),
        ogimg=e(BASE + og),
        img=IMG,
        css=CSS,
        ld=json.dumps(ld if len(ld) > 1 else ld[0], ensure_ascii=False),
        verify=verification_tag(),
        analytics=analytics_tag(),
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


def topbar():
    return """<div class="topbar">
  <div class="wrap">
    <a href="mailto:{mail}">{mail_i}<span>{mail}</span></a>
    <span class="topbar__sep">|</span>
    <a href="tel:{tel_raw}">{ph_i}<span>{tel}</span></a>
    <span class="topbar__sep topbar__hide-sm">|</span>
    <span class="topbar__hide-sm">{tagline}</span>
  </div>
</div>
""".format(
        mail=e(CONTACT["email"]),
        mail_i=icon("mail"),
        ph_i=icon("phone"),
        tel=e(CONTACT["phones"][0]),
        tel_raw=e(CONTACT["phones"][0].replace(" ", "")),
        tagline=e(CO["tagline"]),
    )


def navbar(current):
    links = "".join(
        '<li><a class="nav__link" href="{href}"{cur}>{label}</a></li>'.format(
            href=e(PAGES[key] if key != "home" else "/"),
            label=e(label),
            cur=' aria-current="page"' if key == current else "",
        )
        for key, label in NAV
    )
    return """<nav class="nav" aria-label="Main">
  <div class="wrap">
    <a class="nav__brand" href="/" aria-label="{co} home">
      <img class="nav__logo" src="{img}/logo.png" alt="{co} — {tag}" width="378" height="175">
    </a>
    <button class="nav__toggle" type="button" aria-expanded="false" aria-controls="nav-menu" aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
    <ul class="nav__menu" id="nav-menu">
      {links}
      <li class="nav__cta"><a class="btn btn--primary btn--sm" href="{contact}">Enquire Now</a></li>
    </ul>
  </div>
</nav>
""".format(co=e(CO["name"]), tag=e(CO["tagline"]), img=IMG, links=links, contact=e(PAGES["contact"]))


def rail():
    return """<div class="rail">
  <a class="rail__btn rail__btn--wa" href="https://wa.me/{wa}" target="_blank" rel="noopener" data-label="WhatsApp" aria-label="Chat on WhatsApp">{wa_i}</a>
  <a class="rail__btn rail__btn--phone" href="tel:{tel_raw}" data-label="Call us" aria-label="Call us">{ph_i}</a>
  <a class="rail__btn rail__btn--mail" href="mailto:{mail}" data-label="Email us" aria-label="Email us">{mail_i}</a>
</div>
<button class="totop" type="button" aria-label="Back to top">{up_i}</button>

<div class="mobilebar">
  <div class="mobilebar__inner">
    <a class="mobilebar__btn" href="tel:{tel_raw}">{ph_i2}<span>Call</span></a>
    <a class="mobilebar__btn mobilebar__btn--wa" href="https://wa.me/{wa}" target="_blank" rel="noopener">{wa_i2}<span>WhatsApp</span></a>
    <a class="mobilebar__btn mobilebar__btn--cta" href="{contact}">{mail_i2}<span>Enquire</span></a>
  </div>
</div>
""".format(
        wa=e(CONTACT["whatsapp"]),
        wa_i=icon("whatsapp"),
        wa_i2=icon("whatsapp"),
        tel_raw=e(CONTACT["phones"][0].replace(" ", "")),
        ph_i=icon("phone"),
        ph_i2=icon("phone"),
        mail=e(CONTACT["email"]),
        mail_i=icon("mail"),
        mail_i2=icon("mail"),
        up_i=icon("chevup"),
        contact=e(PAGES["contact"]),
    )


def lightbox():
    return """<div class="lightbox" role="dialog" aria-modal="true" aria-label="Product image" aria-hidden="true">
  <div class="lightbox__stage">
    <button class="lightbox__close" type="button" aria-label="Close">{close}</button>
    <button class="lightbox__nav lightbox__nav--prev" type="button" aria-label="Previous product">{prev}</button>
    <img class="lightbox__img" src="" alt="">
    <p class="lightbox__caption"></p>
    <button class="lightbox__nav lightbox__nav--next" type="button" aria-label="Next product">{next}</button>
  </div>
</div>
""".format(close=icon("close"), prev=icon("chevleft"), next=icon("chevright"))


def footer():
    phones = "".join(
        '<div class="footer__item">{i}<a href="tel:{raw}">{p}</a></div>'.format(
            i=icon("phone"), raw=e(p.replace(" ", "")), p=e(p)
        )
        for p in CONTACT["phones"]
    )
    hours = "".join(
        "<div><dt>{d}</dt><dd>{t}</dd></div>".format(d=e(h["days"]), t=e(h["time"]))
        for h in SITE["hours"]
    )
    quick = "".join(
        '<a href="{href}">{label}</a>'.format(href=e(PAGES[k] if k != "home" else "/"), label=e(l))
        for k, l in NAV
    )
    addr = "{s}, {l}, {c}, {r} {p}".format(
        s=ADDR["street"], l=ADDR["locality"], c=ADDR["city"], r=ADDR["region"], p=ADDR["postalCode"]
    )

    return """<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <img class="footer__logo" src="{img}/logo-white.png" alt="{co}" width="378" height="175">
        <p class="footer__about">{blurb}</p>
      </div>

      <div>
        <h4>Quick Links</h4>
        <div class="footer__links">{quick}</div>
      </div>

      <div>
        <h4>Reach Us</h4>
        <div class="footer__contact">
          <div class="footer__item">{pin}<span>{addr}</span></div>
          {phones}
          <div class="footer__item">{mail_i}<a href="mailto:{mail}">{mail}</a></div>
        </div>
      </div>

      <div>
        <h4>Open Hours</h4>
        <dl class="hours">{hours}</dl>
        <form class="newsletter" action="/healabspharma/backend/signup_newsletter.php" method="POST">
          <label class="sr-only" for="nl-email">Email address</label>
          <div class="hp" aria-hidden="true">
            <label for="nl-website">Leave this field empty</label>
            <input id="nl-website" type="text" name="website" tabindex="-1" autocomplete="off">
          </div>
          <div class="newsletter__row">
            <input id="nl-email" type="email" name="email" placeholder="Your email" required>
            <button class="btn btn--primary btn--sm" type="submit">Join</button>
          </div>
        </form>
      </div>
    </div>

    <p class="disclaimer"><strong>Note:</strong> The product information on this site is intended for
    healthcare professionals and general reference. It is not medical advice. Always consult a
    qualified physician before starting, stopping or changing any medication.</p>

    <div class="footer__bottom">
      <p>&copy; <span data-year>{year}</span> {legal}. All rights reserved.</p>
      <p>{tagline}</p>
    </div>
  </div>
</footer>
{rail}
{lightbox}
<script src="{js}" defer></script>
</body>
</html>
""".format(
        img=IMG, co=e(CO["name"]), blurb=e(CO["blurb"]), quick=quick,
        pin=icon("pin"), addr=e(addr), phones=phones, mail_i=icon("mail"),
        mail=e(CONTACT["email"]), hours=hours, year=date.today().year,
        legal=e(CO["legal"]), tagline=e(CO["tagline"]),
        rail=rail(), lightbox=lightbox(), js=JS,
    )


# ------------------------------------------------------- product card -----
def product_card(p, idx):
    img_path = "%s/product-images/%s" % (IMG, p["image"])
    desc_id = "d-%s" % p["slug"]
    return """<article class="product reveal" data-delay="{delay}" data-category="{cat}" data-name="{name}" data-form="{form}">
  <button class="product__media" type="button"
          data-lightbox="{img}" data-caption="{name}"
          aria-label="View larger image of {name}">
    {pic}
    <span class="product__zoom">{zoom}</span>
  </button>
  <div class="product__body">
    <div class="product__tags">
      <span class="tag">{cat}</span>
      <span class="tag tag--form">{form}</span>
    </div>
    <h3 class="product__name"><a href="{href}">{name}</a></h3>
    <p class="product__desc" id="{did}">{desc}</p>
    <a class="product__more" href="{href}">View details{arrow}</a>
  </div>
</article>
""".format(
        delay=(idx % 3) + 1,
        cat=e(p["category"]),
        name=e(p["name"]),
        form=e(p["form"]),
        img=e(img_path),
        pic=picture(img_path, p["name"] + " — " + p["form"] + " by " + CO["name"],
                    sizes="(max-width: 700px) 92vw, 360px"),
        zoom=icon("zoom"),
        did=e(desc_id),
        desc=e(p["description"]),
        href=e(product_url(p)),
        arrow=icon("chevright"),
    )


def product_ld(p):
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": p["name"],
        "category": p["category"],
        "description": p["description"][:300],
        "image": BASE + IMG + "/product-images/" + p["image"],
        "brand": {"@type": "Brand", "name": CO["name"]},
        "manufacturer": {"@type": "Organization", "name": CO["legal"]},
    }


def initial(name):
    """First letter of the actual name, skipping an honorific like 'Dr.'."""
    parts = [p for p in name.split() if p.rstrip(".").lower() not in ("dr", "mr", "mrs", "ms", "prof")]
    return (parts[0] if parts else name)[0].upper()


def crumbs(label):
    return """<nav class="crumbs" aria-label="Breadcrumb">
  <a href="/">Home</a>{chev}<span aria-current="page">{label}</span>
</nav>
""".format(chev=icon("chevright"), label=e(label))


def pagehead_bg(jpg_path):
    """Two custom properties: a safe JPEG default and a WebP upgrade.

    The stylesheet uses --img normally and only reaches for --img-set inside
    an @supports block, because a var() that resolves to something the
    browser cannot parse drops the declaration entirely.
    """
    jpg = ver(jpg_path)
    webp = re.sub(r"\.(jpe?g|png)$", ".webp", jpg_path, flags=re.I)
    out = "--img:url('%s')" % jpg
    if os.path.exists(os.path.join(ROOT, webp.lstrip("/"))):
        out += ";--img-set:image-set(url('%s') type('image/webp'),url('%s') type('image/jpeg'))" % (ver(webp), jpg)
    return out


def pagehead(title, lead, img, crumb_label):
    return """<header class="pagehead" style="{img}">
  <div class="wrap">
    {crumbs}
    <h1>{title}</h1>
    <p>{lead}</p>
  </div>
</header>
""".format(img=e(pagehead_bg(img)), crumbs=crumbs(crumb_label), title=e(title), lead=e(lead))


# -------------------------------------------------------------- home ------
def about_heading():
    """Only claim a founding year if site.json actually carries one."""
    year = CO.get("founded")
    return "Caring for wellness, since %s" % year if year else "Caring for wellness"


def build_home():
    slides = "".join(
        '<div class="hero__slide{active}" style="{bg}"></div>'.format(
            active=" is-active" if i == 0 else "", bg=e(bg_image(IMG + "/banners/" + s["image"]))
        )
        for i, s in enumerate(SITE["hero"])
    )
    texts = "".join(
        """<div class="hero__text"{hidden}>
      <span class="eyebrow">{eyebrow}</span>
      <h1>{title}</h1>
      <p class="hero__lead">{lead}</p>
      <div class="hero__actions">
        <a class="btn btn--primary" href="{products}">Explore our products{arrow}</a>
        <a class="btn btn--on-dark" href="{contact}">Talk to us</a>
      </div>
    </div>""".format(
            hidden="" if i == 0 else " hidden",
            eyebrow=e(s["eyebrow"]), title=e(s["title"]), lead=e(s["lead"]),
            products=e(PAGES["products"]), contact=e(PAGES["contact"]), arrow=icon("arrow"),
        )
        for i, s in enumerate(SITE["hero"])
    )
    dots = "".join(
        '<button class="hero__dot" type="button" role="tab" aria-selected="{sel}" aria-label="Slide {n}"></button>'.format(
            sel="true" if i == 0 else "false", n=i + 1
        )
        for i in range(len(SITE["hero"]))
    )
    trust = "".join(
        '<div class="trust">{i}<span>{t}</span></div>'.format(i=icon(t["icon"]), t=e(t["text"]))
        for t in SITE["trust"]
    )
    stats = "".join(
        '<div class="stat reveal" data-delay="{d}"><span class="stat__n" data-count="{n}" data-suffix="{s}">0</span>'
        '<span class="stat__label">{l}</span></div>'.format(
            d=i + 1, n=s["n"], s=e(s["suffix"]), l=e(s["label"])
        )
        for i, s in enumerate(SITE["stats"])
    )
    values = "".join(
        '<div class="feature reveal" data-delay="{d}"><div class="feature__icon">{i}</div>'
        "<h3>{t}</h3><p>{x}</p></div>".format(
            d=(i % 4) + 1, i=icon(v["icon"]), t=e(v["title"]), x=e(v["text"])
        )
        for i, v in enumerate(SITE["values"])
    )
    featured = [p for p in PRODUCTS if p.get("featured")] or PRODUCTS[:6]
    cards = "".join(product_card(p, i) for i, p in enumerate(featured))
    quotes = "".join(
        """<figure class="quote reveal" data-delay="{d}">
      <div class="quote__mark" aria-hidden="true">&ldquo;</div>
      <blockquote><p>{q}</p></blockquote>
      <figcaption class="quote__by">
        <span class="quote__avatar" aria-hidden="true">{ini}</span>
        <span><span class="quote__name">{n}</span><span class="quote__role">{r}</span></span>
      </figcaption>
    </figure>""".format(
            d=i + 1, q=e(t["quote"]), ini=e(initial(t["name"])), n=e(t["name"]), r=e(t["role"])
        )
        for i, t in enumerate(SITE["testimonials"])
    )

    body = """{head}{topbar}{nav}
<main id="main" class="page page--flush">

  <section class="hero" aria-label="Featured">
    <div class="hero__slides" aria-hidden="true">{slides}</div>
    <div class="wrap"><div class="hero__inner">{texts}</div></div>
    <div class="hero__dots" role="tablist" aria-label="Choose slide">{dots}</div>
  </section>

  <div class="trustbar">
    <div class="wrap"><div class="grid grid--4">{trust}</div></div>
  </div>

  <section class="section">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Why Heal Labs</span>
        <h2>Medicine you can stand behind</h2>
        <p>We formulate, source and supply with one test in mind — would we give it to our own family?</p>
      </div>
      <div class="grid grid--4">{values}</div>
    </div>
  </section>

  <section class="section section--tint">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Our Products</span>
        <h2>Formulations clinicians reach for</h2>
        <p>A focused range across anti-infectives, pain and fever, respiratory care, gastro and nutrition.</p>
      </div>
      <div class="grid grid--3" data-catalogue>{cards}</div>
      <div class="text-center mt-7 reveal">
        <a class="btn btn--navy" href="{products}">View all {total} products{arrow}</a>
      </div>
    </div>
  </section>

  <section class="section section--navy">
    <div class="wrap"><div class="grid grid--4">{stats}</div></div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="split">
        <div class="split__media reveal">{aboutimg}</div>
        <div class="reveal" data-delay="1">
          <span class="eyebrow">About Us</span>
          <h2>{about_heading}</h2>
          <p>{intro}</p>
          <ul class="checklist">
            <li>{ck}<span>Quality-assured manufacturing at certified facilities</span></li>
            <li>{ck}<span>Pediatric-friendly suspensions, syrups and drops</span></li>
            <li>{ck}<span>Consistent supply for pharmacies and distributors</span></li>
          </ul>
          <p class="mt-6"><a class="btn btn--ghost" href="{about}">More about us{arrow}</a></p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tint">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Testimonials</span>
        <h2>What our partners say</h2>
      </div>
      <div class="grid grid--3">{quotes}</div>
    </div>
  </section>

  <section class="section section--navy">
    <div class="wrap wrap--narrow text-center">
      <div class="reveal">
        <span class="eyebrow">Get in touch</span>
        <h2>Looking for a supply partner?</h2>
        <p>Tell us what you need — we usually reply the same working day.</p>
        <p class="mt-6">
          <a class="btn btn--primary" href="{contact}">Send an enquiry{arrow}</a>
          <a class="btn btn--on-dark" href="https://wa.me/{wa}" target="_blank" rel="noopener">WhatsApp us</a>
        </p>
      </div>
    </div>
  </section>

</main>
{footer}""".format(
        head=head(
            "{co} — {tag} | Pharmaceutical Company in Bengaluru".format(co=CO["name"], tag=CO["tagline"]),
            CO["blurb"],
            "home",
        ),
        topbar=topbar(), nav=navbar("home"),
        slides=slides, texts=texts, dots=dots, trust=trust, values=values,
        cards=cards, products=e(PAGES["products"]), total=len(PRODUCTS), arrow=icon("arrow"),
        stats=stats,
        aboutimg=picture(IMG + "/about.jpeg", "A pharmacist selecting a medication box from a dispensary shelf", loading="lazy"),
        about_heading=e(about_heading()), intro=e(SITE["about"]["intro"]), ck=icon("check"),
        about=e(PAGES["about"]), quotes=quotes, contact=e(PAGES["contact"]),
        wa=e(CONTACT["whatsapp"]),
        footer=footer(),
    )
    return body


# ------------------------------------------------------------- about ------
def build_about():
    values = "".join(
        '<div class="vcard reveal" data-delay="{d}"><h3>{t}</h3><p>{x}</p></div>'.format(
            d=(i % 4) + 1, t=e(v["title"]), x=e(v["text"])
        )
        for i, v in enumerate(SITE["values"])
    )
    return """{head}{topbar}{nav}
<main id="main" class="page page--flush">
  {ph}

  <section class="section">
    <div class="wrap">
      <div class="split">
        <div class="split__media reveal">{img1}</div>
        <div class="reveal" data-delay="1">
          <span class="eyebrow">Who we are</span>
          <h2>A pharmaceutical company built on trust</h2>
          <p>{intro}</p>
          <ul class="checklist">
            <li>{ck}<span>{n} formulations across {c} therapeutic areas</span></li>
            <li>{ck}<span>Based in Bengaluru, supplying across India</span></li>
            <li>{ck}<span>Direct support for clinicians, pharmacies and distributors</span></li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tint">
    <div class="wrap">
      <div class="split split--flip">
        <div class="split__media reveal">{img2}</div>
        <div class="reveal" data-delay="1">
          <span class="eyebrow">Our Mission</span>
          <h2>Closing the gap between patient and medicine</h2>
          <p>{mission}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="split">
        <div class="split__media reveal">{img3}</div>
        <div class="reveal" data-delay="1">
          <span class="eyebrow">Our Vision</span>
          <h2>Healthcare that reaches everyone</h2>
          <p>{vision}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tint">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">What guides us</span>
        <h2>Our values</h2>
      </div>
      <div class="vgrid">{values}</div>
    </div>
  </section>

  <section class="section section--navy">
    <div class="wrap wrap--narrow text-center reveal">
      <h2>Work with us</h2>
      <p>Distributors, pharmacies and clinicians — we would like to hear from you.</p>
      <p class="mt-6"><a class="btn btn--primary" href="{contact}">Contact the team{arrow}</a></p>
    </div>
  </section>
</main>
{footer}""".format(
        head=head(
            "About Us — {co} | {legal}".format(co=CO["name"], legal=CO["legal"]),
            "Heal Labs is a Bengaluru-based pharmaceutical company supplying quality-assured medicines across five therapeutic areas. Read about our mission, vision and values.",
            "about",
            og_image=IMG + "/about.jpeg",
        ),
        topbar=topbar(), nav=navbar("about"),
        ph=pagehead("About Heal Labs",
                    "Caring for wellness — how we work and what we stand for.",
                    IMG + "/title-image.jpeg", "About Us"),
        img1=picture(IMG + "/about.jpeg", "A pharmacist selecting a medication box from a dispensary shelf"),
        img2=picture(IMG + "/about1.jpeg", "Shelves stocked with a wide range of packaged medicines"),
        img3=picture(IMG + "/about2.jpeg", "A scientist pipetting samples into test tubes in a laboratory"),
        intro=e(SITE["about"]["intro"]), ck=icon("check"),
        n=len(PRODUCTS), c=len(set(p["category"] for p in PRODUCTS)),
        mission=e(SITE["about"]["mission"]), vision=e(SITE["about"]["vision"]),
        values=values, contact=e(PAGES["contact"]), arrow=icon("arrow"),
        footer=footer(),
    )


# ---------------------------------------------------------- products ------
def build_products():
    cats = []
    for p in PRODUCTS:
        if p["category"] not in cats:
            cats.append(p["category"])
    cats.sort()

    chips = '<button class="chip" type="button" data-filter="all" aria-pressed="true">All<span class="chip__n">{n}</span></button>'.format(n=len(PRODUCTS))
    for c in cats:
        n = sum(1 for p in PRODUCTS if p["category"] == c)
        chips += '<button class="chip" type="button" data-filter="{c}" aria-pressed="false">{c}<span class="chip__n">{n}</span></button>'.format(c=e(c), n=n)

    cards = "".join(product_card(p, i) for i, p in enumerate(PRODUCTS))

    ld = [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Heal Labs product range",
        "numberOfItems": len(PRODUCTS),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": product_ld(p)}
            for i, p in enumerate(PRODUCTS)
        ],
    }]

    return """{head}{topbar}{nav}
<main id="main" class="page page--flush">
  {ph}

  <section class="section">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Full range</span>
        <h2>Our products</h2>
        <p>Browse by therapeutic area, or search by name and dosage form.
           Showing <strong data-result-count>{n}</strong> of {n} products.</p>
      </div>

      <div class="search reveal">
        {si}
        <label class="sr-only" for="product-search">Search products</label>
        <input id="product-search" type="search" data-search placeholder="Search by name, form or category…" autocomplete="off">
      </div>

      <div class="filters reveal">{chips}</div>

      <div class="grid grid--3" data-catalogue>
        {cards}
        <p class="empty-state" data-empty hidden>No products match that search. Try a different term or choose “All”.</p>
      </div>
    </div>
  </section>

  <section class="section section--navy">
    <div class="wrap wrap--narrow text-center reveal">
      <h2>Need pricing or availability?</h2>
      <p>Send us the list — we will come back to you with stock and rates.</p>
      <p class="mt-6">
        <a class="btn btn--primary" href="{contact}">Request a quote{arrow}</a>
        <a class="btn btn--on-dark" href="https://wa.me/{wa}" target="_blank" rel="noopener">WhatsApp us</a>
      </p>
    </div>
  </section>
</main>
{footer}""".format(
        head=head(
            "Products — {n} Pharmaceutical Formulations | {co}".format(n=len(PRODUCTS), co=CO["name"]),
            "Browse the full Heal Labs range: {n} formulations across anti-infectives, pain and fever, respiratory and allergy, gastro and nutraceuticals.".format(n=len(PRODUCTS)),
            "products",
            extra_ld=ld,
        ),
        topbar=topbar(), nav=navbar("products"),
        ph=pagehead("Our Products",
                    "{n} formulations across {c} therapeutic areas — tablets, suspensions, syrups, drops and injections.".format(
                        n=len(PRODUCTS), c=len(cats)),
                    IMG + "/title-image.jpeg", "Products"),
        n=len(PRODUCTS), si=icon("search"), chips=chips, cards=cards,
        contact=e(PAGES["contact"]), arrow=icon("arrow"), wa=e(CONTACT["whatsapp"]),
        footer=footer(),
    )


# ----------------------------------------------------------- contact ------
def crumbs_deep(trail):
    """Breadcrumbs with more than one level. `trail` is (label, href-or-None)."""
    parts = []
    for label, href in trail:
        if href:
            parts.append('<a href="%s">%s</a>' % (e(href), e(label)))
        else:
            parts.append('<span aria-current="page">%s</span>' % e(label))
    return '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>\n' % icon("chevright").join(parts)


def build_product(p):
    """One page per product — each drug name is something people search for."""
    img_path = "%s/product-images/%s" % (IMG, p["image"])
    url = product_url(p)

    related = [r for r in PRODUCTS if r["category"] == p["category"] and r["slug"] != p["slug"]][:3]
    rel_cards = "".join(
        """<a class="related" href="{href}">
        {pic}
        <span class="related__body">
          <span class="tag tag--form">{form}</span>
          <span class="related__name">{name}</span>
        </span>
      </a>""".format(
            href=e(product_url(r)),
            pic=picture("%s/product-images/%s" % (IMG, r["image"]), r["name"], sizes="180px"),
            form=e(r["form"]), name=e(r["name"]),
        )
        for r in related
    )

    wa_text = "Hello Heal Labs, I would like to enquire about %s (%s)." % (p["name"], p["form"])
    from urllib.parse import quote
    wa_href = "https://wa.me/%s?text=%s" % (CONTACT["whatsapp"], quote(wa_text))

    ld = [
        product_ld(p),
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products", "item": BASE + PAGES["products"]},
                {"@type": "ListItem", "position": 3, "name": p["name"], "item": BASE + url},
            ],
        },
    ]

    desc = p["description"]
    meta = (desc[:150].rsplit(" ", 1)[0] + "…") if len(desc) > 155 else desc

    return """{head}{topbar}{nav}
<main id="main" class="page">
  <section class="section">
    <div class="wrap">
      {crumbs}
      <div class="pd">
        <div class="pd__media reveal">
          <button class="pd__zoom" type="button" data-lightbox="{img}" data-caption="{name}"
                  aria-label="View larger image of {name}">
            {pic}
            <span class="product__zoom">{zoom}</span>
          </button>
        </div>
        <div class="pd__body reveal" data-delay="1">
          <div class="product__tags">
            <span class="tag">{cat}</span>
            <span class="tag tag--form">{form}</span>
          </div>
          <h1>{name}</h1>
          <p class="pd__lead">{desc}</p>

          <dl class="pd__facts">
            <div><dt>Dosage form</dt><dd>{form}</dd></div>
            <div><dt>Therapeutic area</dt><dd>{cat}</dd></div>
            <div><dt>Marketed by</dt><dd>{legal}</dd></div>
          </dl>

          <div class="pd__actions">
            <a class="btn btn--primary" href="{contact}">Request pricing{arrow}</a>
            <a class="btn btn--ghost" href="{wa}" target="_blank" rel="noopener">Ask on WhatsApp</a>
          </div>

          <p class="pd__note">Prescription medicine. The information here is for
             healthcare professionals and general reference, and is not medical
             advice — always follow your physician's direction.</p>
        </div>
      </div>
    </div>
  </section>

  {related_block}
</main>
{footer}""".format(
        head=head(
            "{n} — {form} | {co}".format(n=p["name"], form=p["form"], co=CO["name"]),
            meta,
            url,
            extra_ld=ld,
            og_image=img_path,
        ),
        topbar=topbar(), nav=navbar("products"),
        crumbs=crumbs_deep([("Home", "/"), ("Products", PAGES["products"]), (p["name"], None)]),
        img=e(img_path),
        pic=picture(img_path, "%s — %s by %s" % (p["name"], p["form"], CO["name"]),
                    loading="eager", sizes="(max-width: 800px) 92vw, 460px"),
        zoom=icon("zoom"),
        name=e(p["name"]), cat=e(p["category"]), form=e(p["form"]),
        desc=e(desc), legal=e(CO["legal"]),
        contact=e(PAGES["contact"]), arrow=icon("arrow"), wa=e(wa_href),
        related_block=(
            """<section class="section section--tint">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Same category</span>
        <h2>Other {cat} products</h2>
      </div>
      <div class="related-grid">{cards}</div>
      <p class="text-center mt-7"><a class="btn btn--navy" href="{all}">View all {n} products{arrow}</a></p>
    </div>
  </section>""".format(cat=e(p["category"]), cards=rel_cards, all=e(PAGES["products"]),
                       n=len(PRODUCTS), arrow=icon("arrow"))
            if related else ""
        ),
        footer=footer(),
    )


def build_contact():
    phones = "".join(
        '<a href="tel:{raw}">{p}</a>'.format(raw=e(p.replace(" ", "")), p=e(p))
        for p in CONTACT["phones"]
    )
    addr = "{s}<br>{l}<br>{c}, {r} {p}".format(
        s=e(ADDR["street"]), l=e(ADDR["locality"]), c=e(ADDR["city"]),
        r=e(ADDR["region"]), p=e(ADDR["postalCode"])
    )
    hours = "".join(
        "<div><dt>{d}</dt><dd>{t}</dd></div>".format(d=e(h["days"]), t=e(h["time"]))
        for h in SITE["hours"]
    )

    return """{head}{topbar}{nav}
<main id="main" class="page page--flush">
  {ph}

  <section class="section">
    <div class="wrap">
      <div class="split">
        <div class="reveal">
          <span class="eyebrow">Enquire now</span>
          <h2>Send us a message</h2>
          <p>Whether you are a clinician, pharmacy or distributor — tell us what you need
             and we will get back to you, usually the same working day.</p>

          <div class="grid grid--3 mt-7" style="grid-template-columns:1fr;gap:1rem">
            <div class="contact-card">
              <div class="contact-card__icon">{pin}</div>
              <div><h3>Visit us</h3><p>{addr}</p></div>
            </div>
            <div class="contact-card">
              <div class="contact-card__icon">{ph_i}</div>
              <div><h3>Call us</h3>{phones}</div>
            </div>
            <div class="contact-card">
              <div class="contact-card__icon">{mail_i}</div>
              <div><h3>Email us</h3><a href="mailto:{mail}">{mail}</a></div>
            </div>
            <div class="contact-card">
              <div class="contact-card__icon">{clock}</div>
              <div><h3>Open hours</h3><dl class="hours">{hours}</dl></div>
            </div>
          </div>
        </div>

        <div class="reveal" data-delay="1">
          <form class="form-card" action="/healabspharma/backend/submit_contact.php" method="POST" novalidate>
            <h3>Inquire now</h3>
            <p class="field__hint" style="margin-bottom:1.5rem">Fields marked <span class="req">*</span> are required.</p>

            <div class="field">
              <label for="c-name">Your name <span class="req">*</span></label>
              <input id="c-name" name="name" type="text" required autocomplete="name" placeholder="Full name">
            </div>
            <div class="field">
              <label for="c-email">Email address <span class="req">*</span></label>
              <input id="c-email" name="email" type="email" required autocomplete="email" placeholder="you@example.com">
            </div>
            <div class="field">
              <label for="c-phone">Phone number</label>
              <input id="c-phone" name="phone" type="tel" autocomplete="tel" placeholder="+91 00000 00000"
                     pattern="[0-9+()\\s-]{{7,20}}">
            </div>
            <div class="field">
              <label for="c-message">How can we help? <span class="req">*</span></label>
              <textarea id="c-message" name="message" required placeholder="Products you are interested in, quantities, or any question…"></textarea>
            </div>
            <div class="hp" aria-hidden="true">
              <label for="c-website">Leave this field empty</label>
              <input id="c-website" type="text" name="website" tabindex="-1" autocomplete="off">
            </div>
            <button class="btn btn--primary btn--block" type="submit">Send enquiry{arrow}</button>
            <p class="field__hint text-center" style="margin-top:1rem">
              We use your details only to answer your enquiry.
            </p>
          </form>
        </div>
      </div>
    </div>
  </section>

  <section class="section section--tint">
    <div class="wrap">
      <div class="sec-head sec-head--center reveal">
        <span class="eyebrow">Find us</span>
        <h2>Our location</h2>
      </div>
      <div class="reveal">
        <iframe class="map-frame" src="{map}" title="Map showing the Heal Labs office in Bengaluru"
                loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
      </div>
    </div>
  </section>
</main>
{footer}""".format(
        head=head(
            "Contact Us — {co} | Bengaluru".format(co=CO["name"]),
            "Get in touch with Heal Labs Pharmaceutical, Bengaluru. Call +91 93078 45862, email healabspharma@gmail.com, or send an enquiry for pricing and availability.",
            "contact",
        ),
        topbar=topbar(), nav=navbar("contact"),
        ph=pagehead("Contact Us",
                    "We are available seven days a week for enquiries, pricing and supply.",
                    IMG + "/title-image.jpeg", "Contact"),
        pin=icon("pin"), addr=addr, ph_i=icon("phone"), phones=phones,
        mail_i=icon("mail"), mail=e(CONTACT["email"]), clock=icon("clock"), hours=hours,
        arrow=icon("arrow"), map=e(CONTACT["mapEmbed"]),
        footer=footer(),
    )


# ------------------------------------------------------ status pages ------
def build_status(kind):
    ok = kind == "success"
    title = "Thank you — message received" if ok else "Something went wrong"
    lead = ("Your enquiry has reached us. A member of the team will get back to you shortly, "
            "usually within one working day.") if ok else \
           ("We could not submit your message. Please try again, or reach us directly by phone "
            "or WhatsApp and we will pick it up right away.")
    return """{head}{topbar}{nav}
<main id="main" class="page">
  <section class="status">
    <div class="wrap wrap--narrow">
      <div class="status__icon status__icon--{cls}">{i}</div>
      <h1>{title}</h1>
      <p style="font-size:var(--step-1)">{lead}</p>
      <p class="mt-7">
        <a class="btn btn--primary" href="/">Back to home{arrow}</a>
        <a class="btn btn--ghost" href="{contact}">{again}</a>
      </p>
    </div>
  </section>
</main>
{footer}""".format(
        head=head(("Thank You" if ok else "Submission Failed") + " — " + CO["name"],
                  lead, "contact"),
        topbar=topbar(), nav=navbar(""),
        cls="ok" if ok else "err",
        i=icon("check") if ok else icon("alert"),
        title=e(title), lead=e(lead), arrow=icon("arrow"),
        contact=e(PAGES["contact"]), again="Contact us" if ok else "Try again",
        footer=footer(),
    )


def build_404():
    return """{head}{topbar}{nav}
<main id="main" class="page">
  <section class="status">
    <div class="wrap wrap--narrow">
      <div class="status__icon status__icon--err">{i}</div>
      <p class="eyebrow">Error 404</p>
      <h1>We cannot find that page</h1>
      <p style="font-size:var(--step-1)">The link may be out of date, or the page may have moved.
         Our full product range and contact details are a click away.</p>
      <p class="mt-7">
        <a class="btn btn--primary" href="/">Back to home{arrow}</a>
        <a class="btn btn--ghost" href="{products}">Browse products</a>
      </p>
    </div>
  </section>
</main>
{footer}""".format(
        head=head("Page Not Found — " + CO["name"],
                  "The page you were looking for is not here. Browse the Heal Labs product range or get in touch.",
                  "home").replace('<meta name="robots" content="index, follow">',
                                  '<meta name="robots" content="noindex, follow">'),
        topbar=topbar(), nav=navbar(""), i=icon("alert"), arrow=icon("arrow"),
        products=e(PAGES["products"]), footer=footer(),
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


# ------------------------------------------------------------ sitemap -----
def build_sitemap():
    today = date.today().isoformat()
    entries = [("/", "1.0", "weekly"),
               (PAGES["products"], "0.9", "weekly"),
               (PAGES["about"], "0.7", "monthly"),
               (PAGES["contact"], "0.7", "monthly")]
    entries += [(product_url(p), "0.8", "monthly") for p in PRODUCTS]
    urls = "".join(
        "  <url><loc>{base}{loc}</loc><lastmod>{d}</lastmod>"
        "<changefreq>{cf}</changefreq><priority>{p}</priority></url>\n".format(
            base=BASE, loc=loc, d=today, cf=cf, p=pr
        )
        for loc, pr, cf in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + urls
        + "</urlset>\n"
    )


def build_robots():
    return """User-agent: *
Allow: /
Disallow: /healabspharma/backend/
Disallow: /healabspharma/build/
Disallow: /healabspharma/data/

Sitemap: {base}/sitemap.xml
""".format(base=BASE)


# --------------------------------------------------------------- main -----
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
