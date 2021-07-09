import tkinter as tk
import pynput as pnp

from datetime import datetime
from picamera import PiCamera
from picamera.array import PiRGBArray
from PIL import Image, ImageTk as itk
from pynput.keyboard import KeyCode
from time import sleep, time
from threading import Thread, ThreadError
from collections import deque


class Gui(tk.Tk):
    # Unbedingt anpassen
    TARGET_DIR_PATH = "/home/pi/Pictures"

    # Einstellungen, um die erscheinung anzupassen
    START_IN_FULLSCREEN = True
    LABEL_TOP_MARGIN = 200
    CANVAS_BOTTOM_MARGIN = 200
    BACKGROUND_COLOR = "white"

    # Detail einstellungen
    PREVIEW_RES = (640, 480)
    CAPTURE_RES = (2560, 1920)
    KEYCODE_YES = KeyCode.from_char("1")
    KEYCODE_NO = KeyCode.from_char("0")
    DUMMY_IMAGE = Image.new(mode="RGBA", size=PREVIEW_RES, color="red")
    CAMERA_FPS = 10
    DELAY = 1.0 / CAMERA_FPS
    MAX_QUEUE_LENGTH = 10
    ROTATION = 90

    # Label Texte
    INIT_STRING = "\nDrücke eine beliebige Taste, um PiBooth zu starten"
    WELCOME_STRING = "Willkommen in der PiBooth!\n Drücke eine Taste, um ein Bild zu machen."
    CHOICE_STRING = "Zufrieden?\nBestätigen: GRÜN, Zurück: ROT"
    SAVING_STRING = "\nSpeichere..."
    KLICK = "\nKlick!"

    def __init__(self):
        tk.Tk.__init__(self)
        # ## create Tk object
        self.title("Pybooth")
        self.attributes('-fullscreen', Gui.START_IN_FULLSCREEN)
        self.bind("<F11>", self.toggle_full_screen)
        self.bind("<Escape>", self.quit_full_screen)
        self.geometry(str(self.winfo_screenwidth()) + "x" + str(self.winfo_screenheight()))
        # ## create widgets
        self.main_frame = tk.Frame(master=self, bg=Gui.BACKGROUND_COLOR)
        self.label_title = tk.Label(self.main_frame, text=Gui.INIT_STRING, font=("Arial", 24), bg=Gui.BACKGROUND_COLOR)
        self.canvas = tk.Canvas(self.main_frame, bg=Gui.BACKGROUND_COLOR, bd=0, highlightthickness=0)
        # ## init fields
        # keyboard
        self.yes_key = Gui.KEYCODE_YES
        self.no_key = Gui.KEYCODE_NO
        self.keyboard_listener = pnp.keyboard.Listener(on_press=self.on_key_press)
        # actions
        self.yes_action = None
        self.no_action = None
        # receiving images
        self.camera = PiCamera(framerate=Gui.CAMERA_FPS, resolution=Gui.CAPTURE_RES, rotation=Gui.ROTATION)
        self.preview_target = PiRGBArray(self.camera, size=Gui.PREVIEW_RES)
        self.snapshot_target = PiRGBArray(self.camera, size=Gui.CAPTURE_RES)
        self.frame_queue = deque()  # liste von PiRGBArray.array objekten
        self.is_cam_stream_running = True  # stoppt den receive-thread, falls nötig
        self.continue_preview = True  # steuert, ob ein cam stream gerade angezeigt werden soll
        self.image_filler_thread = None
        self.preview_thread = None
        # misc
        self.full_screen_state = True
        self.snapshot_image_reference = []  # Referenz auf das snapshot bild, das auf dem canvas gezeigt wird
        # ### arrange widgets
        self.main_frame.pack(fill=tk.BOTH, expand=1)
        self.label_title.pack(pady=(Gui.LABEL_TOP_MARGIN, 0))
        self.canvas.pack(fill=tk.BOTH, expand=1, anchor=tk.CENTER, pady=(0, Gui.CANVAS_BOTTOM_MARGIN))

    def mainloop(self):
        self.start_app_functions()
        tk.Tk.mainloop(self)

    def start_app_functions(self):
        self.cofigure_for_first_startup()
        self.keyboard_listener.start()
        print("finished pybooth setup")

    # ---------- User induced actions

    def start_first_preview(self):
        self.start_preview()
        self.configure_for_snapshot()
        self.label_title.configure(text=Gui.WELCOME_STRING)

    def take_picture_and_show(self):
        self.start_and_wait_for_countdown()
        self.stop_preview()
        sleep(0.5)  # gib dem preview thread etwas zeit zum beenden
        self.get_cam_snapshot()
        print("snapshot taken")
        self.display_current_snapshot()
        self.configure_for_choice()
        self.label_title.configure(text=Gui.CHOICE_STRING)

    def save_picture_and_return(self):
        self.save_current_picture()
        print("saved picture")
        self.start_preview()
        self.configure_for_snapshot()
        self.label_title.configure(text=Gui.WELCOME_STRING)

    def discard_and_return(self):
        print("discarded picture")
        self.start_preview()
        self.configure_for_snapshot()
        self.label_title.configure(text=Gui.WELCOME_STRING)

    # ---------- configuration

    def cofigure_for_first_startup(self):
        self.yes_action = self.start_first_preview
        self.no_action = self.start_first_preview

    def configure_for_choice(self):
        self.yes_action = self.save_picture_and_return
        self.no_action = self.discard_and_return

    def configure_for_snapshot(self):
        self.yes_action = self.take_picture_and_show
        self.no_action = self.take_picture_and_show

    # ---------- engine

    def start_and_wait_for_countdown(self, delay: int = 3):
        for i in [x for x in range(delay, 0, -1)]:
            count_str = "\n" + str(i)
            self.label_title.configure(text=count_str)
            sleep(1)
        self.label_title.configure(text=Gui.KLICK)

    def get_cam_snapshot(self):
        assert not self.preview_thread.is_alive() and not self.image_filler_thread.is_alive(), "Can not take snapshot if there is a preview running"
        self.camera.capture(self.snapshot_target, format="rgb", use_video_port=False)

    def display_current_snapshot(self):
        self.canvas.delete("all")
        self.snapshot_target.truncate()
        self.snapshot_target.seek(0)
        if self.snapshot_target.array is not None:
            img = itk.PhotoImage(Image.fromarray(self.snapshot_target.array).resize(Gui.PREVIEW_RES))
            self.canvas.create_image(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                image=img,
                anchor=tk.CENTER
            )
            self.snapshot_image_reference.append(img)  # speichere referenz
        else:
            print("No snapshot available")
            self.canvas.create_image(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                image=itk.PhotoImage(Gui.DUMMY_IMAGE),
                anchor=tk.CENTER
            )

    def save_current_picture(self):
        self.label_title.configure(text=Gui.SAVING_STRING)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        file_name = Gui.TARGET_DIR_PATH + "/" + now + ".jpg"
        Image.fromarray(self.snapshot_target.array).save(fp=file_name, quality=100)

    def start_preview(self):
        if ((self.preview_thread and self.preview_thread.is_alive()) or
                (self.image_filler_thread and self.image_filler_thread.is_alive())):
            raise ThreadError("Trying to start a new preview although there is still a preview running")
        self.snapshot_image_reference.clear()  # Lösche alle snapshot previews
        self.image_filler_thread = Thread(target=self.fill_frames_continuously, name="camera_capturer", daemon=True)
        self.image_filler_thread.start()
        self.preview_thread = Thread(target=self.preview, name="preview_thread", daemon=True)
        self.preview_thread.start()

    def stop_preview(self):
        self.continue_preview = False

    # ---------- image receiving

    def fill_frames_continuously(self):
        """
        Startet das ständige capturen von Bildern und setzt diese in eine liste, die von einer
        anderen Methode ausgelesen werden.
        Diese Methode sollte in einem separaten Thread laufen.
        """
        # setze preview camera einstellungen
        for _ in self.camera.capture_continuous(self.preview_target, format="rgb", use_video_port=True,
                                                resize=Gui.PREVIEW_RES):
            self.preview_target.truncate()
            self.preview_target.seek(0)
            if len(self.frame_queue) > Gui.MAX_QUEUE_LENGTH:
                # entferne ältestes element, falls die maximale länge erreicht ist
                self.frame_queue.popleft()
            self.frame_queue.append(self.preview_target.array)
            if not self.continue_preview:
                # self.camera.close()
                self.frame_queue.clear()
                break

    def preview(self):
        """
        Startet das Abholen von Bildern aus der Queue, solange das Preview-Flag nicht auf false geschaltet wird.
        Diese Methode sollte innerhalb eines separaten Threads laufen.
        """
        print("starting preview")
        self.continue_preview = True
        old_image = None  # gebraucht, um eine referenz auf das alte bild zu haben, während das neue auf dem canvas aufgebaut wrd
        new_image = None
        while self.continue_preview:
            #  hier, solange das flag zum anzeigen des previews auf True steht
            start_time = time()
            if len(self.frame_queue) > 0:
                pil_img = Image.fromarray(self.frame_queue.pop())
                old_image = new_image
                new_image = itk.PhotoImage(pil_img)
                self.canvas.create_image(
                    self.canvas.winfo_width() / 2,
                    self.canvas.winfo_height() / 2,
                    image=new_image,
                    anchor=tk.CENTER
                )
            elapsed_time = time() - start_time
            sleep(max(0., Gui.DELAY - elapsed_time))
        print("stopping preview")

    # ---------- misc

    def on_key_press(self, key):
        if key == self.yes_key:
            if self.yes_action:
                self.yes_action()
        elif key == self.no_key:
            if self.no_action:
                self.no_action()

    def toggle_full_screen(self, event):
        self.full_screen_state = not self.full_screen_state
        self.attributes("-fullscreen", self.full_screen_state)

    def quit_full_screen(self, event):
        self.full_screen_state = False
        self.attributes("-fullscreen", self.full_screen_state)
