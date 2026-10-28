-- Called from the existing dialogue and speaker-name renderers.
-- The scenario tables and backlog entries always retain their original text.
function furigana_print(text, speaker)
    local parts = conf and conf.language == "ja" and conf.furigana == 1
        and furigana_readings[text]
    if not parts then
        e:tag{"print", data=text}
        return
    end
    if speaker then e:tag{"font", rubysize="13", rubyface=init.font01} end
    for _, part in ipairs(parts) do
        if type(part) == "table" then
            e:tag{"ruby", text=part[2]}
            e:tag{"print", data=part[1]}
            e:tag{"/ruby"}
        else
            e:tag{"print", data=part}
        end
    end
    if speaker then e:tag{"/font"} end
end

-- Use the game's normal button dispatch so a click cannot also advance dialogue.
function furigana_add_button(buttons)
    local row = conf.furigana == 1 and 64 or 0
    buttons.bt_furigana = {
        name="bt_furigana", file="mw/bt_furigana", id="mw.bt.dc.1.16",
        x=20, y=730, w=136, h=32, com="btn", flag="1",
        exec="furigana_toggle", clip="0,"..row..",136,32",
        clip_a="0,"..(row+32)..",136,32", clip_c="0,0,136,32"
    }
end

function furigana_button_state()
    if btn and btn.name == "adv" and btn.adv and btn.adv.p.bt_furigana then
        local info = getBtnInfo("bt_furigana")
        local row = conf.furigana == 1 and 64 or 0
        info.clip = "0,"..row..",136,32"
        info.clip_a = "0,"..(row+32)..",136,32"
        local hover = btn.cursor == "bt_furigana"
        e:tag{"lyprop", id=info.idx..".0", clip=hover and info.clip_a or info.clip}
    end
end

function furigana_toggle()
    if flg.ui or flg.dlg or flg.dlg2 or scr.select or flg.delay
        or flg.txclick or flg.waitflag or flg.btnstop then return end
    if not ast or not ast.text or not scr.ip or not ast.text[scr.ip.block] then return end
    autoskip_disable()
    conf.furigana = conf.furigana == 1 and 0 or 1
    se_ok()
    -- Redraw only the paragraphs already reached, without executing wait/voice tags.
    local text = getText()
    if text and not text.lane then
        if text.name then message_name(text.name.text or text.name.name) end
        chgmsg_adv()
        set_message_speed_tween(0, 0, 0)
        local count = scr.ip.textcount or #text
        for i=1, math.min(count, #text) do message_adv(text[i], "sys") end
        chgmsg_adv("close")
        mw_time(scr.mstime)
    end
    furigana_button_state()
    flip()
    autoskip_init()
    asyssave()
end
