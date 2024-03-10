import threading

from mss import mss
from mss.tools import to_png
import ttkbootstrap as tb
from pynput import keyboard
import pywinctl

from foxhole_stockpiles.models.keypress import KeyPress
from foxhole_stockpiles.config.settings import Settings


class App(tb.Window):
    def __init__(self, title: str, width: int = 400, height: int = 600, theme: str = 'darkly'):
        if width is None or width < 0:
            raise ValueError("Width must be a valid positive integer")

        if height is None or height < 0:
            raise ValueError("Height must be a valid positive integer")

        super().__init__(themename=theme, title=title, minsize=(width, height), resizable=(False, False))

        # Create UI
        # Key
        options_frame = tb.Frame(self)
        label = tb.Label(options_frame, text="Screenshot key")
        self.__key_text = tb.StringVar()
        self.__key_entry = tb.Entry(options_frame, name='keybind', textvariable=self.__key_text)
        self.__key_entry.config(state="disabled")

        label.grid(row=0, column=0)
        self.__key_entry.grid(row=0, column=1, sticky=tb.E + tb.W)

        # Server URL
        label = tb.Label(options_frame, text="Server URL")
        self.__url_text = tb.StringVar()
        self.__url_entry = tb.Entry(options_frame, name='url', textvariable=self.__url_text)

        label.grid(row=1, column=0)
        self.__url_entry.grid(row=1, column=1, sticky=tb.E + tb.W)

        # Server Token
        label = tb.Label(options_frame, text="Server Token")
        self.__token_text = tb.StringVar()
        self.__token_entry = tb.Entry(options_frame, name='token', textvariable=self.__token_text, width=50)

        label.grid(row=2, column=0)
        self.__token_entry.grid(row=2, column=1, sticky=tb.E + tb.W)

        buttons_frame = tb.Frame(self)
        centered_frame = tb.Frame(self)
        self.__capture_text = tb.StringVar()
        self.__capture_text.set("Enable capture")
        tb.Button(centered_frame, textvariable=self.__capture_text, bootstyle = 'success', command=self.capture).grid(row=0, column=0, padx=10, sticky=tb.E + tb.W)
        tb.Button(centered_frame, text='save options', command=self.save_options).grid(row=0, column=1, padx=10, sticky=tb.E + tb.W)
        tb.Button(centered_frame, text='change keybind', command=self.change_key).grid(row=0, column=2, padx=10, sticky=tb.E + tb.W)

        options_frame.pack(fill='both', expand=True)
        buttons_frame.pack(fill='both', expand=True)
        centered_frame.place(in_=buttons_frame, anchor="c", relx=.5)

        self.__read_options()
        self.mainloop()

    def change_key(self):
        self.__key_text.set("Waiting for a new key...")
        threading.Thread(target=self.__read_key).start()

    def __read_key(self):
        k = KeyPress()
        key = k.read_key()

        if key is None:
            return

        self.__set_hotkey(key=key)

    def __set_hotkey(self, key: str):
        if not key:
            self.__hotkey = None
            self.__key_text.set('<No key defined>')

        try:
            k = KeyPress()
            self.__hotkey = k.prepare_for_global_hotkey(key)
            self.__key_text.set(key)
        except ValueError:
            self.__hotkey = None
            self.__key_text.set('invalid key detected: {}'.format(key))

    def __read_options(self):
        # Update values
        settings = Settings()
        config_url = settings.get(Settings.SECTION_SERVER, Settings.OPTION_URL)
        config_token = settings.get(Settings.SECTION_SERVER, Settings.OPTION_TOKEN)
        config_key = settings.get(Settings.SECTION_KEYBIND, Settings.OPTION_KEY)

        self.__set_hotkey(key=config_key)
        self.__token_text.set(config_token)
        self.__url_text.set(config_url)

    def save_options(self):
        settings = Settings()
        settings.set(section=Settings.SECTION_SERVER, option=Settings.OPTION_URL, value=self.__url_text.get())
        settings.set(section=Settings.SECTION_SERVER, option=Settings.OPTION_TOKEN, value=self.__token_text.get())
        settings.set(section=Settings.SECTION_KEYBIND, option=Settings.OPTION_KEY, value=self.__key_text.get())
        settings.save()

    def capture(self):
        text = self.__capture_text.get()
        if text == "Enable capture":
            if self.__hotkey:
                self.__capture_text.set('Capturing enabled')
                self.__thread = keyboard.GlobalHotKeys({self.__hotkey: self.screenshot})
                self.__thread.start()
        else:
            self.__capture_text.set('Enable capture')
            if self.__thread:
                self.__thread.stop()
                self.__thread = None

    def screenshot(self):
        try:
            foxhole = pywinctl.getWindowsWithTitle(title="War", condition=pywinctl.Re.STARTSWITH)[0]
        except Exception:
            print("Foxhole is not running")
            return

        if foxhole.isMinimized:
            print("Foxhole is minimized")
            return

        if not foxhole.isActive:
            print("Foxhole should be the active window")
            return

        with mss() as sct:
            sct_img = sct.grab(foxhole.getClientFrame())
            to_png(sct_img.rgb, sct_img.size, output="screenshot.png")
            print("Screenshot taken")
