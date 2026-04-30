"""Auto-build a markdown inventory for tables and figures."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_TABLES = ROOT / "260303" / "outputs" / "tables"
OUT_FIGS = ROOT / "260303" / "outputs" / "figures"
DOC_PATH = ROOT / "260303" / "docs" / "result_inventory_v1.md"



def list_paths(base: Path, pattern: str) -> list[str]:
    if not base.exists():
        return []
    return sorted([str(p.relative_to(ROOT)) for p in base.glob(pattern)])



def to_lines(items: list[str]) -> str:
    if not items:
        return "- (none)\n"
    return "".join([f"- {x}\n" for x in items])



def main() -> None:
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)

    csvs = list_paths(OUT_TABLES, "*.csv")
    txts = list_paths(OUT_TABLES, "*.txt")
    figs = list_paths(OUT_FIGS, "*.png")

    body = (
        "# Result Inventory v1\n\n"
        "## Tables (CSV)\n"
        f"{to_lines(csvs)}\n"
        "## Tables (Text Summary)\n"
        f"{to_lines(txts)}\n"
        "## Figures (PNG)\n"
        f"{to_lines(figs)}\n"
        "## Notes\n"
        "- Update claim-to-evidence mapping after each major rerun.\n"
    )

    DOC_PATH.write_text(body, encoding="utf-8")


if __name__ == "__main__":
    main()
