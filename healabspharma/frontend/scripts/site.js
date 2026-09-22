/* ==========================================================================
   Heal Labs Pharma — site behaviour
   Vanilla JS, no dependencies. Everything degrades gracefully without it.
   ========================================================================== */
(function () {
  "use strict";

  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $  = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  /* ---------------------------------------------------------------- Navbar */
  function initNav() {
    var nav = $(".nav");
    if (!nav) return;

    var toggle = $(".nav__toggle", nav);
    var menu   = $(".nav__menu", nav);

    function onScroll() {
      nav.classList.toggle("is-stuck", window.scrollY > 24);
    }

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    if (toggle && menu) {
      toggle.addEventListener("click", function () {
        var open = menu.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(open));
        document.body.classList.toggle("no-scroll", open);
      });

      // close on link click or Escape
      $$(".nav__link, .nav__cta", menu).forEach(function (a) {
        a.addEventListener("click", function () {
          menu.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
          document.body.classList.remove("no-scroll");
        });
      });
      // If the phone is rotated to a width where the menu is no longer a
      // drawer, drop the open state so the scroll lock is released.
      window.addEventListener("resize", function () {
        if (window.innerWidth > 900 && menu.classList.contains("is-open")) {
          menu.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
          document.body.classList.remove("no-scroll");
        }
      });

      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && menu.classList.contains("is-open")) {
          menu.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
          document.body.classList.remove("no-scroll");
          toggle.focus();
        }
      });
    }
  }

  /* ------------------------------------------------------------ Hero slider */
  function initHero() {
    var hero = $(".hero");
    if (!hero) return;

    var slides = $$(".hero__slide", hero);
    var texts  = $$(".hero__text", hero);
    var dots   = $$(".hero__dot", hero);
    if (slides.length < 2) return;

    var i = 0;
    var timer = null;
    var DURATION = 6000;

    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle("is-active", k === i); });
      dots.forEach(function (d, k) { d.setAttribute("aria-selected", String(k === i)); });
      texts.forEach(function (t, k) {
        var on = k === i;
        t.hidden = !on;
        if (on && !reduceMotion) {
          // restart the staggered entrance
          $$("*", t).forEach(function (el) {
            el.style.animation = "none";
            void el.offsetWidth;
            el.style.animation = "";
          });
        }
      });
    }

    function play()  { if (!reduceMotion) timer = setInterval(function () { show(i + 1); }, DURATION); }
    function pause() { clearInterval(timer); }

    dots.forEach(function (d, k) {
      d.addEventListener("click", function () { pause(); show(k); play(); });
    });

    hero.addEventListener("mouseenter", pause);
    hero.addEventListener("mouseleave", play);
    document.addEventListener("visibilitychange", function () {
      document.hidden ? pause() : play();
    });

    show(0);
    play();
  }

  /* --------------------------------------------------------- Scroll reveal */
  function initReveal() {
    var items = $$(".reveal");
    if (!items.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -60px 0px" });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------- Animated counters */
  function initCounters() {
    var nums = $$("[data-count]");
    if (!nums.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      nums.forEach(function (el) { el.textContent = el.dataset.count + (el.dataset.suffix || ""); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var target = parseFloat(el.dataset.count);
        var suffix = el.dataset.suffix || "";
        var start = performance.now();
        var dur = 1400;

        (function step(now) {
          var p = Math.min((now - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (p < 1) requestAnimationFrame(step);
        })(start);

        io.unobserve(el);
      });
    }, { threshold: 0.5 });

    nums.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------ Product filter + search */
  function initCatalogue() {
    var grid = $("[data-catalogue]");
    if (!grid) return;

    var cards  = $$(".product", grid);
    var chips  = $$("[data-filter]");
    var input  = $("[data-search]");
    var empty  = $("[data-empty]");
    var countEl = $("[data-result-count]");
    var active = "all";

    function apply() {
      var q = (input && input.value || "").trim().toLowerCase();
      var shown = 0;

      cards.forEach(function (card) {
        var matchCat = active === "all" || card.dataset.category === active;
        var matchQ = !q ||
          card.dataset.name.toLowerCase().indexOf(q) > -1 ||
          card.dataset.form.toLowerCase().indexOf(q) > -1 ||
          card.dataset.category.toLowerCase().indexOf(q) > -1;
        var on = matchCat && matchQ;
        card.classList.toggle("is-hidden", !on);
        if (on) shown++;
      });

      if (empty) empty.hidden = shown !== 0;
      if (countEl) countEl.textContent = shown;
    }

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        active = chip.dataset.filter;
        chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
        apply();
      });
    });

    if (input) {
      var t;
      input.addEventListener("input", function () {
        clearTimeout(t);
        t = setTimeout(apply, 140);
      });
    }

    apply();
  }

  /* ------------------------------------------------- Expandable descriptions */
  function initReadMore() {
    $$("[data-more]").forEach(function (btn) {
      var body = $("#" + btn.getAttribute("aria-controls"));
      if (!body) return;
      btn.addEventListener("click", function () {
        var open = body.classList.toggle("is-open");
        btn.setAttribute("aria-expanded", String(open));
        $(".product__more-text", btn).textContent = open ? "Show less" : "Read more";
      });
    });
  }

  /* ------------------------------------------------------------- Lightbox */
  function initLightbox() {
    var box = $(".lightbox");
    if (!box) return;

    var img     = $(".lightbox__img", box);
    var caption = $(".lightbox__caption", box);
    var closeBtn = $(".lightbox__close", box);
    var prevBtn = $(".lightbox__nav--prev", box);
    var nextBtn = $(".lightbox__nav--next", box);
    var triggers = $$("[data-lightbox]");
    var lastFocus = null;
    var idx = 0;

    function visibleTriggers() {
      return triggers.filter(function (t) {
        var card = t.closest(".product");
        return !card || !card.classList.contains("is-hidden");
      });
    }

    function render(list) {
      var t = list[idx];
      if (!t) return;
      img.src = t.dataset.lightbox;
      img.alt = t.dataset.caption || "";
      caption.textContent = t.dataset.caption || "";
      var multi = list.length > 1;
      prevBtn.hidden = !multi;
      nextBtn.hidden = !multi;
    }

    function open(trigger) {
      var list = visibleTriggers();
      idx = Math.max(0, list.indexOf(trigger));
      lastFocus = trigger;
      render(list);
      box.classList.add("is-open");
      box.setAttribute("aria-hidden", "false");
      document.body.classList.add("no-scroll");
      closeBtn.focus();
    }

    function close() {
      box.classList.remove("is-open");
      box.setAttribute("aria-hidden", "true");
      document.body.classList.remove("no-scroll");
      if (lastFocus) lastFocus.focus();
    }

    function step(dir) {
      var list = visibleTriggers();
      idx = (idx + dir + list.length) % list.length;
      render(list);
    }

    triggers.forEach(function (t) {
      t.addEventListener("click", function (e) { e.preventDefault(); open(t); });
    });

    closeBtn.addEventListener("click", close);
    prevBtn.addEventListener("click", function () { step(-1); });
    nextBtn.addEventListener("click", function () { step(1); });
    box.addEventListener("click", function (e) { if (e.target === box) close(); });

    // Swipe between products on touch devices.
    var touchX = null;
    box.addEventListener("touchstart", function (e) {
      touchX = e.changedTouches[0].clientX;
    }, { passive: true });
    box.addEventListener("touchend", function (e) {
      if (touchX === null) return;
      var dx = e.changedTouches[0].clientX - touchX;
      touchX = null;
      if (Math.abs(dx) > 45) step(dx < 0 ? 1 : -1);
    }, { passive: true });

    document.addEventListener("keydown", function (e) {
      if (!box.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "ArrowRight") step(1);
      else if (e.key === "Tab") {
        // simple focus trap
        var focusables = [closeBtn, prevBtn, nextBtn].filter(function (b) { return !b.hidden; });
        var first = focusables[0], last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  /* ----------------------------------------------------------- Back to top */
  function initToTop() {
    var btn = $(".totop");
    if (!btn) return;
    window.addEventListener("scroll", function () {
      btn.classList.toggle("is-visible", window.scrollY > 600);
    }, { passive: true });
    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });
  }

  /* ------------------------------------------------------------ Year stamp */
  function initYear() {
    $$("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
  }

  /* ---------------------------------------------------------------- Start */
  function boot() {
    initNav();
    initHero();
    initReveal();
    initCounters();
    initCatalogue();
    initReadMore();
    initLightbox();
    initToTop();
    initYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
