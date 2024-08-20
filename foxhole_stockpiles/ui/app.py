from datetime import datetime
from io import BytesIO
import re
import threading

from httpx import Client, Timeout
from PIL import ImageGrab
from pynput import keyboard
import pywinctl
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from foxhole_stockpiles.core.config import settings
from foxhole_stockpiles.models.keypress import KeyPress
from foxhole_stockpiles.ui.modal_window import ModalWindow


class App(tb.Window):
    def __init__(self, title: str, width: int = 400, height: int = 600, theme: str = 'darkly'):
        if width is None or width < 0:
            raise ValueError("Width must be a valid positive integer")

        if height is None or height < 0:
            raise ValueError("Height must be a valid positive integer")

        super().__init__(themename=theme, title=title, minsize=(width, height), resizable=(False, False))

        self._counter = 0
        self._capture_enabled = False
        self._thread = None

        # Prepare the profile URL for the token
        pattern = r'^(https?://[^/]+).*'
        replacement = r'\1/profile'

        # Apply the regex substitution
        self._token_url = re.sub(pattern, replacement, settings.server.url)

        # Transform the keybind into a hotkey
        if not settings.keybind.key:
            self._hotkey = None
        else:
            try:
                k = KeyPress()
                self._hotkey = k.prepare_for_global_hotkey(settings.keybind.key)
            except ValueError:
                self._hotkey = None

        self.create_widgets()

        # Change the status of the capture button if options are not set
        if not settings.keybind.key:
            self.message(message="Keybind is not set. Capture is disabled until a keybind is set.")
            self.capture_button.configure(state=DISABLED)

        if not settings.server.token:
            self.message(message="Token is not set. Capture is disabled until a token is set.")
            self.capture_button.configure(state=DISABLED)

        self.mainloop()

    def create_widgets(self):
        """
        Create the widgets for the window
        """
        # Menu
        menubar = tb.Menu(self)
        self.config(menu=menubar)

        settings_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set Keybind", command=self.command_keybind)
        settings_menu.add_command(label="Set Token", command=self.command_token)

        # Main Frame
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        buttons_frame = tb.Frame(main_frame)
        buttons_frame.pack(fill=X, expand=NO)
        # Buttons
        self.capture_button = tb.Button(buttons_frame, text="Start capture", command=self.command_capture, bootstyle=LIGHT)
        self.capture_button.pack(side=LEFT, padx=5)

        # Text Area with Scrollbar
        text_frame = tb.Frame(main_frame)
        text_frame.pack(fill=BOTH, expand=YES)
        # Logs
        #tb.Label(text_frame, text="Logs").pack(side=LEFT, pady=10)

        self._text_area = tb.Text(text_frame, wrap=WORD, height=10)
        self._text_area.pack(side=LEFT, fill=BOTH, expand=YES, pady=10)

        scrollbar = tb.Scrollbar(text_frame, orient=VERTICAL, command=self._text_area.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._text_area.configure(yscrollcommand=scrollbar.set)

    # Menu Commands
    def command_keybind(self):
        """
        'Set Keybind' callback. Used to set the keybind to take screenshots of Foxhole
        Creates a new ModalWindow to set the keybind. If the keybind is modified, it will update the settings and save them
        """
        keybind_window = ModalWindow(
            parent=self,
            title="Keybind Selection",
            label="Keybind selected",
            initial_value=settings.keybind.key,
            default_value="No key defined. Click 'Change keybind' to define a key",
            is_keybind=True
        )
        result = keybind_window.show()
        if result is None:
            return

        try:
            k = KeyPress()
            self._hotkey = k.prepare_for_global_hotkey(result)
        except ValueError:
            self._hotkey = None

        if result == settings.keybind.key:
            return

        settings.keybind.key = result
        self.message(message=f"Keybind updated to {result}.")
        settings.save()
        state = NORMAL if settings.keybind.key and settings.server.token else DISABLED
        self.capture_button.configure(state=state)


    def command_token(self):
        """
        'Set Token' callback. Used to set the token to send the screenshots to the server
        Creates a new ModalWindow to set the token. If the token is modified, it will update the settings and save them
        """
        token_window = ModalWindow(
            parent=self,
            title="Token Selection",
            label="Token",
            initial_value=settings.server.token,
            default_value=f"No token defined. visit {self._token_url} and copy the token here",
            is_keybind=False
        )

        result = token_window.show()
        if result is None:
            return

        if result == settings.server.token:
            return

        settings.server.token = result
        if result:
            self.message(message="Token updated.")
        else:
            self.message(message="Token removed. Capture is disabled until a token is set.")
        settings.save()
        state = NORMAL if settings.keybind.key and settings.server.token else DISABLED
        self.capture_button.configure(state=state)

    def command_capture(self):
        """
        "Enable capture" callback. Used to enable or disable the global keypress to take screenshots of Foxhole
        """
        if self._capture_enabled:
            self.capture_button.configure(text="Start Capture", bootstyle=LIGHT)
            self.message("Capture is disabled.")
            if self._thread:
                self._thread.stop()
                self._thread = None
        else:
            self.message("Capture is now enabled.")
            self.capture_button.configure(text="Stop Capture", bootstyle=DANGER)
            self._thread = keyboard.GlobalHotKeys({self._hotkey: self.command_screenshot})
            self._thread.start()

        self._capture_enabled = not self._capture_enabled

    def command_screenshot(self):
        """
        'Take Screenshot' callback. Used to take a screenshot of Foxhole and send it to the server
        """
        img = self.take_screenshot()
        if not img:
            return

        # Open a new thread to avoid blocking the execution
        threading.Thread(target=self.send_image, args=(img,)).start()

    def send_image(self, img):
        """
        Sends an image to foxhole_stockpiles server

        Args:
            img: Image to send
        """
        self._counter += 1
        current_screenshot = self._counter
        self.message(message="[{}] Sending screenshot...".format(current_screenshot))
        byte_io = BytesIO()
        img.save(byte_io, 'png')
        byte_io.seek(0)

        timeout = Timeout(10.0, read=60.0)
        headers = {"API_KEY": settings.server.token}
        with Client(headers=headers, verify=False, timeout=timeout) as client:
            try:
                response = client.post(
                    url=settings.server.url,
                    files={'image': ('screenshot.png', byte_io, 'image/png')}
                )
            except Exception as ex:
                self.message(message=f"[{current_screenshot}] Error sending the image. {ex}")
            else:
                try:
                    text = response.json().get('message')
                except Exception:
                    text = response.text

                if response.status_code == 200:
                    self.message(message=f"[{current_screenshot}] {text}")
                else:
                    self.message(message=f"[{current_screenshot}] Error sending the image. Status_code: {response.status_code}. Error: {text}")

    def take_screenshot(self):
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
        """
        Add a message to the text area

        Args:
            message: Message to add
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        self._text_area.insert(END, "[{}] {}\n".format(current_time, message))
        self._text_area.see(END)
