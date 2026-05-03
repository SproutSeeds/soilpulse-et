# Data Notes

Keep downloaded challenge files and derived large artifacts local-only.

- do not commit bulky datasets or private submission artifacts
- cite every NASA dataset or NASA-data-derived algorithm used
- note schema and provenance decisions in `docs/WORKLOG.md`
- after any data download or mount, run:
  `PYTHONPATH=src python3 scripts/build_local_data_manifest.py`
