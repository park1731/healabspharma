/* ==========================================================================
   Heal Labs Pharma — site behaviour v2
   Vanilla JS, no dependencies. Every page reads and works without it; the
   script adds motion and conveniences on top. All motion honours
   prefers-reduced-motion.
   ========================================================================== */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var $  = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };
  var clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };

  /* ------------------------------------------------------- Scroll loop ---
     One rAF-throttled scroll handler drives the header, progress bar,
     timeline and parallax, instead of four separate listeners. */
  var scrollJobs = [];
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var y = window.scrollY;
      scrollJobs.forEach(function (fn) { fn(y); });
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);

  /* ---------------------------------------------------------------- Header */
  function initHeader() {
    var header = $("[data-header]");
    if (!header) return;
    var toggle = $(".nav__toggle", header);
    var menu = $(".nav__menu", header);

    // The header stays pinned at all times; it only switches from transparent
    // (over the dark hero) to solid white once the page has scrolled.
    scrollJobs.push(function (y) {
      header.classList.toggle("is-stuck", y > 24);
    });

    if (!toggle || !menu) return;
    function setOpen(open) {
      menu.classList.toggle("is-open", open);
      header.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      document.body.classList.toggle("no-scroll", open);
    }
    toggle.addEventListener("click", function () { setOpen(!menu.classList.contains("is-open")); });
    $$("a", menu).forEach(function (a) { a.addEventListener("click", function () { setOpen(false); }); });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 900 && menu.classList.contains("is-open")) setOpen(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("is-open")) { setOpen(false); toggle.focus(); }
    });
  }

  /* ---------------------------------------------------------- Progress bar */
  function initProgress() {
    var bar = $(".progress");
    if (!bar) return;
    scrollJobs.push(function (y) {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.setProperty("--progress", max > 0 ? clamp(y / max, 0, 1) : 0);
    });
  }

  /* --------------------------------------------------------- Scroll reveal */
  // Tilt cards drive their own transform. Once the entrance has played, drop
  // the reveal classes so the hover/tilt transform takes over. Every path
  // that shows a card (scroll, tab switch, catalogue filter) goes through here.
  function revealNow(el) {
    if (!el.classList.contains("reveal") || el.dataset.revealing) return;
    el.classList.add("is-in");
    if (el.hasAttribute("data-tilt")) {
      el.dataset.revealing = "1";
      var d = (parseInt(el.dataset.delay, 10) || 0) * 80;
      setTimeout(function () { el.classList.remove("reveal", "is-in"); delete el.dataset.revealing; }, reduceMotion ? 0 : 1000 + d);
    }
  }

  function initReveal() {
    var items = $$(".reveal");
    if (!items.length) return;

    var done = revealNow;

    if (reduceMotion || !("IntersectionObserver" in window)) { items.forEach(done); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { done(entry.target); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -50px 0px" });
    items.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------- Animated counters */
  function initCounters() {
    var nums = $$("[data-count]");
    if (!nums.length || reduceMotion || !("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target, target = parseFloat(el.dataset.count), suffix = el.dataset.suffix || "";
        var start = performance.now();
        (function step(now) {
          var p = Math.min((now - start) / 1600, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 4))) + suffix;
          if (p < 1) requestAnimationFrame(step);
        })(start);
        io.unobserve(el);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------ Molecule network */
  function initMolecules() {
    $$("[data-molecules]").forEach(function (canvas) {
      var ctx = canvas.getContext("2d");
      if (!ctx) return;
      var host = canvas.parentElement;              // the .fx layer: sizes the canvas
      var zone = host.parentElement || host;          // the section: receives the pointer
      var low = canvas.dataset.density === "low";
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var W = 0, H = 0, nodes = [], running = false, visible = true, raf = 0;
      var mouse = { x: -9999, y: -9999 };
      var LINK = 140;

      function build() {
        var r = host.getBoundingClientRect();
        W = r.width; H = r.height;
        canvas.width = W * dpr; canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        var n = Math.round(clamp((W * H) / (low ? 26000 : 15000), 18, low ? 46 : 90));
        nodes = [];
        for (var i = 0; i < n; i++) {
          nodes.push({
            x: Math.random() * W, y: Math.random() * H,
            vx: (Math.random() - 0.5) * 0.28, vy: (Math.random() - 0.5) * 0.28,
            r: Math.random() < 0.12 ? 3.2 : 1.6 + Math.random() * 1.2,
            aqua: Math.random() < 0.3
          });
        }
      }

      function draw() {
        ctx.clearRect(0, 0, W, H);
        var i, j, a, b, dx, dy, d;
        for (i = 0; i < nodes.length; i++) {
          a = nodes[i];
          for (j = i + 1; j < nodes.length; j++) {
            b = nodes[j];
            dx = a.x - b.x; dy = a.y - b.y; d = dx * dx + dy * dy;
            if (d < LINK * LINK) {
              ctx.strokeStyle = "rgba(120,170,255," + (0.22 * (1 - Math.sqrt(d) / LINK)).toFixed(3) + ")";
              ctx.lineWidth = 1;
              ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
            }
          }
          dx = a.x - mouse.x; dy = a.y - mouse.y; d = Math.sqrt(dx * dx + dy * dy);
          if (d < 180) {
            ctx.strokeStyle = "rgba(65,227,208," + (0.45 * (1 - d / 180)).toFixed(3) + ")";
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
          }
        }
        for (i = 0; i < nodes.length; i++) {
          a = nodes[i];
          ctx.fillStyle = a.aqua ? "rgba(65,227,208,.85)" : "rgba(160,195,255,.75)";
          ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2); ctx.fill();
          if (a.r > 3) {
            ctx.strokeStyle = "rgba(65,227,208,.35)";
            ctx.beginPath(); ctx.arc(a.x, a.y, a.r + 4, 0, Math.PI * 2); ctx.stroke();
          }
        }
      }

      function step() {
        for (var i = 0; i < nodes.length; i++) {
          var n = nodes[i];
          // gentle repulsion from the cursor
          var dx = n.x - mouse.x, dy = n.y - mouse.y, d2 = dx * dx + dy * dy;
          if (d2 < 120 * 120 && d2 > 1) { var f = 0.6 / Math.sqrt(d2); n.x += dx * f; n.y += dy * f; }
          n.x += n.vx; n.y += n.vy;
          if (n.x < -20) n.x = W + 20; else if (n.x > W + 20) n.x = -20;
          if (n.y < -20) n.y = H + 20; else if (n.y > H + 20) n.y = -20;
        }
        draw();
        raf = requestAnimationFrame(step);
      }

      function start() { if (!running && visible && !document.hidden && !reduceMotion) { running = true; raf = requestAnimationFrame(step); } }
      function stop() { running = false; cancelAnimationFrame(raf); }

      build(); draw();
      if (reduceMotion) return;   // one still frame, no animation

      if ("IntersectionObserver" in window) {
        new IntersectionObserver(function (en) { visible = en[0].isIntersecting; visible ? start() : stop(); }).observe(host);
      }
      document.addEventListener("visibilitychange", function () { document.hidden ? stop() : start(); });
      var rt;
      // Mobile browsers fire resize whenever the address bar slides in or
      // out. Only a real width change re-seeds the network; a height change
      // just resizes the canvas so the molecules do not jump.
      window.addEventListener("resize", function () {
        clearTimeout(rt);
        rt = setTimeout(function () {
          var r = host.getBoundingClientRect();
          if (Math.abs(r.width - W) > 40) build();
          else { H = r.height; canvas.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); }
          draw();
        }, 200);
      });
      if (finePointer) {
        zone.addEventListener("pointermove", function (e) {
          var r = canvas.getBoundingClientRect(); mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
        });
        zone.addEventListener("pointerleave", function () { mouse.x = mouse.y = -9999; });
      }
      start();
    });
  }

  /* ------------------------------------------------------ Hero card deck */
  function initDeck() {
    var deck = $("[data-deck]");
    if (!deck) return;
    var cards = $$(".deck__card", deck);
    if (cards.length < 2) return;
    var order = cards.slice();
    var timer = null;

    function layout() {
      order.forEach(function (c, i) {
        c.dataset.pos = String(Math.min(i, 3));
        c.setAttribute("tabindex", i === 0 ? "0" : "-1");
        c.setAttribute("aria-hidden", i === 0 ? "false" : "true");
      });
    }
    function next() {
      var front = order.shift();
      front.classList.add("is-leaving");
      order.push(front);
      layout();
      setTimeout(function () { front.classList.remove("is-leaving"); }, 700);
    }
    function play() { if (!reduceMotion && !timer) timer = setInterval(next, 3400); }
    function pause() { clearInterval(timer); timer = null; }

    layout();
    deck.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") pause(); });
    deck.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") play(); });
    deck.addEventListener("focusin", pause);
    deck.addEventListener("focusout", play);
    document.addEventListener("visibilitychange", function () { document.hidden ? pause() : play(); });
    play();
  }

  /* ---------------------------------------------------------------- Tabs */
  function initTabs() {
    $$("[data-tabs]").forEach(function (list) {
      var tabs = $$("[role=tab]", list);
      var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute("aria-controls")); });

      function select(i, focus, initial) {
        tabs.forEach(function (t, k) {
          var on = k === i;
          t.setAttribute("aria-selected", String(on));
          t.setAttribute("tabindex", on ? "0" : "-1");
          if (!panels[k]) return;
          panels[k].hidden = !on;
          if (on && !initial) {
            panels[k].classList.remove("is-entering");
            void panels[k].offsetWidth;
            panels[k].classList.add("is-entering");
            // cards inside a freshly shown panel should not wait for scroll
            $$(".reveal", panels[k]).forEach(revealNow);
          }
        });
        if (focus) { tabs[i].focus(); tabs[i].scrollIntoView({ block: "nearest", inline: "nearest" }); }
      }

      tabs.forEach(function (t, i) {
        t.addEventListener("click", function () { select(i); });
        t.addEventListener("keydown", function (e) {
          var k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
          if (e.key === "Home") { e.preventDefault(); select(0, true); }
          else if (e.key === "End") { e.preventDefault(); select(tabs.length - 1, true); }
          else if (k) { e.preventDefault(); select((i + k + tabs.length) % tabs.length, true); }
        });
      });
      select(0, false, true);   // initial: cards still reveal on scroll as usual
    });
  }

  /* --------------------------------------------- Tilt + cursor spotlight */
  function initTilt() {
    if (!finePointer || reduceMotion) return;
    $$("[data-tilt]").forEach(function (el) {
      var max = el.classList.contains("tile--big") || el.classList.contains("mv__card") ? 3 : 6;
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        el.classList.add("is-tilting");
        el.style.setProperty("--rx", ((0.5 - py) * max).toFixed(2) + "deg");
        el.style.setProperty("--ry", ((px - 0.5) * max).toFixed(2) + "deg");
        el.style.setProperty("--mx", (e.clientX - r.left) + "px");
        el.style.setProperty("--my", (e.clientY - r.top) + "px");
      });
      el.addEventListener("pointerleave", function () {
        el.classList.remove("is-tilting");
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
    });
  }

  /* ------------------------------------------------- Timeline fill on scroll */
  function initTimeline() {
    $$("[data-timeline]").forEach(function (tl) {
      var steps = $$(".step", tl);
      if (reduceMotion) { tl.style.setProperty("--p", 1); steps.forEach(function (s) { s.classList.add("is-active"); }); return; }
      scrollJobs.push(function () {
        var r = tl.getBoundingClientRect();
        var vh = window.innerHeight;
        var p = clamp((vh * 0.8 - r.top) / (r.height + vh * 0.25), 0, 1);
        tl.style.setProperty("--p", p.toFixed(3));
        steps.forEach(function (s, i) {
          s.classList.toggle("is-active", p >= (steps.length === 1 ? 0 : i / (steps.length - 1)) - 0.02);
        });
      });
    });
  }

  /* -------------------------------------------------------------- Parallax */
  function initParallax() {
    var els = $$("[data-parallax]");
    if (!els.length || reduceMotion) return;
    scrollJobs.push(function () {
      var vh = window.innerHeight;
      els.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.bottom < -200 || r.top > vh + 200) return;
        var off = (r.top + r.height / 2 - vh / 2) * parseFloat(el.dataset.parallax);
        el.style.setProperty("--py", off.toFixed(1) + "px");
      });
    });
  }

  /* ------------------------------------------- Catalogue: facets + search */
  function initCatalogue() {
    var grid = $("[data-catalogue]");
    if (!grid) return;

    var cards = $$(".pcard", grid);
    var opts = $$("[data-facet]");
    var input = $("[data-search]");
    var empty = $("[data-empty]");
    var countEl = $("[data-result-count]");
    var reset = $("[data-reset]");
    var state = { area: "all", form: "all" };
    var first = true;

    // Search the whole card — name, area, form and description, which
    // carries the molecule names (cefixime, pantoprazole…).
    var haystack = cards.map(function (c) { return c.textContent.toLowerCase().replace(/\s+/g, " "); });

    function valid(facet, value) {
      return opts.some(function (o) { return o.dataset.facet === facet && o.dataset.value === value; });
    }
    function syncUrl(q) {
      if (!window.history.replaceState) return;
      var params = new URLSearchParams();
      if (state.area !== "all") params.set("area", state.area);
      if (state.form !== "all") params.set("form", state.form);
      if (q) params.set("q", q);
      var qs = params.toString();
      history.replaceState(null, "", location.pathname + (qs ? "?" + qs : ""));
    }
    function apply() {
      var q = (input && input.value || "").trim().toLowerCase();
      var shown = 0;
      cards.forEach(function (card, i) {
        var on = (state.area === "all" || card.dataset.area === state.area) &&
                 (state.form === "all" || card.dataset.form === state.form) &&
                 (!q || haystack[i].indexOf(q) > -1);
        var was = !card.classList.contains("is-hidden");
        card.classList.toggle("is-hidden", !on);
        if (on) {
          shown++;
          if (!was && !first && !reduceMotion) {
            card.style.animation = "none"; void card.offsetWidth;
            card.style.animation = "card-in .6s cubic-bezier(.16,1,.3,1) backwards";
          }
          if (!first) revealNow(card);
        }
      });
      opts.forEach(function (o) { o.setAttribute("aria-pressed", String(state[o.dataset.facet] === o.dataset.value)); });
      if (empty) empty.hidden = shown !== 0;
      if (countEl) countEl.textContent = shown;
      if (reset) reset.hidden = state.area === "all" && state.form === "all" && !q;
      if (!first) syncUrl(q);
      first = false;
      onScroll();
    }

    opts.forEach(function (o) {
      o.addEventListener("click", function () { state[o.dataset.facet] = o.dataset.value; apply(); });
    });
    if (input) {
      var t;
      input.addEventListener("input", function () { clearTimeout(t); t = setTimeout(apply, 120); });
      // "/" focuses search, like most catalogue tools
      document.addEventListener("keydown", function (e) {
        if (e.key === "/" && document.activeElement !== input && !/input|textarea/i.test(document.activeElement.tagName)) {
          e.preventDefault(); input.focus();
        }
      });
    }
    if (reset) {
      reset.addEventListener("click", function () {
        state.area = state.form = "all";
        if (input) input.value = "";
        apply();
      });
    }

    var params = new URLSearchParams(location.search);
    ["area", "form"].forEach(function (f) { var v = params.get(f); if (v && valid(f, v)) state[f] = v; });
    if (input && params.get("q")) input.value = params.get("q");
    apply();
  }

  /* ------------------------------------------------------------- Lightbox */
  function initLightbox() {
    var box = $(".lightbox");
    if (!box) return;
    var img = $(".lightbox__img", box), caption = $(".lightbox__caption", box), closeBtn = $(".lightbox__close", box);
    var lastFocus = null;
    function close() {
      box.classList.remove("is-open"); box.setAttribute("aria-hidden", "true");
      document.body.classList.remove("no-scroll");
      if (lastFocus) lastFocus.focus();
    }
    $$("[data-lightbox]").forEach(function (t) {
      t.addEventListener("click", function () {
        lastFocus = t;
        img.src = t.dataset.lightbox; img.alt = t.dataset.caption || ""; caption.textContent = t.dataset.caption || "";
        box.classList.add("is-open"); box.setAttribute("aria-hidden", "false");
        document.body.classList.add("no-scroll");
        closeBtn.focus();
      });
    });
    closeBtn.addEventListener("click", close);
    box.addEventListener("click", function (e) { if (e.target === box) close(); });
    document.addEventListener("keydown", function (e) {
      if (!box.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      else if (e.key === "Tab") { e.preventDefault(); closeBtn.focus(); }
    });
  }

  /* ------------------------------------------------------ Form validation */
  function initForms() {
    $$("form[novalidate]").forEach(function (form) {
      var fields = $$("input:not([type=hidden]):not([tabindex='-1']), textarea", form);
      function message(el) {
        var v = el.validity;
        if (v.valueMissing) return "This field is required.";
        if (v.typeMismatch && el.type === "email") return "Enter a valid email address.";
        if (v.patternMismatch && el.type === "tel") return "Enter a valid phone number.";
        return el.validationMessage;
      }
      function check(el) {
        var wrap = el.closest(".field");
        if (!wrap) return el.checkValidity();
        var err = $(".field__error", wrap), ok = el.checkValidity();
        wrap.classList.toggle("is-invalid", !ok);
        el.setAttribute("aria-invalid", String(!ok));
        if (!ok) {
          if (!err) {
            err = document.createElement("p");
            err.className = "field__error"; err.id = el.id + "-error";
            wrap.appendChild(err);
            el.setAttribute("aria-describedby", err.id);
          }
          err.textContent = message(el);
        } else if (err) {
          err.remove(); el.removeAttribute("aria-describedby");
        }
        return ok;
      }
      fields.forEach(function (el) {
        el.addEventListener("blur", function () { if (el.value) check(el); });
        el.addEventListener("input", function () { if (el.closest(".is-invalid")) check(el); });
      });
      form.addEventListener("submit", function (e) {
        var firstBad = null;
        fields.forEach(function (el) { if (!check(el) && !firstBad) firstBad = el; });
        if (firstBad) { e.preventDefault(); firstBad.focus(); return; }
        var btn = $("button[type=submit]", form);
        if (btn) { btn.disabled = true; btn.dataset.label = btn.firstChild.textContent; btn.firstChild.textContent = "Sending… "; }
      });
      // Back-button restores from cache with the button disabled — re-arm it.
      window.addEventListener("pageshow", function () {
        var btn = $("button[type=submit]", form);
        if (btn && btn.disabled) { btn.disabled = false; btn.firstChild.textContent = btn.dataset.label || btn.firstChild.textContent; }
      });
    });
  }

  /* ----------------------------------------------------------- Back to top */
  function initToTop() {
    var btn = $(".totop");
    if (!btn) return;
    scrollJobs.push(function (y) { btn.classList.toggle("is-visible", y > 800); });
    btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" }); });
  }

  function initYear() {
    $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
  }

  function boot() {
    initHeader();
    initProgress();
    initTabs();
    initReveal();
    initCounters();
    initMolecules();
    initDeck();
    initTilt();
    initTimeline();
    initParallax();
    initCatalogue();
    initLightbox();
    initForms();
    initToTop();
    initYear();
    onScroll();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
