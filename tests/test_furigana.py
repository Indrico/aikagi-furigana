"""Validate the patch in the same Lua 5.1 language version as Artemis."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get('AIKAGI_GAME_DIRECTORY', ROOT))
PACKAGE = Path(os.environ.get('AIKAGI_PATCH_DIRECTORY', ROOT/'dist/furigana'))
sys.path.insert(0, str(ROOT/'tools'))
from build_furigana import Annotator
from manage_patch import manage
from pfs import Archive
from lupa.lua51 import LuaRuntime


class FuriganaTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            emitted = {}
            e = { tag=function(self, value) table.insert(emitted, value) end }
            conf = {language="ja", furigana=1}
            flg = {}
            scr = {ip={block=1, textcount=1}}
            ast = {text={{}}}
            function tag(p) e:tag(p) end
            function getAread() return false end
            function autoskip_disable() end
            function autoskip_init() end
            function se_ok() end
            function asyssave() saved = conf.furigana end
            function flip() end
            function chgmsg_adv() end
            function set_message_speed_tween() end
            function mw_time() end
            function getText() return {{"一段目"}, {"未表示"}} end
            function message_adv(t) table.insert(emitted, {"render", text=t[1]}) end
        ''')
        self.lua.execute((ROOT/'mod/furigana.lua').read_text(encoding='utf-8'))
        self.lua.execute('furigana_readings = {["部屋を見る"]={{"部屋","へや"},"を",{"見","み"},"る"}}')

    def events(self):
        return [dict(v.items()) for _, v in self.lua.globals().emitted.items()]

    def test_off_is_original_single_print(self):
        self.lua.execute('conf.furigana=0; furigana_print("部屋を見る")')
        self.assertEqual(self.events(), [{1: 'print', 'data': '部屋を見る'}])

    def test_on_ruby_balanced_and_text_preserved(self):
        self.lua.execute('furigana_print("部屋を見る")')
        events = self.events()
        self.assertEqual([e[1] for e in events],
                         ['ruby', 'print', '/ruby', 'print', 'ruby', 'print', '/ruby', 'print'])
        self.assertEqual(''.join(e.get('data', '') for e in events), '部屋を見る')
        self.assertEqual([e['text'] for e in events if e[1] == 'ruby'], ['へや', 'み'])

    def test_english_and_unmapped_text_unchanged(self):
        self.lua.execute('conf.language="en"; furigana_print("部屋を見る"); furigana_print("Hello")')
        self.assertEqual([e[1] for e in self.events()], ['print', 'print'])

    def test_toggle_redraws_only_reached_paragraph_and_saves(self):
        self.lua.execute('furigana_toggle()')
        self.assertEqual(self.lua.globals().conf.furigana, 0)
        self.assertEqual(self.lua.globals().saved, 0)
        self.assertEqual([e['text'] for e in self.events() if e[1]=='render'], ['一段目'])
        self.assertFalse(any(e[1] in ('sound', '@', 'wait') for e in self.events()))

    def test_toggle_ignored_during_transitions_and_menus(self):
        for flag in ('ui', 'dlg', 'dlg2', 'delay', 'txclick', 'waitflag', 'btnstop'):
            self.lua.execute(f'flg={{ {flag}=true }}; furigana_toggle()')
            self.assertEqual(self.lua.globals().conf.furigana, 1)
        self.assertEqual(self.events(), [])

    def test_readings_preserve_spaces_and_okurigana(self):
        annotator = Annotator(json.loads((ROOT/'mod/readings.json').read_text(encoding='utf-8')))
        parts = annotator.annotate(' 汐栞の部屋を見る。 ')
        self.assertIn(['汐栞', 'しおり'], parts)
        self.assertIn(['見', 'み'], parts)
        self.assertEqual(''.join(p if isinstance(p,str) else p[0] for p in parts), ' 汐栞の部屋を見る。 ')

    @unittest.skipUnless((GAME/'Aikagi_en.pfs').exists(), 'Requires a local copy of Aikagi')
    def test_rebuild_keeps_all_unmodified_payloads(self):
        backup = GAME/'Aikagi_en.pfs.before-furigana'
        source = Archive(backup if backup.exists() else GAME/'Aikagi_en.pfs')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'roundtrip.pfs'
            source.rebuild(target, {})
            # Rebuilding in original payload order must be byte-for-byte identical.
            self.assertEqual(target.read_bytes(), source.path.read_bytes())

    @unittest.skipUnless((PACKAGE/'Aikagi_en.pfs').exists(), 'Requires a locally built patch')
    def test_actual_patched_renderer_preserves_every_reading(self):
        archive = Archive(PACKAGE/'Aikagi_en.pfs')
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            e = {tag=function(self, p) table.insert(emitted, p) end}
            tags = {}
            conf = {language="ja", furigana=1}
            flg = {}
            function getAread() return false end
            function tag(p) e:tag(p) end
        ''')
        lua.execute(archive.read('system\\msg\\message.lua').decode())
        verified = lua.execute('''
            local count = 0
            for text, _ in pairs(furigana_readings) do
                emitted = {}
                message_adv({text})
                local depth, printed = 0, ""
                for _, p in ipairs(emitted) do
                    if p[1] == "ruby" then
                        assert(depth == 0 and #p.text > 0)
                        depth = depth + 1
                    elseif p[1] == "/ruby" then
                        depth = depth - 1
                        assert(depth == 0)
                    elseif p[1] == "print" then printed = printed .. p.data end
                end
                assert(depth == 0 and printed == text)
                conf.furigana = 0
                emitted = {}
                message_adv({text})
                assert(#emitted == 1 and emitted[1].data == text)
                conf.furigana = 1
                count = count + 1
            end
            return count
        ''')
        self.assertGreater(verified, 3000)

    def test_speaker_ruby_has_its_own_font_size(self):
        self.lua.execute('init={font01="font.ttf"}; furigana_print("部屋を見る", true)')
        self.assertEqual(self.events()[0][1], 'font')
        self.assertEqual(self.events()[0]['rubysize'], '13')
        self.assertEqual(self.events()[-1][1], '/font')

    def test_button_label_and_hover_follow_preference(self):
        self.lua.execute('''
            local buttons = {}
            furigana_add_button(buttons)
            btn = {name="adv", adv={p=buttons}, cursor="bt_furigana"}
            function getBtnInfo(n) local p=btn.adv.p[n]; p.idx="1.80."..p.id; return p end
            furigana_button_state()
        ''')
        self.assertEqual(self.events()[-1]['clip'], '0,96,136,32')
        self.lua.execute('conf.furigana=0; furigana_button_state()')
        self.assertEqual(self.events()[-1]['clip'], '0,32,136,32')

    @unittest.skipUnless((GAME/'Aikagi_en.pfs').exists() and (PACKAGE/'Aikagi_en.pfs').exists(),
                         'Requires a local copy of Aikagi and a built patch')
    def test_installer_backups_and_restores_exact_original(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            backup = GAME/'Aikagi_en.pfs.before-furigana'
            shutil.copy2(backup if backup.exists() else GAME/'Aikagi_en.pfs', game/'Aikagi_en.pfs')
            original = (game/'Aikagi_en.pfs').read_bytes()
            manage(game, PACKAGE)
            self.assertEqual((game/'Aikagi_en.pfs.before-furigana').read_bytes(), original)
            self.assertNotEqual((game/'Aikagi_en.pfs').read_bytes(), original)
            manage(game, PACKAGE, restore=True)
            self.assertEqual((game/'Aikagi_en.pfs').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
