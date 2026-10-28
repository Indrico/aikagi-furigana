FURIGANA TOGGLE - AIKAGI / ARTEMIS

Lua and archive integrity checks have passed (11 tests).
In-game appearance has not been verified: the test environment does not have
the Steam client required by the original executable.

LOCAL BUILD OUTPUT
This package is generated locally from your own game files. It is not included
in the public release. For the public source release, follow README.md and use
the installer in the project's main folder.

INSTALLATION
1. Close the game.
2. Keep the generated package separate from the game's original archive.
   Include the button images in pc and the build-report.json file.
3. From this package's folder, open PowerShell and run:
     .\Install-Furigana.ps1 -GameDirectory "C:\path\to\Aikagi"
   If this package is directly inside the game folder, Install-Furigana.cmd
   can detect the game directory automatically.
4. Launch the game through Steam, select Japanese, and start or resume a story.
5. Click "Furigana: OFF / ON" at the bottom left of the dialogue box.

RESTORE
Close the game and run:
  .\Install-Furigana.ps1 -GameDirectory "C:\path\to\Aikagi" -Restore
The original archive is saved as Aikagi_en.pfs.before-furigana.
Save data is not modified. Unsupported archive versions are rejected.
Automatic directory detection uses the installer's location, not PowerShell's
working directory. The installer was tested with PowerShell on Linux; it has
not been run on Windows by the developer.

NOTES
Furigana follows words and okurigana; some compounds use grouped ruby.
Character names have reading overrides. Automatic readings may still be wrong.
Check button placement, line spacing, backlog rendering, and save/load in-game.
The default is OFF. Your preference is saved through the game's configuration.
