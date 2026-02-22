#!/usr/bin/env python3
"""
Parse sentences.md, generate gTTS audio files, and build index.html.
"""

import os
import re
import html
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
SENTENCES_FILE = BASE_DIR / "sentences.md"
AUDIO_DIR = BASE_DIR / "audio"
HTML_FILE = BASE_DIR / "index.html"
LANG = "en"
TLD = "us"  # American English accent

# ---------------------------------------------------------------------------
# Parse sentences.md
# ---------------------------------------------------------------------------

def parse_sentences(path: Path) -> list[dict]:
    """Return list of {'num': int, 'raw': str} from the markdown file."""
    sentences = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^(\d+)\.\s+(.+)$", line)
            if m:
                sentences.append({"num": int(m.group(1)), "raw": m.group(2)})
    return sentences


def strip_markdown_bold(text: str) -> str:
    """Remove **bold** markers for TTS input."""
    return text.replace("**", "")


def bold_to_html(text: str) -> str:
    """Convert **word** → <b>word</b> for display, escaping HTML first."""
    # We need to protect the bold markers, escape everything else, then restore
    # Split on ** boundaries
    parts = text.split("**")
    # Even-indexed parts are outside bold, odd-indexed are inside bold
    result = []
    for i, part in enumerate(parts):
        escaped = html.escape(part)
        if i % 2 == 1:
            result.append(f"<b>{escaped}</b>")
        else:
            result.append(escaped)
    return "".join(result)


# ---------------------------------------------------------------------------
# Generate audio
# ---------------------------------------------------------------------------

def generate_audio_files(sentences: list[dict]):
    """Generate MP3 files using gTTS. Skips files that already exist."""
    from gtts import gTTS

    AUDIO_DIR.mkdir(exist_ok=True)

    total = len(sentences)
    skipped = 0
    generated = 0
    failed = []

    for i, s in enumerate(sentences):
        num = s["num"]
        filename = AUDIO_DIR / f"{num:04d}.mp3"

        if filename.exists():
            skipped += 1
            if (i + 1) % 50 == 0 or (i + 1) == total:
                print(f"  [{i+1}/{total}] skipped (already exists): {filename.name}")
            continue

        plain_text = strip_markdown_bold(s["raw"])
        try:
            tts = gTTS(text=plain_text, lang=LANG, tld=TLD)
            tts.save(str(filename))
            generated += 1
        except Exception as e:
            failed.append((num, str(e)))
            print(f"  [ERROR] sentence {num}: {e}")

        if (i + 1) % 10 == 0 or (i + 1) == total:
            print(f"  [{i+1}/{total}] generated so far: {generated}, skipped: {skipped}")

        # Small delay to avoid rate-limiting from Google
        if generated % 20 == 0 and generated > 0:
            time.sleep(1)

    print(f"\nAudio generation complete: {generated} new, {skipped} skipped, {len(failed)} failed.")
    if failed:
        print("Failed sentences:")
        for num, err in failed:
            print(f"  #{num}: {err}")


# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>1000 English Sentences — Speaker</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: #f5f5f5;
    color: #222;
    line-height: 1.6;
  }}
  header {{
    background: #1a73e8;
    color: #fff;
    padding: 1.2rem 1rem;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }}
  header h1 {{ font-size: 1.4rem; font-weight: 600; }}
  header p {{ font-size: .85rem; opacity: .85; margin-top: .25rem; }}
  .container {{
    max-width: 900px;
    margin: 1.5rem auto;
    padding: 0 1rem;
  }}
  .controls {{
    display: flex;
    gap: .5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
  }}
  .controls input {{
    flex: 1;
    min-width: 200px;
    padding: .5rem .75rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: .95rem;
  }}
  .sentence {{
    display: flex;
    align-items: flex-start;
    gap: .75rem;
    background: #fff;
    border-radius: 8px;
    padding: .75rem 1rem;
    margin-bottom: .5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    transition: background .15s;
  }}
  .sentence:hover {{ background: #f0f6ff; }}
  .sentence.playing {{ background: #e3f0ff; border-left: 3px solid #1a73e8; }}
  .num {{
    min-width: 3rem;
    font-weight: 700;
    color: #1a73e8;
    font-size: .95rem;
    padding-top: 2px;
    text-align: right;
  }}
  .text {{
    flex: 1;
    font-size: 1rem;
  }}
  .text b {{ color: #c62828; }}
  .play-btn {{
    background: #1a73e8;
    color: #fff;
    border: none;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    font-size: 1rem;
    cursor: pointer;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background .15s, transform .1s;
  }}
  .play-btn:hover {{ background: #1557b0; transform: scale(1.1); }}
  .play-btn.active {{ background: #c62828; }}
  .hidden {{ display: none !important; }}
  @media (max-width: 600px) {{
    .sentence {{ padding: .6rem .7rem; gap: .5rem; }}
    .num {{ min-width: 2.2rem; font-size: .85rem; }}
    .text {{ font-size: .92rem; }}
  }}
</style>
</head>
<body>

<header>
  <h1>&#128264; 1000 English Sentences</h1>
  <p>Click the play button to hear each sentence</p>
</header>

<div class="container">
  <div class="controls">
    <input type="text" id="search" placeholder="Search sentences..." autocomplete="off">
  </div>

  <div id="list">
{rows}
  </div>
</div>

<script>
(function() {{
  const audio = new Audio();
  let activeBtn = null;
  let activeRow = null;

  audio.addEventListener('ended', () => {{
    if (activeBtn) activeBtn.classList.remove('active');
    if (activeBtn) activeBtn.textContent = '▶';
    if (activeRow) activeRow.classList.remove('playing');
    activeBtn = null;
    activeRow = null;
  }});

  document.getElementById('list').addEventListener('click', (e) => {{
    const btn = e.target.closest('.play-btn');
    if (!btn) return;

    const row = btn.closest('.sentence');
    const src = 'audio/' + btn.dataset.file;

    // If same button clicked again, toggle pause/play
    if (btn === activeBtn) {{
      if (audio.paused) {{
        audio.play();
        btn.textContent = '⏸';
        btn.classList.add('active');
        row.classList.add('playing');
      }} else {{
        audio.pause();
        btn.textContent = '▶';
        btn.classList.remove('active');
        row.classList.remove('playing');
      }}
      return;
    }}

    // Stop previous
    if (activeBtn) {{
      activeBtn.textContent = '▶';
      activeBtn.classList.remove('active');
    }}
    if (activeRow) activeRow.classList.remove('playing');

    // Play new
    audio.src = src;
    audio.play();
    btn.textContent = '⏸';
    btn.classList.add('active');
    row.classList.add('playing');
    activeBtn = btn;
    activeRow = row;
  }});

  // Search / filter
  const search = document.getElementById('search');
  const rows = document.querySelectorAll('.sentence');
  search.addEventListener('input', () => {{
    const q = search.value.toLowerCase();
    rows.forEach(r => {{
      const text = r.querySelector('.text').textContent.toLowerCase();
      r.classList.toggle('hidden', q && !text.includes(q));
    }});
  }});
}})();
</script>
</body>
</html>
"""


def generate_html(sentences: list[dict]):
    """Build index.html from the sentence list."""
    rows = []
    for s in sentences:
        num = s["num"]
        display_text = bold_to_html(s["raw"])
        filename = f"{num:04d}.mp3"
        row = (
            f'    <div class="sentence">'
            f'<span class="num">{num}.</span>'
            f'<span class="text">{display_text}</span>'
            f'<button class="play-btn" data-file="{filename}" title="Play sentence {num}">▶</button>'
            f'</div>'
        )
        rows.append(row)

    html_content = HTML_TEMPLATE.format(rows="\n".join(rows))
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML written to {HTML_FILE}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Parsing {SENTENCES_FILE} ...")
    sentences = parse_sentences(SENTENCES_FILE)
    print(f"Found {len(sentences)} sentences.\n")

    print("Generating HTML ...")
    generate_html(sentences)

    print(f"\nGenerating audio files in {AUDIO_DIR}/ ...")
    generate_audio_files(sentences)

    print("\n✓ All done!")


if __name__ == "__main__":
    main()
