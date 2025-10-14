"""Main application window for the Foxhole Stockpiles Client."""

import re
import threading
from datetime import datetime
from io import BytesIO
from typing import Any

import pywinctl
import ttkbootstrap as tb
from httpx import Client, Timeout
from PIL import ImageGrab
from pynput import keyboard
from ttkbootstrap.constants import (
    BOTH,
    DANGER,
    DISABLED,
    END,
    LEFT,
    LIGHT,
    NO,
    NORMAL,
    RIGHT,
    VERTICAL,
    WORD,
    YES,
    X,
    Y,
)

from foxhole_stockpiles.core.config import settings
from foxhole_stockpiles.enums.auth_type import AuthType
from foxhole_stockpiles.models.keypress import KeyPress
from foxhole_stockpiles.ui.settings_window import SettingsWindow


class App(tb.Window):  # type: ignore[misc]
    """Main application window."""

    def __init__(
        self, title: str, width: int = 400, height: int = 600, theme: str = "darkly"
    ) -> None:
        """Initialize the main application window.

        Args:
            title: Window title
            width: Window width in pixels
            height: Window height in pixels
            theme: ttkbootstrap theme name
        """
        if width < 0:
            raise ValueError("Width must be a valid positive integer")

        if height < 0:
            raise ValueError("Height must be a valid positive integer")

        super().__init__(
            themename=theme,
            title=title,
            minsize=(width, height),
            resizable=(False, False),
        )

        self._counter = 0
        self._capture_enabled = False
        self._thread = None

        # Prepare the profile URL for the token
        pattern = r"^(https?://[^/]+).*"
        replacement = r"\1/profile"

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

        if not self._check_auth_configured():
            self.message(
                message="Authentication is not configured. Capture is disabled until auth is set."
            )
            self.capture_button.configure(state=DISABLED)

        self.mainloop()

    def create_widgets(self) -> None:
        """Create the widgets for the window."""
        # Menu
        menubar = tb.Menu(self)
        self.config(menu=menubar)

        settings_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure", command=self.command_settings)

        # Main Frame
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        buttons_frame = tb.Frame(main_frame)
        buttons_frame.pack(fill=X, expand=NO)
        # Buttons
        self.capture_button = tb.Button(
            buttons_frame,
            text="Start capture",
            command=self.command_capture,
            bootstyle=LIGHT,
        )
        self.capture_button.pack(side=LEFT, padx=5)

        # Text Area with Scrollbar
        text_frame = tb.Frame(main_frame)
        text_frame.pack(fill=BOTH, expand=YES)
        # Logs
        # tb.Label(text_frame, text="Logs").pack(side=LEFT, pady=10)

        self._text_area = tb.Text(text_frame, wrap=WORD, height=10)
        self._text_area.pack(side=LEFT, fill=BOTH, expand=YES, pady=10)

        scrollbar = tb.Scrollbar(text_frame, orient=VERTICAL, command=self._text_area.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._text_area.configure(yscrollcommand=scrollbar.set)

    # Menu Commands
    def command_settings(self) -> None:
        """'Settings' callback. Opens the settings configuration window."""
        settings_window = SettingsWindow(parent=self)
        saved = settings_window.show()

        if saved:
            self.message(message="Settings saved successfully.")

            # Update hotkey if keybind changed
            if settings.keybind.key:
                try:
                    k = KeyPress()
                    self._hotkey = k.prepare_for_global_hotkey(settings.keybind.key)
                except ValueError:
                    self._hotkey = None
            else:
                self._hotkey = None

            # Update capture button state
            state = NORMAL if settings.keybind.key and self._check_auth_configured() else DISABLED
            self.capture_button.configure(state=state)

    def command_capture(self) -> None:
        """Enable capture callback.

        Used to enable or disable the global keypress to take screenshots of Foxhole.
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

    def command_screenshot(self) -> None:
        """Take Screenshot callback.

        Used to take a screenshot of Foxhole and send it to the server.
        """
        img = self.take_screenshot()
        if not img:
            return

        # Open a new thread to avoid blocking the execution
        threading.Thread(target=self.send_image, args=(img,)).start()

    def send_image(self, img: Any) -> None:
        """Sends an image to foxhole_stockpiles server.

        Args:
            img: Image to send
        """
        self._counter += 1
        current_screenshot = self._counter
        self.message(message=f"[{current_screenshot}] Sending screenshot...")
        byte_io = BytesIO()
        img.save(byte_io, "png")
        byte_io.seek(0)

        # Prepare authentication headers based on auth type
        auth_type = settings.server.auth_type
        headers: dict[str, str] = {}
        auth: tuple[str, str] | None = None

        if auth_type == AuthType.BEARER:
            # Pydantic validation ensures token is not None for BEARER auth
            token = settings.server.token
            if token:  # Type guard for mypy
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == AuthType.BASIC:
            # Pydantic validation ensures username and password are not None for BASIC auth
            username = settings.server.username
            password = settings.server.password
            if username and password:  # Type guard for mypy
                auth = (username, password)
        # For None auth_type, no additional auth needed

        # Add webhook forward auth header if configured
        webhook_token = settings.webhook.token
        webhook_header = settings.webhook.header
        if webhook_token and webhook_header:  # Pydantic validation ensures both are set
            headers[webhook_header] = webhook_token

        timeout = Timeout(10.0, read=60.0)
        with Client(auth=auth, headers=headers, verify=False, timeout=timeout) as client:
            try:
                response = client.post(
                    url=settings.server.url,
                    files={"image": ("screenshot.png", byte_io, "image/png")},
                )
            except Exception as ex:
                self.message(message=f"[{current_screenshot}] Error sending the image. {ex}")
            else:
                try:
                    text = response.json().get("message")
                except Exception:
                    text = response.text

                if response.status_code == 200:
                    self.message(message=f"[{current_screenshot}] {text}")
                else:
                    error_msg = (
                        f"[{current_screenshot}] Error sending the image. "
                        f"Status_code: {response.status_code}. Error: {text}"
                    )
                    self.message(message=error_msg)

    def take_screenshot(self) -> Any:
        """Take an screeshot of Foxhole."""
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

        region = foxhole.getClientFrame()
        return ImageGrab.grab(bbox=region, all_screens=True)

    def message(self, message: str) -> None:
        """Add a message to the text area.

        Args:
            message: Message to add
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        self._text_area.insert(END, f"[{current_time}] {message}\n")
        self._text_area.see(END)

    def _check_auth_configured(self) -> bool:
        """Check if authentication is properly configured based on auth type.

        Returns:
            bool: True if auth is configured, False otherwise
        """
        auth_type = settings.server.auth_type

        if auth_type is None:
            return True
        elif auth_type == AuthType.BASIC:
            return bool(settings.server.username and settings.server.password)
        elif auth_type == AuthType.BEARER:
            return bool(settings.server.token)
        return False
