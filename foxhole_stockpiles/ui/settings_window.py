"""Settings window for configuring all application settings."""

import threading
from typing import Any

import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, BOTTOM, LEFT, PRIMARY, RIGHT, SECONDARY, YES, X

from foxhole_stockpiles.core.config import settings
from foxhole_stockpiles.models.keypress import KeyPress


class SettingsWindow(tb.Toplevel):  # type: ignore[misc]
    """Settings dialog window for all application configuration."""

    def __init__(self, parent: Any) -> None:
        """Create settings window.

        Args:
            parent: Parent window
        """
        super().__init__(parent, minsize=(600, 400), resizable=(False, False))
        self.title("Settings")
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
        notebook.add(keybind_frame, text="Keybind")
        self.create_keybind_tab(keybind_frame)

        # Server tab
        server_frame = tb.Frame(notebook, padding=10)
        notebook.add(server_frame, text="Server")
        self.create_server_tab(server_frame)

        # Webhook tab
        webhook_frame = tb.Frame(notebook, padding=10)
        notebook.add(webhook_frame, text="Webhook")
        self.create_webhook_tab(webhook_frame)

        # Buttons at bottom
        button_frame = tb.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.pack(fill=X, side=BOTTOM)

        tb.Button(button_frame, text="Cancel", command=self.on_cancel, bootstyle=SECONDARY).pack(
            side=RIGHT, padx=5
        )
        tb.Button(button_frame, text="Save", command=self.on_save, bootstyle=PRIMARY).pack(
            side=RIGHT, padx=5
        )

    def create_keybind_tab(self, parent: Any) -> None:
        """Create keybind configuration tab.

        Args:
            parent: Parent frame
        """
        assert settings.keybind is not None

        tb.Label(parent, text="Screenshot Keybind", font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Keybind entry
        keybind_frame = tb.Frame(parent)
        keybind_frame.pack(fill=X, pady=5)

        tb.Label(keybind_frame, text="Key:", width=15).pack(side=LEFT)
        self.keybind_var = tb.StringVar(
            value=settings.keybind.key
            if settings.keybind.key
            else "No key defined. Click 'Change' to set a key"
        )
        tb.Entry(keybind_frame, textvariable=self.keybind_var, state="readonly").pack(
            side=LEFT, fill=X, expand=YES, padx=(0, 10)
        )
        tb.Button(keybind_frame, text="Change", command=self.change_keybind).pack(side=LEFT)

        tb.Label(
            parent,
            text="Press the key combination you want to use for taking screenshots",
            font=("", 9),
        ).pack(anchor="w", pady=(5, 0))

    def create_server_tab(self, parent: Any) -> None:
        """Create server configuration tab.

        Args:
            parent: Parent frame
        """
        assert settings.server is not None

        tb.Label(parent, text="Server Configuration", font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Server URL
        url_frame = tb.Frame(parent)
        url_frame.pack(fill=X, pady=5)
        tb.Label(url_frame, text="Server URL:", width=15).pack(side=LEFT)
        self.server_url_var = tb.StringVar(value=settings.server.url)
        tb.Entry(url_frame, textvariable=self.server_url_var).pack(side=LEFT, fill=X, expand=YES)

        # Separator
        tb.Separator(parent, orient="horizontal").pack(fill=X, pady=20)

        # Authentication section
        tb.Label(parent, text="Authentication", font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        # Auth type
        auth_frame = tb.Frame(parent)
        auth_frame.pack(fill=X, pady=5)
        tb.Label(auth_frame, text="Auth Type:", width=15).pack(side=LEFT)
        self.auth_type_var = tb.StringVar(
            value=settings.server.auth_type if settings.server.auth_type else "none"
        )
        auth_combo = tb.Combobox(
            auth_frame,
            textvariable=self.auth_type_var,
            values=["none", "basic", "bearer"],
            state="readonly",
        )
        auth_combo.pack(side=LEFT, fill=X, expand=YES)
        auth_combo.bind("<<ComboboxSelected>>", self.on_auth_type_changed)

        # Basic auth fields
        self.basic_auth_frame = tb.Frame(parent)
        self.basic_auth_frame.pack(fill=X, pady=(10, 0))

        username_frame = tb.Frame(self.basic_auth_frame)
        username_frame.pack(fill=X, pady=5)
        tb.Label(username_frame, text="Username:", width=15).pack(side=LEFT)
        self.username_var = tb.StringVar(
            value=settings.server.username if settings.server.username else ""
        )
        tb.Entry(username_frame, textvariable=self.username_var).pack(side=LEFT, fill=X, expand=YES)

        password_frame = tb.Frame(self.basic_auth_frame)
        password_frame.pack(fill=X, pady=5)
        tb.Label(password_frame, text="Password:", width=15).pack(side=LEFT)
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
        tb.Label(token_frame, text="Token:", width=15).pack(side=LEFT)
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
        assert settings.webhook is not None

        tb.Label(parent, text="Webhook Forward Auth", font=("", 12, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        tb.Label(
            parent,
            text="Optional: Configure a custom header for webhook forwarding",
            font=("", 9),
        ).pack(anchor="w", pady=(0, 20))

        # Webhook token
        token_frame = tb.Frame(parent)
        token_frame.pack(fill=X, pady=5)
        tb.Label(token_frame, text="Token:", width=15).pack(side=LEFT)
        self.webhook_token_var = tb.StringVar(
            value=settings.webhook.token if settings.webhook.token else ""
        )
        tb.Entry(token_frame, textvariable=self.webhook_token_var).pack(
            side=LEFT, fill=X, expand=YES
        )

        # Webhook header
        header_frame = tb.Frame(parent)
        header_frame.pack(fill=X, pady=5)
        tb.Label(header_frame, text="Header Name:", width=15).pack(side=LEFT)
        self.webhook_header_var = tb.StringVar(value=settings.webhook.header)
        tb.Entry(header_frame, textvariable=self.webhook_header_var).pack(
            side=LEFT, fill=X, expand=YES
        )

    def on_auth_type_changed(self, event: Any) -> None:
        """Handle auth type selection change.

        Args:
            event: Event object (unused)
        """
        auth_type = self.auth_type_var.get()

        if auth_type == "basic":
            self.basic_auth_frame.pack(fill=X, pady=(10, 0))
            self.bearer_frame.pack_forget()
        elif auth_type == "bearer":
            self.basic_auth_frame.pack_forget()
            self.bearer_frame.pack(fill=X, pady=(10, 0))
        else:  # none
            self.basic_auth_frame.pack_forget()
            self.bearer_frame.pack_forget()

    def change_keybind(self) -> None:
        """Change keybind callback. Opens a thread to capture a new keybind."""
        self.keybind_var.set("Waiting for a new key...")
        threading.Thread(target=self.read_keybind).start()

    def read_keybind(self) -> None:
        """Waits for a new key combination and updates the keybind field."""
        k = KeyPress()
        key = k.read_key()

        if not key:
            self.keybind_var.set("No key defined. Click 'Change' to set a key")
            return

        try:
            # Validate the key can be used as a global hotkey
            k.prepare_for_global_hotkey(key)
            self.keybind_var.set(key)
        except ValueError:
            self.keybind_var.set(f"Invalid key detected: {key}")

    def validate_settings(self) -> bool:
        """Validate all settings before saving.

        Returns:
            bool: True if all settings are valid, False otherwise
        """
        # Validate webhook header
        webhook_header = self.webhook_header_var.get()
        if webhook_header.lower() in self.dangerous_headers:
            tb.dialogs.Messagebox.show_error(
                f"Cannot use '{webhook_header}' header. This is a protected HTTP header.",
                "Invalid Header",
                parent=self,
            )
            return False

        if not all(c.isalnum() or c in "-_" for c in webhook_header):
            tb.dialogs.Messagebox.show_error(
                f"Invalid header name '{webhook_header}'. "
                "Use only letters, numbers, hyphens, and underscores.",
                "Invalid Header",
                parent=self,
            )
            return False

        # Validate auth type
        auth_type = self.auth_type_var.get()
        if auth_type not in ["none", "basic", "bearer"]:
            tb.dialogs.Messagebox.show_error(
                f"Invalid auth type: {auth_type}",
                "Invalid Auth Type",
                parent=self,
            )
            return False

        return True

    def on_save(self) -> None:
        """Handle save button click."""
        if not self.validate_settings():
            return

        assert settings.keybind is not None
        assert settings.server is not None
        assert settings.webhook is not None

        # Save keybind
        keybind_value = self.keybind_var.get()
        if (
            keybind_value
            and not keybind_value.startswith("No key")
            and not keybind_value.startswith("Invalid")
        ):
            settings.keybind.key = keybind_value
        else:
            settings.keybind.key = None

        # Save server settings
        settings.server.url = self.server_url_var.get()

        # Save auth settings
        auth_type = self.auth_type_var.get()
        settings.server.auth_type = None if auth_type == "none" else auth_type

        if auth_type == "basic":
            settings.server.username = self.username_var.get() if self.username_var.get() else None
            settings.server.password = self.password_var.get() if self.password_var.get() else None
            settings.server.token = None
        elif auth_type == "bearer":
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
        settings.webhook.token = webhook_token if webhook_token else None
        settings.webhook.header = self.webhook_header_var.get()

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
