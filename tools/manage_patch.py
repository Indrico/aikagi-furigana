"""Install or restore this local patch, preserving the exact original main archive."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manage(game, package, restore=False):
    game, package = game.resolve(), package.resolve()
    archive = game/'Aikagi_en.pfs'
    backup = game/'Aikagi_en.pfs.before-furigana'
    report = json.loads((package/'build-report.json').read_text())
    if restore:
        if not backup.exists() or digest(backup) != report['source_sha256']:
            raise ValueError('The verified original backup is missing')
        if digest(archive) not in (report['source_sha256'], report['patch_sha256']):
            raise ValueError('Archive changed since installation; refusing to overwrite it')
        shutil.copy2(backup, archive)
        print('Original archive restored. Save data was preserved.')
        return
    if digest(package/'Aikagi_en.pfs') != report['patch_sha256']:
        raise ValueError('Patch checksum mismatch')
    current = digest(archive)
    if current == report['patch_sha256']:
        print('Furigana patch is already installed.')
        return
    if current != report['source_sha256']:
        raise ValueError('Game archive differs from the supported original version')
    if backup.exists() and digest(backup) != report['source_sha256']:
        raise ValueError('A different backup already exists')
    assets = [p for p in (package/'pc').rglob('*.png')]
    for source in assets:
        target = game/source.relative_to(package)
        if target.exists() and digest(target) != digest(source):
            raise ValueError(f'Asset already exists with different contents: {target}')
    if not backup.exists():
        shutil.copy2(archive, backup)
    for source in assets:
        target = game/source.relative_to(package)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    temporary = game/'Aikagi_en.pfs.furigana-installing'
    shutil.copy2(package/'Aikagi_en.pfs', temporary)
    temporary.replace(archive)
    print(f'Furigana patch installed. Original: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'restore'])
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1]/'dist/furigana')
    args = parser.parse_args()
    manage(args.game, args.package, args.action == 'restore')
