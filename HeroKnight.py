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

ATTACK_DURATION = 0.45


TIME_PER_ACTION   = 0.5
ACTION_PER_TIME   = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8

ROLL_SPEED_PPS   = RUN_SPEED_PPS * 2.0
ROLL_DURATION    = 0.45
ROLL_COOLTIME    = 10.0                  #  구르기만 10초 쿨타임



GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

# dt 스파이크 상한 (초) — 30fps보다 긴 프레임은 이 값까지만 처리
MAX_DT = 1.0 / 30.0



def right_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT
def right_up(e):    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_RIGHT
def left_down(e):   return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT
def left_up(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_LEFT

def space_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE
def up_down(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_UP
def a_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_a
def s_down(e):      return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_s
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
        if not hasattr(self.boy, 'vy'):
            self.boy.vy = 0.0
        self.boy.vy = JUMP_SPEED_PPS
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


class Roll:
    def __init__(self, boy):
        self.boy = boy
        self.elapsed = 0.0
        self.move_dir = 0

    def enter(self, e):
        self.boy.anim = self.boy.roll_images
        self.boy.max_frames = len(self.boy.anim)
        self.boy.frame = 0
        self.elapsed = 0.0
        self.move_dir = self.boy.dir if self.boy.dir != 0 else self.boy.face_dir

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT: dt = MAX_DT

        self.elapsed += dt
        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames


        self.boy.x += self.move_dir * ROLL_SPEED_PPS * dt
        self.boy.x = max(self.boy.left_bound, min(self.boy.x, self.boy.right_bound))


        if self.elapsed >= ROLL_DURATION:
            next_state = self.boy.RUN if self.boy.dir != 0 else self.boy.IDLE
            self.boy.state_machine.change_state(next_state)

    def draw(self):
        self.boy.draw_current_frame()



class Attack:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        import random
        # 어떤 공격을 쓸지 결정(1회)
        self.pick = random.choice([1, 2])
        self.boy.frame = 0
        self.boy.prev_time = get_time()

        # 공격 중에는 수평 이동 정지
        self.saved_dir = self.boy.dir
        self.boy.dir = 0

        # 이번 공격 동안은 아직 한 번도 맞추지 않은 상태
        self.boy.did_hit = False

        self.boy.anim = self.boy.attack1 if self.pick == 1 else self.boy.attack2
        self.boy.max_frames = len(self.boy.anim)
        self.fps = self.boy.max_frames / ATTACK_DURATION

    def exit(self, e):
        # 이동키가 눌려 있었다면 원래 방향 복구
        self.boy.dir = self.saved_dir

    def do(self):

        now = get_time()
        dt = min(now - self.boy.prev_time, MAX_DT)
        self.boy.prev_time = now
        self.boy.frame += self.fps * dt
        if self.boy.frame >= self.boy.max_frames:

            if self.boy.dir == 0:
                self.boy.state_machine.change_state(self.boy.IDLE)
            else:
                self.boy.state_machine.change_state(self.boy.RUN)

    def draw(self):
        self.boy.draw_current_frame()




class Block:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.vy = 0.0
        self.boy.y = self.boy.ground_y
        self.boy.frame = 0
        self.boy.prev_time = get_time()
        self.boy.anim = self.boy.block_idle_images
        self.boy.max_frames = len(self.boy.anim)

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT
        self.boy.frame = (
            self.boy.frame
            + self.boy.max_frames * ACTION_PER_TIME * dt
        ) % self.boy.max_frames

    def draw(self):
        self.boy.draw_current_frame()






class Boy:
    def __init__(self):
        self.images = [load_image(p('HeroKnight', 'Idle', f'HeroKnight_Idle_{i}.png')) for i in range(8)]
        self.run_images = [load_image(p('HeroKnight', 'Run', f'HeroKnight_Run_{i}.png')) for i in range(10)]
        self.roll_images = [load_image(p('HeroKnight', 'Roll', f'HeroKnight_Roll_{i}.png')) for i in range(9)]
        self.attack1 = [load_image(p('HeroKnight', 'Attack1', f'HeroKnight_Attack1_{i}.png')) for i in range(6)]
        self.attack2 = [load_image(p('HeroKnight', 'Attack2', f'HeroKnight_Attack2_{i}.png')) for i in range(6)]
        self.block_idle_images = [load_image(p('HeroKnight', 'BlockIdle', f'HeroKnight_Block Idle_{i}.png')) for i in range(8)]





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

        self.anim = self.images
        self.max_frames = len(self.anim)

        self.body_w_ratio = 0.35
        self.body_h_ratio = 0.75
        self.bb_y_offset_ratio = 0.09

        self.roll_cool = 0.0

        self.max_hp = 100
        self.hp = self.max_hp
        self.did_hit = False

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)
        self.ROLL = Roll(self)
        self.ATTACK = Attack(self)
        self.BLOCK = Block(self)

        self.rules = {
            self.IDLE: {
                a_down: self.ATTACK,
                s_down: self.BLOCK,
                right_down: self.RUN,
                left_down: self.RUN,
                up_down: self.JUMP,
            },
            self.RUN: {
                a_down: self.ATTACK,
                s_down: self.BLOCK,
                right_up: self.IDLE,
                left_up: self.IDLE,
                right_down: self.RUN,
                left_down: self.RUN,
                up_down: self.JUMP,
            },
            self.JUMP: {

            },
            self.FALL: {
                right_down: self.FALL,
                left_down: self.FALL,
                landed_run: self.RUN,
                landed_idle: self.IDLE,
            },
            self.ROLL: {},
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

    def get_bb(self):
        fi = int(self.frame) % self.max_frames
        img = self.anim[fi]

        full_w = img.w * self.scale
        full_h = img.h * self.scale

        w = full_w * self.body_w_ratio
        h = full_h * self.body_h_ratio

        half_w = w / 2
        half_h = h / 2

        offset = full_h * self.bb_y_offset_ratio
        cy = self.y - offset

        left = self.x - half_w
        bottom = cy - half_h
        right = self.x + half_w
        top = cy + half_h
        return left, bottom, right, top

    def get_attack_bb(self):
        from HeroKnight import Attack
        if not isinstance(self.state_machine.cur_state, Attack):
            return None

        fi = int(self.frame) % self.max_frames
        img = self.anim[fi]

        full_w = img.w * self.scale
        full_h = img.h * self.scale

        body_w = full_w * self.body_w_ratio
        sword_w = body_w * 0.9
        sword_h = full_h * 0.5


        cx = self.x + self.face_dir * (body_w * 0.5 + sword_w * 0.5)
        cy = self.y + full_h * 0.1

        half_w = sword_w / 2
        half_h = sword_h / 2
        left = cx - half_w
        bottom = cy - half_h
        right = cx + half_w
        top = cy + half_h
        return left, bottom, right, top

    def handle_event(self, e):
        if isinstance(self.state_machine.cur_state, Attack):
            self.state_machine.handle_state_event(('INPUT', e))
            return

        if isinstance(self.state_machine.cur_state, Block):

            if e.type == SDL_KEYDOWN:
                if e.key == SDLK_RIGHT:
                    self.dir = 1
                    self.face_dir = 1
                elif e.key == SDLK_LEFT:
                    self.dir = -1
                    self.face_dir = -1
            elif e.type == SDL_KEYUP:
                if e.key == SDLK_RIGHT and self.dir == 1:
                    self.dir = 0
                elif e.key == SDLK_LEFT and self.dir == -1:
                    self.dir = 0
                elif e.key == SDLK_s:
                    next_state = self.RUN if self.dir != 0 else self.IDLE
                    self.state_machine.change_state(next_state)
            return

        self.state_machine.handle_state_event(('INPUT', e))

        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_RIGHT:
                self.dir = 1;
                self.face_dir = 1
            elif e.key == SDLK_LEFT:
                self.dir = -1;
                self.face_dir = -1
            elif e.key == SDLK_SPACE:
                if (self.state_machine.cur_state not in (self.JUMP, self.FALL, self.ROLL)
                        and self.roll_cool <= 0.0):  # 구르기만 쿨
                    self.state_machine.change_state(self.ROLL)
                    self.roll_cool = ROLL_COOLTIME
        if e.type == SDL_KEYUP:
            if e.key == SDLK_RIGHT and self.dir == 1: self.dir = 0
            if e.key == SDLK_LEFT and self.dir == -1: self.dir = 0

    def update(self):
        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - game_framework.frame_time)
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)
        atk_bb = self.get_attack_bb()
        if atk_bb is not None:
            draw_rectangle(*atk_bb)
