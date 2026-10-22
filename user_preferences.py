"""Minimal private, local settings: no filename inventory, network or telemetry."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILE = 'settings.json'
MAX_BYTES = 16_384
VALID_PRESETS = frozenset(('All file types', 'Audio (.mp3, .flac, .wav)',
                           'MP3 only', 'FLAC only', 'WAV only', 'Custom list…'))


@dataclass(frozen=True)
class Preferences:
    last_folder: str = ''
    file_type_preset: str = 'All file types'
    custom_file_types: str = '.mp3, .flac'


def settings_path(*, home: Path | None = None) -> Path:
    if home is not None:
        return home / 'GreeklishRenamer' / CONFIG_FILE
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA')
        if base:
            return Path(base) / 'GreeklishRenamer' / CONFIG_FILE
        return Path.home() / 'AppData' / 'Local' / 'GreeklishRenamer' / CONFIG_FILE
    base = os.environ.get('XDG_CONFIG_HOME')
    return (Path(base) if base else Path.home() / '.config') / 'GreeklishRenamer' / CONFIG_FILE


def safe_folder(folder: str) -> str:
    if not isinstance(folder, str) or not folder.strip() or len(folder) > 4_096 or '\x00' in folder:
        return ''
    try:
        path = Path(folder).expanduser()
        from rename_greek_to_greeklish import is_link_or_junction
        if is_link_or_junction(path) or not path.is_dir():
            return ''
        return str(path.resolve(strict=True))
    except (OSError, ValueError, RuntimeError):
        return ''


def sanitize(raw: object) -> Preferences:
    if not isinstance(raw, dict):
        return Preferences()
    preset = raw.get('file_type_preset')
    if not isinstance(preset, str) or preset not in VALID_PRESETS:
        preset = 'All file types'
    custom = raw.get('custom_file_types')
    if not isinstance(custom, str) or len(custom) > 512:
        custom = '.mp3, .flac'
    try:
        from renamer_service import parse_extensions
        parse_extensions(custom)
    except ValueError:
        custom = '.mp3, .flac'
    return Preferences(safe_folder(raw.get('last_folder', '')),
                       preset, custom)


def load(path: Path | None = None) -> Preferences:
    file = path or settings_path()
    try:
        if not file.is_file() or file.stat().st_size > MAX_BYTES:
            return Preferences()
        return sanitize(json.loads(file.read_text(encoding='utf-8')))
    except (OSError, ValueError, UnicodeError, TypeError):
        return Preferences()


def save(preferences: Preferences, path: Path | None = None) -> bool:
    """Atomically replace settings; never destroy previous settings on errors."""
    file = path or settings_path()
    content = sanitize({
        'last_folder': preferences.last_folder,
        'file_type_preset': preferences.file_type_preset,
        'custom_file_types': preferences.custom_file_types,
    })
    text = json.dumps({'schema_version': 1, **content.__dict__}, ensure_ascii=False, indent=2) + '\n'
    temporary = None
    try:
        file.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n',
                                         dir=file.parent, prefix='.settings-', suffix='.tmp',
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, file)
        return True
    except OSError:
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
