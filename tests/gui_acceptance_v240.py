"""Interactive headless-desktop QA; run with xvfb-run python tests/gui_acceptance_v240.py."""
from __future__ import annotations
import os
import sys
import tempfile
import time
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tkinter as tk
import greeklish_gui as ui
from user_preferences import settings_path, load
from rename_greek_to_greeklish import ScanCancelled

with tempfile.TemporaryDirectory() as td:
    home = Path(td)
    os.environ['XDG_CONFIG_HOME'] = str(home / 'configuration')
    data = home / 'my music'
    data.mkdir()
    for i in range(400):
        (data / f'Ελληνικά {i:04}.mp3').write_bytes(b'data')
    root = tk.Tk()
    root.withdraw()
    window = ui.GreeklishWindow(root)
    assert window.folder.get() != str(data)
    window.folder.set(str(data))
    window.extension_preset.set('MP3 only')
    root.update()
    window._save_settings()
    assert load().last_folder == str(data.resolve()), load()
    assert load().file_type_preset == 'MP3 only'
    window._on_close()

    root = tk.Tk()
    root.withdraw()
    window = ui.GreeklishWindow(root)
    assert window.folder.get() == str(data.resolve())
    assert window.extension_preset.get() == 'MP3 only'
    orig = ui.create_preview
    started = threading.Event()
    cancelled = threading.Event()
    def slow_preview(*args, **kwargs):
        callback = kwargs['scan_progress']
        signal = kwargs['should_cancel']
        def wrapped(folders, files, current):
            callback(folders, files, current)
            started.set()
            while not signal():
                time.sleep(.008)
            cancelled.set()
        kwargs['scan_progress'] = wrapped
        return orig(*args, **kwargs)
    with patch.object(ui, 'create_preview', slow_preview):
        window._preview()
        deadline=time.monotonic()+12
        while not started.is_set() and time.monotonic()<deadline:
            root.update();time.sleep(.008)
        assert started.is_set(), 'preview did not start'
        root.update()
        assert window.cancel_scan_btn['state']=='normal', window.cancel_scan_btn['state']
        with patch.object(ui.messagebox, 'askyesno', return_value=True):
            window._on_close()
        assert window.scan_cancel_event.is_set()
        assert root.winfo_exists(), 'active window was destroyed instead of cancelling'
        while window.processing and time.monotonic()<deadline:
            root.update();time.sleep(.008)
        assert not window.processing and cancelled.is_set()
        root.update()
        assert window.state.get()=='SCAN CANCELLED',window.state.get()
        assert not window.current_preview
        assert not list(data.glob('greeklish_rename_log*'))
        assert len(list(data.glob('*.mp3')))==400
    window._preview()
    deadline=time.monotonic()+12
    while window.processing and time.monotonic()<deadline:
        root.update();time.sleep(.008)
    assert window.current_preview.count==400,window.current_preview.count
    assert window.checked[0]
    window._on_close()
    print('PASS interactive v2.4.0: remembers folder and MP3 filter, active Cancel scan and protected close, no partial preview, subsequent full preview')
