#!/usr/bin/env python3
"""
generate_index.py
-----------------
Scans the output/ directory for completed Cambridge IELTS workbook pages
and regenerates index.html with organised navigation.

Filename format expected:
  Cambridge IELTS 4 - Test 1 - Listening Part 1 Workbook.html
  Cambridge IELTS 4 - Test 1 - Reading Passage 1 Workbook.html

Run locally:   python scripts/generate_index.py
Run in CI:     same command (GitHub Actions)
"""

import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = REPO_ROOT / "output"
INDEX_FILE   = REPO_ROOT / "index.html"

BOOKS            = list(range(4, 22))
TESTS_PER_BOOK   = 4
LISTENING_PARTS  = [1, 2, 3, 4]
READING_PASSAGES = [1, 2, 3]
UNITS_PER_TEST   = len(LISTENING_PARTS) + len(READING_PASSAGES)
TOTAL_UNITS      = len(BOOKS) * TESTS_PER_BOOK * UNITS_PER_TEST   # 504

PATTERN = re.compile(
    r"Cambridge IELTS (\d+) - Test (\d+) - (Listening Part|Reading Passage) (\d+) Workbook\.html",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def scan_workbooks() -> dict:
    found = {}
    if not OUTPUT_DIR.exists():
        return found
    for f in sorted(OUTPUT_DIR.glob("*.html")):
        m = PATTERN.match(f.name)
        if m:
            key = (int(m.group(1)), int(m.group(2)),
                   m.group(3).lower().replace(" ", "_"), int(m.group(4)))
            found[key] = f"output/{f.name}"
    return found


def chip(label, url=None, kind="listening"):
    if url:
        cls = "chip-l" if kind == "listening" else "chip-r"
        encoded_url = quote(url, safe="/")
        return f'<a href="{encoded_url}" class="chip {cls}" title="Open workbook">{label}</a>'
    return f'<span class="chip chip-off">{label}</span>'


def book_section(book: int, available: dict) -> str:
    book_done  = sum(1 for k in available if k[0] == book)
    book_total = TESTS_PER_BOOK * UNITS_PER_TEST
    pct        = int(book_done / book_total * 100) if book_total else 0
    has_any    = book_done > 0

    tests_rows = ""
    for test in range(1, TESTS_PER_BOOK + 1):
        l_chips = "".join(
            chip(f"L{p}", available.get((book, test, "listening_part", p)), "listening")
            for p in LISTENING_PARTS
        )
        r_chips = "".join(
            chip(f"R{p}", available.get((book, test, "reading_passage", p)), "reading")
            for p in READING_PASSAGES
        )
        tests_rows += f"""
        <div class="test-row">
          <span class="test-lbl">Test {test}</span>
          <div class="chip-row">
            <div class="chip-grp">{l_chips}</div>
            <span class="chip-div"></span>
            <div class="chip-grp">{r_chips}</div>
          </div>
        </div>"""

    active_cls = "book-active" if has_any else ""
    return f"""
  <div class="book-card {active_cls}" id="book-{book}">
    <button class="book-hd" onclick="toggleBook(this)" aria-expanded="false">
      <span class="book-title">
        <span class="book-icon">{'📖' if has_any else '📘'}</span>
        Cambridge IELTS {book}
      </span>
      <span class="book-right">
        <span class="book-ct {'book-ct-done' if has_any else ''}">{book_done}/{book_total}</span>
        <span class="mini-bar-wrap"><span class="mini-bar" style="width:{pct}%"></span></span>
        <span class="chevron">›</span>
      </span>
    </button>
    <div class="book-body">{tests_rows}
    </div>
  </div>"""


# ---------------------------------------------------------------------------
# Build full index.html
# ---------------------------------------------------------------------------
def build_index(available: dict) -> str:
    completed = len(available)
    pct       = round(completed / TOTAL_UNITS * 100, 1)
    updated   = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    books_html = "\n".join(book_section(b, available) for b in BOOKS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cambridge IELTS Workbooks — Lexilink Ideation IELTS Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    /* ── Tokens ─────────────────────────────────────────── */
    :root {{
      --red:        #C8102E;
      --red-dark:   #8B1727;
      --red-deeper: #4D0812;
      --red-light:  #FEE8EC;
      --red-pale:   #FDF5F6;
      --gold:       #C9963E;
      --gold-light: #FDF3E0;
      --gold-dark:  #7A5A18;
      --white:      #FFFFFF;
      --card:       #FFFFFF;
      --bg:         #FBF4F5;
      --text:       #1C0A0D;
      --muted:      #7A5560;
      --border:     #EAD8DB;
      --radius:     12px;
      --shadow-sm:  0 1px 4px rgba(200,16,46,.09);
      --shadow-md:  0 4px 16px rgba(200,16,46,.12);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── Top bar ─────────────────────────────────────────── */
    .top-bar {{
      background: var(--red-deeper);
      padding: 0 28px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .logo {{
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
    }}
    .logo-text {{ line-height: 1.2; }}
    .logo-name {{
      font-weight: 800;
      font-size: .78rem;
      letter-spacing: .12em;
      color: #fff;
    }}
    .logo-studio {{
      font-size: .65rem;
      letter-spacing: .18em;
      color: var(--gold);
      font-weight: 600;
    }}
    .top-bar-link {{
      font-size: .75rem;
      color: rgba(255,255,255,.55);
      text-decoration: none;
    }}
    .top-bar-link:hover {{ color: #fff; }}

    /* ── Hero ────────────────────────────────────────────── */
    .hero {{
      background: linear-gradient(160deg, var(--red-deeper) 0%, var(--red-dark) 45%, var(--red) 100%);
      color: #fff;
      padding: 56px 28px 48px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}
    /* Decorative circles */
    .hero::before, .hero::after {{
      content: '';
      position: absolute;
      border-radius: 50%;
      opacity: .08;
      background: var(--gold);
    }}
    .hero::before {{ width: 420px; height: 420px; top: -180px; right: -120px; }}
    .hero::after  {{ width: 280px; height: 280px; bottom: -140px; left: -80px; }}

    .hero-eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(201,150,62,.2);
      border: 1px solid rgba(201,150,62,.4);
      border-radius: 50px;
      padding: 5px 16px;
      font-size: .72rem;
      font-weight: 700;
      letter-spacing: .15em;
      color: var(--gold);
      text-transform: uppercase;
      margin-bottom: 20px;
    }}
    .hero h1 {{
      font-size: clamp(1.6rem, 5vw, 2.8rem);
      font-weight: 900;
      letter-spacing: -1px;
      line-height: 1.15;
      margin-bottom: 10px;
    }}
    .hero h1 span {{ color: var(--gold); }}
    .hero-sub {{
      font-size: .95rem;
      opacity: .75;
      margin-bottom: 36px;
      letter-spacing: .02em;
    }}
    .hero-zh {{
      font-size: .82rem;
      opacity: .5;
      margin-top: 4px;
    }}

    /* Progress pill */
    .progress-pill {{
      display: inline-flex;
      align-items: center;
      gap: 16px;
      background: rgba(255,255,255,.1);
      border: 1px solid rgba(255,255,255,.2);
      backdrop-filter: blur(8px);
      border-radius: 50px;
      padding: 12px 24px;
      font-size: .85rem;
    }}
    .progress-pill strong {{ font-size: 1.05rem; }}
    .prog-track {{
      width: 160px;
      height: 8px;
      background: rgba(255,255,255,.2);
      border-radius: 4px;
      overflow: hidden;
    }}
    .prog-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--gold) 0%, #F0C060 100%);
      border-radius: 4px;
      transition: width .6s cubic-bezier(.4,0,.2,1);
    }}
    .prog-pct {{
      font-weight: 700;
      color: var(--gold);
      min-width: 40px;
      text-align: right;
    }}

    /* ── Stats bar ───────────────────────────────────────── */
    .stats-bar {{
      display: flex;
      justify-content: center;
      gap: 0;
      background: var(--red-dark);
      border-bottom: 1px solid rgba(255,255,255,.08);
    }}
    .stat {{
      flex: 1;
      max-width: 180px;
      text-align: center;
      padding: 14px 12px;
      border-right: 1px solid rgba(255,255,255,.08);
    }}
    .stat:last-child {{ border-right: none; }}
    .stat-num {{
      font-size: 1.3rem;
      font-weight: 800;
      color: #fff;
      line-height: 1;
    }}
    .stat-label {{
      font-size: .68rem;
      color: rgba(255,255,255,.45);
      letter-spacing: .08em;
      text-transform: uppercase;
      margin-top: 4px;
    }}

    /* ── Legend ──────────────────────────────────────────── */
    .legend {{
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 20px;
      padding: 14px 16px;
      background: var(--card);
      border-bottom: 1px solid var(--border);
      font-size: .78rem;
      color: var(--muted);
    }}
    .legend-item {{ display: flex; align-items: center; gap: 6px; font-weight: 500; }}
    .ld {{ width: 28px; height: 20px; border-radius: 5px; font-size: .65rem; font-weight: 700;
            display: flex; align-items: center; justify-content: center; }}
    .ld-l {{ background: var(--red); color: #fff; }}
    .ld-r {{ background: var(--gold); color: var(--red-deeper); }}
    .ld-off {{ background: #EEE6E8; color: #B0A0A5; border: 1px solid #DDD3D5; }}

    /* ── Container ───────────────────────────────────────── */
    .container {{
      max-width: 880px;
      margin: 0 auto;
      padding: 28px 16px 80px;
    }}
    .section-heading {{
      font-size: .7rem;
      font-weight: 700;
      letter-spacing: .14em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-heading::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}

    /* ── Book cards ──────────────────────────────────────── */
    .book-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 10px;
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      transition: box-shadow .2s;
    }}
    .book-card.book-active {{
      border-color: rgba(200,16,46,.25);
      box-shadow: var(--shadow-md);
    }}
    .book-hd {{
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 15px 20px;
      background: none;
      border: none;
      cursor: pointer;
      font-family: inherit;
      font-size: .95rem;
      font-weight: 700;
      color: var(--text);
      text-align: left;
      gap: 12px;
      transition: background .15s;
    }}
    .book-card.book-active .book-hd {{ background: linear-gradient(90deg, var(--red-pale) 0%, transparent 100%); }}
    .book-hd:hover {{ background: var(--red-pale); }}
    .book-title {{
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .book-icon {{ font-size: 1.1rem; }}
    .book-right {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }}
    .book-ct {{
      font-size: .75rem;
      color: var(--muted);
      font-weight: 500;
      min-width: 36px;
      text-align: right;
    }}
    .book-ct-done {{ color: var(--red); font-weight: 700; }}
    .mini-bar-wrap {{
      width: 72px;
      height: 5px;
      background: var(--border);
      border-radius: 3px;
      overflow: hidden;
    }}
    .mini-bar {{
      height: 100%;
      background: linear-gradient(90deg, var(--red) 0%, var(--gold) 100%);
      border-radius: 3px;
    }}
    .chevron {{
      color: var(--muted);
      font-size: 1.2rem;
      transition: transform .2s;
      display: inline-block;
      line-height: 1;
    }}
    .book-card.open .chevron {{ transform: rotate(90deg); }}

    .book-body {{
      display: none;
      border-top: 1px solid var(--border);
      background: #FDFBFB;
      padding: 4px 0;
    }}
    .book-card.open .book-body {{ display: block; }}

    /* ── Test rows ───────────────────────────────────────── */
    .test-row {{
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 10px 20px;
    }}
    .test-row:not(:last-child) {{ border-bottom: 1px solid #F5EDEF; }}
    .test-lbl {{
      font-size: .75rem;
      font-weight: 700;
      color: var(--muted);
      min-width: 48px;
      flex-shrink: 0;
    }}
    .chip-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .chip-grp {{ display: flex; gap: 5px; }}
    .chip-div {{
      width: 1px;
      height: 22px;
      background: var(--border);
      flex-shrink: 0;
    }}

    /* ── Chips ───────────────────────────────────────────── */
    .chip {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 30px;
      border-radius: 6px;
      font-size: .72rem;
      font-weight: 800;
      text-decoration: none;
      letter-spacing: .02em;
      transition: transform .1s, box-shadow .15s;
    }}
    .chip-l {{
      background: var(--red);
      color: #fff;
    }}
    .chip-l:hover {{
      transform: translateY(-2px);
      box-shadow: 0 5px 14px rgba(200,16,46,.4);
    }}
    .chip-r {{
      background: var(--gold);
      color: var(--red-deeper);
    }}
    .chip-r:hover {{
      transform: translateY(-2px);
      box-shadow: 0 5px 14px rgba(201,150,62,.4);
    }}
    .chip-off {{
      background: #EEE6E8;
      color: #C0ADAF;
      cursor: default;
    }}

    /* ── Footer ──────────────────────────────────────────── */
    .site-footer {{
      background: var(--red-deeper);
      color: rgba(255,255,255,.45);
      text-align: center;
      padding: 28px 24px;
      font-size: .75rem;
    }}
    .footer-logo {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .footer-logo .logo-mark {{
      width: 28px;
      height: 28px;
      font-size: .9rem;
    }}
    .footer-logo .logo-name {{ font-size: .72rem; }}
    .footer-logo .logo-studio {{ font-size: .6rem; }}
    .site-footer a {{
      color: var(--gold);
      text-decoration: none;
    }}
    .site-footer a:hover {{ text-decoration: underline; }}

    @media (max-width: 540px) {{
      .hero {{ padding: 40px 16px 36px; }}
      .stats-bar {{ flex-wrap: wrap; }}
      .stat {{ min-width: 50%; }}
      .progress-pill {{ gap: 10px; padding: 10px 16px; }}
      .prog-track {{ width: 100px; }}
    }}
  </style>
</head>
<body>

  <!-- ── Top bar ── -->
  <div class="top-bar">
    <a class="logo" href="#">
      <div class="logo-text">
        <div class="logo-name">LEXILINK IDEATION</div>
        <div class="logo-studio">IELTS STUDIO</div>
      </div>
    </a>
    <a class="top-bar-link" href="https://github.com/lexilink-ideation/Cambridge-IELTS-workbooks" target="_blank">GitHub ↗</a>
  </div>

  <!-- ── Hero ── -->
  <section class="hero">
    <div class="hero-eyebrow">Cambridge IELTS 4 – 21</div>
    <h1>Interactive Practice<br><span>Workbooks</span></h1>
    <p class="hero-sub">Listening &amp; Reading · Step-by-step exam digest for every test</p>
    <p class="hero-zh">逐题精讲 · 剑桥雅思全真题练习册</p>
    <br>
    <div class="progress-pill">
      <span><strong>{completed}</strong> / {TOTAL_UNITS} units</span>
      <div class="prog-track">
        <div class="prog-fill" style="width:{pct}%"></div>
      </div>
      <span class="prog-pct">{pct}%</span>
    </div>
  </section>

  <!-- ── Stats bar ── -->
  <div class="stats-bar">
    <div class="stat">
      <div class="stat-num">18</div>
      <div class="stat-label">Books</div>
    </div>
    <div class="stat">
      <div class="stat-num">72</div>
      <div class="stat-label">Tests</div>
    </div>
    <div class="stat">
      <div class="stat-num">288</div>
      <div class="stat-label">Listening Units</div>
    </div>
    <div class="stat">
      <div class="stat-num">216</div>
      <div class="stat-label">Reading Units</div>
    </div>
    <div class="stat">
      <div class="stat-num">{completed}</div>
      <div class="stat-label">Available Now</div>
    </div>
  </div>

  <!-- ── Legend ── -->
  <div class="legend">
    <span class="legend-item"><span class="ld ld-l">L1</span> Listening</span>
    <span class="legend-item"><span class="ld ld-r">R1</span> Reading</span>
    <span class="legend-item"><span class="ld ld-off">L1</span> Not yet available</span>
  </div>

  <!-- ── Book list ── -->
  <div class="container">
    <div class="section-heading">All Cambridge IELTS Books</div>
    {books_html}
  </div>

  <!-- ── Footer ── -->
  <footer class="site-footer">
    <div class="footer-logo">
      <div class="logo-text">
        <div class="logo-name">LEXILINK IDEATION</div>
        <div class="logo-studio">IELTS STUDIO</div>
      </div>
    </div>
    <p>Cambridge IELTS Practice Workbooks · Built for IELTS learners · Updated regularly</p>
    <p style="margin-top:6px;">
      Last updated: {updated} ·
      <a href="https://github.com/lexilink-ideation/Cambridge-IELTS-workbooks" target="_blank">View on GitHub</a>
    </p>
  </footer>

  <script>
    function toggleBook(btn) {{
      const card = btn.closest('.book-card');
      const isOpen = card.classList.toggle('open');
      btn.setAttribute('aria-expanded', isOpen);
    }}
  </script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    available = scan_workbooks()
    html      = build_index(available)
    INDEX_FILE.write_text(html, encoding="utf-8")
    print(f"✅  index.html updated — {len(available)}/{TOTAL_UNITS} units complete")
    if available:
        for key, path in sorted(available.items()):
            book, test, kind, num = key
            label = "Listening Part" if "listening" in kind else "Reading Passage"
            print(f"    • Cambridge IELTS {book} – Test {test} – {label} {num}")
