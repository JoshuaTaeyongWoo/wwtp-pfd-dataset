"""make_pdf.py — export .docx files to PDF with Word (COM). Copies each file to an ASCII temp path first.
Usage: python make_pdf.py A.docx [B.docx ...]"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

def to_pdf(docx: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="pdf_")); src = tmp / docx.name; shutil.copy2(docx, src); pdf = src.with_suffix(".pdf")
    ps = f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open('{src}', $false, $true); $d.ExportAsFixedFormat('{pdf}', 17); $d.Close($false); $w.Quit()"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    out = docx.with_suffix(".pdf"); shutil.copy2(pdf, out); shutil.rmtree(tmp, ignore_errors=True); return out

if __name__ == "__main__":
    for a in sys.argv[1:]:
        print("saved", to_pdf(Path(a).resolve()))
