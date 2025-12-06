from pico2d import *
import os
import game_framework

from state_machine import StateMachine

BASE = os.path.dirname(__file__)


def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)


def cave_path(*names):
    return os.path.join(BASE, 'cave', *names)


PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

ATTACK_DURATION = 0.45

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8

ROLL_SPEED_PPS = RUN_SPEED_PPS * 2.0
ROLL_DURATION = 0.45
ROLL_COOLTIME = 10.0  # 구르기만 10초 쿨타임

GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

# dt 스파이크 상한 (초)
MAX_DT = 1.0 / 30.0

# 피격 관련 상수
HIT_EFFECT_DURATION = 2.0        # 2초 동안 깜빡
HIT_KNOCKBACK_DURATION = 0.2     # 0.2초 동안 넉백
HIT_KNOCKBACK_SPEED_PPS = 250.0  # 넉백 속도

# 방어 성공 시 넉백 속도(조금만 밀리도록)
BLOCK_KNOCKBACK_SPEED_PPS = 100.0

# 각성 관련 상수
SUPER_THRESHOLD_HP = 50          # HP 50 미만에서 각성
SUPER_SPEED_SCALE = 1.3          # 이동 속도 배율
SUPER_SCALE_FACTOR = 1.4         # 캐릭터 크기 배율


def right_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT
def right_up(e):    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_RIGHT
def left_down(e):   return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT
def left_up(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP and e[1].key == SDLK_LEFT

def space_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE
def up_down(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_UP
def a_down(e):      return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_a
def s_down(e):      return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_s
def jump_done(e):   return e[0] == 'JUMP_DONE'
def fall_done(e):   return e[0] == 'FALL_DONE'
def landed_run(e):  return e[0] == 'LANDED_RUN'
def landed_idle(e): return e[0] == 'LANDED_IDLE'


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

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * self.boy.speed_scale * dt
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

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * self.boy.speed_scale * dt
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

        self.boy.x += self.boy.dir * RUN_SPEED_PPS * self.boy.speed_scale * dt
        self.boy.x = max(self.boy.left_bound,
                         min(self.boy.x, self.boy.right_bound))

        self.boy.vy -= GRAVITY_PPS2 * dt
        self.boy.y += self.boy.vy * dt

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
        if dt > MAX_DT:
            dt = MAX_DT

        self.elapsed += dt
        self.boy.frame = (self.boy.frame
                          + self.boy.max_frames * ACTION_PER_TIME * dt) % self.boy.max_frames

        self.boy.x += self.move_dir * ROLL_SPEED_PPS * self.boy.speed_scale * dt
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
        self.pick = random.choice([1, 2])
        self.boy.frame = 0
        self.boy.prev_time = get_time()

        self.saved_dir = self.boy.dir
        self.boy.dir = 0

        self.boy.did_hit = False

        self.boy.anim = self.boy.attack1 if self.pick == 1 else self.boy.attack2
        self.boy.max_frames = len(self.boy.anim)
        self.fps = self.boy.max_frames / ATTACK_DURATION

    def exit(self, e):
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


class Die:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0
        if not hasattr(self.boy, 'vy'):
            self.boy.vy = 0.0
        self.boy.vy = 0.0

        self.boy.anim = self.boy.death_images
        self.boy.max_frames = len(self.boy.anim)
        self.boy.frame = 0.0
        self.boy.prev_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.boy.frame += self.boy.max_frames * ACTION_PER_TIME * dt
        if self.boy.frame >= self.boy.max_frames:
            self.boy.frame = self.boy.max_frames - 1

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
        self.death_images = [load_image(p('HeroKnight', 'Death', f'HeroKnight_Death_{i}.png')) for i in range(10)]

        self.JUMP_LAST = 1
        self.FALL_LAST = 3
        self.jump_images = [load_image(p('HeroKnight', 'Jump', f'HeroKnight_Jump_{i}.png')) for i in range(self.JUMP_LAST + 1)]
        self.fall_images = [load_image(p('HeroKnight', 'Fall', f'HeroKnight_Fall_{i}.png')) for i in range(self.FALL_LAST + 1)]

        self.frame = 0.0
        self.fps = 10

        # 기본 크기와 현재 크기
        self.base_scale = 2.0
        self.scale = self.base_scale

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

        # 피격 효과 + 넉백
        self.hit_timer = 0.0
        self.knockback_timer = 0.0
        self.knockback_dir = 0
        self.knockback_speed = HIT_KNOCKBACK_SPEED_PPS

        # 방어 게이지 (그림에 맞게 4칸)
        self.guard_max = 4
        self.guard_current = self.guard_max
        self.guard_recharge_delay = 3.0  # 3초마다 1칸 회복
        self.guard_recharge_timer = 0.0

        # 각성 상태
        self.awakened = False
        self.speed_scale = 1.0

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)
        self.ROLL = Roll(self)
        self.ATTACK = Attack(self)
        self.BLOCK = Block(self)
        self.DIE = Die(self)

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
            self.JUMP: {},
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

    # 일반 피격
    def start_hit_effect(self, knockback_dir=None):
        self.hit_timer = HIT_EFFECT_DURATION
        self.knockback_timer = HIT_KNOCKBACK_DURATION
        self.knockback_speed = HIT_KNOCKBACK_SPEED_PPS

        if knockback_dir is not None:
            self.knockback_dir = knockback_dir
        else:
            self.knockback_dir = -self.face_dir

    def apply_damage(self, amount, knockback_dir=None):
        if self.hp <= 0:
            return
        if self.hit_timer > 0.0:
            return

        self.hp = max(0, self.hp - amount)
        self.start_hit_effect(knockback_dir)

    # 방어 성공 시(깜빡임 없이 약한 넉백)
    def start_block_knockback(self, knockback_dir):
        if knockback_dir is None:
            knockback_dir = -self.face_dir
        self.knockback_dir = knockback_dir
        self.knockback_timer = HIT_KNOCKBACK_DURATION
        self.knockback_speed = BLOCK_KNOCKBACK_SPEED_PPS

    def consume_guard(self, knockback_dir, use_all=False):
        if self.guard_current <= 0:
            return False

        if use_all:
            self.guard_current = 0
        else:
            self.guard_current -= 1

        self.guard_recharge_timer = 0.0
        self.start_block_knockback(knockback_dir)
        return True

    # 각성 발동
    def super_power(self):
        if (not self.awakened) and self.hp < SUPER_THRESHOLD_HP:
            self.awakened = True
            self.speed_scale = SUPER_SPEED_SCALE
            # 각성 시 캐릭터 전체 크기 1.4배
            self.scale = self.base_scale * SUPER_SCALE_FACTOR

    def handle_event(self, e):
        if self.hp <= 0:
            return

        self.state_machine.handle_state_event(('INPUT', e))

        if e.type == SDL_KEYDOWN:
            if e.key == SDLK_RIGHT:
                self.dir = 1
                self.face_dir = 1
            elif e.key == SDLK_LEFT:
                self.dir = -1
                self.face_dir = -1
            elif e.key == SDLK_SPACE:
                if (self.state_machine.cur_state not in (self.JUMP, self.FALL, self.ROLL)
                        and self.roll_cool <= 0.0):
                    self.state_machine.change_state(self.ROLL)
                    self.roll_cool = ROLL_COOLTIME
        if e.type == SDL_KEYUP:
            if e.key == SDLK_RIGHT and self.dir == 1:
                self.dir = 0
            if e.key == SDLK_LEFT and self.dir == -1:
                self.dir = 0

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
                self.dir = 1
                self.face_dir = 1
            elif e.key == SDLK_LEFT:
                self.dir = -1
                self.face_dir = -1
            elif e.key == SDLK_SPACE:
                if (self.state_machine.cur_state not in (self.JUMP, self.FALL, self.ROLL)
                        and self.roll_cool <= 0.0):
                    self.state_machine.change_state(self.ROLL)
                    self.roll_cool = ROLL_COOLTIME
        if e.type == SDL_KEYUP:
            if e.key == SDLK_RIGHT and self.dir == 1:
                self.dir = 0
            if e.key == SDLK_LEFT and self.dir == -1:
                self.dir = 0

    def update(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        # 피격/넉백 처리
        if self.hit_timer > 0.0:
            self.hit_timer = max(0.0, self.hit_timer - dt)
        if self.knockback_timer > 0.0:
            self.knockback_timer = max(0.0, self.knockback_timer - dt)
            self.x += self.knockback_dir * self.knockback_speed * dt
            self.x = max(self.left_bound, min(self.x, self.right_bound))

        if self.hp <= 0:
            if self.state_machine.cur_state is not self.DIE:
                self.dir = 0
                if not hasattr(self, 'vy'):
                    self.vy = 0.0
                self.vy = 0.0
                self.state_machine.change_state(self.DIE)
            self.state_machine.update()
            return

        # 각성 상태 체크
        self.super_power()

        # 방어 게이지 회복
        if self.guard_current < self.guard_max:
            self.guard_recharge_timer += dt
            if self.guard_recharge_timer >= self.guard_recharge_delay:
                self.guard_current += 1
                if self.guard_current > self.guard_max:
                    self.guard_current = self.guard_max
                self.guard_recharge_timer = 0.0
        else:
            self.guard_recharge_timer = 0.0

        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - game_framework.frame_time)

        self.state_machine.update()

    def draw(self):
        visible = True
        if self.hit_timer > 0.0:
            elapsed = HIT_EFFECT_DURATION - self.hit_timer
            if int(elapsed * 20) % 2 == 0:
                visible = False

        if visible:
            # 오라 없이 캐릭터만 그림
            self.state_machine.draw()

        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)
        atk_bb = self.get_attack_bb()
        if atk_bb is not None:
            draw_rectangle(atk_bb[0], atk_bb[1], atk_bb[2], atk_bb[3])
