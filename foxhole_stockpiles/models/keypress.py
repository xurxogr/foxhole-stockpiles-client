from pynput.keyboard import Listener
from pynput.keyboard import Key
from pynput.keyboard import KeyCode
from pynput.keyboard import HotKey

class KeyPress():
    def __init__(self):
        self.__listener = None
        self.__clean_vars()

    def __clean_vars(self):
        self.__key = None
        self.__modifiers = []
        self.__pressed_keys = set()

    def __on_release(self, key):
        """
        callback for release of keys.
        If it's the last release, return the combination of key(s)
        """
        if key in self.__pressed_keys:
            self.__pressed_keys.remove(key)
            if len(self.__pressed_keys) == 0:
                return False

    def __on_press(self, key):
        """
        callback for pressing keys
        Keeps trac9k of number of keys pressed removing duplicates
        """
        if key == Key.esc:
            self.__clean_vars()
            return False

        if key not in self.__pressed_keys:
            self.__pressed_keys.add(key)

        # If there is already a non modifier, ignore any other key press
        # ctrl+a is valid but a+ctrl is not. same for a+s
        if self.__key is not None:
            return

        canonical_key = self.__listener.canonical(key=key)
        if type(key) == Key:
            # ctrl, shift, alt, cmd
            if type(canonical_key) == Key:
                name = "<{}>".format(canonical_key.name)
                if name in self.__modifiers:
                    return

                self.__modifiers.append(name)
            # Pause, left, scroll, tab, space, etc
            else:
                self.__key = "<{}>".format(key.name)
        else:
            if 96 <= key.vk and key.vk <= 105: # Numpad
                self.__key = "numpad_{}".format(key.vk - 96)
            elif key.vk == 107:
                self.__key = "numpad_plus"
            elif key.vk == 109:
                self.__key = "numpad_-"
            else:
                self.__key = str(canonical_key).replace("'", "")

    def read_key(self) -> str:
        self.__clean_vars()
        self.__listener = Listener(on_press=self.__on_press, on_release=self.__on_release)
        with self.__listener:
            self.__listener.join()

        key_list = []
        if self.__modifiers:
            key_list = self.__modifiers

        if self.__key:
            key_list.append(self.__key)

        return "+".join(key_list)

    def prepare_for_global_hotkey(self, keys: str = None) -> str:
        def _transform(key: str) -> str:
            if 'numpad_' not in key:
                return key

            _key = key.replace('numpad_', '')
            if _key == 'plus':
                return '<107>'

            if _key == '-':
                return '<109>'

            print(_key)

            return "<{}>".format(int(_key) + 96)


        hotkey_list = []
        for key in keys.split('+'):
            hotkey_list.append(_transform(key))

        try:
            parsed_keys = HotKey.parse("+".join(hotkey_list))
        except Exception as ex:
            raise ValueError("Error parsing [{}]".format(keys)) from None

        modified_keys = []
        for index, key in enumerate(parsed_keys):
            if type(key) != KeyCode and key.name not in {'shift', 'ctrl', 'alt', 'cmd'}:
                modified_keys.append(str(key.value))
            else:
                modified_keys.append(hotkey_list[index])

        return "+".join(modified_keys)
