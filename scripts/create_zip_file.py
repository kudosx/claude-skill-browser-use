#!/usr/bin/env python3
"""Create a zip file of the browser-use folder."""

import zipfile
from pathlib import Path


def create_zip(
    source_dir: Path,
    output_path: Path,
    exclude_patterns: list[str] | None = None,
) -> None:
    """Create a zip file from a directory.

    Args:
        source_dir: Directory to zip
        output_path: Path for the output zip file
        exclude_patterns: List of patterns to exclude (e.g., '.git', '__pycache__')
    """
    if exclude_patterns is None:
        exclude_patterns = []

    def should_exclude(path: Path) -> bool:
        for pattern in exclude_patterns:
            if pattern in path.parts:
                return True
        return False

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file() and not should_exclude(file_path):
                arcname = file_path.relative_to(source_dir.parent)
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")


def main() -> None:
    # Target: .claude/skills/browser-use folder
    scripts_dir = Path(__file__).parent
    project_root = scripts_dir.parent
    browser_use_dir = project_root / ".claude" / "skills" / "browser-use"
    output_path = project_root / "browser-use.zip"

    # Patterns to exclude
    exclude = [
        ".git",
        ".auth",
        "__pycache__",
        ".DS_Store",
        "downloads",
        ".venv",
        "node_modules",
    ]

    print(f"Creating zip from: {browser_use_dir}")
    print(f"Output: {output_path}")
    print(f"Excluding: {exclude}")
    print("-" * 40)

    create_zip(browser_use_dir, output_path, exclude)

    print("-" * 40)
    print(f"Created: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
