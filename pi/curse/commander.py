import curses
from functools import partial


def _do_quit():
    raise KeyboardInterrupt


def _dialog_read_line(msg, stdscr):
    # TODO: check if staying in the dialog somehow breaks anything
    rows, cols = stdscr.getmaxyx()
    dialog = curses.newwin(4, 40, 4, 8)
    dialog.border(0)
    dialog.addstr(0, 2, msg)
    curses.echo()
    dialog.addstr(1, 1, ">>")
    ret = dialog.getstr(1, 4, 3)
    curses.noecho()
    return ret


def _dialog_read_rgb_color(msg, stdscr):
    # TODO: handle bad input
    return tuple(int(chr(num)) for num in _dialog_read_line(stdscr, msg))


class CurseCommandBuilder:
    def __init__(self):
        self._keypool = ["R", "B", "O", "J"]
        self.key_to_cmd = {"Q": (None, None, _do_quit)}
        self.key_to_descr = {"Q": "Quit"}

    def add_command(self, keypress, cmd, descr):
        self.key_to_cmd[keypress] = cmd
        self.key_to_descr[keypress] = descr

    def add_led(self, led_name):
        self.add_command(self._keypool.pop(), (led_name, False, None), f"Turn {led_name} off")
        self.add_command(self._keypool.pop(), (led_name, True, None), f"Turn {led_name} on")

    def add_abz(self, abz_name, buzz=None):
        # TODO: take input here like RGB
        if not buzz:
            buzz = {"pitch": 440, "duration": 0.3}
        self.add_command(self._keypool.pop(), (abz_name, buzz, None), f"Buzz the buzzer")

    def add_rgb(self, rgb_name):
        self.add_command(self._keypool.pop(),
                         (rgb_name, None, partial(_dialog_read_rgb_color,
                                                  f"Enter {rgb_name} color (format: ### eg. 101),")),
                         f"Set {rgb_name} color")

    def build(self):
        return self.key_to_cmd, self.key_to_descr
