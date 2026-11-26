"""Apply the optional expanded-map overlay from the installed release."""
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
from zipfile import ZipFile

from importer import child, digest


def prepare(app, data, profile):
    root = data / "gamedata"
    imported = json.loads((root / "import-receipt.json").read_text(encoding="utf-8-sig"))
    if imported.get("map_size", imported.get("maps")) != "2x":
        return
    if imported.get("manifest_sha256") == profile["content_manifest_sha256"]:
        return
    marker = root / ".esencia-expanded-maps"
    expected = profile["expanded_maps_sha256"]
    if marker.is_file() and marker.read_text(encoding="ascii") == expected:
        return

    package = app / "expanded-maps.zip"
    if digest(package) != expected:
        raise ValueError("Expanded-map package failed verification")
    destination = child(root, "mods/pak3us1")
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(package) as archive, tempfile.TemporaryDirectory(dir=destination) as stage:
        stage = Path(stage)
        manifest = json.loads(archive.read("manifest.json"))
        for name, wanted in manifest.items():
            if not re.fullmatch(r"[0-9]{5}\.bin", name):
                raise ValueError("Unexpected expanded-map filename")
            path = child(destination, name)
            if path.is_file():
                if digest(path) == wanted:
                    continue
                raise ValueError("Existing expanded map differs from the verified installation: " + name)
            raw = archive.read(name)
            if hashlib.sha256(raw).hexdigest() != wanted:
                raise ValueError("Expanded-map file failed verification: " + name)
            (stage / name).write_bytes(raw)
        for path in stage.iterdir():
            # A simultaneous launch may already have installed the same verified map.
            target = child(destination, path.name)
            try:
                os.link(path, target)
            except FileExistsError:
                if digest(target) != manifest[path.name]:
                    raise
    marker.write_text(expected, encoding="ascii")

