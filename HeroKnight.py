from pico2d import *
import os
import game_framework



# self.vy(수직속도), self.g(중력), self.jump_speed(초기속도), self.ground_y(바닥 높이)
# self.air_vx(공중에서 유지할 수평 속도),


from state_machine import StateMachine

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)


PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM  = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS  = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS  = (RUN_SPEED_MPS * PIXEL_PER_METER)


TIME_PER_ACTION   = 0.5
ACTION_PER_TIME   = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8


GRAVITY_MPS2 = 9.8
GRAVITY_PPS2 = GRAVITY_MPS2 * PIXEL_PER_METER

# dt 스파이크 상한 (초) — 30fps보다 긴 프레임은 이 값까지만 처리
MAX_DT = 1.0 / 30.0



def right_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT
def right_up(e):    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_RIGHT
def left_down(e):   return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT
def left_up(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_LEFT

def space_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE
def jump_done(e):   return e[0] == 'JUMP_DONE'
def fall_done(e):   return e[0] == 'FALL_DONE'
def landed_run(e):   return e[0] == 'LANDED_RUN'     # 착지 + 이동중
def landed_idle(e):  return e[0] == 'LANDED_IDLE'    # 착지 + 정지


class Idle:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0
        self.boy.y = self.boy.ground_y
        self.boy.vy = 0
        self.boy.frame = 0
        self.boy.prev_time = get_time()
        self.boy.anim = self.boy.images
        self.boy.max_frames = len(self.boy.anim)

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT
        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames

    def draw(self):
        self.boy.draw_current_frame()



class Run:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        if right_down(e):
            self.boy.dir = 1
            self.boy.face_dir = 1
        elif left_down(e):
            self.boy.dir = -1
            self.boy.face_dir = -1
        self.boy.y = self.boy.ground_y
        self.boy.vy = 0
        self.boy.frame = 0
        self.boy.prev_time = get_time()
        self.boy.anim = self.boy.run_images
        self.boy.max_frames = len(self.boy.anim)

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * dt

        self.boy.x = max(self.boy.left_bound,
                         min(self.boy.x, self.boy.right_bound))

    def draw(self):
        self.boy.draw_current_frame()




class Jump:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.current_row = 2
        if not hasattr(self.boy, 'vy'):
            self.boy.vy = 0.0
        self.boy.vy = 600.0
        self.boy.anim = self.boy.jump_images
        self.boy.max_frames = len(self.boy.anim)
        self.boy.frame = 0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * dt

        self.boy.x = max(self.boy.left_bound,
                         min(self.boy.x, self.boy.right_bound))

        self.boy.vy -= GRAVITY_PPS2 * dt
        self.boy.y += self.boy.vy * dt

        if self.boy.vy <= 0:
            self.boy.state_machine.change_state(self.boy.FALL)

    def draw(self):
        self.boy.draw_current_frame()




class Fall:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.current_row = 3
        self.boy.anim = self.boy.fall_images
        self.boy.max_frames = len(self.boy.anim)
        self.boy.frame = 0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * dt

        self.boy.x = max(self.boy.left_bound,
                         min(self.boy.x, self.boy.right_bound))

        self.boy.vy -= GRAVITY_PPS2 * dt
        self.boy.y  += self.boy.vy * dt

        ground_y = getattr(self.boy, 'ground_y', 70)
        if self.boy.y <= ground_y:
            self.boy.y = ground_y
            self.boy.vy = 0.0
            if self.boy.dir == 0:
                self.boy.state_machine.change_state(self.boy.IDLE)
            else:
                self.boy.state_machine.change_state(self.boy.RUN)

    def draw(self):
        self.boy.draw_current_frame()






class Boy:
    def __init__(self):
        self.images = [load_image(p('HeroKnight', 'Idle', f'HeroKnight_Idle_{i}.png')) for i in range(8)]
        self.run_images = [load_image(p('HeroKnight', 'Run', f'HeroKnight_Run_{i}.png')) for i in range(10)]


        self.JUMP_LAST = 1
        self.FALL_LAST = 3
        self.jump_images = [load_image(p('HeroKnight', 'Jump', f'HeroKnight_Jump_{i}.png')) for i in range(self.JUMP_LAST + 1)]
        self.fall_images = [load_image(p('HeroKnight', 'Fall', f'HeroKnight_Fall_{i}.png')) for i in range(self.FALL_LAST + 1)]

        self.frame = 0.0
        self.fps = 10
        self.scale = 2.0
        self.x, self.y = 320, 80
        self.prev_time = get_time()

        self.dir = 0
        self.face_dir = 1
        self.left_bound, self.right_bound = 30, 770

        self.jump_idx = 0
        self.fall_idx = 0
        self.anim_acc = 0.0

        self.ground_y = self.y
        self.vy = 0.0
        self.g = -1200.0
        self.jump_speed = 600.0
        self.run_px_per_sec = 300.0
        self.air_vx = 0.0

        self.anim = self.images
        self.max_frames = len(self.anim)

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)

        self.rules = {
            self.IDLE: {
                right_down: self.RUN, left_down: self.RUN,
                space_down: self.JUMP,
            },
            self.RUN: {
                right_up: self.IDLE, left_up: self.IDLE,
                right_down: self.RUN, left_down: self.RUN,
                space_down: self.JUMP,
            },
            self.JUMP: {
                right_down: self.JUMP, left_down: self.JUMP,
                jump_done: self.FALL,
            },
            self.FALL: {
                right_down: self.FALL, left_down: self.FALL,
                landed_run: self.RUN,
                landed_idle: self.IDLE,
            },
        }

        self.state_machine = StateMachine(self.IDLE, self.rules)

    def draw_current_frame(self):
        fi = int(self.frame) % self.max_frames
        img = self.anim[fi]
        # 이미지 원본 크기에 scale 적용
        try:
            w, h = img.w, img.h
            tw, th = int(w * self.scale), int(h * self.scale)
        except:
            tw = th = None

        if self.face_dir == 1:
            if tw and th:
                img.draw(self.x, self.y, tw, th)
            else:
                img.draw(self.x, self.y)
        else:
            if tw and th:
                img.composite_draw(0, 'h', self.x, self.y, tw, th)
            else:
                img.composite_draw(0, 'h', self.x, self.y)

    def handle_event(self, e):
        self.state_machine.handle_state_event(('INPUT', e))
        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_RIGHT:
                self.dir = 1
                self.face_dir = 1
            elif e.key == SDLK_LEFT:
                self.dir = -1
                self.face_dir = -1
        if e.type == SDL_KEYUP:
            if e.key == SDLK_RIGHT and self.dir == 1:
                self.dir = 0
            if e.key == SDLK_LEFT and self.dir == -1:
                self.dir = 0

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()
