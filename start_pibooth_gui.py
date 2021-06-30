from classes.piboothgui import Gui
from threading import Thread

def start_gui():
    gui = Gui()
    print("starting pybooth")
    gui.mainloop()

if __name__ == '__main__':
    start_gui()
