import sys
import os
import ctypes

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def enable_high_dpi():
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


from ui.app import ControlApp


def main():
    enable_high_dpi()
    app = ControlApp()
    app.mainloop()


if __name__ == "__main__":
    main()
