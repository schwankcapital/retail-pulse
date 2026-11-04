"""Install only Retail Pulse web assets into an existing project.

This installer never opens or writes .env, runtime/, databases, models or Python
backend files. It makes a dated backup outside the target repository and rolls
back changed assets if copying fails.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ASSETS = ('index.html', 'app.js', 'style.css', 'favicon.svg')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy(source: Path, destination: Path) -> None:
    fd, name = tempfile.mkstemp(prefix='.rp-ui-', suffix='.tmp', dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(source.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=Path, required=True,
                        help='Existing retail-pulse project folder (contains pyproject.toml and src).')
    parser.add_argument('--dry-run', action='store_true', help='Validate and show changes without writing.')
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parents[1] / 'src' / 'retail_pulse' / 'web'
    target = args.target.expanduser().resolve()
    web = target / 'src' / 'retail_pulse' / 'web'
    if not (target / 'pyproject.toml').is_file() or not (web / 'index.html').is_file():
        parser.error('Target is not a Retail Pulse project. Choose the folder containing pyproject.toml and src.')
    if any(part.is_symlink() for part in (target / 'src', target / 'src' / 'retail_pulse', web)):
        parser.error('Refusing to modify a symlinked web path.')
    for name in ASSETS:
        if not (source / name).is_file():
            parser.error(f'Update asset is missing: {name}')
        if (web / name).is_symlink():
            parser.error(f'Refusing to replace a symlink: {name}')
    if 'In-Store Retail Super Intelligence' not in (source / 'index.html').read_text(encoding='utf-8'):
        parser.error('Source assets do not match the Retail Pulse UI update.')
    changes = [name for name in ASSETS if not (web / name).exists() or digest(web / name) != digest(source / name)]
    if not changes:
        print('This project already has these interface assets. No changes made.')
        return 0
    print('Target:', target)
    print('Files:', ', '.join(changes))
    print('Backend, .env, runtime data and model files will not be changed.')
    if args.dry_run:
        print('Dry run complete. Nothing was written.')
        return 0
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = target.parent / f'{target.name}-ui-backups' / stamp
    backup.mkdir(parents=True, exist_ok=False)
    manifest = {'target': str(target), 'created_utc': stamp, 'files': {}}
    for name in changes:
        exists = (web / name).exists()
        if exists:
            shutil.copy2(web / name, backup / name)
        manifest['files'][name] = {'previously_existed': exists,
                                   'old_sha256': digest(web / name) if exists else None,
                                   'new_sha256': digest(source / name)}
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    written: list[str] = []
    try:
        for name in changes:
            atomic_copy(source / name, web / name)
            written.append(name)
            if digest(web / name) != digest(source / name):
                raise OSError(f'Checksum mismatch after copying {name}')
    except Exception:
        for name in reversed(written):
            if manifest['files'][name]['previously_existed']:
                atomic_copy(backup / name, web / name)
            else:
                (web / name).unlink(missing_ok=True)
        print('Installation failed; changed assets were restored. Backup:', backup, file=sys.stderr)
        raise
    print('Interface update installed. Backup:', backup)
    print('Restart your existing Retail Pulse server; refresh the browser with Ctrl+F5.')
    print('Do not rerun demo generation or overwrite .env for this interface-only update.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
