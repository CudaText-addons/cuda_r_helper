import sys
import datetime
import os
from time import sleep
from subprocess import Popen, PIPE, STDOUT
from threading import Thread, Lock

import cudatext_keys as keys
import cudatext_cmd as cmds
from cudatext import *

fn_icon = os.path.join(os.path.dirname(__file__), 'r_console.png')
fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_r_helper.ini')
MAX_BUFFER = 100*1000
IS_WIN = os.name=='nt'
IS_MAC = sys.platform=='darwin'
READSIZE = 4*1024
HOMEDIR = os.path.expanduser('~')
INPUT_H = 26

def bool_to_str(v):
    return '1' if v else '0'

def str_to_bool(s):
    return s=='1'

class Command:
    title = 'R Console'
    h_dlg = None

    def __init__(self):

        try:
            self.font_size = int(ini_read(fn_config, 'op', 'font_size', '9'))
        except:
            pass

        try:
            self.max_history = int(ini_read(fn_config, 'op', 'max_history', '10'))
        except:
            pass

        self.dark_colors = str_to_bool(ini_read(fn_config, 'op', 'dark_colors', '1'))
        
        self.h_menu = menu_proc(0, MENU_CREATE)

        self.load_history()

        #for-loop don't work here
        self.menu_calls = []
        self.menu_calls += [ lambda: self.run_cmd_n(0) ]
        self.menu_calls += [ lambda: self.run_cmd_n(1) ]
        self.menu_calls += [ lambda: self.run_cmd_n(2) ]
        self.menu_calls += [ lambda: self.run_cmd_n(3) ]
        self.menu_calls += [ lambda: self.run_cmd_n(4) ]
        self.menu_calls += [ lambda: self.run_cmd_n(5) ]
        self.menu_calls += [ lambda: self.run_cmd_n(6) ]
        self.menu_calls += [ lambda: self.run_cmd_n(7) ]
        self.menu_calls += [ lambda: self.run_cmd_n(8) ]
        self.menu_calls += [ lambda: self.run_cmd_n(9) ]
        self.menu_calls += [ lambda: self.run_cmd_n(10) ]
        self.menu_calls += [ lambda: self.run_cmd_n(11) ]
        self.menu_calls += [ lambda: self.run_cmd_n(12) ]
        self.menu_calls += [ lambda: self.run_cmd_n(13) ]
        self.menu_calls += [ lambda: self.run_cmd_n(14) ]
        self.menu_calls += [ lambda: self.run_cmd_n(15) ]
        self.menu_calls += [ lambda: self.run_cmd_n(16) ]
        self.menu_calls += [ lambda: self.run_cmd_n(17) ]
        self.menu_calls += [ lambda: self.run_cmd_n(18) ]
        self.menu_calls += [ lambda: self.run_cmd_n(19) ]
        self.menu_calls += [ lambda: self.run_cmd_n(20) ]
        self.menu_calls += [ lambda: self.run_cmd_n(21) ]


    def upd_history_combo(self):

        self.input.set_prop(PROP_COMBO_ITEMS, '\n'.join(self.history))


    def load_history(self):

        self.history = []
        for i in range(self.max_history):
            s = ini_read(fn_config, 'history', str(i), '')
            if s:
                self.history += [s]


    def save_history(self):

        ini_proc(INI_DELETE_SECTION, fn_config, 'history')
        for (i, s) in enumerate(self.history):
            ini_write(fn_config, 'history', str(i), s)


    def open_init(self):

        self.h_dlg = self.init_form()
        h_embed = self.h_dlg

        app_proc(PROC_BOTTOMPANEL_ADD_DIALOG, (self.title, h_embed, fn_icon))


    def open_console(self):

        #dont init form twice!
        if not self.h_dlg:
            self.open_init()

        dlg_proc(self.h_dlg, DLG_CTL_FOCUS, name='input')

        app_proc(PROC_BOTTOMPANEL_ACTIVATE, (self.title, True)) #True - set focus


    def init_form(self):

        colors = app_proc(PROC_THEME_UI_DICT_GET,'')
        color_btn_back = colors['ButtonBgPassive']['color']
        color_btn_font = colors['ButtonFont']['color']

        color_memo_back = 0x0 if self.dark_colors else color_btn_back
        color_memo_font = 0xC0C0C0 if self.dark_colors else color_btn_font

        cur_font_size = self.font_size

        h = dlg_proc(0, DLG_CREATE)
        dlg_proc(h, DLG_PROP_SET, prop={
            'border': False,
            'keypreview': True,
            'on_key_down': self.form_key_down,
            #'on_show': self.form_show,
            #'on_hide': self.form_hide,
            'color': color_btn_back,
            })

        n = dlg_proc(h, DLG_CTL_ADD, 'button_ex')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'break',
            'a_l': None,
            'a_t': None,
            'a_r': ('', ']'),
            'a_b': ('', ']'),
            'w': 90,
            'h': INPUT_H,
            'cap': 'Break',
            'hint': 'Hotkey: Break',
            'on_change': self.button_break_click,
            })

        n = dlg_proc(h, DLG_CTL_ADD, 'editor_combo')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'input',
            'border': True,
            'h': INPUT_H,
            'a_l': ('', '['),
            'a_r': ('break', '['),
            'a_t': ('break', '-'),
            'font_size': cur_font_size,
            'texthint': 'Enter command here',
            })
        self.input = Editor(dlg_proc(h, DLG_CTL_HANDLE, index=n))

        n = dlg_proc(h, DLG_CTL_ADD, 'editor')
        dlg_proc(h, DLG_CTL_PROP_SET, index=n, prop={
            'name': 'memo',
            'a_t': ('', '['),
            'a_l': ('', '['),
            'a_r': ('', ']'),
            'a_b': ('break', '['),
            'font_size': cur_font_size,
            })
        self.memo = Editor(dlg_proc(h, DLG_CTL_HANDLE, index=n))

        self.memo.set_prop(PROP_RO, True)
        self.memo.set_prop(PROP_CARET_VIRTUAL, False)
        self.memo.set_prop(PROP_GUTTER_ALL, False)
        self.memo.set_prop(PROP_UNPRINTED_SHOW, False)
        self.memo.set_prop(PROP_MARGIN, 2000)
        self.memo.set_prop(PROP_MARGIN_STRING, '')
        self.memo.set_prop(PROP_LAST_LINE_ON_TOP, False)
        self.memo.set_prop(PROP_HILITE_CUR_LINE, False)
        self.memo.set_prop(PROP_HILITE_CUR_COL, False)
        self.memo.set_prop(PROP_MODERN_SCROLLBAR, True)
        self.memo.set_prop(PROP_MINIMAP, False)
        self.memo.set_prop(PROP_MICROMAP, False)
        self.memo.set_prop(PROP_COLOR, (COLOR_ID_TextBg, color_memo_back))
        self.memo.set_prop(PROP_COLOR, (COLOR_ID_TextFont, color_memo_font))

        self.input.set_prop(PROP_ONE_LINE, True)
        self.input.set_prop(PROP_GUTTER_ALL, True)
        self.input.set_prop(PROP_GUTTER_NUM, False)
        self.input.set_prop(PROP_GUTTER_FOLD, False)
        self.input.set_prop(PROP_GUTTER_BM, False)
        self.input.set_prop(PROP_GUTTER_STATES, False)
        self.input.set_prop(PROP_UNPRINTED_SHOW, False)
        self.input.set_prop(PROP_MARGIN, 2000)
        self.input.set_prop(PROP_MARGIN_STRING, '')
        self.input.set_prop(PROP_HILITE_CUR_LINE, False)
        self.input.set_prop(PROP_HILITE_CUR_COL, False)

        self.upd_history_combo()

        dlg_proc(h, DLG_SCALE)
        return h


    def config(self):

        ini_write(fn_config, 'op', 'max_history', str(self.max_history))
        ini_write(fn_config, 'op', 'font_size', str(self.font_size))

        file_open(fn_config)


    def form_key_down(self, id_dlg, id_ctl, data='', info=''):

        #Enter
        if (id_ctl==keys.VK_ENTER) and (data==''):
            text = self.input.get_text_line(0)
            self.input.set_text_all('')
            self.input.set_caret(0, 0)
            self.run_cmd(text)
            return False

        #Up/Down: scroll memo
        if (id_ctl==keys.VK_UP) and (data==''):
            self.memo.cmd(cmds.cCommand_ScrollLineUp)
            return False

        if (id_ctl==keys.VK_DOWN) and (data==''):
            self.memo.cmd(cmds.cCommand_ScrollLineDown)
            return False

        #PageUp/PageDown: scroll memo
        if (id_ctl==keys.VK_PAGEUP) and (data==''):
            self.memo.cmd(cmds.cCommand_ScrollPageUp)
            return False

        if (id_ctl==keys.VK_PAGEDOWN) and (data==''):
            self.memo.cmd(cmds.cCommand_ScrollPageDown)
            return False

        #Ctrl+Down: history menu
        if (id_ctl==keys.VK_DOWN) and (data=='c'):
            self.show_history()
            return False

        #Escape: go to editor
        if (id_ctl==keys.VK_ESCAPE) and (data==''):
            # Stops the timer
            timer_proc(TIMER_STOP, self.timer_update, 0)
            ed.focus()
            ed.cmd(cmds.cmd_ToggleBottomPanel)
            return False

        #Break (cannot react to Ctrl+Break)
        if (id_ctl==keys.VK_PAUSE):
            self.button_break_click(0, 0)
            return False


    def show_history(self):

        menu_proc(self.h_menu, MENU_CLEAR)
        for (index, item) in enumerate(self.history):
            menu_proc(self.h_menu, MENU_ADD,
                index=0,
                caption=item,
                command=self.menu_calls[index],
                )

        prop = dlg_proc(self.h_dlg, DLG_CTL_PROP_GET, name='input')
        x, y = prop['x'], prop['y']
        x, y = dlg_proc(self.h_dlg, DLG_COORD_LOCAL_TO_SCREEN, index=x, index2=y)
        menu_proc(self.h_menu, MENU_SHOW, command=(x, y))


    def run_cmd(self, text):

        if text=='clear':
            self.memo.set_prop(PROP_RO, False)
            self.memo.set_text_all('')
            self.memo.set_prop(PROP_RO, True)
            return

        while len(self.history) >= self.max_history:
            del self.history[0]

        try:
            n = self.history.index(text)
            del self.history[n]
        except:
            pass

        self.history += [text]
        self.upd_history_combo()
        self.input.set_text_all('')
        
        self.memo.set_prop(PROP_RO, False)
        self.memo.set_text_line(-1, '>>> '+text)
        self.memo.set_prop(PROP_SCROLL_VERT, 0x7FFFFFFF)
        self.memo.set_prop(PROP_RO, True)

        self.exec(text)


    def exec(self, s):
        
        pass


    def run_cmd_n(self, n):

        if n<len(self.history):
            s = self.history[n]
            self.input.set_text_all(s)
            self.input.set_caret(len(s), 0)


    def update_output(self, s):

        self.memo.set_prop(PROP_RO, False)
        self.memo.set_text_all(s)
        self.memo.set_prop(PROP_RO, True)

        self.memo.cmd(cmds.cCommand_GotoTextEnd)
        self.memo.set_prop(PROP_LINE_TOP, self.memo.get_line_count()-3)


    def on_exit(self, ed_self):

        self.save_history()


    def button_break_click(self, id_dlg, id_ctl, data='', info=''):

        pass
