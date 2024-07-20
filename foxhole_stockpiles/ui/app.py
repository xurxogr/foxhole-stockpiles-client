from datetime import datetime
from io import BytesIO
import threading

from httpx import Client
from httpx import Timeout
from PIL import ImageGrab
from pynput import keyboard
import pywinctl
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

        self._key_text = tb.StringVar()
        self._token_text = tb.StringVar()
        self._counter = 0
        self._capture_enabled = False

        self.create_widgets()

        # Fill the components with the values from config.ini
        self.read_options()
        self.mainloop()


    def create_widgets(self):
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        # Screenshot Key
        tb.Label(main_frame, text="Screenshot key:").grid(row=0, column=0, sticky=W, padx=(0, 5), pady=5)
        tb.Entry(main_frame, textvariable=self._key_text, state="disabled").grid(row=0, column=1, sticky=EW, pady=5)

        # Server Token
        tb.Label(main_frame, text="Server token:").grid(row=1, column=0, sticky=W, padx=(0, 5), pady=5)
        tb.Entry(main_frame, textvariable=self._token_text).grid(row=1, column=1, sticky=EW, pady=5)

        # Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.capture_button = tb.Button(button_frame, text="Start capture", command=self.capture, bootstyle=LIGHT)
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

        self._text_area = tb.Text(text_frame, wrap=WORD, height=10)
        self._text_area.pack(side=LEFT, fill=BOTH, expand=YES)

        scrollbar = tb.Scrollbar(text_frame, orient=VERTICAL, command=self._text_area.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._text_area.configure(yscrollcommand=scrollbar.set)

    def change_key(self):
        """
        "Change keybind" callback.
        Opens a new thread to capture a new keybind.
        """
        self._key_text.set("Waiting for a new key...")
        threading.Thread(target=self.read_key).start()

    def read_key(self):
        """
        Waits for a new combinations of key pressed and stores it in the appropriate entry
        """
        k = KeyPress()
        key = k.read_key()

        if key is None:
            return

        self.set_hotkey(key=key)

    def set_hotkey(self, key: str):
        """
        Updates the UI with the defined keybind.
        If there is keybind or it's invalid to be used as global hotkey a message will be displayes
        """
        if not key:
            self._hotkey = None
            self._key_text.set('<No key defined>')

        try:
            k = KeyPress()
            self._hotkey = k.prepare_for_global_hotkey(key)
            self._key_text.set(key)
        except ValueError:
            self._hotkey = None
            self._key_text.set('invalid key detected: {}'.format(key))

    def read_options(self):
        """
        Read the config.ini file options and update the appropriate UI fields
        """
        # Update values
        settings = Settings()
        self.__url = settings.get(Settings.SECTION_SERVER, Settings.OPTION_URL)
        config_token = settings.get(Settings.SECTION_SERVER, Settings.OPTION_TOKEN)
        config_key = settings.get(Settings.SECTION_KEYBIND, Settings.OPTION_KEY)

        self.set_hotkey(key=config_key)
        self._token_text.set(config_token)

    def save_options(self):
        """
        Save the options to config.ini
        """
        settings = Settings()
        settings.set(section=Settings.SECTION_SERVER, option=Settings.OPTION_TOKEN, value=self._token_text.get())
        settings.set(section=Settings.SECTION_KEYBIND, option=Settings.OPTION_KEY, value=self._key_text.get())
        settings.save()

    def capture(self):
        """
        "Enable capture" callback. Used to enable or disable the global keypress to take screenshots of Foxhole
        """
        if self._capture_enabled:
            self.capture_button.configure(text="Start Capture", bootstyle=LIGHT)
            self.message("Capture is disabled.")
            if self._thread:
                self._thread.stop()
                self._thread = None
        elif self._hotkey: # Enable the capture if the hotkey is set
            self.message("Capture is now enabled.")
            self.capture_button.configure(text="Stop Capture", bootstyle=DANGER)
            self._thread = keyboard.GlobalHotKeys({self._hotkey: self.screenshot})
            self._thread.start()


        self._capture_enabled = not self._capture_enabled

    def screenshot(self):
        img = self._screenshot()
        if not img:
            return

        # Open a new thread to avoid blocking the execution
        threading.Thread(target=self.send_image, args=(img,)).start()

    def send_image(self, img):
        """
        Sends an image to foxhole_stockpiles server
        :param img: Image to send
        """
        self._counter += 1
        current_screenshot = self._counter
        self.message(message="[{}] Sending screenshot...".format(current_screenshot))
        byte_io = BytesIO()
        img.save(byte_io, 'png')
        byte_io.seek(0)

        timeout = Timeout(10.0, read=30.0)
        headers = {"API_KEY": self._token_text.get()}
        with Client(headers=headers, verify=False, timeout=timeout) as client:
            try:
                response = client.post(
                    url=self.__url,
                    files={'image': ('screenshot.png', byte_io, 'image/png')}
                )
            except Exception as ex:
                self.message(message="[{}] Error sending the image. {}".format(current_screenshot, str(ex)))
            else:
                try:
                    text = response.json().get('message')
                except Exception:
                    text = response.text

                if response.status_code == 200:
                    self.message(message="[{}] {}".format(current_screenshot, text))
                else:
                    self.message(message="[{}] Error sending the image. Status_code: {}. Error: {}".format(current_screenshot, response.status_code, text))

    def _screenshot(self):
        """
        Take an screeshot of Foxhole
        """
        try:
            foxhole = pywinctl.getWindowsWithTitle(title="War", condition=pywinctl.Re.STARTSWITH)[0]
        except Exception:
            self.message(message="Foxhole is not running")
            return None

        if foxhole.isMinimized:
            self.message(message="Foxhole is minimized")
            return None

        if not foxhole.isActive:
            self.message(message="Foxhole should be the active window")
            return None

        region=foxhole.getClientFrame()
        return ImageGrab.grab(bbox=region, all_screens=True)

    def message(self, message: str):
        current_time = datetime.now().strftime("%H:%M:%S")
        self._text_area.insert(END, "[{}] {}\n".format(current_time, message))
        self._text_area.see(END)
