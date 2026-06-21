# EPP Viewer (standalone)

A lightweight desktop renderer for `.epp` (Easy Paper Package) documents —
a Python port of the EPP Viewer browser extension, with the same look
(dark toolbar, cream paper pages) and the same parsing rules.

No installation required for viewing. Only the PDF export feature needs
one extra library (`reportlab`).

## Files

- `epp_viewer.py` — the GUI app (run this one)
- `epp_parser.py` — parses `.epp` source text into pages/blocks
- `epp_render.py` — draws pages on screen (Tkinter canvas)
- `epp_pdf.py` — exports a document to PDF (used by the "Print / Export PDF" button)
- `EPP Viewer.bat` — Windows double-click launcher
- `requirements.txt` — optional dependency for PDF export

## Why double-clicking the `.py` file doesn't work

Windows doesn't run `.py` files as GUI apps by default — double-clicking
either does nothing, flashes a console and closes, or opens the file in
a text editor, depending on how Python was installed. This is normal
Windows behavior, not a bug in the app.

**Use `EPP Viewer.bat` instead** — double-click that file and it will
launch the app properly (it runs `epp_viewer.py` using `pythonw`, which
has no console window).

If double-clicking the `.bat` file also does nothing, open Command
Prompt in this folder and run:
```
python epp_viewer.py
```
This will print any error directly so we can see what's wrong (most
commonly: Python isn't installed, or isn't on PATH).

## Requirements

- Python 3.8+ with **Tkinter** (included by default on Windows and macOS
  python.org installers; on Linux you may need `sudo apt install python3-tk`)
- Optional, for the "Print / Export PDF" button:
  ```
  pip install -r requirements.txt
  ```
  Without it, viewing and page navigation still work — only PDF export
  is disabled, and the app tells you how to enable it.

## Usage

Open a specific file directly:
```
python epp_viewer.py path\to\file.epp
```

Or just run `epp_viewer.py` / `EPP Viewer.bat` with no arguments to see
a built-in sample document, then use "Open file…" to load your own.

## Associating .epp files with this app (optional)

So that double-clicking an `.epp` file anywhere opens this viewer:

1. Right-click any `.epp` file → **Open with** → **Choose another app**
2. Browse to `EPP Viewer.bat` in this folder
3. Check "Always use this app to open .epp files"

## Packaging as a single .exe (optional)

If you'd rather ship one `.exe` than a folder of `.py` files:
```
pip install pyinstaller reportlab
pyinstaller --onefile --windowed --name "EPP Viewer" epp_viewer.py
```
The resulting `dist/EPP Viewer.exe` is fully standalone — recipients
don't need Python installed at all.
