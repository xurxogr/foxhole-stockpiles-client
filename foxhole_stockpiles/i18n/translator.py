"""Translation management for multi-language support."""

import json
from pathlib import Path
from typing import Any


class Translator:
    """Handles loading and accessing translation strings."""

    def __init__(self, language: str = "en") -> None:
        """Initialize translator with a specific language.

        Args:
            language: Language code (e.g., 'en', 'es')
        """
        self.language = language
        self.translations: dict[str, Any] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translation file for the current language."""
        translations_dir = Path(__file__).parent / "translations"
        translation_file = translations_dir / f"{self.language}.json"

        if not translation_file.exists():
            # Fallback to English if language file doesn't exist
            translation_file = translations_dir / "en.json"

        with open(translation_file, encoding="utf-8") as f:
            self.translations = json.load(f)

    def get(self, key: str, **kwargs: Any) -> str:
        """Get a translation string by its key path.

        Args:
            key: Dot-separated path to the translation (e.g., 'app.menu.settings')
            **kwargs: Format parameters for the translation string

        Returns:
            Translated and formatted string
        """
        keys = key.split(".")
        value: Any = self.translations

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return key  # Return key if translation not found
            else:
                return key

        if isinstance(value, str) and kwargs:
            return value.format(**kwargs)

        return str(value) if value is not None else key

    def __call__(self, key: str, **kwargs: Any) -> str:
        """Shorthand for get method.

        Args:
            key: Dot-separated path to the translation
            **kwargs: Format parameters for the translation string

        Returns:
            Translated and formatted string
        """
        return self.get(key, **kwargs)


def get_available_languages() -> list[tuple[str, str]]:
    """Get list of available languages.

    Returns:
        List of tuples (language_code, language_name)
    """
    translations_dir = Path(__file__).parent / "translations"
    languages: list[tuple[str, str]] = []

    for translation_file in sorted(translations_dir.glob("*.json")):
        language_code = translation_file.stem
        with open(translation_file, encoding="utf-8") as f:
            data = json.load(f)
            language_name = data.get("language_name", language_code)
            languages.append((language_code, language_name))

    return languages


# Global translator instance
_translator: Translator | None = None


def get_translator(language: str | None = None) -> Translator:
    """Get or create the global translator instance.

    Args:
        language: Language code to use (None to keep current)

    Returns:
        Translator instance
    """
    global _translator

    if language is not None:
        _translator = Translator(language)
    elif _translator is None:
        _translator = Translator("en")

    return _translator


def t(key: str, **kwargs: Any) -> str:
    """Convenience function for translation.

    Args:
        key: Dot-separated path to the translation
        **kwargs: Format parameters for the translation string

    Returns:
        Translated and formatted string
    """
    translator = get_translator()
    return translator(key, **kwargs)
