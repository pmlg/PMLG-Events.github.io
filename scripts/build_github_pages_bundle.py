#!/usr/bin/env python3
"""Assemble a self-contained GitHub Pages deployment folder from dist/public."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BUILD_ROOT = PROJECT / "dist" / "public"
OUTPUT_ROOT = PROJECT / "github-pages"
ZIP_PATH = PROJECT / "github-pages.zip"

DEPLOY_README = """# PMLG GitHub Pages bundle

This folder is the compiled, static deployment for the Perth Machine Learning Group website.

## Deploy with a repository branch

Copy the contents of this folder—not the folder itself—to the root of the GitHub Pages repository, commit, and push. In the repository settings, select **Settings → Pages → Deploy from a branch**, then choose the branch and `/ (root)` folder.

The bundle includes `index.html`, `404.html`, `.nojekyll`, compiled JavaScript and CSS, the PMLG logo, `upcoming-events.json`, `upcoming-event-template.json`, and the embedded 379-record local event archive. It intentionally excludes raw MHTML source pages, project source files, development tooling, and server code.

This bundle is compiled for the project site `https://pmlg.github.io/PMLG-Events.github.io/`. Copy the bundle contents to the repository root; do not change the asset paths.

## Deploy with GitHub Actions

Alternatively, upload this folder as the artifact for a Pages deployment workflow. The artifact root must contain `index.html` directly.

## Manage upcoming events

Edit the root-level `upcoming-events.json` file in the GitHub Pages repository. Keep it as a JSON array and copy the shape from `upcoming-event-template.json`. Add one event object per listing, commit, and push. The site fetches this file at runtime, so adding or changing an upcoming event does not require rebuilding the JavaScript bundle. The event signup action opens the PMLG LinkedIn page; no public email address is stored in the site.

## Custom domain

After the first deployment, add `pmlg.com.au` in **Settings → Pages → Custom domain**, then configure DNS with your registrar. Do not add a `CNAME` file to this bundle until the final domain is confirmed.

## Local preview

Serve the folder with any static server, for example:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/`.
"""


def strip_manus_debug(html: str) -> str:
    return html.replace('    <script defer src="/__manus__/debug-collector.js"></script>\n', "")


def main() -> None:
    if not BUILD_ROOT.is_dir():
        raise SystemExit(f"Missing production output: {BUILD_ROOT}. Run pnpm build first.")

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()

    for source in BUILD_ROOT.iterdir():
        if source.name in {"__manus__", ".gitkeep"}:
            continue
        destination = OUTPUT_ROOT / source.name
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    index_path = OUTPUT_ROOT / "index.html"
    index_html = strip_manus_debug(index_path.read_text(encoding="utf-8"))
    index_path.write_text(index_html, encoding="utf-8")
    (OUTPUT_ROOT / "404.html").write_text(index_html, encoding="utf-8")
    (OUTPUT_ROOT / ".nojekyll").write_text("", encoding="utf-8")
    (OUTPUT_ROOT / "README_DEPLOY.md").write_text(DEPLOY_README, encoding="utf-8")

    archive_path = PROJECT / "client" / "src" / "data" / "events-archive.json"
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "deploymentBase": "/PMLG-Events.github.io/",
        "siteUrl": "https://pmlg.github.io/PMLG-Events.github.io/",
        "eventRecordsEmbedded": len(archive),
        "sourceBatches": 38,
        "sourceMhtmlPages": 380,
        "validEventRecords": 379,
        "skippedInvalidPages": 1,
        "rawMhtmlIncluded": False,
    }
    (OUTPUT_ROOT / "ARCHIVE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(OUTPUT_ROOT.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(OUTPUT_ROOT).as_posix())

    files = sorted(path.relative_to(OUTPUT_ROOT).as_posix() for path in OUTPUT_ROOT.rglob("*") if path.is_file())
    print(json.dumps({
        "folder": str(OUTPUT_ROOT),
        "zip": str(ZIP_PATH),
        "files": files,
        "fileCount": len(files),
        "folderBytes": sum((OUTPUT_ROOT / file).stat().st_size for file in files),
        "zipBytes": ZIP_PATH.stat().st_size,
    }, indent=2))


if __name__ == "__main__":
    main()
