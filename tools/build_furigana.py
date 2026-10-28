"""Build the Aikagi furigana mod from the user's original archive. No game is bundled."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

from fugashi import Tagger
from lupa.lua51 import LuaRuntime
from PIL import Image, ImageDraw, ImageFont

from pfs import Archive

ROOT = Path(__file__).resolve().parents[1]
KANJI = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]')
RUNS = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]+|[^\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]+')


def hiragana(text):
    return ''.join(chr(ord(c)-0x60) if '\u30a1' <= c <= '\u30f6' else c for c in text)


def align(surface, reading):
    """Keep okurigana outside ruby; jukujikun retain a whole-word reading."""
    runs = RUNS.findall(surface)
    pattern = ''.join('(.+?)' if KANJI.search(r) else re.escape(hiragana(r)) for r in runs)
    match = re.fullmatch(pattern, reading)
    if not match:
        return [[surface, reading]]
    groups = iter(match.groups())
    return [[r, next(groups)] if KANJI.search(r) else r for r in runs]


class Annotator:
    def __init__(self, overrides):
        self.tagger = Tagger()
        self.overrides = overrides
        # Multi-character names must be recognized before morphological tokenization.
        self.names = re.compile('(' + '|'.join(re.escape(n) for n in sorted(overrides, key=len, reverse=True)
                                             if len(n) > 1) + ')')
        self.unknown = set()

    @lru_cache(maxsize=None)
    def annotate(self, text):
        result = []
        for fragment in self.names.split(text):
            if not fragment:
                continue
            if fragment in self.overrides:
                result.extend(align(fragment, self.overrides[fragment]))
                continue
            cursor = 0
            for token in self.tagger(fragment):
                surface = token.surface
                start = fragment.index(surface, cursor)
                if start > cursor:
                    result.append(fragment[cursor:start])
                cursor = start + len(surface)
                if not KANJI.search(surface):
                    result.append(surface)
                    continue
                reading = self.overrides.get(surface) or hiragana(token.feature.kana or '')
                if not reading or reading == '*':
                    self.unknown.add(surface)
                    result.append(surface)
                else:
                    result.extend(align(surface, reading))
            if cursor < len(fragment):
                result.append(fragment[cursor:])
        # Merge plain fragments, reducing the amount of work in the game renderer.
        merged = []
        for part in result:
            if isinstance(part, str) and merged and isinstance(merged[-1], str):
                merged[-1] += part
            else:
                merged.append(part)
        assert ''.join(p if isinstance(p, str) else p[0] for p in merged) == text
        return merged


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def lookup_source(strings, annotator):
    lines = ['furigana_readings = {']
    annotations = 0
    for text in sorted(strings):
        parts = annotator.annotate(text)
        if not any(isinstance(p, list) for p in parts):
            continue
        values = []
        for part in parts:
            if isinstance(part, str):
                values.append(quote(part))
            else:
                values.append('{' + quote(part[0]) + ',' + quote(part[1]) + '}')
                annotations += 1
        lines.append('[' + quote(text) + ']={' + ','.join(values) + '},')
    lines.append('}\n')
    return '\n'.join(lines), annotations


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'Unsupported script version, expected one occurrence: {old!r}')
    return source.replace(old, new)


def sprite(destination, font_bytes):
    import io
    image = Image.new('RGBA', (136, 128))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(io.BytesIO(font_bytes), 15)
    for row, (label, color) in enumerate([
        ('Furigana: OFF', '#087fa8'), ('Furigana: OFF', '#13a4d2'),
        ('Furigana: ON', '#187b58'), ('Furigana: ON', '#259c71')
    ]):
        top = row * 32
        draw.rounded_rectangle((1, top+1, 134, top+30), radius=5, fill=color, outline='white', width=2)
        draw.text((68, top+16), label, font=font, anchor='mm', fill='white', stroke_width=0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)


def build(game, output):
    backup = game/'Aikagi_en.pfs.before-furigana'
    original = Archive(backup if backup.exists() else game/'Aikagi_en.pfs')
    if hashlib.sha256(original.path.read_bytes()).hexdigest() != '45a744e4b22e4248b8af545340dfccd6cca0275dbef9b6c3279a08ef28016b24':
        raise ValueError('Unsupported original archive. Restore the original Steam game files before building.')
    lua = LuaRuntime(unpack_returned_tuples=True)
    strings = set()
    blocks = 0
    for entry in original.entries:
        if not entry.name.startswith('script\\') or not entry.name.endswith('.ast'):
            continue
        lua.execute(original.read(entry).decode('utf-8-sig'))
        scenario = lua.globals().ast
        if scenario.text is None:
            continue
        for _, block in scenario.text.items():
            if not block.ja:
                continue
            blocks += 1
            japanese = block.ja
            if japanese.name and japanese.name.name:
                strings.add(japanese.name.name)
            for key, paragraph in japanese.items():
                if isinstance(key, int):
                    for _, part in paragraph.items():
                        if isinstance(part, str):
                            strings.add(part)
    annotator = Annotator(json.loads((ROOT/'mod/readings.json').read_text(encoding='utf-8')))
    lookup, count = lookup_source(strings, annotator)
    message = original.read('system\\msg\\message.lua').decode('utf-8-sig').replace('\r\n', '\n')
    message = replace_once(message, 'tag{"print", data=(text)}', 'furigana_print(text, true)')
    message = replace_once(message, 'e:tag{"print", data=(t)}', 'furigana_print(t)')
    message += '\n' + (ROOT/'mod/furigana.lua').read_text(encoding='utf-8') + '\n' + lookup
    extend = original.read('system\\extend\\adv_mw.lua').decode('utf-8-sig').replace('\r\n', '\n')
    extend = replace_once(extend, 'csvbtn3("adv", id, v)',
                          'furigana_add_button(v)\n\t\tcsvbtn3("adv", id, v)\n\t\tfurigana_button_state()')
    replacements = {'system\\msg\\message.lua': message.encode(),
                    'system\\extend\\adv_mw.lua': extend.encode()}
    for source in replacements.values():
        lua.compile(source.decode())
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output/'Aikagi_en.pfs'
    if archive_path.resolve() == original.path.resolve():
        raise ValueError('Build output must be separate from the source game')
    original.rebuild(archive_path, replacements)
    rebuilt = Archive(archive_path)
    for entry in original.entries:
        assert rebuilt.read(entry.name) == replacements.get(entry.name, original.read(entry))
    fonts = Archive(game/'Aikagi_en.pfs.000')
    font = fonts.read('font\\GenJyuuGothic-Monospace-Bold.ttf')
    for language in ('uija', 'uien'):
        sprite(output/'pc'/language/'mw/bt_furigana.png', font)
    report = {'source_sha256': hashlib.sha256(original.path.read_bytes()).hexdigest(),
              'patch_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
              'japanese_blocks': blocks, 'unique_strings': len(strings),
              'ruby_spans': count, 'unknown_tokens': sorted(annotator.unknown),
              'changed_entries': list(replacements), 'verified_archive_entries': len(original.entries)}
    (output/'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for name in ('Install-Furigana.ps1', 'Install-Furigana.cmd', 'Restore-Furigana.cmd'):
        contents = (ROOT/'mod'/name).read_text().replace('\n', '\r\n')
        (output/name).write_bytes(contents.encode('ascii'))
    (output/'README.txt').write_bytes((ROOT/'mod/README-PATCH.txt').read_bytes())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/furigana')
    args = parser.parse_args()
    build(args.game, args.output)
