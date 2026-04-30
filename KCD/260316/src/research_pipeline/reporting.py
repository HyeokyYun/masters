from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def build_output_manifest(work_dir: Path) -> pd.DataFrame:
    rows = []
    for rel in ["outputs/tables", "outputs/figures", "outputs/logs", "artifacts/models"]:
        base = work_dir / rel
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file():
                stat = path.stat()
                rows.append(
                    {
                        "category": rel,
                        "relative_path": str(path.relative_to(work_dir)),
                        "size_bytes": stat.st_size,
                        "modified_at": pd.Timestamp(stat.st_mtime, unit="s"),
                    }
                )
    return pd.DataFrame(rows)


def build_markdown_inventory(manifest: pd.DataFrame) -> str:
    lines = ["# 260316 Output Inventory", "", "실행 후 생성된 파일 목록입니다.", ""]
    if manifest.empty:
        lines.append("- 아직 생성된 산출물이 없습니다.")
        return "\n".join(lines)

    for category, group in manifest.groupby("category"):
        lines.append(f"## {category}")
        lines.append("")
        for _, row in group.sort_values("relative_path").iterrows():
            lines.append(f"- `{row['relative_path']}` ({int(row['size_bytes'])} bytes)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_inventory_bundle(work_dir: Path) -> Dict[str, object]:
    manifest = build_output_manifest(work_dir)
    markdown = build_markdown_inventory(manifest)
    return {"manifest": manifest, "markdown": markdown}
