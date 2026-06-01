"""Build a Linux-friendly source package for the server deployment."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "build" / "meeting-server-linux.zip"


def iter_server_files():
    package_root = ROOT / "meeting_room_system"
    keep_roots = [
        package_root / "server",
    ]
    keep_files = [
        package_root / "__init__.py",
        package_root / "config.py",
    ]
    for file_path in keep_files:
        yield file_path
    for root in keep_roots:
        for file_path in root.rglob("*"):
            if file_path.is_file() and "__pycache__" not in file_path.parts:
                yield file_path


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for file_path in iter_server_files():
            archive.write(file_path, file_path.relative_to(ROOT).as_posix())
    print(OUTPUT)


if __name__ == "__main__":
    main()
