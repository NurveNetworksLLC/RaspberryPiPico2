"""
================================================================================
HAL 9000: VECTOR BATTLEZONE v3.5 (Debris Geometry Patch)
Hardware: RP2350 (Pico 2) | I2C1: SDA=GP14, SCL=GP15
Requires: HAL_Engine_01.py
================================================================================
"""
import machine
import time
import math
import random
import gc
from HAL_Engine_01 import FastOLED, Gamepad

# ==============================================================================
# 3D MATH & FULL VECTOR FONT
# ==============================================================================

VECTOR_FONT = {
    '0': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,4),(0,0))],
    '1': [((1,0),(1,4)), ((0,1),(1,0)), ((0,4),(2,4))],
    '2': [((0,0),(2,0)), ((2,0),(2,2)), ((2,2),(0,2)), ((0,2),(0,4)), ((0,4),(2,4))],
    '3': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,2),(2,2))],
    '4': [((0,0),(0,2)), ((0,2),(2,2)), ((2,0),(2,4))],
    '5': [((2,0),(0,0)), ((0,0),(0,2)), ((0,2),(2,2)), ((2,2),(2,4)), ((2,4),(0,4))],
    '6': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4)), ((2,4),(2,2)), ((2,2),(0,2))],
    '7': [((0,0),(2,0)), ((2,0),(2,4))],
    '8': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,4),(0,0)), ((0,2),(2,2))],
    '9': [((2,4),(2,0)), ((2,0),(0,0)), ((0,0),(0,2)), ((0,2),(2,2))],
    'A': [((0,4),(0,0)), ((0,0),(2,0)), ((2,0),(2,4)), ((0,2),(2,2))],
    'B': [((0,0),(0,4)), ((0,0),(1.5,0)), ((1.5,0),(2,1)), ((2,1),(1.5,2)), ((1.5,2),(0,2)), ((1.5,2),(2,3)), ((2,3),(1.5,4)), ((1.5,4),(0,4))],
    'C': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4))],
    'D': [((0,0),(0,4)), ((0,0),(1.5,0)), ((1.5,0),(2,1)), ((2,1),(2,3)), ((2,3),(1.5,4)), ((1.5,4),(0,4))],
    'E': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4)), ((0,2),(1.5,2))],
    'F': [((0,4),(0,0)), ((0,0),(2,0)), ((0,2),(1.5,2))],
    'G': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4)), ((2,4),(2,2)), ((1,2),(2,2))],
    'H': [((0,0),(0,4)), ((2,0),(2,4)), ((0,2),(2,2))],
    'I': [((1,0),(1,4)), ((0,0),(2,0)), ((0,4),(2,4))],
    'J': [((0,3),(0,4)), ((0,4),(2,4)), ((2,4),(2,0)), ((2,0),(1,0))],
    'K': [((0,0),(0,4)), ((2,0),(0,2)), ((0,2),(2,4))],
    'L': [((0,0),(0,4)), ((0,4),(2,4))],
    'M': [((0,4),(0,0)), ((0,0),(1,2)), ((1,2),(2,0)), ((2,0),(2,4))],
    'N': [((0,4),(0,0)), ((0,0),(2,4)), ((2,4),(2,0))],
    'O': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,4),(0,0))],
    'P': [((0,4),(0,0)), ((0,0),(2,0)), ((2,0),(2,2)), ((2,2),(0,2))],
    'Q': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,4),(0,0)), ((1,3),(2,4))],
    'R': [((0,4),(0,0)), ((0,0),(2,0)), ((2,0),(2,2)), ((2,2),(0,2)), ((1,2),(2,4))],
    'S': [((2,0),(0,0)), ((0,0),(0,2)), ((0,2),(2,2)), ((2,2),(2,4)), ((2,4),(0,4))],
    'T': [((0,0),(2,0)), ((1,0),(1,4))],
    'U': [((0,0),(0,4)), ((0,4),(2,4)), ((2,4),(2,0))],
    'V': [((0,0),(1,4)), ((1,4),(2,0))],
    'W': [((0,0),(0,4)), ((0,4),(1,2)), ((1,2),(2,4)), ((2,4),(2,0))],
    'X': [((0,0),(2,4)), ((2,0),(0,4))],
    'Y': [((0,0),(1,2)), ((2,0),(1,2)), ((1,2),(1,4))],
    'Z': [((0,0),(2,0)), ((2,0),(0,4)), ((0,4),(2,4))],
    '-': [((0,2),(2,2))],
    '.': [((1,4),(1,4))],
    ' ': []
}

def draw_vector_text(oled, text, start_x, start_y, scale=1):
    for i, char in enumerate(str(text)):
        if char in VECTOR_FONT:
            for line in VECTOR_FONT[char]:
                oled.line(int(start_x + (i * 4 * scale) + line[0][0] * scale), 
                          int(start_y + line[0][1] * scale), 
                          int(start_x + (i * 4 * scale) + line[1][0] * scale), 
                          int(start_y + line[1][1] * scale), 1)

def draw_invader(oled, x, y):
    lines = [
        (2, 0, 1), (8, 0, 1), (3, 1, 1), (7, 1, 1), 
        (2, 2, 7), (1, 3, 2), (4, 3, 3), (8, 3, 2), 
        (0, 4, 11), (0, 5, 1), (2, 5, 7), (10, 5, 1), 
        (0, 6, 1), (2, 6, 1), (8, 6, 1), (10, 6, 1), 
        (3, 7, 2), (6, 7, 2)
    ]
    for lx, ly, ll in lines:
        oled.hline(x + lx, y + ly, ll, 1)

def generate_3d_text_model(text):
    lines = []
    scale = 1.5 
    char_spacing = 4
    start_x = -(len(text) * char_spacing / 2.0)
    for i, char in enumerate(text):
        if char in VECTOR_FONT:
            for line in VECTOR_FONT[char]:
                lx1 = (start_x + (i * char_spacing) + line[0][0]) * scale
                ly1 = (2 - line[0][1]) * scale 
                lx2 = (start_x + (i * char_spacing) + line[1][0]) * scale
                ly2 = (2 - line[1][1]) * scale
                lines.append((lx1, ly1, 0, lx2, ly2, 0))
    return lines

SIN_LUT = [math.sin(i * math.pi / 360.0) for i in range(720)]
COS_LUT = [math.cos(i * math.pi / 360.0) for i in range(720)]

@micropython.native
def get_sin(angle): 
    return SIN_LUT[int((angle % 6.2831853) * 114.59155) % 720]

@micropython.native
def get_cos(angle): 
    return COS_LUT[int((angle % 6.2831853) * 114.59155) % 720]

@micropython.native
def clip_z(x1, y1, z1, x2, y2, z2, near_z=0.1):
    if z1 < near_z and z2 < near_z: 
        return None
    if z1 >= near_z and z2 >= near_z: 
        return (x1, y1, z1, x2, y2, z2)
    if z1 < near_z:
        t = (near_z - z1) / (z2 - z1)
        x1 = x1 + (x2 - x1) * t
        y1 = y1 + (y2 - y1) * t
        z1 = near_z
    else:
        t = (near_z - z2) / (z1 - z2)
        x2 = x2 + (x1 - x2) * t
        y2 = y2 + (y1 - y2) * t
        z2 = near_z
    return (x1, y1, z1, x2, y2, z2)

@micropython.native
def clip_2d(x0, y0, x1, y1, xmin=0, ymin=0, xmax=99, ymax=31):
    INSIDE = 0
    LEFT = 1
    RIGHT = 2
    BOTTOM = 4
    TOP = 8
    
    def get_code(x, y):
        c = INSIDE
        if x < xmin: 
            c |= LEFT
        elif x > xmax: 
            c |= RIGHT
        if y < ymin: 
            c |= BOTTOM
        elif y > ymax: 
            c |= TOP
        return c
        
    c0 = get_code(x0, y0)
    c1 = get_code(x1, y1)
    
    while True:
        if not (c0 | c1): 
            return int(x0), int(y0), int(x1), int(y1)
        if c0 & c1: 
            return None
            
        c_out = c0 if c0 else c1
        x = 0
        y = 0
        
        if c_out & TOP: 
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0) if y1 != y0 else x0
            y = ymax
        elif c_out & BOTTOM: 
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0) if y1 != y0 else x0
            y = ymin
        elif c_out & RIGHT: 
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0) if x1 != x0 else y0
            x = xmax
        elif c_out & LEFT: 
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0) if x1 != x0 else y0
            x = xmin
            
        if c_out == c0: 
            x0 = x
            y0 = y
            c0 = get_code(x0, y0)
        else: 
            x1 = x
            y1 = y
            c1 = get_code(x1, y1)

@micropython.native
def draw_3d_line(oled, x1, y1, z1, x2, y2, z2, cx, cy, cz, cam_sin, cam_cos, cl_xmax=99, scx=50):
    dx1 = x1 - cx
    dy1 = y1 - cy
    dz1 = z1 - cz
    dx2 = x2 - cx
    dy2 = y2 - cy
    dz2 = z2 - cz
    
    rx1 = dx1 * cam_cos - dz1 * cam_sin
    rz1 = dx1 * cam_sin + dz1 * cam_cos
    rx2 = dx2 * cam_cos - dz2 * cam_sin
    rz2 = dx2 * cam_sin + dz2 * cam_cos
    
    clipped_z = clip_z(rx1, dy1, rz1, rx2, dy2, rz2)
    if not clipped_z: 
        return
        
    cx1, cy1, cz1, cx2, cy2, cz2 = clipped_z
    FOV = 60
    sx1 = int(scx + (cx1 / cz1) * FOV)
    sy1 = int(16 - (cy1 / cz1) * FOV)
    sx2 = int(scx + (cx2 / cz2) * FOV)
    sy2 = int(16 - (cy2 / cz2) * FOV)
    
    clipped_screen = clip_2d(sx1, sy1, sx2, sy2, xmax=cl_xmax)
    if clipped_screen: 
        oled.line(clipped_screen[0], clipped_screen[1], clipped_screen[2], clipped_screen[3], 1)

@micropython.native
def draw_3d_point(oled, x, y, z, cx, cy, cz, cam_sin, cam_cos):
    dx = x - cx
    dy = y - cy
    dz = z - cz
    rx = dx * cam_cos - dz * cam_sin
    rz = dx * cam_sin + dz * cam_cos
    if rz > 0.1:
        sx = int(50 + (rx / rz) * 60)
        sy = int(16 - (dy / rz) * 60)
        if 0 <= sx < 99 and 0 <= sy < 32: 
            oled.pixel(sx, sy, 1)

# ==============================================================================
# GAME ENTITIES
# ==============================================================================
class Tank:
    def __init__(self, x, z):
        self.x = float(x)
        self.z = float(z)
        self.yaw = random.uniform(0, 6.28)
        self.cooldown = random.randint(30, 90)
        self.sway = 0.0
        self.sway_vel = 0.0
        o = 1.5 
        self.model = [
            (-4, o, -6, 4, o, -6), (4, o, -6, 4, o, 6), (4, o, 6, -4, o, 6), (-4, o, 6, -4, o, -6),
            (-3, o+4, -6, 3, o+4, -6), (3, o+4, -6, 3, o+4, 2), (3, o+4, 2, -3, o+4, 2), (-3, o+4, 2, -3, o+4, -6),
            (-4, o, -6, -3, o+4, -6), (4, o, -6, 3, o+4, -6), (-4, o, 6, -3, o+4, 2), (4, o, 6, 3, o+4, 2),
            (0, o+3, 2, 0, o+3, 10) 
        ]
        
    def update(self, px, pz):
        dx = px - self.x
        dz = pz - self.z
        actual_turn = 0.0
        
        if dx**2 + dz**2 < 20000: 
            target_yaw = math.atan2(dx, dz)
            yaw_diff = (target_yaw - self.yaw) % 6.283
            if yaw_diff > math.pi: 
                yaw_diff -= 6.283
                
            if abs(yaw_diff) > 0.1: 
                actual_turn = 0.04 if yaw_diff > 0 else -0.04
                self.yaw += actual_turn
            else:
                self.cooldown -= 1
                if self.cooldown <= 0:
                    self.cooldown = 45 
                    return True 
                    
        self.sway_vel -= actual_turn * 0.8  
        self.sway_vel += random.uniform(-0.02, 0.02)
        self.sway_vel -= self.sway * 0.15 
        self.sway_vel *= 0.85             
        self.sway += self.sway_vel
        self.x += get_sin(self.yaw) * 0.4
        self.z += get_cos(self.yaw) * 0.4
        return False
        
    def draw(self, oled, cx, cy, cz, cam_sin, cam_cos):
        tsin = get_sin(self.yaw)
        tcos = get_cos(self.yaw)
        
        for lx1, ly1, lz1, lx2, ly2, lz2 in self.model:
            wx1 = lx1 * tcos + lz1 * tsin + self.x
            wz1 = -lx1 * tsin + lz1 * tcos + self.z
            wx2 = lx2 * tcos + lz2 * tsin + self.x
            wz2 = -lx2 * tsin + lz2 * tcos + self.z
            draw_3d_line(oled, wx1, ly1, wz1, wx2, ly2, wz2, cx, cy, cz, cam_sin, cam_cos)
            
        ax = 0.0
        ay = 5.5
        az = -5.0 
        seg_len = 3.5 
        for i in range(1, 4):
            bend = self.sway * i 
            nx = ax + math.sin(bend) * seg_len
            ny = ay + math.cos(bend) * seg_len
            nz = az 
            wx1 = ax * tcos + az * tsin + self.x
            wz1 = -ax * tsin + az * tcos + self.z
            wx2 = nx * tcos + nz * tsin + self.x
            wz2 = -nx * tsin + nz * tcos + self.z
            draw_3d_line(oled, wx1, ay, wz1, wx2, ny, wz2, cx, cy, cz, cam_sin, cam_cos)
            ax = nx
            ay = ny
            az = nz

class Saucer:
    def __init__(self):
        self.active = False
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.move_angle = 0.0
        self.zig_timer = 0
        raw_model = [(-3, 2, 3, 2), (-8, 0.5, -3, 2), (8, 0.5, 3, 2), (-8, 0.5, 8, 0.5), (-8, -0.5, 8, -0.5), (-8, -0.5, -8, 0.5), (8, -0.5, 8, 0.5), (-3, -2, 3, -2), (-8, -0.5, -3, -2), (8, -0.5, 3, -2)]
        self.model = [(a*0.7, b*0.7, c*0.7, d*0.7) for a, b, c, d in raw_model]
        
    def spawn(self, px, pz, pyaw):
        self.active = True
        ang = pyaw + random.uniform(-0.8, 0.8)
        self.x = px + get_sin(ang) * 120
        self.z = pz + get_cos(ang) * 120
        self.y = 30.0
        self.zig_timer = 0
        
    def update(self, px, pz):
        if not self.active: 
            return False
        if self.y > 6.0: 
            self.y -= 0.3
            
        self.zig_timer -= 1
        if self.zig_timer <= 0:
            self.zig_timer = random.randint(15, 45) 
            ang_to_player = math.atan2(px - self.x, pz - self.z)
            self.move_angle = ang_to_player + random.uniform(-0.8, 0.8)
            
        self.x += get_sin(self.move_angle) * 1.5
        self.z += get_cos(self.move_angle) * 1.5
        if (self.x - px)**2 + (self.z - pz)**2 < 64: 
            return True 
        return False
        
    def draw(self, oled, cx, cy, cz, cam_sin, cam_cos, frames):
        if not self.active: 
            return
            
        def draw_billboard_line(lx1, ly1, lx2, ly2):
            wx1 = self.x + lx1 * cam_cos
            wy1 = self.y + ly1
            wz1 = self.z - lx1 * cam_sin
            wx2 = self.x + lx2 * cam_cos
            wy2 = self.y + ly2
            wz2 = self.z - lx2 * cam_sin
            draw_3d_line(oled, wx1, wy1, wz1, wx2, wy2, wz2, cx, cy, cz, cam_sin, cam_cos)
            
        for lx1, ly1, lx2, ly2 in self.model: 
            draw_billboard_line(lx1, ly1, lx2, ly2)
            
        for i in range(3):
            lx = math.sin(frames * 0.3 + i * 2.09) * 4.2 
            draw_billboard_line(lx, -0.35, lx, 0.35)
            
    def explode(self, cam_sin, cam_cos):
        deb = []
        for lx1, ly1, lx2, ly2 in self.model:
            wx1 = self.x + lx1 * cam_cos
            wy1 = self.y + ly1
            wz1 = self.z - lx1 * cam_sin
            wx2 = self.x + lx2 * cam_cos
            wy2 = self.y + ly2
            wz2 = self.z - lx2 * cam_sin
            deb.append([wx1, wy1, wz1, wx2, wy2, wz2, random.uniform(-3, 3), random.uniform(1, 5), random.uniform(-3, 3), random.randint(20, 40)])
        return deb

def build_static_world():
    ARENA = ["X.^.....^.X", ".X.......X.", "^....X....^", "...........", "...X...X...", "...........", "^....X....^", ".X.......X.", "X.^.....^.X"]
    lines = []
    for row_idx, row in enumerate(ARENA):
        for col_idx, char in enumerate(row):
            if char == '.': 
                continue
            wx = (col_idx - 5) * 40
            wz = (row_idx - 4) * 40
            if char == 'X': 
                s = 6
                h = 14
                lines.append([wx, wz, [(wx-s, 0, wz-s, wx+s, 0, wz-s), (wx+s, 0, wz-s, wx+s, 0, wz+s), (wx+s, 0, wz+s, wx-s, 0, wz+s), (wx-s, 0, wz+s, wx-s, 0, wz-s), (wx-s, h, wz-s, wx+s, h, wz-s), (wx+s, h, wz-s, wx+s, h, wz+s), (wx+s, h, wz+s, wx-s, h, wz+s), (wx-s, h, wz+s, wx-s, h, wz-s), (wx-s, 0, wz-s, wx-s, h, wz-s), (wx+s, 0, wz-s, wx+s, h, wz-s), (wx+s, 0, wz+s, wx+s, h, wz+s), (wx-s, 0, wz+s, wx-s, h, wz+s)]])
            elif char == '^':
                s = 8
                h = 18
                lines.append([wx, wz, [(wx-s, 0, wz-s, wx+s, 0, wz-s), (wx+s, 0, wz-s, wx+s, 0, wz+s), (wx+s, 0, wz+s, wx-s, 0, wz+s), (wx-s, 0, wz+s, wx-s, 0, wz-s), (wx-s, 0, wz-s, wx, h, wz), (wx+s, 0, wz-s, wx, h, wz), (wx+s, 0, wz+s, wx, h, wz), (wx-s, 0, wz+s, wx, h, wz)]])
    return lines

def generate_cracks():
    cracks = []
    for tx, ty in [(0,0), (127,0), (0,31), (127,31), (64,0), (64,31), (0,16), (127,16), (32,0), (96,0), (32,31), (96,31)]:
        x1 = 64
        y1 = 16 
        for i in range(1, 5):
            bx = 64 + (tx - 64) * (i/4)
            by = 16 + (ty - 16) * (i/4)
            if i < 4: 
                bx += random.uniform(-6, 6)
                by += random.uniform(-6, 6)
            cracks.append((int(x1), int(y1), int(bx), int(by)))
            x1 = bx
            y1 = by
    return cracks

# ==============================================================================
# MAIN ENGINE
# ==============================================================================
def run_battlezone():
    i2c = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(15), freq=1000000)
    oled = FastOLED(i2c)
    gamepad = Gamepad()
    
    game_state = 4 
    score = 0 
    high_scores = [10000, 7500, 5000]
    recent_score_index = -1
    px = 0.0
    py = 3.0
    pz = 0.0
    pyaw = 0.0
    
    death_timer = 0
    player_fire_cooldown = 0
    level_clear_timer = 0
    tanks_destroyed_counter = 0
    ufo_timer = 0
    
    frames = 0
    last_state_time = time.ticks_ms()
    
    static_objects = build_static_world()
    tanks = []
    ground_dots = [[random.uniform(-150, 150), random.uniform(-150, 150)] for _ in range(60)]
    player_missiles = []
    enemy_missiles = []
    debris = []
    cracks = []
    
    game_over_mesh = generate_3d_text_model("GAME OVER")
    ufo = Saucer()
    
    def reset_game():
        nonlocal px, py, pz, pyaw, score, death_timer, player_fire_cooldown, level_clear_timer
        nonlocal tanks_destroyed_counter, ufo_timer, tanks, player_missiles, enemy_missiles, debris
        nonlocal recent_score_index
        
        px = 0.0
        py = 3.0
        pz = 0.0
        pyaw = 0.0
        score = 0
        death_timer = 0
        player_fire_cooldown = 0
        level_clear_timer = 0
        tanks_destroyed_counter = 0
        ufo_timer = 0
        recent_score_index = -1
        
        ufo.active = False
        tanks = [Tank(random.choice([-30, 0, 30]), random.randint(60, 140)) for _ in range(3)]
        player_missiles.clear()
        enemy_missiles.clear()
        debris.clear()
    
    def check_high_score(s):
        nonlocal recent_score_index
        high_scores.append(s)
        high_scores.sort(reverse=True)
        while len(high_scores) > 3: 
            high_scores.pop()
            
        if s in high_scores:
            recent_score_index = high_scores.index(s)
        else:
            recent_score_index = -1

    gc.collect() 
    
    try:
        while True:
            pad = gamepad.read()
            frames += 1
            now = time.ticks_ms()

            if game_state == 4:
                oled.clear()
                draw_vector_text(oled, "RASPBERRY", 28, 2, scale=2)
                draw_vector_text(oled, "ZONE 3D", 36, 12, scale=2)
                if (frames % 30) < 15: 
                    draw_vector_text(oled, "PRESS START", 20, 22, scale=2)
                oled.show()
                
                if time.ticks_diff(now, last_state_time) > 10000:
                    game_state = 5
                    last_state_time = now
                if pad[6]:
                    reset_game()
                    game_state = 0

            elif game_state == 5:
                oled.clear()
                draw_vector_text(oled, "HIGH SCORES", 42, 2)
                for idx, val in enumerate(high_scores):
                    draw_vector_text(oled, f"{idx+1}. {val:05d}", 42, 12 + (idx * 7))
                    if idx == recent_score_index and (frames % 30) < 22:
                        draw_invader(oled, 26, 11 + (idx * 7))
                oled.show()
                
                if time.ticks_diff(now, last_state_time) > 10000:
                    game_state = 4
                    last_state_time = now
                if pad[6]:
                    reset_game()
                    game_state = 0

            elif game_state == 3:
                oled.restore_snapshot()
                tz = 30 + math.sin(frames * 0.15) * 10.0
                for lx1, ly1, lz1, lx2, ly2, lz2 in game_over_mesh:
                    draw_3d_line(oled, lx1, ly1, lz1 + tz, lx2, ly2, lz2 + tz, 0, 0, 0, 0.0, 1.0, cl_xmax=127, scx=64)
                oled.show()
                
                if time.ticks_diff(now, last_state_time) > 5000 or pad[6]:
                    check_high_score(score)
                    game_state = 5
                    last_state_time = now

            elif game_state == 1:
                death_timer += 1
                oled.restore_snapshot() 
                
                crack_limit = min(len(cracks), int((death_timer / 60.0) * len(cracks)))
                for i in range(crack_limit):
                    cx1, cy1, cx2, cy2 = cracks[i]
                    clipped = clip_2d(cx1, cy1, cx2, cy2, xmax=127) 
                    if clipped: 
                        oled.line(clipped[0], clipped[1], clipped[2], clipped[3], 1)
                oled.show()
                
                if death_timer >= 60: 
                    game_state = 2
                    death_timer = 0
            
            elif game_state == 2:
                death_timer += 1
                oled.restore_snapshot()
                t = min(1.0, death_timer / 60.0)
                tz = 150 - (120 * t)
                ty = -math.sin(t * math.pi) * 8.0 
                for lx1, ly1, lz1, lx2, ly2, lz2 in game_over_mesh:
                    draw_3d_line(oled, lx1, ly1 + ty, lz1 + tz, lx2, ly2 + ty, lz2 + tz, 0, 0, 0, 0.0, 1.0, cl_xmax=127, scx=64)
                oled.show()
                
                if death_timer > 60: 
                    game_state = 3
                    last_state_time = now

            elif game_state == 0:
                cam_sin = get_sin(pyaw)
                cam_cos = get_cos(pyaw)
                
                if tanks_destroyed_counter >= 3 and not ufo.active:
                    if ufo_timer == 0: 
                        ufo_timer = random.randint(75, 450) 
                    else:
                        ufo_timer -= 1
                        if ufo_timer <= 0:
                            ufo.spawn(px, pz, pyaw)
                            tanks_destroyed_counter = 0
                            
                if ufo.active:
                    if ufo.update(px, pz):
                        game_state = 1
                        oled.take_snapshot()
                        cracks = generate_cracks()
                        death_timer = 0
                        continue
                
                if pad[0]: 
                    px += cam_sin * 2.0
                    pz += cam_cos * 2.0
                if pad[1]: 
                    px -= cam_sin * 2.0
                    pz -= cam_cos * 2.0
                if pad[2]: 
                    pyaw -= 0.12 
                if pad[3]: 
                    pyaw += 0.12 
                
                if player_fire_cooldown > 0: 
                    player_fire_cooldown -= 1
                    
                if pad[4] and len(player_missiles) < 3 and player_fire_cooldown == 0:
                    vy = 0.0
                    c_dist = 999999
                    for t in tanks:
                        d = math.sqrt((t.x-px)**2 + (t.z-pz)**2)
                        if d < c_dist: 
                            c_dist = d
                            
                    if ufo.active:
                        u_dist = math.sqrt((ufo.x-px)**2 + (ufo.z-pz)**2)
                        if u_dist < c_dist and ((cam_sin * (ufo.x-px)/u_dist) + (cam_cos * (ufo.z-pz)/u_dist)) > 0.7:
                            vy = (ufo.y - 2.5) / (u_dist / 8.0) if u_dist > 0 else 0
                            
                    player_missiles.append([px, py-0.5, pz, pyaw, 25, vy]) 
                    player_fire_cooldown = 15

                for obj in static_objects:
                    dx = px - obj[0]
                    dz = pz - obj[1]
                    dist_sq = dx**2 + dz**2
                    if dist_sq < 256: 
                        dist = math.sqrt(dist_sq) or 0.1 
                        overlap = 16.0 - dist
                        px += (dx / dist) * overlap
                        pz += (dz / dist) * overlap

                if len(tanks) == 0:
                    level_clear_timer += 1
                    if level_clear_timer > 120: 
                        for _ in range(3):
                            ang = pyaw + random.uniform(-1.0, 1.0)
                            dist = random.uniform(120, 180)
                            tanks.append(Tank(px + get_sin(ang)*dist, pz + get_cos(ang)*dist))
                        level_clear_timer = 0

                for t in tanks: 
                    if t.update(px, pz) and len(enemy_missiles) < 3: 
                        enemy_missiles.append([t.x, 4.5, t.z, t.yaw, 30])
                
                for m in player_missiles[:]:
                    hit = False
                    msin = get_sin(m[3])
                    mcos = get_cos(m[3])
                    m[0] += msin * 8.0
                    m[2] += mcos * 8.0
                    m[1] += m[5]
                    m[4] -= 1
                    
                    if ufo.active and (m[0] - ufo.x)**2 + (m[2] - ufo.z)**2 < 100 and abs(m[1] - ufo.y) < 6.0:
                        hit = True
                        score += 500
                        debris.extend(ufo.explode(cam_sin, cam_cos))
                        ufo.active = False
                    
                    if not hit:
                        for t in tanks:
                            if (m[0] - t.x)**2 + (m[2] - t.z)**2 < 64:
                                hit = True
                                score += int(math.sqrt((px - t.x)**2 + (pz - t.z)**2)) * 10
                                if score > 99999: 
                                    score = 99999
                                ts = get_sin(t.yaw)
                                tc = get_cos(t.yaw)
                                for l1, l2, l3, l4, l5, l6 in t.model:
                                    w1 = l1*tc + l3*ts + t.x
                                    w2 = -l1*ts + l3*tc + t.z
                                    w3 = l4*tc + l6*ts + t.x
                                    w4 = -l4*ts + l6*tc + t.z
                                    debris.append([w1, l2, w2, w3, l5, w4, random.uniform(-1.5, 1.5), random.uniform(1, 3), random.uniform(-1.5, 1.5), random.randint(15, 30)])
                                tanks.remove(t)
                                tanks_destroyed_counter += 1
                                break
                    if hit or m[4] <= 0:
                        if m in player_missiles: 
                            player_missiles.remove(m)
                        
                for em in enemy_missiles[:]:
                    emsin = get_sin(em[3])
                    emcos = get_cos(em[3])
                    em[0] += emsin * 7.0
                    em[2] += emcos * 7.0
                    em[4] -= 1
                    if (em[0] - px)**2 + (em[2] - pz)**2 < 16:
                        game_state = 1
                        oled.take_snapshot()
                        cracks = generate_cracks()
                        death_timer = 0
                        break 
                    if em[4] <= 0:
                        if em in enemy_missiles: 
                            enemy_missiles.remove(em)
                        
                for dot in ground_dots:
                    if (dot[0] - px)**2 + (dot[1] - pz)**2 > 22500: 
                        ang = pyaw + random.uniform(-1.5, 1.5)
                        dot[0] = px + get_sin(ang) * 140
                        dot[1] = pz + get_cos(ang) * 140

                for d in debris[:]:
                    d[0] += d[6]
                    d[1] += d[7]
                    d[2] += d[8]
                    d[3] += d[6]
                    d[4] += d[7]
                    d[5] += d[8]
                    d[7] -= 0.25 
                    if d[1] < 0: 
                        d[1] = 0
                    if d[4] < 0: 
                        d[4] = 0
                    d[9] -= 1
                    if d[9] <= 0: 
                        debris.remove(d)

                oled.clear()
                oled.hline(0, 16, 99, 1)
                
                for dot in ground_dots: 
                    draw_3d_point(oled, dot[0], 0, dot[1], px, py, pz, cam_sin, cam_cos)
                    
                for obj in static_objects:
                    for lx1, ly1, lz1, lx2, ly2, lz2 in obj[2]: 
                        draw_3d_line(oled, lx1, ly1, lz1, lx2, ly2, lz2, px, py, pz, cam_sin, cam_cos)
                        
                for t in tanks: 
                    t.draw(oled, px, py, pz, cam_sin, cam_cos)
                    
                if ufo.active: 
                    ufo.draw(oled, px, py, pz, cam_sin, cam_cos, frames)
                    
                for m in player_missiles + enemy_missiles:
                    s = 1.5
                    ms = get_sin(m[3])
                    mc = get_cos(m[3])
                    
                    wx1 = -s * mc + m[0]
                    wz1 = s * ms + m[2]
                    wx2 = s * mc + m[0]
                    wz2 = -s * ms + m[2]
                    yt = m[1] + s
                    yb = m[1] - s
                    
                    draw_3d_line(oled, wx1, yt, wz1, wx2, yt, wz2, px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, wx1, yb, wz1, wx2, yb, wz2, px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, wx1, yt, wz1, wx1, yb, wz1, px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, wx2, yt, wz2, wx2, yb, wz2, px, py, pz, cam_sin, cam_cos)
                    
                for d in debris: 
                    draw_3d_line(oled, d[0], d[1], d[2], d[3], d[4], d[5], px, py, pz, cam_sin, cam_cos)
                
                oled.fill_rect(100, 0, 28, 32, 0)
                oled.vline(99, 0, 32, 1) 
                
                radar_cx = 114
                radar_cy = 16
                r_scale = 0.05
                oled.pixel(radar_cx, radar_cy, 1) 
                
                for obj in static_objects:
                    rx = (obj[0]-px)*cam_cos - (obj[1]-pz)*cam_sin
                    rz = (obj[0]-px)*cam_sin + (obj[1]-pz)*cam_cos
                    sx = int(radar_cx + rx * r_scale)
                    sy = int(radar_cy - rz * r_scale)
                    if 101 <= sx <= 126 and 1 <= sy <= 30: 
                        oled.pixel(sx, sy, 1)
                        
                for t in tanks:
                    rx = (t.x-px)*cam_cos - (t.z-pz)*cam_sin
                    rz = (t.x-px)*cam_sin + (t.z-pz)*cam_cos
                    sx = int(radar_cx + rx * r_scale)
                    sy = int(radar_cy - rz * r_scale)
                    if 101 <= sx <= 126 and 1 <= sy <= 30: 
                        oled.fill_rect(sx-1, sy-1, 3, 3, 1)
                        
                for em in enemy_missiles:
                    if (frames % 4) < 2: 
                        rx = (em[0]-px)*cam_cos - (em[2]-pz)*cam_sin
                        rz = (em[0]-px)*cam_sin + (em[2]-pz)*cam_cos
                        sx = int(radar_cx + rx * r_scale)
                        sy = int(radar_cy - rz * r_scale)
                        if 101 <= sx <= 126 and 1 <= sy <= 30: 
                            oled.pixel(sx, sy, 1)
                            
                if ufo.active and (frames % 4) < 2: 
                    rx = (ufo.x-px)*cam_cos - (ufo.z-pz)*cam_sin
                    rz = (ufo.x-px)*cam_sin + (ufo.z-pz)*cam_cos
                    sx = int(radar_cx + rx * r_scale)
                    sy = int(radar_cy - rz * r_scale)
                    if 101 <= sx <= 126 and 1 <= sy <= 30: 
                        oled.hline(sx-1, sy, 3, 1)
                
                draw_vector_text(oled, f"{score:05d}", 102, 2)
                oled.show()

    except KeyboardInterrupt:
        oled.clear()
        oled.show()
        print("HAL 9000: System Terminated.")

run_battlezone()