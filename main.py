"""Maple Lane Finds - launch the game.

    python main.py              play
    python main.py --selftest   run the automated play-through test (uses a temporary save folder)
"""
import os
import sys
import tempfile
import traceback


def _show_error(msg):
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, msg, "Maple Lane Finds", 0x40)
            return
        except Exception:
            pass
    print(msg, file=sys.stderr)


def main():
    selftest = "--selftest" in sys.argv
    if selftest:
        os.environ.setdefault("MLF_DATA_DIR", tempfile.mkdtemp(prefix="mlf_selftest_"))
        os.environ.setdefault("MLF_UPDATE_URL", "https://offline.invalid/version.json")  # simulate no internet
        if "--headless" in sys.argv:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if sys.platform.startswith("win"):
        try:  # crisp rendering on high-DPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    from game.app import App
    from game.menus import TitleScreen
    from game.paths import data_file

    driver = None
    if selftest:
        from game.selftest import Driver
        driver = Driver()
    try:
        app = App(test_driver=driver)
        app.run(TitleScreen(app))
    except Exception:
        tb = traceback.format_exc()
        try:
            with open(data_file("logs", "crash.log"), "a", encoding="utf-8") as f:
                f.write(tb + "\n")
        except Exception:
            pass
        if selftest:
            print(tb)
            sys.exit(2)
        _show_error("Sorry, Maple Lane Finds ran into a problem and needs to close.\n\n"
                    "Your progress is saved. Details were written to crash.log in the save folder.")
        sys.exit(1)
    if driver is not None:
        sys.exit(1 if driver.failed or not driver.done else 0)


if __name__ == "__main__":
    main()
