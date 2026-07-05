"""
CV/CL compiler: supports LaTeX (.tex) and HTML (.html) inputs.

Usage:
  python compile_cv.py <file>

Examples:
  python compile_cv.py output/Company_Role/Your_Name_CV_Company.tex
  python compile_cv.py output/Company_Role/Your_Name_CL_Company.tex
  python compile_cv.py output/Company_Role/Your_Name_CV_CN.html

LaTeX routing:
  - CL_ files   -> xelatex (fontspec / Times New Roman)
  - CV_CN files -> xelatex (xeCJK / a CJK font)
  - CV files    -> pdflatex

HTML routing:
  - Any .html file -> Chrome headless --print-to-pdf (A4, no header/footer)
  - Output PDF placed in the same folder as the .html file
"""

import subprocess
import os
import sys
import shutil


def _find_tex(cmd):
    """Prefer a local miktex_install/ tree, else fall back to PATH."""
    local = os.path.join(os.path.dirname(__file__), "miktex_install", "miktex", "bin", "x64", cmd + ".exe")
    if os.path.exists(local):
        return local
    found = shutil.which(cmd)
    if found:
        return found
    print(f"Error: {cmd} not found. Install MiKTeX or TeX Live and ensure it is on PATH.")
    sys.exit(1)


MIKTEX   = shutil.which("miktex")
INITEXMF = shutil.which("initexmf")
WORK_DIR = os.path.dirname(__file__)

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def run_update_check():
    if not (MIKTEX and INITEXMF):
        return
    subprocess.run([MIKTEX, "packages", "check-update"], cwd=WORK_DIR, capture_output=True, timeout=30)
    subprocess.run([INITEXMF, "--update-fndb"], cwd=WORK_DIR, capture_output=True, timeout=30)


def compile_latex(tex_file):
    if not os.path.isabs(tex_file):
        tex_file = os.path.join(WORK_DIR, tex_file)

    tex_file = os.path.normpath(tex_file)

    if not os.path.exists(tex_file):
        print(f"Error: {tex_file} not found")
        sys.exit(1)

    out_dir  = os.path.dirname(tex_file)
    base     = os.path.basename(tex_file)
    pdf_name = os.path.splitext(base)[0] + ".pdf"
    pdf_path = os.path.join(out_dir, pdf_name)

    # Choose engine:
    #   CL_  → xelatex (fontspec / Times New Roman)
    #   CV_CN_ → xelatex (xeCJK / Microsoft YaHei)
    #   CV_  → pdflatex
    is_cl  = "CL_" in base
    is_cn  = "CV_CN" in base
    # Resolve the TeX engine lazily so the HTML/Chrome path (Chinese CVs need no
    # LaTeX) still works on a machine without a TeX distribution installed.
    engine = _find_tex("xelatex") if (is_cl or is_cn) else _find_tex("pdflatex")
    runs   = 2  # always 2 passes for cross-references

    engine_name = 'xelatex' if (is_cl or is_cn) else 'pdflatex'
    print(f"Compiling {base} with {engine_name} ...")

    for run in range(runs):
        result = subprocess.run(
            [engine, "-interaction=nonstopmode", f"-output-directory={out_dir}", base],
            cwd=out_dir,
            capture_output=True,
            timeout=180
        )
        if result.returncode != 0 and run == runs - 1:
            output = result.stdout.decode("utf-8", errors="replace")
            # Check for MiKTeX update issue
            if "you have not checked for MiKTeX updates" in output:
                print("MiKTeX update check required, running fix...")
                run_update_check()
                # Retry
                result = subprocess.run(
                    [engine, "-interaction=nonstopmode", f"-output-directory={out_dir}", base],
                    cwd=out_dir,
                    capture_output=True,
                    timeout=180
                )
            else:
                print("Compile errors:", output[-1500:])

    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        size = os.path.getsize(pdf_path)
        print(f"Done: {pdf_path} ({size:,} bytes)")
    else:
        print(f"Error: PDF not generated or is empty. Check {os.path.splitext(tex_file)[0]}.log")


def find_chrome():
    for path in CHROME_PATHS:
        if os.path.exists(path):
            return path
    return None


def compile_html(html_file):
    if not os.path.isabs(html_file):
        html_file = os.path.join(WORK_DIR, html_file)

    html_file = os.path.normpath(html_file)

    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found")
        sys.exit(1)

    chrome = find_chrome()
    if not chrome:
        print("Error: Chrome/Edge not found. Install Chrome to compile HTML files.")
        sys.exit(1)

    out_dir  = os.path.dirname(html_file)
    base     = os.path.basename(html_file)
    pdf_name = os.path.splitext(base)[0] + ".pdf"
    pdf_path = os.path.join(out_dir, pdf_name)

    # Convert Windows path to file:/// URL
    file_url = "file:///" + html_file.replace("\\", "/")

    print(f"Compiling {base} with Chrome headless ...")

    result = subprocess.run(
        [
            chrome,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-extensions",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=5000",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={pdf_path}",
            file_url,
        ],
        cwd=out_dir,
        capture_output=True,
        timeout=60,
    )

    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        size = os.path.getsize(pdf_path)
        print(f"Done: {pdf_path} ({size:,} bytes)")
    else:
        err = result.stderr.decode("utf-8", errors="replace")
        print(f"Error: PDF not generated.\n{err[-800:]}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compile_cv.py <file.tex|file.html>")
        sys.exit(1)

    input_file = sys.argv[1]
    if input_file.lower().endswith(".html"):
        compile_html(input_file)
    else:
        compile_latex(input_file)
