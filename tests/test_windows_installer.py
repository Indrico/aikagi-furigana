"""Exercise the actual PowerShell installer in both supported directory layouts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PWSH = shutil.which('pwsh') or str(ROOT/'.tools/pwsh/pwsh')
ORIGINAL = b'original game archive'
PATCH = b'patched game archive'


@unittest.skipUnless(Path(PWSH).is_file(), 'PowerShell runtime is unavailable')
class WindowsInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.game = self.root/'Game [JP] & spaces'
        self.game.mkdir()
        (self.game/'Aikagi_en.exe').write_bytes(b'MZ')
        (self.game/'Aikagi_en.pfs').write_bytes(ORIGINAL)
        self.cwd = self.root/'unrelated working directory'
        self.cwd.mkdir()

    def package(self, directory, legacy=False):
        directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/'mod/Install-Furigana.ps1', directory/'Install-Furigana.ps1')
        archive = directory/'Aikagi_en.pfs' if legacy else directory/'payload/Aikagi_en.pfs'
        archive.parent.mkdir(exist_ok=True)
        archive.write_bytes(PATCH)
        report = {'source_sha256': hashlib.sha256(ORIGINAL).hexdigest(),
                  'patch_sha256': hashlib.sha256(PATCH).hexdigest()}
        (directory/'build-report.json').write_text(json.dumps(report))
        asset = directory/'pc/uija/mw/bt_furigana.png'
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b'button image')
        return directory

    def run_installer(self, package, *arguments, success=True):
        result = subprocess.run([PWSH, '-NoLogo', '-NoProfile', '-File',
                                 str(package/'Install-Furigana.ps1'), *arguments],
                                cwd=self.cwd, capture_output=True, text=True, timeout=45)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result.stdout + result.stderr

    def check_install_and_restore(self, package, *arguments):
        self.run_installer(package, *arguments)
        self.assertEqual((self.game/'Aikagi_en.pfs').read_bytes(), PATCH)
        self.assertEqual((self.game/'Aikagi_en.pfs.before-furigana').read_bytes(), ORIGINAL)
        self.run_installer(package, *arguments)
        self.assertEqual((self.game/'Aikagi_en.pfs.before-furigana').read_bytes(), ORIGINAL)
        self.run_installer(package, *arguments, '-Restore')
        self.assertEqual((self.game/'Aikagi_en.pfs').read_bytes(), ORIGINAL)

    def test_same_directory_and_unrelated_working_directory(self):
        self.check_install_and_restore(self.package(self.game))

    def test_subdirectory_and_asset_repair(self):
        package = self.package(self.game/'furigana_patch')
        self.check_install_and_restore(package)
        asset = self.game/'pc/uija/mw/bt_furigana.png'
        asset.unlink()
        self.run_installer(package)
        self.assertEqual(asset.read_bytes(), b'button image')

    def test_explicit_game_directory(self):
        package = self.package(self.root/'package elsewhere')
        self.check_install_and_restore(package, '-GameDirectory', str(self.game))

    def test_missing_directory_has_actionable_error(self):
        package = self.package(self.root/'package elsewhere')
        output = self.run_installer(package, success=False)
        self.assertIn('Folder game tidak ditemukan', output)
        self.assertNotIn('Resolve-Path', output)

    def test_unknown_game_version_does_not_create_backup(self):
        package = self.package(self.game)
        (self.game/'Aikagi_en.pfs').write_bytes(b'other version')
        self.run_installer(package, success=False)
        self.assertEqual((self.game/'Aikagi_en.pfs').read_bytes(), b'other version')
        self.assertFalse((self.game/'Aikagi_en.pfs.before-furigana').exists())

    def test_legacy_same_directory_preserves_missing_backup(self):
        package = self.package(self.game, legacy=True)
        output = self.run_installer(package)
        self.assertIn('Patch already installed', output)
        self.assertIn('backup asli tidak ditemukan', output)
        self.assertFalse((self.game/'Aikagi_en.pfs.before-furigana').exists())


if __name__ == '__main__':
    unittest.main()
