"""Orchestrator helper to build a CV PDF from the JSON model.

This module provides a small entrypoint so you can run:

	python orchestor.py

It will load `models/cv_model.json` and call
`latex_module.latex_pdf_creator.generate_cv_pdf` to produce
`output/victor_cv.pdf` by default.

Notes:
- Requires a LaTeX installation and `latexmk` on PATH.
- The function is intentionally simple; use it as a test harness.
"""

import json
import sys
from pathlib import Path

from latex_module.latex_pdf_creator import generate_cv_pdf


# Small utility: deep-merge a template dict with an override dict.
def _deep_merge(base, override):
	"""Return a new dict which is base overlaid by override.

	Rules:
	- dicts are merged recursively
	- lists in override replace lists in base when override list is non-empty
	- scalar values in override replace base when override value is not None
	"""
	if override is None:
		return base
	if isinstance(base, dict) and isinstance(override, dict):
		out = dict(base)
		for k, v in override.items():
			if k in out and isinstance(out[k], dict) and isinstance(v, dict):
				out[k] = _deep_merge(out[k], v)
			else:
				out[k] = v
		return out
	if isinstance(base, list) and isinstance(override, list):
		return override if override else base
	# for other types (including None), prefer override when not None
	return override if override is not None else base


def _merge_sections_by_id(base_sections: list, override_sections: list) -> list:
	"""Merge two lists of section dicts by their 'id' key.

	For each section in base_sections, if an override with the same 'id' exists,
	deep-merge them (so template fields like title/type are preserved unless
	overridden). Any override sections with new ids are appended.
	"""
	base_by_id = {s.get("id"): s for s in base_sections}
	out = []

	# First, merge base sections in original order
	for s in base_sections:
		sid = s.get("id")
		if sid is None:
			# keep as-is if no id
			out.append(s)
			continue
		# find override with same id
		ov = next((o for o in override_sections if o.get("id") == sid), None)
		if ov is None:
			out.append(s)
		else:
			merged = _deep_merge(s, ov)
			out.append(merged)

	# Append any override sections that are new (id not in base)
	base_ids = {s.get("id") for s in base_sections if s.get("id") is not None}
	for o in override_sections:
		oid = o.get("id")
		if oid is None or oid not in base_ids:
			out.append(o)

	return out


def run_orchestrator(model_path: str = "models/cv_model.json", output_pdf: str = "output/victor_cv.pdf", templates_dir: str = None, cv_override: dict = None) -> None:
	"""Load the JSON model and generate a PDF using the latex generator.

	Parameters:
	- model_path: path to cv_model.json (template)
	- output_pdf: path where the generated PDF will be written
	- templates_dir: optional path to templates/CV if you want to override the default
	- cv_override: pass a dict directly to use as the CV model (skips reading the file)
	"""
	if cv_override is not None:
		cv = cv_override
	else:
		model_file = Path(model_path)
		if not model_file.exists():
			raise FileNotFoundError(f"Model file not found: {model_file}")

		with model_file.open("r", encoding="utf-8") as f:
			cv = json.load(f)

	# Call the generator
	generate_cv_pdf(cv, output_pdf, templates_dir=templates_dir, tex_basename="test1")


if __name__ == "__main__":
	# Allow optional CLI overrides: python orchestor.py [model.json] [output.pdf] [templates_dir]
	try:
		args = sys.argv[1:]
		model_arg = args[0] if len(args) >= 1 else "models/cv_model.json"
		out_arg = args[1] if len(args) >= 2 else "output/victor_cv.pdf"
		templates_arg = args[2] if len(args) >= 3 else None

		print(f"Loading model: {model_arg}")
		print(f"Output PDF: {out_arg}")
		if templates_arg:
			print(f"Using templates dir: {templates_arg}")

		# Load the template model and apply small example modifications here in the orchestrator.
		# This demonstrates taking the canonical template at `models/cv_model.json`, overlaying
		# user-specific data, and generating a PDF from the merged model.
		model_file = Path(model_arg)
		with model_file.open("r", encoding="utf-8") as f:
			base_cv = json.load(f)

		# Example modifications: replace name, contact and add one education entry and a skill
		example_mods = {
			"meta": {
				"name": "Victor-Stefan Florescu",
				"personal_info": {"email": "victor.s.florescu@gmail.com", "phone": "+40 737 861 886"}
			},
			"sections": [
				{
					"id": "education",
					"items": [
						{
							"title": "B.Sc. Computer Science & Engineering",
							"institution": "University Politehnica of Bucharest",
							"start": "2024",
							"end": "Present",
							"location": "Bucharest, Romania"
						}
					]
				},
				{
					"id": "technical_skills",
					"items": ["Python", "C/C++", "Linux"]
				}
			]
		}

		merged = _deep_merge(base_cv, example_mods)
		# Special-case merge for `sections`: merge by section `id` so template
		# fields like title/type are preserved when the override only supplies
		# items or small changes.
		if "sections" in base_cv and "sections" in example_mods:
			merged["sections"] = _merge_sections_by_id(base_cv.get("sections", []), example_mods.get("sections", []))

		run_orchestrator(model_arg, out_arg, templates_arg, cv_override=merged)
		print("PDF generation finished successfully.")
	except Exception as e:
		print("Error during PDF generation:", str(e))
		sys.exit(1)

