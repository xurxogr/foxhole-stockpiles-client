from io import BytesIO
import threading

from httpx import Client
from httpx import Timeout
from mss import mss
from PIL import Image
from pynput import keyboard
import pywinctl
import ttkbootstrap as tb
from ttkbootstrap.toast import ToastNotification

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
        self.__token_text = tb.StringVar()
        self.__capture_text = tb.StringVar()

        # Create UI
        options_frame = tb.Frame(self)

        # Key
        tb.Label(options_frame, text="Screenshot key").grid(row=0, column=0)
        key_entry = tb.Entry(options_frame, name='keybind', textvariable=self.__key_text)
        key_entry.config(state="disabled")
        key_entry.grid(row=0, column=1, sticky=tb.E + tb.W)

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
                self.__print(message="Error sending the image. {}".format(str(ex)), error=True)
            else:
                try:
                    text = response.json().get('message')
                except Exception:
                    text = response.text

                if response.status_code == 200:
                    self.__print(message=text)
                else:
                    self.__print(message="Error sending the image. Status_code: {}. Error: {}".format(response.status_code, text), error=True)

    def __screenshot(self):
        """
        Take an screeshot of Foxhole
        """
        try:
            foxhole = pywinctl.getWindowsWithTitle(title="War", condition=pywinctl.Re.STARTSWITH)[0]
        except Exception:
            self.__print(message="Foxhole is not running", error=True)
            return None

        if foxhole.isMinimized:
            self.__print(message="Foxhole is minimized", error=True)
            return None

        if not foxhole.isActive:
            self.__print(message="Foxhole should be the active window", error=True)
            return None

        img = None
        with mss() as sct:
            sct_img = sct.grab(foxhole.getClientFrame())
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        return img

    def __print(self, message: str, error: bool = False):
        print(message)
        toast = ToastNotification(
            title="Foxhole Stockpiles",
            message=message,
            duration=5000,
            alert=error
        )

        toast.show_toast()
