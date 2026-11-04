"""UI updater preserves private configuration, runtime and original assets."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ui_updater', ROOT / 'scripts' / 'apply_ui_upgrade.py')
UPDATER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATER)


def target_tree(tmp_path):
    target = tmp_path / 'existing-retail-pulse'
    web = target / 'src' / 'retail_pulse' / 'web'
    web.mkdir(parents=True)
    (target / 'pyproject.toml').write_text('[project]\nname = "retail-pulse"\n')
    for name in ('index.html', 'app.js', 'style.css'):
        (web / name).write_text('original ' + name)
    (target / '.env').write_text('LOCAL_SENTINEL=do-not-touch\n')
    (target / 'runtime').mkdir()
    (target / 'runtime' / 'model.bin').write_bytes(b'private runtime sentinel')
    return target, web


def test_updater_dry_run_is_read_only(tmp_path):
    target, web = target_tree(tmp_path)
    assert UPDATER.main(['--target', str(target), '--dry-run']) == 0
    assert (web / 'index.html').read_text() == 'original index.html'
    assert not list(tmp_path.glob('*-ui-backups'))
    assert not (web / 'favicon.svg').exists()


def test_updater_copies_only_assets_and_backs_up(tmp_path):
    target, web = target_tree(tmp_path)
    before_env = (target / '.env').read_bytes()
    before_runtime = (target / 'runtime' / 'model.bin').read_bytes()
    assert UPDATER.main(['--target', str(target)]) == 0
    for name in UPDATER.ASSETS:
        assert (web / name).read_bytes() == (ROOT / 'src/retail_pulse/web' / name).read_bytes()
    assert (target / '.env').read_bytes() == before_env
    assert (target / 'runtime' / 'model.bin').read_bytes() == before_runtime
    backups = list(tmp_path.glob('*-ui-backups/*/manifest.json'))
    assert len(backups) == 1
    assert (backups[0].parent / 'index.html').read_text() == 'original index.html'


def test_updater_is_idempotent(tmp_path):
    target, _ = target_tree(tmp_path)
    UPDATER.main(['--target', str(target)])
    UPDATER.main(['--target', str(target)])
    assert len(list(tmp_path.glob('*-ui-backups/*/manifest.json'))) == 1


def test_updater_rolls_back_on_write_failure(tmp_path, monkeypatch):
    target, web = target_tree(tmp_path)
    original_copy = UPDATER.atomic_copy

    def failing_copy(source, destination):
        if source.parent == ROOT / 'src/retail_pulse/web' and source.name == 'style.css':
            raise OSError('simulated copy failure')
        original_copy(source, destination)

    monkeypatch.setattr(UPDATER, 'atomic_copy', failing_copy)
    with pytest.raises(OSError, match='simulated copy failure'):
        UPDATER.main(['--target', str(target)])
    for name in ('index.html', 'app.js', 'style.css'):
        assert (web / name).read_text() == 'original ' + name
    assert not (web / 'favicon.svg').exists()


def test_updater_rejects_wrong_folder(tmp_path):
    with pytest.raises(SystemExit) as exc:
        UPDATER.main(['--target', str(tmp_path)])
    assert exc.value.code == 2
