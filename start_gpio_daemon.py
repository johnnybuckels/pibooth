from time import sleep
from classes.GpioHelper import ButtonToKeyListener, AliveIndicator
from subprocess import call

def start_gpio_loop():
    listener_green = None
    listener_red = None

    indicator = AliveIndicator()
        
    listener_green = ButtonToKeyListener(gpio_button_number=2, emit_key="1", name="green_listener")
    listener_red = ButtonToKeyListener(gpio_button_number=3, emit_key="0", name="red_listener", alive_indicator=indicator)
    listener_green.start_listening()
    listener_red.start_listening()
        
    while indicator.is_living():
        sleep(1)

    print("turning of power...")
    call("sudo shutdown --poweroff now", shell=True)

if __name__ == "__main__":
    start_gpio_loop()