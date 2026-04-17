"""
================================================================================
HAL_ENGINE: High-Performance OLED & Input Driver
Hardware: RP2350 (Pico 2) | I2C1 | SSD1306 (128x32)
================================================================================
"""
import machine
import framebuf

# ==============================================================================
# GAMEPAD CONTROLLER
# ==============================================================================
class Gamepad:
    """
    Reads a digital gamepad using internal pull-up resistors.
    Default Pins: GP0 through GP6.
    """
    def __init__(self, pins=(0, 1, 2, 3, 4, 5, 6)):
        self.pad_pins = [machine.Pin(i, machine.Pin.IN, machine.Pin.PULL_UP) for i in pins]

    def read(self):
        """
        Scans all pins and returns their active-low state as active-high integers.
        Returns:
            list: [0 or 1] for each button. 1 = pressed.
            Standard mapping: [0:Up, 1:Down, 2:Left, 3:Right, 4:Fire, 5:Alt, 6:Reset]
        """
        return [1 if p.value() == 0 else 0 for p in self.pad_pins]


# ==============================================================================
# ACCELERATED OLED DRIVER
# ==============================================================================
class FastOLED(framebuf.FrameBuffer):
    """
    Hardware-Accelerated SSD1306 OLED Driver with Double-Buffering capability.
    Inherits directly from MicroPython's C-level framebuf.FrameBuffer.
    
    --- INHERITED C-LEVEL DRAWING API ---
    pixel(x, y, color)
        Draws a single pixel. Color is 1 (white) or 0 (black).
        
    line(x1, y1, x2, y2, color)
        Draws a straight line between two points.
        
    hline(x, y, width, color) / vline(x, y, height, color)
        Optimized functions for purely horizontal or vertical lines.
        
    rect(x, y, width, height, color)
        Draws the outline of a rectangle.
        
    fill_rect(x, y, width, height, color)
        Draws a solid, filled rectangle.
        
    ellipse(x, y, x_radius, y_radius, color, filled=False)
        Draws an ellipse or circle. 'filled' is a boolean.
        
    text(string, x, y, color)
        Draws basic 8x8 pixel text to the screen.
        
    blit(fbuf, x, y, key=-1)
        Draws another FrameBuffer onto this one at coordinates x, y. 
        'key' specifies a color to treat as transparent (e.g., key=0).
    """
    
    def __init__(self, i2c, address=0x3c, rotation=0):
        """
        Initializes the display matrix and memory buffers.
        Parameters:
            i2c (machine.I2C): The initialized I2C bus object.
            address (int): The I2C hex address of the OLED (usually 0x3c).
            rotation (int): 0, 90, 180, or 270 degrees.
        """
        self.i2c = i2c
        self.addr = address
        self.rot = rotation
        
        # Handle portrait vs landscape dimensions
        if self.rot == 90 or self.rot == 270:
            self.width, self.height = 32, 128
        else:
            self.width, self.height = 128, 32
        
        # Payload buffer includes the I2C control byte (0x40) at index 0
        self.payload = bytearray(513)
        self.payload[0] = 0x40 
        
        # The actual pixel data memory view (512 bytes)
        self.buffer = memoryview(self.payload)[1:] 
        
        # The secondary backup buffer for cinematic/static caching
        self.snapshot_buffer = bytearray(512)
        
        # Initialize the C-level framebuf over our active memory block
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        
        self._init_display()

    def _init_display(self):
        """ Sends the proprietary boot-up command sequence to the SSD1306 chip. """
        seg_remap = 0xA1 if self.rot != 180 else 0xA0
        com_scan = 0xC8 if self.rot != 180 else 0xC0
        init_cmds = [
            0xAE, 0xD5, 0x80, 0xA8, 0x1F, 0xD3, 0x00, 0x40, 
            0x8D, 0x14, 0x20, 0x00, seg_remap, com_scan, 
            0xDA, 0x02, 0x81, 0x8F, 0xD9, 0xF1, 0xDB, 0x40, 
            0xA4, 0xA6, 0xAF
        ]
        for cmd in init_cmds:
            self.i2c.writeto(self.addr, bytes([0x00, cmd]))

    def show(self):
        """ Pushes the active buffer payload over I2C to the physical OLED. """
        self.i2c.writeto(self.addr, self.payload)

    def take_snapshot(self):
        """ 
        Copies the current active display state into the secondary background buffer.
        Highly useful for freezing 3D scenes or creating complex UI overlays.
        """
        self.snapshot_buffer[:] = self.buffer[:]

    def restore_snapshot(self):
        """ Instantly overwrites the active buffer with the cached snapshot data. """
        self.buffer[:] = self.snapshot_buffer[:]
        
    def clear(self):
        """ Erases the active buffer (fills with black). """
        self.fill(0)
        
    @micropython.native
    def circle(self, x, y, radius, color=1, filled=False):
        """
        Convenience wrapper for a perfect circle.
        Parameters:
            x, y (int): Center coordinates.
            radius (int): Circle radius in pixels.
            color (int): 1 for white, 0 for black.
            filled (bool): True for a solid disk, False for an outline.
        """
        self.ellipse(x, y, radius, radius, color, filled)