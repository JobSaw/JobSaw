import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional


def _escape_latex(text: Optional[str]) -> str:
    """Escape characters that would break LaTeX. Leave Unicode characters intact (inputenc utf8 used in the class).

    This is a lightweight escaper — it handles the most common unsafe chars.
    """
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s


def _date_range(start: Optional[str], end: Optional[str]) -> str:
    if start and end:
        return f"{_escape_latex(start)} -- {_escape_latex(end)}"
    if start and not end:
        return _escape_latex(start)
    if not start and end:
        return _escape_latex(end)
    return ""


def generate_cv_pdf(cv_json: Dict, output_pdf_path: str, templates_dir: Optional[str] = None, tex_basename: str = "cv") -> None:
    """Generate a PDF CV from a JSON object matching `models/cv_model.json`.

    Parameters
    - cv_json: dict loaded from the model JSON (meta, sections_order, sections)
    - output_pdf_path: where to place the generated PDF (including filename)
    - templates_dir: optional path to the directory that contains `CV.tex` and `altacv.cls`.
                     By default it will use the repository's `templates/CV` folder.
    - tex_basename: base name for the temporary tex file (without extension)

    Notes
    - This function does not create a main. Call it from other code.
    - Requires `latexmk` installed and available on PATH.
    - The function copies the entire templates dir to a temp working directory so the class
      file and any dependencies are available during compilation.
    - The function attempts to run `latexmk -pdf` and then moves the produced PDF to
      `output_pdf_path`. It will run `latexmk -c` to clean auxiliary files.
    """

    # Resolve templates dir
    if templates_dir is None:
        base = Path(__file__).resolve().parents[1]
        templates_dir = base / "templates" / "CV"
    templates_dir = Path(templates_dir)
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    # Validate some basic structure
    if not isinstance(cv_json, dict):
        raise TypeError("cv_json must be a dict parsed from cv_model.json")
    meta = cv_json.get("meta", {})
    sections_order = cv_json.get("sections_order", [])
    sections = {s.get("id"): s for s in cv_json.get("sections", [])}

    # Build LaTeX document string
    lines = []
    # enable withhyper so altacv prints proper hyperlinks instead of fallback text
    lines.append(r"\documentclass[withhyper,10pt,a4paper]{altacv}")
    lines.append(r"\usepackage{hyperref}")
    lines.append(r"\usepackage{fontawesome5}")
    lines.append("")

    # Personal info
    name = _escape_latex(meta.get("name", ""))
    tagline = _escape_latex(meta.get("tagline", ""))
    personal = meta.get("personal_info", {})
    email = personal.get("email")
    phone = personal.get("phone")
    location = personal.get("location")
    linkedin = None
    if isinstance(personal.get("links"), dict):
        linkedin = personal["links"].get("linkedin") if "linkedin" in personal["links"] else personal.get("links").get("linkedin") if personal.get("links") else None
    # Fallback more defensive checks
    if linkedin is None and isinstance(personal.get("links"), dict):
        linkedin = personal.get("links", {}).get("linkedin")

    lines.append(f"\\name{{{name}}}")
    if tagline:
        lines.append(f"\\tagline{{{tagline}}}")

    # personalinfo block
    pi_lines = []
    if email:
        pi_lines.append(f"  \\email{{{_escape_latex(email)}}}")
    if phone:
        pi_lines.append(f"  \\phone{{{_escape_latex(phone)}}}")
    if location:
        pi_lines.append(f"  \\location{{{_escape_latex(location)}}}")
    if linkedin:
        esc_link = _escape_latex(linkedin)
        # render as href like original template
        pi_lines.append(f"  \\href{{{esc_link}}}{{\\textcolor{{blue!70!black}}{{\\faLinkedin}}\\ {esc_link}}}")

    if pi_lines:
        lines.append("\\personalinfo{")
        lines.extend(pi_lines)
        lines.append("}")

    lines.append("")
    lines.append(r"\begin{document}")
    lines.append(r"\makecvheader")
    lines.append("")

    # Helper to render each section
    def render_section(sec: Dict):
        stype = sec.get("type")
        title = _escape_latex(sec.get("title", ""))
        out = []
        out.append(f"\\cvsection{{{title}}}")
        if stype == "events":
            for it in sec.get("items", []):
                t = _escape_latex(it.get("title", ""))
                inst = _escape_latex(it.get("institution", ""))
                date = _date_range(it.get("start"), it.get("end"))
                loc = _escape_latex(it.get("location", ""))
                out.append(f"\\cvevent{{{t}}}{{{inst}}}{{{date}}}{{{loc}}}")
                # details as itemize
                details = it.get("details", []) or []
                if details:
                    out.append("\\begin{itemize}")
                    for d in details:
                        out.append(f"  \\item {_escape_latex(d)}")
                    out.append("\\end{itemize}")
        elif stype == "roles":
            for it in sec.get("items", []):
                t = _escape_latex(it.get("title", ""))
                org = _escape_latex(it.get("organization", ""))
                date = _date_range(it.get("start"), it.get("end"))
                loc = _escape_latex(it.get("location", ""))
                out.append(f"\\cvevent{{{t}}}{{{org}}}{{{date}}}{{{loc}}}")
                bullets = it.get("bullets", []) or []
                if bullets:
                    out.append("\\begin{itemize}")
                    for b in bullets:
                        out.append(f"  \\item {_escape_latex(b)}")
                    out.append("\\end{itemize}")
                out.append("")
        elif stype == "tags":
            for tag in sec.get("items", []):
                out.append(f"\\cvtag{{{_escape_latex(tag)}}} ")
        elif stype == "projects":
            for it in sec.get("items", []):
                t = _escape_latex(it.get("title", ""))
                subtitle = _escape_latex(it.get("subtitle", ""))
                date = _date_range(it.get("start"), it.get("end"))
                out.append(f"\\cvevent{{{t}}}{{{subtitle}}}{{{date}}}{{}}")
                desc = it.get("description")
                bullets = it.get("bullets", []) or []
                if desc or bullets:
                    out.append("\\begin{itemize}")
                    if desc:
                        out.append(f"  \\item {_escape_latex(desc)}")
                    for b in bullets:
                        out.append(f"  \\item {_escape_latex(b)}")
                    out.append("\\end{itemize}")
        elif stype == "list":
            items = sec.get("items", []) or []
            if items:
                out.append("\\begin{itemize}")
                for it in items:
                    title = _escape_latex(it.get("title", ""))
                    detail = _escape_latex(it.get("detail", ""))
                    if detail:
                        out.append(f"  \\item \\textbf{{{title}}} -- {detail}")
                    else:
                        out.append(f"  \\item {title}")
                out.append("\\end{itemize}")
        else:
            # custom or unknown: dump raw text if provided
            for it in sec.get("items", []):
                out.append(_escape_latex(str(it)))
        return out

    # Render sections in order
    for sid in sections_order:
        sec = sections.get(sid)
        if not sec:
            continue
        lines.extend(render_section(sec))
        lines.append("")

    lines.append(r"\end{document}")

    # Write to a temp working directory and copy templates
    tmpdir = Path(tempfile.mkdtemp(prefix="cv_build_"))
    try:
        # Copy template files so the class is available
        dest_templates = tmpdir / "templates"
        shutil.copytree(templates_dir, dest_templates)

        tex_filename = f"{tex_basename}.tex"
        tex_path = tmpdir / tex_filename
        with open(tex_path, "w", encoding="utf-8") as f:
            # We want altacv.cls to be found; put templates contents into same folder as tex
            # so copy all files to working dir root instead of templates subfolder
            f.write("\n".join(lines))

            # Create a minimal .xmpdata file to satisfy pdfx and avoid the "No file <name>.xmpdata" warning.
            xmp_path = tmpdir / f"{tex_basename}.xmpdata"
            try:
                with open(xmp_path, "w", encoding="utf-8") as xf:
                    title = cv_json.get("meta", {}).get("name", "")
                    xf.write(f"\\Title{{{_escape_latex(title)}}}\n")
                    xf.write(f"\\Author{{{_escape_latex(title)}}}\n")
            except Exception:
                # Non-fatal: if writing fails, continue and let LaTeX emit its own warning
                pass
        # Move template files from dest_templates into tmpdir root so latexmk finds them
        for item in dest_templates.iterdir():
            target = tmpdir / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    # Run latexmk
        # latexmk -pdf -output-directory=<tmpdir> <texfile>
        proc = subprocess.run([
            "latexmk",
            "-pdf",
            f"-output-directory={tmpdir}" ,
            tex_path.name
        ], cwd=tmpdir)
        if proc.returncode != 0:
            # On failure, preserve the tmpdir to help debugging
            raise RuntimeError(f"latexmk failed to build the PDF (return code {proc.returncode}). Temporary build dir: {tmpdir}")

        built_pdf = tmpdir / f"{tex_basename}.pdf"
        if not built_pdf.exists():
            # latexmk may name pdf after tex base name; try to find any pdf in tmpdir
            candidates = list(tmpdir.glob("*.pdf"))
            if candidates:
                built_pdf = candidates[0]
            else:
                raise FileNotFoundError("Built PDF not found after latexmk run")

        # Ensure output dir exists, then move
        out_path = Path(output_pdf_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(built_pdf), str(out_path))

        # Clean with latexmk -c
        subprocess.run(["latexmk", "-c", tex_path.name], cwd=tmpdir)

    finally:
        # Remove temp dir
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
