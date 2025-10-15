"""Settings window for configuring all application settings."""

import threading
from typing import Any

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, BOTTOM, LEFT, PRIMARY, RIGHT, SECONDARY, YES, X

from foxhole_stockpiles.core.config import settings
from foxhole_stockpiles.enums.auth_type import AuthType
from foxhole_stockpiles.i18n import get_available_languages, get_translator, t
from foxhole_stockpiles.models.keypress import KeyPress


class SettingsWindow(tb.Toplevel):  # type: ignore[misc]
    """Settings dialog window for all application configuration."""

    def __init__(self, parent: Any) -> None:
        """Create settings window.

        Args:
            parent: Parent window
        """
        super().__init__(parent, minsize=(600, 400), resizable=(False, False))
        self.title(t("settings.title"))
        self.grab_set()  # Make the window modal
        self.result = False  # Track if settings were saved

        # Center the window on the parent window
        self.transient(parent)
        self.update_idletasks()

        # Get parent window position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get this window size
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        # Set the window position
        self.geometry(f"+{x}+{y}")

        # Dangerous headers that should be blocked
        self.dangerous_headers = {
            "authorization",
            "host",
            "connection",
            "content-length",
            "transfer-encoding",
            "te",
            "trailer",
            "upgrade",
            "proxy-authorization",
            "proxy-authenticate",
            "content-encoding",
            "content-type",
        }

        self.create_widgets()

    def create_widgets(self) -> None:
        """Create the widgets for the window."""
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # Create notebook for tabs
        notebook = tb.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=YES)

        # Keybind tab
        keybind_frame = tb.Frame(notebook, padding=10)
        notebook.add(keybind_frame, text=t("settings.tab.keybind"))
        self.create_keybind_tab(keybind_frame)

        # Server tab
        server_frame = tb.Frame(notebook, padding=10)
        notebook.add(server_frame, text=t("settings.tab.server"))
        self.create_server_tab(server_frame)

        # Webhook tab
        webhook_frame = tb.Frame(notebook, padding=10)
        notebook.add(webhook_frame, text=t("settings.tab.webhook"))
        self.create_webhook_tab(webhook_frame)

        # Language tab
        language_frame = tb.Frame(notebook, padding=10)
        notebook.add(language_frame, text=t("settings.tab.language"))
        self.create_language_tab(language_frame)

        # Buttons at bottom
        button_frame = tb.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill=X, side=BOTTOM)

        cancel_button = tb.Button(
            button_frame,
            text=t("settings.button.cancel"),
            command=self.on_cancel,
            bootstyle=SECONDARY,
        )
        cancel_button.pack(side=RIGHT, padx=5)

        save_button = tb.Button(
            button_frame,
            text=t("settings.button.save"),
            command=self.on_save,
            bootstyle=PRIMARY,
        )
        save_button.pack(side=RIGHT, padx=5)

    def create_keybind_tab(self, parent: Any) -> None:
        """Create keybind configuration tab.

        Args:
            parent: Parent frame
        """
        tb.Label(parent, text=t("settings.keybind.title"), font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Keybind entry
        keybind_frame = tb.Frame(parent)
        keybind_frame.pack(fill=X, pady=5)

        tb.Label(keybind_frame, text=t("settings.keybind.label_key"), width=22).pack(side=LEFT)
        self.keybind_var = tb.StringVar(
            value=settings.keybind.key
            if settings.keybind.key
            else t("settings.keybind.no_key_defined")
        )
        tb.Entry(keybind_frame, textvariable=self.keybind_var, state="readonly").pack(
            side=LEFT, fill=X, expand=YES, padx=(0, 10)
        )
        change_button = tb.Button(
            keybind_frame, text=t("settings.button.change"), command=self.change_keybind
        )
        change_button.pack(side=LEFT)

        tb.Label(
            parent,
            text=t("settings.keybind.hint"),
            font=("", 9),
        ).pack(anchor="w", pady=(5, 0))

    def create_server_tab(self, parent: Any) -> None:
        """Create server configuration tab.

        Args:
            parent: Parent frame
        """
        tb.Label(parent, text=t("settings.server.title"), font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Server URL
        url_frame = tb.Frame(parent)
        url_frame.pack(fill=X, pady=5)
        tb.Label(url_frame, text=t("settings.server.label_url"), width=22).pack(side=LEFT)
        self.server_url_var = tb.StringVar(value=settings.server.url)
        tb.Entry(url_frame, textvariable=self.server_url_var).pack(side=LEFT, fill=X, expand=YES)

        # Separator
        tb.Separator(parent, orient="horizontal").pack(fill=X, pady=20)

        # Authentication section
        tb.Label(parent, text=t("settings.server.auth_title"), font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Auth type
        auth_frame = tb.Frame(parent)
        auth_frame.pack(fill=X, pady=5)
        tb.Label(auth_frame, text=t("settings.server.label_auth_type"), width=22).pack(side=LEFT)
        if settings.server.auth_type:
            auth_value = settings.server.auth_type.value
        else:
            auth_value = t("settings.server.auth_none")
        self.auth_type_var = tb.StringVar(value=auth_value)
        auth_combo = tb.Combobox(
            auth_frame,
            textvariable=self.auth_type_var,
            values=[t("settings.server.auth_none"), AuthType.BASIC.value, AuthType.BEARER.value],
            state="readonly",
        )
        auth_combo.pack(side=LEFT, fill=X, expand=YES)
        auth_combo.bind("<<ComboboxSelected>>", self.on_auth_type_changed)

        # Basic auth fields
        self.basic_auth_frame = tb.Frame(parent)
        self.basic_auth_frame.pack(fill=X, pady=(10, 0))

        username_frame = tb.Frame(self.basic_auth_frame)
        username_frame.pack(fill=X, pady=5)
        tb.Label(username_frame, text=t("settings.server.label_username"), width=22).pack(side=LEFT)
        self.username_var = tb.StringVar(
            value=settings.server.username if settings.server.username else ""
        )
        tb.Entry(username_frame, textvariable=self.username_var).pack(side=LEFT, fill=X, expand=YES)

        password_frame = tb.Frame(self.basic_auth_frame)
        password_frame.pack(fill=X, pady=5)
        tb.Label(password_frame, text=t("settings.server.label_password"), width=22).pack(side=LEFT)
        self.password_var = tb.StringVar(
            value=settings.server.password if settings.server.password else ""
        )
        tb.Entry(password_frame, textvariable=self.password_var, show="*").pack(
            side=LEFT, fill=X, expand=YES
        )

        # Bearer token field
        self.bearer_frame = tb.Frame(parent)
        self.bearer_frame.pack(fill=X, pady=(10, 0))

        token_frame = tb.Frame(self.bearer_frame)
        token_frame.pack(fill=X, pady=5)
        tb.Label(token_frame, text=t("settings.server.label_token"), width=22).pack(side=LEFT)
        self.bearer_token_var = tb.StringVar(
            value=settings.server.token if settings.server.token else ""
        )
        tb.Entry(token_frame, textvariable=self.bearer_token_var).pack(
            side=LEFT, fill=X, expand=YES
        )

        # Show/hide auth fields based on type
        self.on_auth_type_changed(None)

    def create_webhook_tab(self, parent: Any) -> None:
        """Create webhook configuration tab.

        Args:
            parent: Parent frame
        """
        tb.Label(parent, text=t("settings.webhook.title"), font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        tb.Label(
            parent,
            text=t("settings.webhook.hint"),
            font=("", 9),
        ).pack(anchor="w", pady=(0, 20))

        # Webhook token
        token_frame = tb.Frame(parent)
        token_frame.pack(fill=X, pady=5)
        tb.Label(token_frame, text=t("settings.webhook.label_token"), width=22).pack(side=LEFT)
        self.webhook_token_var = tb.StringVar(
            value=settings.webhook.token if settings.webhook.token else ""
        )
        tb.Entry(token_frame, textvariable=self.webhook_token_var).pack(
            side=LEFT, fill=X, expand=YES
        )

        # Webhook header
        header_frame = tb.Frame(parent)
        header_frame.pack(fill=X, pady=5)
        tb.Label(header_frame, text=t("settings.webhook.label_header"), width=22).pack(side=LEFT)
        self.webhook_header_var = tb.StringVar(
            value=settings.webhook.header if settings.webhook.header else ""
        )
        tb.Entry(header_frame, textvariable=self.webhook_header_var).pack(
            side=LEFT, fill=X, expand=YES
        )

    def create_language_tab(self, parent: Any) -> None:
        """Create language configuration tab.

        Args:
            parent: Parent frame
        """
        tb.Label(parent, text=t("settings.language.title"), font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        tb.Label(
            parent,
            text=t("settings.language.hint"),
            font=("", 9),
        ).pack(anchor="w", pady=(0, 20))

        # Language selection
        lang_frame = tb.Frame(parent)
        lang_frame.pack(fill=X, pady=5)
        tb.Label(lang_frame, text=t("settings.language.label_language"), width=22).pack(side=LEFT)

        # Get available languages dynamically
        available_languages = get_available_languages()
        language_names = [name for _, name in available_languages]
        language_codes = {name: code for code, name in available_languages}

        # Find current language name
        current_lang_code = settings.language
        current_lang_name = next(
            (name for code, name in available_languages if code == current_lang_code), "English"
        )

        self.language_var = tb.StringVar(value=current_lang_name)
        self.language_codes = language_codes

        lang_combo = tb.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=language_names,
            state="readonly",
        )
        lang_combo.pack(side=LEFT, fill=X, expand=YES)

    def on_auth_type_changed(self, event: Any) -> None:
        """Handle auth type selection change.

        Args:
            event: Event object (unused)
        """
        auth_type = self.auth_type_var.get()

        if auth_type == AuthType.BASIC.value:
            self.basic_auth_frame.pack(fill=X, pady=(10, 0))
            self.bearer_frame.pack_forget()
        elif auth_type == AuthType.BEARER.value:
            self.basic_auth_frame.pack_forget()
            self.bearer_frame.pack(fill=X, pady=(10, 0))
        else:  # none
            self.basic_auth_frame.pack_forget()
            self.bearer_frame.pack_forget()

    def change_keybind(self) -> None:
        """Change keybind callback. Opens a thread to capture a new keybind."""
        self.keybind_var.set(t("settings.keybind.waiting"))
        threading.Thread(target=self.read_keybind).start()

    def read_keybind(self) -> None:
        """Waits for a new key combination and updates the keybind field."""
        k = KeyPress()
        key = k.read_key()

        if not key:
            self.keybind_var.set(t("settings.keybind.no_key_defined"))
            return

        try:
            # Validate the key can be used as a global hotkey
            k.prepare_for_global_hotkey(key)
            self.keybind_var.set(key)
        except ValueError:
            self.keybind_var.set(t("settings.keybind.invalid_key") + f" {key}")

    def validate_settings(self) -> bool:
        """Validate all settings before saving.

        Returns:
            bool: True if all settings are valid, False otherwise
        """
        # Validate webhook configuration
        webhook_token = self.webhook_token_var.get()
        webhook_header = self.webhook_header_var.get()

        if webhook_token and not webhook_header:
            tb.dialogs.Messagebox.show_error(
                t("settings.validation.webhook_header_required"),
                t("settings.validation.missing_webhook_header"),
                parent=self,
            )
            return False

        if webhook_header and not webhook_token:
            tb.dialogs.Messagebox.show_error(
                t("settings.validation.webhook_token_required"),
                t("settings.validation.missing_webhook_token"),
                parent=self,
            )
            return False

        # Validate webhook header format (only if provided)
        if webhook_header:
            if webhook_header.lower() in self.dangerous_headers:
                tb.dialogs.Messagebox.show_error(
                    t("settings.validation.protected_header", header=webhook_header),
                    t("settings.validation.invalid_header"),
                    parent=self,
                )
                return False

            if not all(c.isalnum() or c in "-_" for c in webhook_header):
                tb.dialogs.Messagebox.show_error(
                    t("settings.validation.invalid_header_format", header=webhook_header),
                    t("settings.validation.invalid_header"),
                    parent=self,
                )
                return False

        # Validate auth type
        auth_type = self.auth_type_var.get()
        valid_types = [t("settings.server.auth_none"), AuthType.BASIC.value, AuthType.BEARER.value]
        if auth_type not in valid_types:
            tb.dialogs.Messagebox.show_error(
                t("settings.validation.invalid_auth_type_message", auth_type=auth_type),
                t("settings.validation.invalid_auth_type"),
                parent=self,
            )
            return False

        # Validate auth credentials match auth type
        if auth_type == AuthType.BASIC.value:
            username = self.username_var.get()
            password = self.password_var.get()
            if not username or not password:
                tb.dialogs.Messagebox.show_error(
                    t("settings.validation.basic_auth_required"),
                    t("settings.validation.missing_credentials"),
                    parent=self,
                )
                return False
        elif auth_type == AuthType.BEARER.value:
            token = self.bearer_token_var.get()
            if not token:
                tb.dialogs.Messagebox.show_error(
                    t("settings.validation.bearer_token_required"),
                    t("settings.validation.missing_token"),
                    parent=self,
                )
                return False

        return True

    def on_save(self) -> None:
        """Handle save button click."""
        if not self.validate_settings():
            return

        # Save keybind
        keybind_value = self.keybind_var.get()
        no_key_msg = t("settings.keybind.no_key_defined")
        invalid_key_msg = t("settings.keybind.invalid_key")
        waiting_msg = t("settings.keybind.waiting")

        if (
            keybind_value
            and keybind_value != no_key_msg
            and not keybind_value.startswith(invalid_key_msg)
            and keybind_value != waiting_msg
        ):
            settings.keybind.key = keybind_value
        else:
            settings.keybind.key = None

        # Save server settings
        settings.server.url = self.server_url_var.get()

        # Save auth settings
        auth_type_str = self.auth_type_var.get()
        if auth_type_str == t("settings.server.auth_none"):
            settings.server.auth_type = None
        elif auth_type_str == AuthType.BASIC.value:
            settings.server.auth_type = AuthType.BASIC
        elif auth_type_str == AuthType.BEARER.value:
            settings.server.auth_type = AuthType.BEARER

        if auth_type_str == AuthType.BASIC.value:
            settings.server.username = self.username_var.get() if self.username_var.get() else None
            settings.server.password = self.password_var.get() if self.password_var.get() else None
            settings.server.token = None
        elif auth_type_str == AuthType.BEARER.value:
            settings.server.token = (
                self.bearer_token_var.get() if self.bearer_token_var.get() else None
            )
            settings.server.username = None
            settings.server.password = None
        else:  # none
            settings.server.username = None
            settings.server.password = None
            settings.server.token = None

        # Save webhook settings
        webhook_token = self.webhook_token_var.get()
        webhook_header = self.webhook_header_var.get()
        settings.webhook.token = webhook_token if webhook_token else None
        settings.webhook.header = webhook_header if webhook_header else None

        # Save language settings
        language_name = self.language_var.get()
        language_code = self.language_codes.get(language_name, "en")
        settings.language = language_code

        # Update translator with new language
        get_translator(language_code)

        # Save to file
        settings.save()

        self.result = True
        self.destroy()

    def on_cancel(self) -> None:
        """Handle cancel button click."""
        self.result = False
        self.destroy()

    def show(self) -> bool:
        """Show the settings window and return whether settings were saved.

        Returns:
            bool: True if settings were saved, False if cancelled
        """
        self.wait_window()
        return self.result
