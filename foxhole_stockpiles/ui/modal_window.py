import threading

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from foxhole_stockpiles.models.keypress import KeyPress


class ModalWindow(tb.Toplevel):
    def __init__(self, parent, title: str, label: str, initial_value: str, default_value: str, is_keybind: bool):
        """
        Create a modal window

        Args:
            parent: Parent window
            title: Window title
            label: Label text
            initial_value: Initial value for the entry
            default_value: Default value for the entry. If accept is pressed and the entry is the default value, the result will be None
            is_keybind: If the entry is a keybind
        """
        super().__init__(parent, minsize=(400, 100), resizable=(False, False))
        self.title(title)
        self.grab_set()  # Make the window modal
        self.is_keybind = is_keybind
        self.result = None

        self.label_text = label
        self.value_text = tb.StringVar(value=initial_value or default_value)
        self.default_value = default_value

        self.create_widgets()

    def create_widgets(self):
        """
        Create the widgets for the window
        """
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        label_frame = tb.Frame(main_frame)
        label_frame.pack(fill=X, expand=YES)
        # Screenshot Key
        state = "readonly" if self.is_keybind else "normal"
        tb.Entry(label_frame, textvariable=self.value_text, state=state).pack(fill=X, expand=YES)

        # Buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=BOTH, expand=YES)

        if self.is_keybind:
            tb.Button(button_frame, text="Change keybind", command=self.change_key).pack(side=LEFT, padx=5)

        tb.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)
        tb.Button(button_frame, text="Accept", command=self.on_accept, bootstyle=PRIMARY).pack(side=RIGHT, padx=5)

    def change_key(self):
        """
        "Change keybind" callback.
        Opens a new thread to capture a new keybind.
        """
        self.value_text.set("Waiting for a new key...")
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
            self.result = None
            self.value_text.set("No key defined. Click 'Change keybind' to define a key")
            return

        try:
            # Check if the key is valid
            k = KeyPress()
            k.prepare_for_global_hotkey(key)
            self.value_text.set(key)
            self.result = key
        except ValueError:
            self.result = None
            self.value_text.set('invalid key detected: {}'.format(key))

    def on_cancel(self):
        self.result = None
        self.destroy()

    def on_accept(self):
        self.result = self.value_text.get()
        if self.result == self.default_value:
            self.result = None
        self.destroy()

    def show(self):
        self.wait_window()
        return self.result
