"""Shared helpers for the v1.1 build (tools/v20)."""
import json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(HERE, '..', '..'))          # Succubi_Server/
OVERLAY = os.path.join(PROJECT, 'overlay')
FONT_THAI = os.path.join(PROJECT, 'fonts', 'NotoSansThai.ttf')

VERSION = [1, 1, 2]
VERSION_TEXT = '.'.join(map(str, VERSION))
MIN_ENGINE = [1, 21, 90]

CORE_BP, CORE_RP = 'Succubi Server BP', 'Succubi Server RP'
GUNS_BP, GUNS_RP = 'Succubi Guns BP', 'Succubi Guns RP'
LINK_BP = 'Succubi Server Link BP'

# UUIDs: core + link keep the old ones (updates install over v1.0.x), the gun packs are new
UUID = {
    CORE_BP: ('344a2ed9-b5c1-4651-af5b-b888f88e66f0', 'e090b637-2b11-4c3e-b902-05cf051b3d81', 'e4ea6532-fef0-4f73-8973-96cdc74eb93a'),
    CORE_RP: ('5485ae30-e95c-4ba6-8cf9-c50b4fb71226', '047e96bb-f3dc-4edc-8139-0f5f1702625f'),
    GUNS_BP: ('7c3f5a1e-2d4b-4e8a-9b61-3f0c2a9d5e17', '1b8e4c2a-6f3d-4a5e-8c7b-9d0e1f2a3b4c', '5d6e7f80-9a1b-4c2d-8e3f-4a5b6c7d8e9f'),
    GUNS_RP: ('a2b3c4d5-e6f7-4819-8a2b-3c4d5e6f7081', 'b3c4d5e6-f708-4192-9a3b-4c5d6e7f8092'),
    LINK_BP: ('d79b13ff-4947-4314-924f-c5a0ea6fad16', 'cd8033c4-d087-4e53-bbaf-116127c1037d', '795a65c6-305a-44ee-b75c-1314f7d495c4'),
}


def strip_comments(s):
    out, i, n, in_str = [], 0, len(s), False
    while i < n:
        c = s[i]
        if in_str:
            out.append(c)
            if c == '\\':
                out.append(s[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if s.startswith('//', i):
            j = s.find('\n', i); i = n if j < 0 else j; continue
        if s.startswith('/*', i):
            j = s.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return ''.join(out)


def rjson(path):
    with open(path, encoding='utf-8-sig') as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except ValueError:
        return json.loads(re.sub(r',(\s*[}\]])', r'\1', strip_comments(raw)))


def wjson(path, data, indent=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write('\n')


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def walk_strings(node):
    """every string (keys and values) inside a JSON value"""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def read_lang(path):
    """[(key or None, raw line)] keeping comments and blank lines"""
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        for line in f.read().splitlines():
            s = line.strip()
            if not s or s.startswith('#') or '=' not in s:
                rows.append((None, line))
            else:
                rows.append((s.split('=', 1)[0].strip(), line))
    return rows


def write_lang(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(line for _, line in rows).rstrip('\n') + '\n')
