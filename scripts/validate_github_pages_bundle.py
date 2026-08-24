from pathlib import Path
import hashlib
import json
import re

root = Path('/home/ubuntu/pmlg-website/github-pages')
required = ['index.html', '404.html', '.nojekyll', 'README_DEPLOY.md', 'ARCHIVE_MANIFEST.json', 'logo.png']
missing = [item for item in required if not (root / item).exists()]
files = [path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_file()]
forbidden = [item for item in files if item.endswith(('.mhtml', '.mht')) or item.startswith('__manus__/')]
index = (root / 'index.html').read_text(encoding='utf-8')
index_404 = (root / '404.html').read_text(encoding='utf-8')
refs = re.findall(r'(?:src|href)="(/[^"?#]+)', index)
base = '/PMLG-Events.github.io/'
root_asset_refs = [ref for ref in refs if ref.startswith(base)]
asset_refs = [ref[len(base):] for ref in root_asset_refs]
missing_refs = [ref for ref in asset_refs if not (root / ref).exists()]
manifest = json.loads((root / 'ARCHIVE_MANIFEST.json').read_text(encoding='utf-8'))
checks = {
    'required_files_present': not missing,
    'missing_required_files': missing,
    'no_raw_mhtml_or_manus_debug_files': not forbidden,
    'forbidden_files': forbidden,
    'index_has_project_site_asset_references': root_asset_refs,
    'all_index_asset_references_use_project_base': len(root_asset_refs) == len(asset_refs),
    'all_index_asset_references_resolve': not missing_refs,
    'missing_asset_references': missing_refs,
    '404_matches_index': index == index_404,
    'archive_records_embedded': manifest.get('eventRecordsEmbedded'),
    'source_mhtml_pages': manifest.get('sourceMhtmlPages'),
    'valid_event_records': manifest.get('validEventRecords'),
    'zip_ready': True,
}
print(json.dumps(checks, indent=2))
if missing or forbidden or missing_refs or len(root_asset_refs) != len(asset_refs) or index != index_404 or manifest.get('eventRecordsEmbedded') != 379:
    raise SystemExit(1)
