"""
================================================================================
HAL 9000: VECTOR BATTLEZONE v2.8 (FOV Targeting & Scaled Saucer)
Hardware: RP2350 (Pico 2) | I2C1: SDA=GP14, SCL=GP15
Requires: hal_engine_01.py
================================================================================
"""
import machine
import time
import math
import random
import gc
from HAL_Engine_01 import FastOLED, Gamepad

# ==============================================================================
# 3D MATH & VECTOR DEFINITIONS
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
    'G': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4)), ((2,4),(2,2)), ((1,2),(2,2))],
    'A': [((0,4),(0,0)), ((0,0),(2,0)), ((2,0),(2,4)), ((0,2),(2,2))],
    'M': [((0,4),(0,0)), ((0,0),(1,2)), ((1,2),(2,0)), ((2,0),(2,4))],
    'E': [((2,0),(0,0)), ((0,0),(0,4)), ((0,4),(2,4)), ((0,2),(2,2))],
    'O': [((0,0),(2,0)), ((2,0),(2,4)), ((2,4),(0,4)), ((0,4),(0,0))],
    'V': [((0,0),(1,4)), ((1,4),(2,0))],
    'R': [((0,0),(0,4)), ((0,0),(2,0)), ((2,0),(2,2)), ((2,2),(0,2)), ((0,2),(2,4))],
    ' ': []
}

def draw_vector_text(oled, text, start_x, start_y):
    for i, char in enumerate(str(text)):
        if char in VECTOR_FONT:
            for line in VECTOR_FONT[char]:
                oled.line(start_x + (i * 4) + line[0][0], start_y + line[0][1], 
                          start_x + (i * 4) + line[1][0], start_y + line[1][1], 1)

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
def get_sin(angle): return SIN_LUT[int((angle % 6.2831853) * 114.59155) % 720]

@micropython.native
def get_cos(angle): return COS_LUT[int((angle % 6.2831853) * 114.59155) % 720]

@micropython.native
def clip_z(x1, y1, z1, x2, y2, z2, near_z=0.1):
    if z1 < near_z and z2 < near_z: return None
    if z1 >= near_z and z2 >= near_z: return (x1, y1, z1, x2, y2, z2)
    if z1 < near_z:
        t = (near_z - z1) / (z2 - z1)
        x1 = x1 + (x2 - x1) * t; y1 = y1 + (y2 - y1) * t; z1 = near_z
    else:
        t = (near_z - z2) / (z1 - z2)
        x2 = x2 + (x1 - x2) * t; y2 = y2 + (y1 - y2) * t; z2 = near_z
    return (x1, y1, z1, x2, y2, z2)

@micropython.native
def clip_2d(x0, y0, x1, y1, xmin=0, ymin=0, xmax=99, ymax=31):
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
    def get_code(x, y):
        c = INSIDE
        if x < xmin: c |= LEFT
        elif x > xmax: c |= RIGHT
        if y < ymin: c |= BOTTOM
        elif y > ymax: c |= TOP
        return c
    c0, c1 = get_code(x0, y0), get_code(x1, y1)
    while True:
        if not (c0 | c1): return int(x0), int(y0), int(x1), int(y1)
        if c0 & c1: return None
        c_out = c0 if c0 else c1
        x, y = 0, 0
        if c_out & TOP: x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0); y = ymax
        elif c_out & BOTTOM: x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0); y = ymin
        elif c_out & RIGHT: y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0); x = xmax
        elif c_out & LEFT: y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0); x = xmin
        if c_out == c0: x0, y0 = x, y; c0 = get_code(x0, y0)
        else: x1, y1 = x, y; c1 = get_code(x1, y1)

@micropython.native
def draw_3d_line(oled, x1, y1, z1, x2, y2, z2, cx, cy, cz, cam_sin, cam_cos, cl_xmax=99, scx=50):
    dx1, dy1, dz1 = x1 - cx, y1 - cy, z1 - cz
    dx2, dy2, dz2 = x2 - cx, y2 - cy, z2 - cz
    rx1 = dx1 * cam_cos - dz1 * cam_sin; rz1 = dx1 * cam_sin + dz1 * cam_cos
    rx2 = dx2 * cam_cos - dz2 * cam_sin; rz2 = dx2 * cam_sin + dz2 * cam_cos
    clipped_z = clip_z(rx1, dy1, rz1, rx2, dy2, rz2)
    if not clipped_z: return
    cx1, cy1, cz1, cx2, cy2, cz2 = clipped_z
    FOV = 60
    sx1 = int(scx + (cx1 / cz1) * FOV); sy1 = int(16 - (cy1 / cz1) * FOV)
    sx2 = int(scx + (cx2 / cz2) * FOV); sy2 = int(16 - (cy2 / cz2) * FOV)
    clipped_screen = clip_2d(sx1, sy1, sx2, sy2, xmax=cl_xmax)
    if clipped_screen:
        oled.line(clipped_screen[0], clipped_screen[1], clipped_screen[2], clipped_screen[3], 1)

@micropython.native
def draw_3d_point(oled, x, y, z, cx, cy, cz, cam_sin, cam_cos):
    dx, dy, dz = x - cx, y - cy, z - cz
    rx = dx * cam_cos - dz * cam_sin; rz = dx * cam_sin + dz * cam_cos
    if rz > 0.1:
        sx = int(50 + (rx / rz) * 60); sy = int(16 - (dy / rz) * 60)
        if 0 <= sx < 99 and 0 <= sy < 32: oled.pixel(sx, sy, 1)

# ==============================================================================
# GAME ENTITIES
# ==============================================================================

class Tank:
    def __init__(self, x, z):
        self.x, self.z = float(x), float(z)
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
        dx, dz = px - self.x, pz - self.z
        actual_turn = 0.0
        if dx**2 + dz**2 < 20000: 
            target_yaw = math.atan2(dx, dz)
            yaw_diff = (target_yaw - self.yaw) % 6.283
            if yaw_diff > math.pi: yaw_diff -= 6.283
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
        tsin, tcos = get_sin(self.yaw), get_cos(self.yaw)
        for lx1, ly1, lz1, lx2, ly2, lz2 in self.model:
            wx1 = lx1 * tcos + lz1 * tsin + self.x; wz1 = -lx1 * tsin + lz1 * tcos + self.z
            wx2 = lx2 * tcos + lz2 * tsin + self.x; wz2 = -lx2 * tsin + lz2 * tcos + self.z
            draw_3d_line(oled, wx1, ly1, wz1, wx2, ly2, wz2, cx, cy, cz, cam_sin, cam_cos)

        ax, ay, az = 0.0, 5.5, -5.0 
        seg_len = 3.5 
        for i in range(1, 4):
            bend = self.sway * i 
            nx = ax + math.sin(bend) * seg_len
            ny = ay + math.cos(bend) * seg_len
            nz = az 
            wx1 = ax * tcos + az * tsin + self.x; wz1 = -ax * tsin + az * tcos + self.z
            wx2 = nx * tcos + nz * tsin + self.x; wz2 = -nx * tsin + nz * tcos + self.z
            draw_3d_line(oled, wx1, ay, wz1, wx2, ny, wz2, cx, cy, cz, cam_sin, cam_cos)
            ax, ay, az = nx, ny, nz

class Saucer:
    def __init__(self):
        self.active = False
        self.x = self.y = self.z = 0.0
        self.move_angle = 0.0
        self.zig_timer = 0
        
        # Base wide model
        raw_model = [
            (-3, 2, 3, 2), (-8, 0.5, -3, 2), (8, 0.5, 3, 2),           
            (-8, 0.5, 8, 0.5), (-8, -0.5, 8, -0.5),                    
            (-8, -0.5, -8, 0.5), (8, -0.5, 8, 0.5),                    
            (-3, -2, 3, -2), (-8, -0.5, -3, -2), (8, -0.5, 3, -2)      
        ]
        
        # HAL UPGRADE: Scale geometry to 70%
        self.model = [(a*0.7, b*0.7, c*0.7, d*0.7) for a, b, c, d in raw_model]

    def spawn(self, px, pz, pyaw):
        self.active = True
        # HAL UPGRADE: Spawns directly in front of player (+/- ~45 degrees)
        ang = pyaw + random.uniform(-0.8, 0.8)
        self.x = px + get_sin(ang) * 120
        self.z = pz + get_cos(ang) * 120
        self.y = 30.0 
        self.zig_timer = 0

    def update(self, px, pz):
        if not self.active: return False
        
        if self.y > 6.0:
            self.y -= 0.3
            
        self.zig_timer -= 1
        if self.zig_timer <= 0:
            self.zig_timer = random.randint(15, 45) 
            ang_to_player = math.atan2(px - self.x, pz - self.z)
            self.move_angle = ang_to_player + random.uniform(-0.8, 0.8)
            
        # HAL UPGRADE: Reduced speed to 1.5 for better playability
        self.x += get_sin(self.move_angle) * 1.5
        self.z += get_cos(self.move_angle) * 1.5
        
        dist_sq = (self.x - px)**2 + (self.z - pz)**2
        if dist_sq < 64: 
            return True 
        return False

    def draw(self, oled, cx, cy, cz, cam_sin, cam_cos, frames):
        if not self.active: return
        
        def draw_billboard_line(lx1, ly1, lx2, ly2):
            wx1 = self.x + lx1 * cam_cos; wy1 = self.y + ly1; wz1 = self.z - lx1 * cam_sin
            wx2 = self.x + lx2 * cam_cos; wy2 = self.y + ly2; wz2 = self.z - lx2 * cam_sin
            draw_3d_line(oled, wx1, wy1, wz1, wx2, wy2, wz2, cx, cy, cz, cam_sin, cam_cos)

        for lx1, ly1, lx2, ly2 in self.model:
            draw_billboard_line(lx1, ly1, lx2, ly2)
            
        for i in range(3):
            offset = i * 2.09 
            # Scaled interior sweep to match 70% model
            lx = math.sin(frames * 0.3 + offset) * 4.2 
            draw_billboard_line(lx, -0.35, lx, 0.35)

    def explode(self, cam_sin, cam_cos):
        deb = []
        for lx1, ly1, lx2, ly2 in self.model:
            wx1 = self.x + lx1 * cam_cos; wy1 = self.y + ly1; wz1 = self.z - lx1 * cam_sin
            wx2 = self.x + lx2 * cam_cos; wy2 = self.y + ly2; wz2 = self.z - lx2 * cam_sin
            deb.append([wx1, wy1, wz1, wx2, wy2, wz2, random.uniform(-3, 3), random.uniform(1, 5), random.uniform(-3, 3), random.randint(20, 40)])
        return deb


def build_static_world():
    ARENA = ["X.^.....^.X", ".X.......X.", "^....X....^", "...........", "...X...X...", "...........", "^....X....^", ".X.......X.", "X.^.....^.X"]
    lines = []
    for row_idx, row in enumerate(ARENA):
        for col_idx, char in enumerate(row):
            if char == '.': continue
            wx, wz = (col_idx - 5) * 40, (row_idx - 4) * 40
            if char == 'X': 
                s, h = 6, 14
                lines.append([wx, wz, [(wx-s, 0, wz-s, wx+s, 0, wz-s), (wx+s, 0, wz-s, wx+s, 0, wz+s), (wx+s, 0, wz+s, wx-s, 0, wz+s), (wx-s, 0, wz+s, wx-s, 0, wz-s), (wx-s, h, wz-s, wx+s, h, wz-s), (wx+s, h, wz-s, wx+s, h, wz+s), (wx+s, h, wz+s, wx-s, h, wz+s), (wx-s, h, wz+s, wx-s, h, wz-s), (wx-s, 0, wz-s, wx-s, h, wz-s), (wx+s, 0, wz-s, wx+s, h, wz-s), (wx+s, 0, wz+s, wx+s, h, wz+s), (wx-s, 0, wz+s, wx-s, h, wz+s)]])
            elif char == '^':
                s, h = 8, 18
                lines.append([wx, wz, [(wx-s, 0, wz-s, wx+s, 0, wz-s), (wx+s, 0, wz-s, wx+s, 0, wz+s), (wx+s, 0, wz+s, wx-s, 0, wz+s), (wx-s, 0, wz+s, wx-s, 0, wz-s), (wx-s, 0, wz-s, wx, h, wz), (wx+s, 0, wz-s, wx, h, wz), (wx+s, 0, wz+s, wx, h, wz), (wx-s, 0, wz+s, wx, h, wz)]])
    return lines

def generate_cracks():
    cracks = []
    targets = [(0,0), (127,0), (0,31), (127,31), (64,0), (64,31), (0,16), (127,16), (32,0), (96,0), (32,31), (96,31)]
    cx, cy = 64, 16 
    for tx, ty in targets:
        steps = 4; x1, y1 = cx, cy
        for i in range(1, steps + 1):
            t = i / steps; bx = cx + (tx - cx) * t; by = cy + (ty - cy) * t
            if i < steps: bx += random.uniform(-6, 6); by += random.uniform(-6, 6)
            cracks.append((int(x1), int(y1), int(bx), int(by)))
            x1, y1 = bx, by
    return cracks

# ==============================================================================
# MAIN GAME LOOP
# ==============================================================================

def run_battlezone():
    print("HAL 9000: Initializing Simulation v2.8 (Dot-Product Targeting)")
    i2c = machine.I2C(1, sda=machine.Pin(14), scl=machine.Pin(15), freq=1000000)
    oled = FastOLED(i2c)
    gamepad = Gamepad()
    
    px, py, pz, pyaw = 0.0, 3.0, 0.0, 0.0
    score, game_state, death_timer, player_fire_cooldown, level_clear_timer = 0, 0, 0, 0, 0
    
    static_objects = build_static_world()
    tanks = [Tank(random.choice([-30, 0, 30]), random.randint(60, 140)) for _ in range(3)]
    ground_dots = [[random.uniform(-150, 150), random.uniform(-150, 150)] for _ in range(60)]
    
    player_missiles, enemy_missiles, debris, cracks = [], [], [], []
    game_over_mesh = generate_3d_text_model("GAME OVER")
    
    ufo = Saucer()
    tanks_destroyed_counter = 0
    ufo_timer = 0
    
    debug_fps, frames, current_fps, last_time = False, 0, 0, time.ticks_ms()
    gc.collect() 
    
    try:
        while True:
            pad = gamepad.read()
            frames += 1
            now = time.ticks_ms()
            if time.ticks_diff(now, last_time) >= 1000:
                current_fps = frames; frames = 0; last_time = now

            if game_state == 3:
                if pad[6]:
                    px, py, pz, pyaw, score = 0.0, 3.0, 0.0, 0.0, 0
                    game_state, death_timer, player_fire_cooldown, level_clear_timer = 0, 0, 0, 0
                    tanks_destroyed_counter, ufo_timer = 0, 0
                    ufo.active = False
                    tanks = [Tank(random.choice([-30, 0, 30]), random.randint(60, 140)) for _ in range(3)]
                    player_missiles.clear(); enemy_missiles.clear(); debris.clear()
                    continue
                
                oled.restore_snapshot()
                tz = 30 + math.sin(frames * 0.3) * 3.0
                for lx1, ly1, lz1, lx2, ly2, lz2 in game_over_mesh:
                    draw_3d_line(oled, lx1, ly1, lz1 + tz, lx2, ly2, lz2 + tz, 0, 0, 0, 0.0, 1.0, cl_xmax=127, scx=64)
                oled.show()
                continue

            if game_state == 1:
                death_timer += 1
                if death_timer > 30: 
                    game_state = 2; death_timer = 0
                    oled.take_snapshot() 
            elif game_state == 2:
                death_timer += 1
                if death_timer > 60: game_state = 3

            cam_sin, cam_cos = get_sin(pyaw), get_cos(pyaw)
            
            if game_state == 0:
                
                if tanks_destroyed_counter >= 3 and not ufo.active:
                    if ufo_timer == 0:
                        ufo_timer = random.randint(75, 450) 
                    else:
                        ufo_timer -= 1
                        if ufo_timer <= 0:
                            ufo.spawn(px, pz, pyaw) # Passing pyaw so it spawns in front
                            tanks_destroyed_counter = 0
                            
                if ufo.active:
                    hit_player = ufo.update(px, pz)
                    if hit_player:
                        game_state = 1
                        oled.clear()
                        oled.hline(0, 16, 99, 1)
                        for dot in ground_dots: draw_3d_point(oled, dot[0], 0, dot[1], px, py, pz, cam_sin, cam_cos)
                        for obj in static_objects:
                            for lx1, ly1, lz1, lx2, ly2, lz2 in obj[2]: draw_3d_line(oled, lx1, ly1, lz1, lx2, ly2, lz2, px, py, pz, cam_sin, cam_cos)
                        for t in tanks: t.draw(oled, px, py, pz, cam_sin, cam_cos)
                        for d in debris: draw_3d_line(oled, d[0], d[1], d[2], d[3], d[4], d[5], px, py, pz, cam_sin, cam_cos)
                        ufo.draw(oled, px, py, pz, cam_sin, cam_cos, frames) 
                        
                        oled.fill_rect(100, 0, 28, 32, 0); oled.vline(99, 0, 32, 1) 
                        radar_cx, radar_cy = 114, 16; oled.pixel(radar_cx, radar_cy, 1) 
                        draw_vector_text(oled, f"{score:04d}", 102, 2)
                        
                        oled.take_snapshot()
                        oled.show()
                        cracks = generate_cracks()
                        continue
                
                # Player Controls
                if pad[0]: px += cam_sin * 2.0; pz += cam_cos * 2.0
                if pad[1]: px -= cam_sin * 2.0; pz -= cam_cos * 2.0
                if pad[2]: pyaw -= 0.12 
                if pad[3]: pyaw += 0.12 
                
                if player_fire_cooldown > 0: player_fire_cooldown -= 1
                
                # HAL UPGRADE: Dot-Product Smart Targeting System
                if pad[4] and len(player_missiles) < 3 and player_fire_cooldown == 0:
                    vy = 0.0
                    closest_dist = 999999
                    
                    for t in tanks:
                        d = math.sqrt((t.x - px)**2 + (t.z - pz)**2)
                        if d < closest_dist: closest_dist = d
                        
                    if ufo.active:
                        ufo_dist = math.sqrt((ufo.x - px)**2 + (ufo.z - pz)**2)
                        if ufo_dist < closest_dist:
                            # Verify Saucer is in front of the player using the Dot Product
                            # cam_sin and cam_cos represent the player's normalized forward vector
                            ux = (ufo.x - px) / ufo_dist
                            uz = (ufo.z - pz) / ufo_dist
                            dot_product = (cam_sin * ux) + (cam_cos * uz)
                            
                            # 0.707 is roughly +/- 45 degrees
                            if dot_product > 0.7:
                                time_to_hit = ufo_dist / 8.0 
                                if time_to_hit > 0:
                                    vy = (ufo.y - (py - 0.5)) / time_to_hit
                                
                    player_missiles.append([px, py-0.5, pz, pyaw, 25, vy]) 
                    player_fire_cooldown = 15

                for obj in static_objects:
                    ox, oz = obj[0], obj[1]
                    dx, dz = px - ox, pz - oz
                    dist_sq = dx**2 + dz**2
                    if dist_sq < 256: 
                        dist = math.sqrt(dist_sq)
                        if dist == 0: dist = 0.1 
                        overlap = 16.0 - dist
                        px += (dx / dist) * overlap
                        pz += (dz / dist) * overlap

                if len(tanks) == 0:
                    level_clear_timer += 1
                    if level_clear_timer > 120: 
                        for _ in range(3):
                            spawn_ang = pyaw + random.uniform(-1.0, 1.0)
                            dist = random.uniform(120, 180)
                            tanks.append(Tank(px + get_sin(spawn_ang)*dist, pz + get_cos(spawn_ang)*dist))
                        level_clear_timer = 0

                for t in tanks: 
                    fired = t.update(px, pz)
                    if fired and len(enemy_missiles) < 3: enemy_missiles.append([t.x, 4.5, t.z, t.yaw, 30])
                
                for m in player_missiles[:]:
                    hit = False
                    m_sin, m_cos = get_sin(m[3]), get_cos(m[3])
                    m[0] += m_sin * 8.0; m[2] += m_cos * 8.0; 
                    m[1] += m[5] 
                    m[4] -= 1
                    
                    if ufo.active:
                        if (m[0] - ufo.x)**2 + (m[2] - ufo.z)**2 < 100 and abs(m[1] - ufo.y) < 6.0:
                            hit = True
                            score += 500
                            debris.extend(ufo.explode(cam_sin, cam_cos))
                            ufo.active = False
                    
                    if not hit:
                        for t in tanks:
                            if (m[0] - t.x)**2 + (m[2] - t.z)**2 < 64:
                                hit = True
                                score += int(math.sqrt((px - t.x)**2 + (pz - t.z)**2)) * 10
                                if score > 9999: score = 9999
                                tsin, tcos = get_sin(t.yaw), get_cos(t.yaw)
                                for lx1, ly1, lz1, lx2, ly2, lz2 in t.model:
                                    wx1 = lx1 * tcos + lz1 * tsin + t.x; wz1 = -lx1 * tsin + lz1 * tcos + t.z
                                    wx2 = lx2 * tcos + lz2 * tsin + t.x; wz2 = -lx2 * tsin + lz2 * tcos + t.z
                                    debris.append([wx1, ly1, wz1, wx2, ly2, wz2, random.uniform(-1.5, 1.5), random.uniform(1.0, 3.0), random.uniform(-1.5, 1.5), random.randint(15, 30)])
                                tanks.remove(t)
                                tanks_destroyed_counter += 1
                                break
                    
                    if hit or m[4] <= 0:
                        if m in player_missiles: player_missiles.remove(m)
                        
                for em in enemy_missiles[:]:
                    em_sin, em_cos = get_sin(em[3]), get_cos(em[3])
                    em[0] += em_sin * 7.0; em[2] += em_cos * 7.0; em[4] -= 1
                    
                    if (em[0] - px)**2 + (em[2] - pz)**2 < 16:
                        game_state = 1
                        oled.clear()
                        oled.hline(0, 16, 99, 1)
                        for dot in ground_dots: draw_3d_point(oled, dot[0], 0, dot[1], px, py, pz, cam_sin, cam_cos)
                        for obj in static_objects:
                            for lx1, ly1, lz1, lx2, ly2, lz2 in obj[2]: draw_3d_line(oled, lx1, ly1, lz1, lx2, ly2, lz2, px, py, pz, cam_sin, cam_cos)
                        for t in tanks: t.draw(oled, px, py, pz, cam_sin, cam_cos)
                        if ufo.active: ufo.draw(oled, px, py, pz, cam_sin, cam_cos, frames)
                        for d in debris: draw_3d_line(oled, d[0], d[1], d[2], d[3], d[4], d[5], px, py, pz, cam_sin, cam_cos)
                        
                        oled.fill_rect(100, 0, 28, 32, 0)
                        oled.vline(99, 0, 32, 1) 
                        radar_cx, radar_cy = 114, 16
                        oled.pixel(radar_cx, radar_cy, 1) 
                        R_SCALE = 0.05
                        for obj in static_objects:
                            rx = (obj[0] - px) * cam_cos - (obj[1] - pz) * cam_sin; rz = (obj[0] - px) * cam_sin + (obj[1] - pz) * cam_cos
                            sx, sy = int(radar_cx + rx * R_SCALE), int(radar_cy - rz * R_SCALE)
                            if 101 <= sx <= 126 and 1 <= sy <= 30: oled.pixel(sx, sy, 1)
                        for t in tanks:
                            rx = (t.x - px) * cam_cos - (t.z - pz) * cam_sin; rz = (t.x - px) * cam_sin + (t.z - pz) * cam_cos
                            sx, sy = int(radar_cx + rx * R_SCALE), int(radar_cy - rz * R_SCALE)
                            if 101 <= sx <= 126 and 1 <= sy <= 30: oled.fill_rect(sx-1, sy-1, 3, 3, 1)
                        draw_vector_text(oled, f"{score:04d}", 102, 2)
                        
                        oled.take_snapshot()
                        oled.show()
                        cracks = generate_cracks()
                        break 
                    if em[4] <= 0:
                        if em in enemy_missiles: enemy_missiles.remove(em)
                        
                for dot in ground_dots:
                    if (dot[0] - px)**2 + (dot[1] - pz)**2 > 22500: 
                        ang = pyaw + random.uniform(-1.5, 1.5)
                        dot[0] = px + get_sin(ang) * 140; dot[1] = pz + get_cos(ang) * 140

            for d in debris[:]:
                d[0]+=d[6]; d[1]+=d[7]; d[2]+=d[8]; d[3]+=d[6]; d[4]+=d[7]; d[5]+=d[8]; d[7]-=0.25 
                if d[1]<0: d[1]=0
                if d[4]<0: d[4]=0
                d[9]-=1
                if d[9]<=0: debris.remove(d)

            # --- ACTIVE RENDERING ---
            if game_state == 0:
                oled.clear()
                oled.hline(0, 16, 99, 1)
                for dot in ground_dots: draw_3d_point(oled, dot[0], 0, dot[1], px, py, pz, cam_sin, cam_cos)
                for obj in static_objects:
                    for lx1, ly1, lz1, lx2, ly2, lz2 in obj[2]: draw_3d_line(oled, lx1, ly1, lz1, lx2, ly2, lz2, px, py, pz, cam_sin, cam_cos)
                for t in tanks: t.draw(oled, px, py, pz, cam_sin, cam_cos)
                if ufo.active: ufo.draw(oled, px, py, pz, cam_sin, cam_cos, frames)
                for m in player_missiles + enemy_missiles:
                    s = 1.5; msin, mcos = get_sin(m[3]), get_cos(m[3])
                    draw_3d_line(oled, -s*mcos+m[0], m[1]+s, s*msin+m[2], s*mcos+m[0], m[1]+s, -s*msin+m[2], px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, -s*mcos+m[0], m[1]-s, s*msin+m[2], s*mcos+m[0], m[1]-s, -s*msin+m[2], px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, -s*mcos+m[0], m[1]-s, s*msin+m[2], -s*mcos+m[0], m[1]+s, s*msin+m[2], px, py, pz, cam_sin, cam_cos)
                    draw_3d_line(oled, s*mcos+m[0], m[1]-s, -s*msin+m[2], s*mcos+m[0], m[1]+s, -s*msin+m[2], px, py, pz, cam_sin, cam_cos)
                for d in debris: draw_3d_line(oled, d[0], d[1], d[2], d[3], d[4], d[5], px, py, pz, cam_sin, cam_cos)
                
                oled.fill_rect(100, 0, 28, 32, 0)
                oled.vline(99, 0, 32, 1) 
                radar_cx, radar_cy = 114, 16
                oled.pixel(radar_cx, radar_cy, 1) 
                R_SCALE = 0.05
                for obj in static_objects:
                    rx=(obj[0]-px)*cam_cos-(obj[1]-pz)*cam_sin; rz=(obj[0]-px)*cam_sin+(obj[1]-pz)*cam_cos
                    sx, sy = int(radar_cx+rx*R_SCALE), int(radar_cy-rz*R_SCALE)
                    if 101<=sx<=126 and 1<=sy<=30: oled.pixel(sx,sy,1)
                for t in tanks:
                    rx=(t.x-px)*cam_cos-(t.z-pz)*cam_sin; rz=(t.x-px)*cam_sin+(t.z-pz)*cam_cos
                    sx, sy = int(radar_cx+rx*R_SCALE), int(radar_cy-rz*R_SCALE)
                    if 101<=sx<=126 and 1<=sy<=30: oled.fill_rect(sx-1,sy-1,3,3,1)
                for em in enemy_missiles:
                    if (frames % 4) < 2: 
                        rx=(em[0]-px)*cam_cos-(em[2]-pz)*cam_sin; rz=(em[0]-px)*cam_sin+(em[2]-pz)*cam_cos
                        sx, sy = int(radar_cx+rx*R_SCALE), int(radar_cy-rz*R_SCALE)
                        if 101<=sx<=126 and 1<=sy<=30: oled.pixel(sx,sy,1)
                        
                if ufo.active and (frames % 4) < 2: 
                    rx=(ufo.x-px)*cam_cos-(ufo.z-pz)*cam_sin; rz=(ufo.x-px)*cam_sin+(ufo.z-pz)*cam_cos
                    sx, sy = int(radar_cx+rx*R_SCALE), int(radar_cy-rz*R_SCALE)
                    if 101<=sx<=126 and 1<=sy<=30: oled.hline(sx-1, sy, 3, 1)
                        
                draw_vector_text(oled, f"{score:04d}", 102, 2)
                if debug_fps: draw_vector_text(oled, f"{current_fps:02d}", 118, 26)
                oled.show()

            elif game_state == 1:
                oled.restore_snapshot() 
                crack_limit = int((death_timer / 30) * len(cracks))
                for i in range(crack_limit):
                    cx1, cy1, cx2, cy2 = cracks[i]
                    clipped = clip_2d(cx1, cy1, cx2, cy2, xmax=127) 
                    if clipped: oled.line(clipped[0], clipped[1], clipped[2], clipped[3], 1)
                oled.show()

            elif game_state == 2:
                oled.restore_snapshot()
                t = min(1.0, death_timer / 60.0)
                tz, ty = 150 - (120 * t), -math.sin(t * math.pi) * 8.0 
                for lx1, ly1, lz1, lx2, ly2, lz2 in game_over_mesh:
                    draw_3d_line(oled, lx1, ly1 + ty, lz1 + tz, lx2, ly2 + ty, lz2 + tz, 0, 0, 0, 0.0, 1.0, cl_xmax=127, scx=64)
                oled.show()

    except KeyboardInterrupt:
        oled.clear(); oled.show()
        print("HAL 9000: Battlezone Terminated.")

run_battlezone()