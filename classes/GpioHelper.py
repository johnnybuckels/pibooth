from pynput.keyboard import Controller
from gpiozero import Button


class AliveIndicator:
    
    def __init__(self):
        self.is_alive = True
        
        
    def kill(self):
        self.is_alive=False
        
        
    def is_living(self) -> bool:
        return self.is_alive
    

class ButtonToKeyListener:
    
    def __init__(self, gpio_button_number, emit_key, name="", alive_indicator: AliveIndicator=None):
        self.name = name
        self.gpio_button_number = gpio_button_number
        self.emit_key = emit_key
        self.alive_indicator = alive_indicator
        
        self.controller = Controller()
        
    def start_listening(self):
        print(self.name, ": start listening")
        self.button = Button(self.gpio_button_number)
        self.button.when_pressed = self.emulate_key_press
        if self.alive_indicator:
            self.button.hold_time = 4
            self.button.when_held = self.turn_off
    
    def emulate_key_press(self):
        self.controller.type(self.emit_key)
        
    def turn_off(self):
        print(self.name, ": turning of indicator")
        if self.alive_indicator:
            self.alive_indicator.kill()
