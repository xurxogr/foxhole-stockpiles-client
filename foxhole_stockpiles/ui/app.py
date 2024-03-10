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

        # text of the entries. It will be used for storing config options
        self.__key_text = tb.StringVar()
        self.__url_text = tb.StringVar()
        self.__token_text = tb.StringVar()
        self.__capture_text = tb.StringVar()

        # Create UI
        options_frame = tb.Frame(self)

        # Key
        tb.Label(options_frame, text="Screenshot key").grid(row=0, column=0)
        key_entry = tb.Entry(options_frame, name='keybind', textvariable=self.__key_text)
        key_entry.config(state="disabled")
        key_entry.grid(row=0, column=1, sticky=tb.E + tb.W)

        # Server URL
        label = tb.Label(options_frame, text="Server URL").grid(row=1, column=0)
        self.__url_entry = tb.Entry(options_frame, name='url', textvariable=self.__url_text)
        self.__url_entry.grid(row=1, column=1, sticky=tb.E + tb.W)

        # Server Token
        tb.Label(options_frame, text="Server Token").grid(row=2, column=0)
        self.__token_entry = tb.Entry(options_frame, name='token', textvariable=self.__token_text, width=50)
        self.__token_entry.grid(row=2, column=1, sticky=tb.E + tb.W)

        buttons_frame = tb.Frame(self)
        centered_frame = tb.Frame(self)

        self.__capture_text.set("Enable capture")
        tb.Button(centered_frame, textvariable=self.__capture_text, bootstyle = 'success', command=self.capture).grid(row=0, column=0, padx=10, sticky=tb.E + tb.W)
        tb.Button(centered_frame, text='save options', command=self.save_options).grid(row=0, column=1, padx=10, sticky=tb.E + tb.W)
        tb.Button(centered_frame, text='change keybind', command=self.change_key).grid(row=0, column=2, padx=10, sticky=tb.E + tb.W)

        options_frame.pack(fill='both', expand=True)
        buttons_frame.pack(fill='both', expand=True)
        centered_frame.place(in_=buttons_frame, anchor="c", relx=.5)

        # Fill the components with the values from config.ini
        self.__read_options()
        self.mainloop()

    def change_key(self):
        """
        "Change keybind" callback.
        Opens a new thread to capture a new keybind.
        """
        self.__key_text.set("Waiting for a new key...")
        threading.Thread(target=self.__read_key).start()

    def __read_key(self):
        """
        Waits for a new combinations of key pressed and stores it in the appropriate entry
        """
        k = KeyPress()
        key = k.read_key()

        if key is None:
            return

        self.__set_hotkey(key=key)

    def __set_hotkey(self, key: str):
        """
        Updates the UI with the defined keybind.
        If there is keybind or it's invalid to be used as global hotkey a message will be displayes
        """
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
        """
        Read the config.ini file options and update the appropriate UI fields
        """
        # Update values
        settings = Settings()
        config_url = settings.get(Settings.SECTION_SERVER, Settings.OPTION_URL)
        config_token = settings.get(Settings.SECTION_SERVER, Settings.OPTION_TOKEN)
        config_key = settings.get(Settings.SECTION_KEYBIND, Settings.OPTION_KEY)

        self.__set_hotkey(key=config_key)
        self.__token_text.set(config_token)
        self.__url_text.set(config_url)

    def save_options(self):
        """
        Save the options to config.ini
        """
        settings = Settings()
        settings.set(section=Settings.SECTION_SERVER, option=Settings.OPTION_URL, value=self.__url_text.get())
        settings.set(section=Settings.SECTION_SERVER, option=Settings.OPTION_TOKEN, value=self.__token_text.get())
        settings.set(section=Settings.SECTION_KEYBIND, option=Settings.OPTION_KEY, value=self.__key_text.get())
        settings.save()

    def capture(self):
        """
        "Enable capture" callback. Used to enable or disable the global keypress to take screenshots of Foxhole
        """
        text = self.__capture_text.get()
        if text == "Enable capture":
            # Enable the capture if the hotkey is set
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
        """
        Take an screeshot of Foxhole
        """
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
