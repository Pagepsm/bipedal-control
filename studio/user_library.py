"""Bounded, atomic on-disk terrain/settings storage for one local user.

No arbitrary paths or user-supplied filenames reach the filesystem; only UUID IDs.
For an internet-facing service this must be replaced by authenticated per-session storage.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from typing import Any
from app_paths import ensure_data_dirs, data_root
from robust_bipedal.terrain_geometry import TerrainProfile

MAX_NAME_LENGTH = 72
MAX_TERRAINS = 200
MAX_SETTINGS_BYTES = 8192
ID_PATTERN = re.compile(r'^[a-f0-9]{32}$')


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=str(path.parent), prefix='.writing-', suffix='.tmp', delete=False) as f:
            tmp = Path(f.name)
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def _terrain_path(uid: str) -> Path:
    if not ID_PATTERN.fullmatch(uid):
        raise ValueError('Invalid terrain ID')
    return data_root() / 'terrains' / (uid + '.json')


def save_terrain(name: str, terrain: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(name, str) or not name.strip() or len(name) > MAX_NAME_LENGTH or any(ord(c) < 32 for c in name):
        raise ValueError('地形名は1〜72文字の印字可能な文字にしてください')
    profile = TerrainProfile.from_data(terrain)
    folder = ensure_data_dirs() / 'terrains'
    if len(list(folder.glob('*.json'))) >= MAX_TERRAINS:
        raise ValueError('保存数の上限に達しました（200件）')
    uid = uuid.uuid4().hex
    record = {'id': uid, 'name': name.strip(), 'sha256': profile.terrain_sha256, 'terrain': profile.to_data()}
    raw = (json.dumps(record, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')
    _write_atomic(_terrain_path(uid), raw)
    return {'id': uid, 'name': record['name'], 'sha256': record['sha256']}


def read_terrain(uid: str) -> dict[str, Any]:
    raw = json.loads(_terrain_path(uid).read_text(encoding='utf-8'))
    profile = TerrainProfile.from_data(raw['terrain'])
    if raw['id'] != uid or profile.terrain_sha256 != raw['sha256']:
        raise ValueError('保存された地形のSHA検証に失敗しました')
    return raw


def list_terrains() -> list[dict[str, Any]]:
    folder = ensure_data_dirs() / 'terrains'
    result = []
    for file in sorted(folder.glob('*.json')):
        if not ID_PATTERN.fullmatch(file.stem):
            continue
        try:
            item = read_terrain(file.stem)
            result.append({k: item[k] for k in ('id', 'name', 'sha256')})
        except (OSError, KeyError, ValueError, json.JSONDecodeError):
            # Invalid entries must not silently become valid; report corruption.
            result.append({'id': file.stem, 'name': '[破損したデータ]', 'invalid': True})
    return result


def delete_terrain(uid: str) -> None:
    _terrain_path(uid).unlink()  # raise FileNotFoundError to caller


def read_settings() -> dict[str, Any]:
    path = ensure_data_dirs() / 'settings' / 'preferences.json'
    if not path.is_file():
        return {'schema_version': 'ui.preferences.v1', 'values': {}}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 'ui.preferences.v1' or not isinstance(data.get('values'), dict):
        raise ValueError('保存設定の形式が不正です')
    return data


def save_settings(data: dict[str, Any]) -> None:
    if set(data) != {'schema_version', 'values'} or data['schema_version'] != 'ui.preferences.v1' or not isinstance(data['values'], dict):
        raise ValueError('保存設定の形式が不正です')
    allowed = {'training_seed', 'evaluation_seed', 'playback_speed', 'domain', 'show_xray'}
    if not set(data['values']).issubset(allowed):
        raise ValueError('未対応の設定キーがあります')
    raw = (json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    if len(raw) > MAX_SETTINGS_BYTES:
        raise ValueError('設定データが大きすぎます')
    _write_atomic(ensure_data_dirs() / 'settings' / 'preferences.json', raw)
