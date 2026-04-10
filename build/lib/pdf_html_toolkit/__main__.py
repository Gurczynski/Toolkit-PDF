from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

from convert_pdfs_to_html import main as converter_main


def main(argv: list[str] | None = None) -> int:
    rules_resource = files("pdf_html_toolkit").joinpath("render_rules.json")
    with as_file(rules_resource) as rules_path:
        return converter_main(
            argv=argv,
            default_input=Path.cwd(),
            default_rules_path=Path(rules_path),
        )


if __name__ == "__main__":
    raise SystemExit(main())
