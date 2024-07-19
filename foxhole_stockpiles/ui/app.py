from datetime import datetime
from io import BytesIO
import threading

from httpx import Client
from httpx import Timeout
from PIL import ImageGrab
from pynput import keyboard
import pywinctl


import locale
import os

# Try to set the locale to the user's default setting
try:
    locale.setlocale(locale.LC_ALL, '')
except locale.Error:
    # If that fails, force it to a common locale
    os.environ['LC_ALL'] = 'C'
    locale.setlocale(locale.LC_ALL, 'C')

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from foxhole_stockpiles.models.keypress import KeyPress
from foxhole_stockpiles.config.settings import Settings


class App(tb.Window):
    def __init__(self, title: str, width: int = 400, height: int = 600, theme: str = 'darkly'):
        if width is None or width < 0:
            raise ValueError("Width must be a valid positive integer")

        if height is None or height < 0:
            raise ValueError("Height must be a valid positive integer")

        super().__init__(themename=theme, title=title, minsize=(width, height), resizable=(False, False))

        self.__key_text = tb.StringVar()
        self.__token_text = tb.StringVar()
        self.__capture_text = tb.StringVar(value="Enable capture")
        self.__counter = 0

        self.create_widgets()

        # Fill the components with the values from config.ini
        self.__read_options()
        self.mainloop()


    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        # Screenshot Key
        tb.Label(main_frame, text="Screenshot key:").grid(row=0, column=0, sticky=W, padx=(0, 5), pady=5)
        tb.Entry(main_frame, textvariable=self.__key_text, state="disabled").grid(row=0, column=1, sticky=EW, pady=5)

        # Server Token
        tb.Label(main_frame, text="Server token:").grid(row=1, column=0, sticky=W, padx=(0, 5), pady=5)
        tb.Entry(main_frame, textvariable=self.__token_text).grid(row=1, column=1, sticky=EW, pady=5)

        # Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.capture_button = tb.Button(button_frame, textvariable=self.__capture_text, command=self.capture, bootstyle="success")
        self.capture_button.pack(side=LEFT, padx=5)

        tb.Button(button_frame, text="Save options", command=self.save_options).pack(side=LEFT, padx=5)
        tb.Button(button_frame, text="Change keybind", command=self.change_key).pack(side=LEFT, padx=5)

        # Logs
        tb.Label(main_frame, text="Logs").grid(row=3, column=0, columnspan=2, sticky=W, pady=(10, 5))

        # Text Area with Scrollbar
        text_frame = tb.Frame(main_frame)
        text_frame.grid(row=4, column=0, columnspan=2, sticky=NSEW)
        main_frame.rowconfigure(4, weight=1)
        main_frame.columnconfigure(1, weight=1)

        self.__text_area = tb.Text(text_frame, wrap=WORD, height=10)
        self.__text_area.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = tb.Scrollbar(text_frame, orient=VERTICAL, command=self.__text_area.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.__text_area.configure(yscrollcommand=scrollbar.set)

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
        self.__url = settings.get(Settings.SECTION_SERVER, Settings.OPTION_URL)
        config_token = settings.get(Settings.SECTION_SERVER, Settings.OPTION_TOKEN)
        config_key = settings.get(Settings.SECTION_KEYBIND, Settings.OPTION_KEY)

        self.__set_hotkey(key=config_key)
        self.__token_text.set(config_token)

    def save_options(self):
        """
        Save the options to config.ini
        """
        settings = Settings()
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
        img = self.__screenshot()
        if not img:
            return

        # Open a new thread to avoid blocking the execution
        threading.Thread(target=self.__send_image, args=(img,)).start()

    def __send_image(self, img):
        """
        Sends an image to foxhole_stockpiles server
        :param img: Image to send
        """
        self.__counter += 1
        current_screenshot = self.__counter
        self.__print(message="[{}] Sending screenshot...".format(current_screenshot))
        byte_io = BytesIO()
        img.save(byte_io, 'png')
        byte_io.seek(0)

        timeout = Timeout(10.0, read=30.0)
        headers = {"API_KEY": self.__token_text.get()}
        with Client(headers=headers, verify=False, timeout=timeout) as client:
            try:
                response = client.post(
                    url=self.__url,
                    files={'image': ('screenshot.png', byte_io, 'image/png')}
                )
            except Exception as ex:
                self.__print(message="[{}] Error sending the image. {}".format(current_screenshot, str(ex)))
            else:
                try:
                    text = response.json().get('message')
                except Exception:
                    text = response.text

                if response.status_code == 200:
                    self.__print(message="[{}] {}".format(current_screenshot, text))
                else:
                    self.__print(message="[{}] Error sending the image. Status_code: {}. Error: {}".format(current_screenshot, response.status_code, text))

    def __screenshot(self):
        """
        Take an screeshot of Foxhole
        """
        try:
            foxhole = pywinctl.getWindowsWithTitle(title="War", condition=pywinctl.Re.STARTSWITH)[0]
        except Exception:
            self.__print(message="Foxhole is not running")
            return None

        if foxhole.isMinimized:
            self.__print(message="Foxhole is minimized")
            return None

        if not foxhole.isActive:
            self.__print(message="Foxhole should be the active window")
            return None

        region=foxhole.getClientFrame()
        return ImageGrab.grab(bbox=region, all_screens=True)

    def __print(self, message: str):
        self.__add_message(message)

    def __add_message(self, message: str):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.__text_area.insert(END, "[{}] {}\n".format(current_time, message))
        self.__text_area.see(END)
