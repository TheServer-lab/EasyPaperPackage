#!/usr/bin/env python3
"""
EPP Viewer — standalone desktop renderer for .epp (Easy Paper Package) files.

A lightweight, dependency-free (standard library only) GUI viewer that
mirrors the look and behavior of the EPP Viewer browser extension:
dark "chrome" toolbar, cream paper pages, page navigation, printing
(export to PDF), and an Open File dialog.

Run:
    python3 epp_viewer.py [path/to/file.epp]

Packaging into a single executable (optional):
    pip install pyinstaller
    pyinstaller --onefile --windowed --name "EPP Viewer" epp_viewer.py
"""

import os
import sys
import tempfile
import traceback

import tkinter as tk
from tkinter import filedialog, messagebox

from epp_parser import parse_epp, parse_epp_file, EPPDocument, Page
from epp_render import PageCanvas, Fonts, PAGE_WIDTH

APP_TITLE = "EPP Viewer"

CHROME_BG = "#1b1b1a"
CHROME_FG = "#e7e2d3"
CHROME_BORDER = "#33322c"
CHROME_MUTED = "#a39d8c"
BTN_BORDER = "#4a4940"
ACCENT = "#c98a3e"
APP_BG = "#141413"

SAMPLE_SOURCE = '''%epp=0.2%
; Metadata
@meta title="EPP Example Document"
@meta author="SD"
@meta version="0.2"
; Printed on every page
@header "EPP Example Document"
@footer "Page [page]"
@page 1
@title "Easy Paper Package"
@heading "Introduction" {align=center,bold,italic,underline}
@text "EPP is a lightweight UTF-8 document format designed for creating printable documents."
@space
@quote "Simple formats survive longer than complicated ones."
@line
@heading "Features"
@bullet "UTF-8 text only"
@bullet "Multi-page documents"
@bullet "Easy parsing"
@bullet "Human readable"
@space
@heading "Installation Steps"
@bullet "Download the renderer" {type=number}
@bullet "Open an .epp document" {type=number}
@bullet "Print or export" {type=number}
@label intro_end
@newpage
@page 2
@heading "Tables"
@text "EPP supports simple text tables."
@table "Name|Role|Age"
@row "Alice|Developer|25"
@row "Bob|Designer|30"
@row "Charlie|Writer|22"
@space
@heading "Code Example"
@code "print('Hello World')[newline]print('Welcome to EPP')"
@line
@heading "Bullet Styles"
@bullet "Standard bullet" {type=disc}
@bullet "Check bullet" {type=check}
@bullet "Arrow bullet" {type=arrow}
@bullet "Star bullet" {type=star}
@newpage
@page 3
@heading "Conclusion"
@text "This document demonstrates all standard EPP 0.2 features."
@quote "A format should be as simple as possible, but no simpler."
@text "End of document."
'''


class EPPViewerApp(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=APP_BG)
        self.geometry("760x880")
        self.minsize(420, 480)

        self.doc: EPPDocument = None
        self.current_index = 0
        self.current_path = None
        self.fonts = Fonts(self)

        self._build_toolbar()
        self._build_page_area()
        self._bind_keys()

        if initial_path:
            self.load_file(initial_path)
        else:
            self.set_document(parse_epp(SAMPLE_SOURCE), path=None)

    # ---------- UI construction ----------

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=CHROME_BG, height=44)
        bar.pack(side="top", fill="x")
        bottom_rule = tk.Frame(self, bg=CHROME_BORDER, height=1)
        bottom_rule.pack(side="top", fill="x")

        self.brand_label = tk.Label(bar, text="EPP document", bg=CHROME_BG, fg=CHROME_FG,
                                     font=("Georgia", 10, "italic"), anchor="w")
        self.brand_label.pack(side="left", padx=(14, 6), pady=8)

        nav = tk.Frame(bar, bg=CHROME_BG)
        nav.pack(side="left", padx=10)
        self.prev_btn = self._make_button(nav, "\u2039", self.go_prev, width=3)
        self.prev_btn.pack(side="left", padx=4)
        self.indicator_label = tk.Label(nav, text="1 / 1", bg=CHROME_BG, fg=CHROME_MUTED,
                                         font=("Courier", 9), width=8)
        self.indicator_label.pack(side="left", padx=4)
        self.next_btn = self._make_button(nav, "\u203A", self.go_next, width=3)
        self.next_btn.pack(side="left", padx=4)

        actions = tk.Frame(bar, bg=CHROME_BG)
        actions.pack(side="right", padx=14)
        self.print_btn = self._make_button(actions, "Print / Export PDF", self.print_document, primary=True)
        self.print_btn.pack(side="right", padx=(8, 0))
        self.open_btn = self._make_button(actions, "Open file\u2026", self.open_file_dialog)
        self.open_btn.pack(side="right", padx=(8, 0))

    def _make_button(self, parent, text, command, width=None, primary=False):
        kwargs = dict(
            text=text, command=command,
            font=("Courier", 9), relief="flat", bd=1,
            padx=10, pady=5, cursor="hand2",
            highlightthickness=1,
        )
        if width:
            kwargs["width"] = width
        if primary:
            kwargs.update(bg=ACCENT, fg=CHROME_BG, activebackground="#dba052",
                           activeforeground=CHROME_BG, highlightbackground=ACCENT,
                           highlightcolor=ACCENT)
        else:
            kwargs.update(bg=CHROME_BG, fg=CHROME_FG, activebackground="#2a2a27",
                           activeforeground=ACCENT, highlightbackground=BTN_BORDER,
                           highlightcolor=ACCENT)
        btn = tk.Button(parent, **kwargs)
        return btn

    def _build_page_area(self):
        outer = tk.Frame(self, bg=APP_BG)
        outer.pack(side="top", fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(outer, bg=APP_BG, highlightthickness=0)
        vscroll = tk.Scrollbar(outer, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.page_holder = tk.Frame(self.scroll_canvas, bg=APP_BG)
        self.page_holder_id = self.scroll_canvas.create_window((0, 0), window=self.page_holder, anchor="n")

        self.page_holder.bind("<Configure>", self._on_holder_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scroll_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scroll_canvas.bind_all("<Button-4>", lambda e: self.scroll_canvas.yview_scroll(-3, "units"))
        self.scroll_canvas.bind_all("<Button-5>", lambda e: self.scroll_canvas.yview_scroll(3, "units"))

        self.page_card = tk.Frame(self.page_holder, bg=CHROME_BG)
        self.page_card.pack(pady=28)
        self.shadow = tk.Frame(self.page_card, bg="#0c0c0b")
        self.shadow.pack(padx=0, pady=0)
        self.page_canvas = PageCanvas(self.shadow, self.fonts, width=PAGE_WIDTH, height=600)
        self.page_canvas.pack(padx=0, pady=0)

    def _on_holder_configure(self, event):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.scroll_canvas.coords(self.page_holder_id, event.width / 2, 0)

    def _on_mousewheel(self, event):
        delta = -1 * int(event.delta / 40) if abs(event.delta) >= 40 else -1 * event.delta
        self.scroll_canvas.yview_scroll(delta, "units")

    def _bind_keys(self):
        self.bind("<Right>", lambda e: self.go_next())
        self.bind("<Down>", lambda e: self.go_next())
        self.bind("<Left>", lambda e: self.go_prev())
        self.bind("<Up>", lambda e: self.go_prev())
        self.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.bind("<Control-p>", lambda e: self.print_document())

    # ---------- document handling ----------

    def set_document(self, doc: EPPDocument, path):
        self.doc = doc
        self.current_path = path
        self.current_index = 0
        title = doc.title or "EPP document"
        self.brand_label.configure(text=title)
        self.title(f"{title} \u2014 {APP_TITLE}" if path else APP_TITLE)
        self.render_current_page()

    def load_file(self, path):
        try:
            doc = parse_epp_file(path)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Couldn't open this file as an EPP document:\n\n{exc}")
            return
        self.set_document(doc, path)

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Open EPP document",
            filetypes=[("EPP documents", "*.epp"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.load_file(path)

    # ---------- navigation ----------

    def go_next(self):
        if not self.doc:
            return
        self.current_index = min(self.current_index + 1, len(self.doc.pages) - 1)
        self.render_current_page()

    def go_prev(self):
        if not self.doc:
            return
        self.current_index = max(self.current_index - 1, 0)
        self.render_current_page()

    def render_current_page(self):
        if not self.doc or not self.doc.pages:
            return
        total = len(self.doc.pages)
        self.current_index = max(0, min(self.current_index, total - 1))
        page = self.doc.pages[self.current_index]
        label = page.number or str(self.current_index + 1)
        self.indicator_label.configure(text=f"{label} / {total}")

        page_number_for_footer = page.number or str(self.current_index + 1)
        height = self.page_canvas.draw_page(page, page_number_for_footer, self.doc.header, self.doc.footer)
        self.shadow.configure(width=PAGE_WIDTH, height=height)
        self.page_canvas.configure(width=PAGE_WIDTH, height=height)
        self.update_idletasks()
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    # ---------- printing / export ----------

    def print_document(self):
        if not self.doc:
            return
        try:
            from epp_pdf import export_pdf
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"PDF export isn't available:\n{exc}")
            return

        default_name = (self.doc.title or "document").strip() or "document"
        safe_name = "".join(c for c in default_name if c.isalnum() or c in " _-").strip() or "document"
        out_path = filedialog.asksaveasfilename(
            title="Export to PDF",
            defaultextension=".pdf",
            initialfile=f"{safe_name}.pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not out_path:
            return
        try:
            export_pdf(self.doc, out_path, self.fonts)
        except Exception:
            messagebox.showerror(APP_TITLE, f"Export failed:\n\n{traceback.format_exc()}")
            return
        messagebox.showinfo(APP_TITLE, f"Saved:\n{out_path}")


def main():
    initial_path = sys.argv[1] if len(sys.argv) > 1 else None
    if initial_path and not os.path.isfile(initial_path):
        print(f"File not found: {initial_path}", file=sys.stderr)
        initial_path = None
    app = EPPViewerApp(initial_path)
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # On Windows, double-clicking a .py file (especially with pythonw)
        # gives no visible console, so an unhandled exception would just
        # look like "nothing happened." Show it in a dialog instead.
        err = traceback.format_exc()
        print(err, file=sys.stderr)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(APP_TITLE, f"EPP Viewer failed to start:\n\n{err}")
        except Exception:
            pass
        sys.exit(1)
