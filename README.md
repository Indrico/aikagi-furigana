# Aikagi Furigana

A **Furigana: OFF / ON** toggle for Japanese text in Aikagi (Artemis Engine).
The button appears at the bottom left of the dialogue box. The game saves your
preference in its configuration; the default is OFF. Furigana is added when
dialogue, speaker names, and dialogue text in the backlog are rendered.

## Windows installation

1. Close the game and install **Python 3.12, 64-bit** from [python.org](https://www.python.org/downloads/windows/).
2. Download the ZIP from [GitHub Releases](https://github.com/Indrico/aikagi-furigana/releases).
3. Extract the `aikagi-furigana` folder into the folder containing `Aikagi_en.exe`.
   You can also place its entire contents directly in the game folder.
4. Run `Install-Furigana.cmd`. The first installation requires an internet
   connection for Python dependencies and may take several minutes.
5. Launch the game through Steam, select **Japanese**, and try the toggle while
   dialogue is displayed.

The installer detects the game folder from its own location, including paths
containing spaces. You do not need to edit a `D:\SteamLibrary` path or change
PowerShell's working directory. You can also specify another location:

```powershell
.\Install-Furigana.cmd -GameDirectory "D:\SteamLibrary\steamapps\common\Aikagi"
```

The release contains source code and an installer. The patch is built
**locally** from your own copy of the game. Game executables, archives, fonts,
and scripts are not included in the repository or ZIP. The Python virtual
environment is stored in `.venv`, and build output is stored in `.build/furigana`.

## Restore the original game

Close the game, then run `Restore-Furigana.cmd`. The original archive is backed
up as `Aikagi_en.pfs.before-furigana`. Save data is not modified. Keep the
`.build` folder until you have restored the original archive. The installer
rejects unsupported archive versions and mismatched backups.

If an earlier patch is already installed, the builder can use its original
backup. If the original archive has been overwritten and no backup is
available, restore the game files through Steam before building the patch.

## Coverage and status

- The reference build covers **3,505 Japanese dialogue blocks** and **10,692 ruby spans**.
- Okurigana stays separate. Compounds such as 部屋（へや） and 汐栞（しおり）
  use grouped ruby. Plain kana does not receive additional annotations.
- Readings are generated with MeCab/UniDic. Name and word overrides are stored
  in `mod/readings.json`. Ambiguous words may still receive incorrect readings.
- Supported original archive SHA-256:
  `45a744e4b22e4248b8af545340dfccd6cca0275dbef9b6c3279a08ef28016b24`.
- Only two Lua entries are replaced. All 117 repacked entries are verified;
  the executable and `.pfs.000` through `.pfs.002` archives are not replaced.
- The installer directory fix has been confirmed by the user. Lua, archive
  integrity, and PowerShell installer tests have passed on Linux.
- **Furigana appearance and save/load behavior in the Steam game have not been
  verified by the developer.** Further in-game testing is still needed.

## Manual build

```sh
python -m venv .venv
# On Windows, use .venv\Scripts\python.exe instead of .venv/bin/python.
.venv/bin/python -m pip install -r tools/requirements.txt
.venv/bin/python tools/build_furigana.py --game /path/to/Aikagi --output .build/furigana
.venv/bin/python tools/manage_patch.py install --game /path/to/Aikagi --package .build/furigana
```

Use the `restore` action instead of `install` to restore the original archive.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Integration tests require your own copy of the game. Set
`AIKAGI_GAME_DIRECTORY` and `AIKAGI_PATCH_DIRECTORY` to the relevant locations.
These tests are skipped when the required files are unavailable. Installer
tests require `pwsh`.

## How it works and references

The builder reads the PF8 archive, generates a Japanese reading table, and adds
Lua helpers to the renderer and the game's existing button dispatcher.
Scenario data and backlog entries retain their original text. Repacking
updates offsets, sizes, the index SHA-1, and payload encryption.

The initial investigation used [REA](https://github.com/morluto/rea) for PE metadata.
The PF8 format was checked against [GARbro's implementation](https://github.com/morkt/GARbro/blob/master/ArcFormats/Artemis/ArcPFS.cs),
and ruby syntax was checked against an [open Artemis implementation](https://github.com/Alphaly2K/art3m1s-core).
