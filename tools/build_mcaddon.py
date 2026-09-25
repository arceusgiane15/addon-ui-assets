"""Packs addon/ into dist/Succubi_Server_v<version>.mcaddon (the version comes from Succubi Server BP's manifest).
Python's zipfile marks non-ASCII names as UTF-8 (one Guns RP folder is "throabçes"), like the original file."""
import json
import os
import zipfile

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ADDON = os.path.join(REPO, "addon")
PACKS = ["Succubi Guns BP", "Succubi Guns RP", "Succubi Server BP", "Succubi Server Link BP", "Succubi Server RP"]


def main():
    with open(os.path.join(ADDON, "Succubi Server BP", "manifest.json"), encoding="utf-8") as f:
        version = ".".join(map(str, json.load(f)["header"]["version"]))
    out = os.path.join(REPO, "dist", f"Succubi_Server_v{version}.mcaddon")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for pack in PACKS:
            for root, dirs, files in os.walk(os.path.join(ADDON, pack)):
                dirs.sort()
                for name in sorted(files):
                    path = os.path.join(root, name)
                    z.write(path, os.path.relpath(path, ADDON).replace(os.sep, "/"))
                    count += 1
    print(f"{os.path.relpath(out, REPO)}: {count} files, {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
