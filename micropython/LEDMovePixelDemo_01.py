import machine
import neopixel
import time

# Configuration for LED matrix interface
DATAPIN = 25      # GPIO pin connected to DI
NUMPIXELS = 25    # Number of LEDs in ZSRGB-2017H-08-Z3 strip
LED_ORDER = 3     # RGB
LED_COLS  = 4     # Size of LED matrix
LED_ROWS  = 4

# Initialize the LEDs and create NeoPixel object
np = neopixel.NeoPixel(machine.Pin(DATAPIN), NUMPIXELS, bpp=LED_ORDER)

# --- Joystick configuration IO pins
PIN_UP    = 0
PIN_DOWN  = 1
PIN_LEFT  = 2
PIN_RIGHT = 3
PIN_MID   = 4
PIN_SET   = 5
PIN_RST   = 6

# Initialize with internal pull-ups (0 = Pressed, 1 = Released)
button_up     = machine.Pin(PIN_UP, machine.Pin.IN, machine.Pin.PULL_UP)
button_down   = machine.Pin(PIN_DOWN, machine.Pin.IN, machine.Pin.PULL_UP)
button_left   = machine.Pin(PIN_LEFT, machine.Pin.IN, machine.Pin.PULL_UP)
button_right  = machine.Pin(PIN_RIGHT, machine.Pin.IN, machine.Pin.PULL_UP)
button_middle = machine.Pin(PIN_MID, machine.Pin.IN, machine.Pin.PULL_UP)
button_set    = machine.Pin(PIN_SET, machine.Pin.IN, machine.Pin.PULL_UP)
button_rst    = machine.Pin(PIN_RST, machine.Pin.IN, machine.Pin.PULL_UP)

# pixel position
pixelX = 2
pixelY = 2

# main render/event loop
while True:

    # initialize LED matrix to dark blue each frame
    for i in range( NUMPIXELS ):
        np[i] = (0, 0, 2)

    # did player move pixel with joystick
    if (not button_up.value()):
        pixelY = pixelY-1
    elif (not button_down.value()):
        pixelY = pixelY+1

    if (not button_right.value()):
        pixelX = pixelX+1
    elif (not button_left.value()):
        pixelX = pixelX-1

    # collision with edges
    if (pixelX >= LED_COLS):
        pixelX = 0
    elif (pixelX < 0): 
        pixelX = LED_COLS-1

    if (pixelY >= LED_ROWS):
        pixelY = 0
    elif (pixelY < 0): 
        pixelY = LED_ROWS-1

    # set the player pixel
    np[pixelX + pixelY*LED_COLS] = (0,32,0)
    
    # write the pixels
    np.write()
    
    # wait a moment
    time.sleep( 0.1 )
    

