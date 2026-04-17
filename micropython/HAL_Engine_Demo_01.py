import machine
from HAL_Engine_01 import FastOLED, Gamepad

i2c = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(15), freq=1000000)
oled = FastOLED(i2c)
controls = Gamepad()

x = 64
y = 16


while True:
    
    # Ready to draw!
    oled.clear()
    
    x=x+1
    
    if (x > 128):
        x = 0
        
    oled.circle(x, y, 8, 1, True)
    oled.show()