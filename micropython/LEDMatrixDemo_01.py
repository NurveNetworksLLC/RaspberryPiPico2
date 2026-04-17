import machine
import neopixel

# Configuration
PIN = 25          # GPIO pin connected to DI
PIXELS = 25       # Number of LEDs in ZSRGB-2017H-08-Z3 strip
LED_ORDER = 3     # RGB

# Initialize
np = neopixel.NeoPixel(machine.Pin(PIN), PIXELS, bpp=LED_ORDER)

# Set Colors (note 255 is 100% brightness and will blind you and draw a LOT of current, so use smaller numbers!)
np[0] = (32, 0, 0)
np[1] = (0, 32, 0)
np[2] = (0, 0, 32)
np[3] = (32, 32, 0)
np[4] = (32, 0, 32)
np[5] = (0, 32, 32)
np[6] = (32, 32, 32)

# write the pixels
np.write()