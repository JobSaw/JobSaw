"""
retry_latex.py -- Regenerate or recompile the CV PDF from existing files.

Usage:
    # 1. Rerun AI (generate new .tex) AND recompile
    python retry_latex.py <path_to_output_dir>

    # 2. Only recompile the existing .tex file (skip AI generation)
    python retry_latex.py <path_to_output_dir> --compile-only
"""

import argparse
import os
import sys
import logging

from cv_generator.cv_writer_agent import CvWriterAgent
from cv_generator.compiler import LatexCompiler
from logging_config import setup_logging

logger = logging.getLogger("retry")

def main():
    parser = argparse.ArgumentParser(description="Retry CV generation or compilation.")
    parser.add_argument("out_dir", help="Path to the timestamped output directory")
    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="Skip AI generation and only recompile the existing 04_tailored_cv.tex file",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    if not os.path.exists(out_dir):
        print(f"Error: Directory not found -> {out_dir}")
        sys.exit(1)

    setup_logging(out_dir)

    tex_path = os.path.join(out_dir, "04_tailored_cv.tex")

    if args.compile_only:
        logger.info("Skipping AI generation. Recompiling existing LaTeX file in: %s", out_dir)
        if not os.path.exists(tex_path):
            logger.error("Cannot find %s to compile.", tex_path)
            sys.exit(1)
    else:
        logger.info("Retrying AI LaTeX generation from existing data in: %s", out_dir)
        
        # 1. Read existing JSONs
        try:
            with open(os.path.join(out_dir, "01_profile_data.json"), "r", encoding="utf-8") as f:
                profile_json = f.read()
            with open(os.path.join(out_dir, "02_job_analysis.json"), "r", encoding="utf-8") as f:
                job_analysis_json = f.read()
            with open(os.path.join(out_dir, "03_selected_profile.json"), "r", encoding="utf-8") as f:
                selected_json = f.read()
        except Exception as e:
            logger.error("Failed to read intermediate JSON files from %s.", out_dir)
            sys.exit(1)

        # 2. Read template
        template_path = os.path.join("templates", "cv_template.tex")
        if not os.path.exists(template_path):
            logger.error("Template not found: %s", template_path)
            sys.exit(1)

        with open(template_path, "r", encoding="utf-8") as f:
            latex_template = f.read()

        # 3. Re-run CvWriterAgent
        writer = CvWriterAgent()
        logger.info("Generating new LaTeX content...")
        try:
            tailored_latex = writer.generate(
                latex_template=latex_template,
                profile_json=profile_json,
                selected_json=selected_json,
                job_analysis_json=job_analysis_json,
            )
        except Exception as e:
            logger.exception("AI Generation failed.")
            sys.exit(1)

        # 4. Save new .tex
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tailored_latex)
        logger.info("New LaTeX saved to: %s", tex_path)

    # 5. Compile
    compiler = LatexCompiler()
    logger.info("Compiling LaTeX to PDF...")
    try:
        pdf_path, num_pages = compiler.compile(tex_path, out_dir)
        final_pdf_path = os.path.join(out_dir, "05_tailored_cv.pdf")
        if os.path.exists(final_pdf_path):
            os.remove(final_pdf_path)
        os.rename(pdf_path, final_pdf_path)
        print("\n" + "#" * 60)
        print("  RETRY SUCCESSFUL")
        print("#" * 60)
        print(f"\nPDF generated at: {final_pdf_path} (Pages: {num_pages})\n")
        if num_pages > 1:
            print(f"WARNING: The generated PDF is {num_pages} pages long. You may want to edit 04_tailored_cv.tex and run with --compile-only")
    except Exception as e:
        logger.exception("Compilation failed.")
        print("\nFailed to compile PDF. Check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
