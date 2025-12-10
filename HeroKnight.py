from pico2d import *
import os

import game_framework
from state_machine import StateMachine

# 이 모듈은 플레이어 캐릭터 HeroKnight의 상태, 움직임, 피격 처리를 담당하며
# play_mode.py에서 생성되어 EvilKnight.py의 EvilKnight와 싸운다.

BASE = os.path.dirname(__file__)


def cave_path(name):
    # cave 폴더 안의 PNG 파일 경로를 구성하는 헬퍼 함수이다.
    return os.path.join(BASE, 'cave', name)


PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

ATTACK_DURATION = 0.45   # 공격 1회 재생 시간(초)

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION

ROLL_SPEED_PPS = RUN_SPEED_PPS * 2.0
ROLL_DURATION = 0.45
ROLL_COOLTIME = 10.0

GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

MAX_DT = 1.0 / 30.0

HIT_EFFECT_DURATION = 2.0
HIT_KNOCKBACK_DURATION = 0.2
HIT_KNOCKBACK_SPEED_PPS = 250.0

BLOCK_KNOCKBACK_SPEED_PPS = 100.0

SUPER_THRESHOLD_HP = 50
SUPER_SPEED_SCALE = 1.3
SUPER_SCALE_FACTOR = 1.4


# 아래 입력 검사 함수들은 상태 머신 전이 규칙에서 사용되며
# play_mode.handle_events에서 전달된 SDL 이벤트를 해석한다.
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
    # 이 상태는 가만히 서 있는 상태이며
    # Boy.update에서 StateMachine을 통해 반복 호출된다.
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
    # 이 상태는 좌우로 달리는 상태이며
    # 방향키 입력으로 전이되고 이동 속도를 적용한다.
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
    # 이 상태는 점프 상승 구간을 처리하며
    # Boy.handle_event의 위 방향 입력으로 진입한다.
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

        # 상승이 끝나고 속도가 0 이하가 되면 낙하 상태로 전환한다.
        if self.boy.vy <= 0:
            self.boy.state_machine.change_state(self.boy.FALL)

    def draw(self):
        self.boy.draw_current_frame()


class Fall:
    # 이 상태는 점프 후 낙하 구간을 처리하며
    # play_mode.resolve_ground에서 착지 시 Idle/Run으로 전환된다.
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

    def draw(self):
        self.boy.draw_current_frame()


class Roll:
    # 이 상태는 구르기 무적/이동을 처리하며
    # Boy.handle_event에서 스페이스 입력으로 진입한다.
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
    # 이 상태는 공격 1/2 애니메이션을 재생하며
    # play_mode.resolve_attack에서 공격 판정을 사용한다.
    def __init__(self, boy):
        self.boy = boy
        self.pick = 1
        self.fps = 0.0
        self.desired_dir = 0
        self.queued_block = False

    def enter(self, e):
        import random
        self.pick = random.choice([1, 2])
        self.boy.frame = 0
        self.boy.prev_time = get_time()

        self.desired_dir = self.boy.dir
        self.queued_block = False

        self.boy.dir = 0
        self.boy.did_hit = False

        self.boy.anim = self.boy.attack1 if self.pick == 1 else self.boy.attack2
        self.boy.max_frames = len(self.boy.anim)
        self.fps = self.boy.max_frames / ATTACK_DURATION

    def exit(self, e):
        pass

    def do(self):
        now = get_time()
        dt = min(now - self.boy.prev_time, MAX_DT)
        if dt < 0.0:
            dt = 0.0
        self.boy.prev_time = now
        self.boy.frame += self.fps * dt

        if self.boy.frame >= self.boy.max_frames:
            self.boy.dir = self.desired_dir

            if self.queued_block:
                self.boy.state_machine.change_state(self.boy.BLOCK)
            else:
                if self.boy.dir == 0:
                    self.boy.state_machine.change_state(self.boy.IDLE)
                else:
                    self.boy.state_machine.change_state(self.boy.RUN)

    def draw(self):
        self.boy.draw_current_frame()


class Block:
    # 이 상태는 방어 자세를 유지하는 상태이며
    # play_mode.resolve_attack에서 가드 판정에 사용된다.
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
    # 이 상태는 플레이어가 사망했을 때 죽는 모션을 재생하며
    # play_mode.update에서 death_done 플래그를 보고 패배를 판정한다.
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

        self.boy.death_done = False

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.boy.frame += self.boy.max_frames * ACTION_PER_TIME * dt
        if self.boy.frame >= self.boy.max_frames:
            self.boy.frame = self.boy.max_frames - 1
            self.boy.death_done = True

    def draw(self):
        self.boy.draw_current_frame()


class Boy:
    # 이 클래스는 플레이어 캐릭터 전체 로직을 담당하며
    # play_mode.py에서 한 개 인스턴스로 사용된다.
    def __init__(self):
        # 스프라이트 이미지는 모두 cave 폴더에 평탄하게 들어 있다고 가정한다.
        self.images = [load_image(f'cave/HeroKnight_Idle_{i}.png') for i in range(8)]
        self.run_images = [load_image(f'cave/HeroKnight_Run_{i}.png') for i in range(10)]
        self.roll_images = [load_image(f'cave/HeroKnight_Roll_{i}.png') for i in range(9)]
        self.attack1 = [load_image(f'cave/HeroKnight_Attack1_{i}.png') for i in range(6)]
        self.attack2 = [load_image(f'cave/HeroKnight_Attack2_{i}.png') for i in range(6)]
        self.block_idle_images = [load_image(f'cave/HeroKnight_Block Idle_{i}.png') for i in range(8)]
        self.death_images = [load_image(f'cave/HeroKnight_Death_{i}.png') for i in range(10)]

        self.JUMP_LAST = 1
        self.FALL_LAST = 3
        self.jump_images = [load_image(f'cave/HeroKnight_Jump_{i}.png') for i in range(self.JUMP_LAST + 1)]
        self.fall_images = [load_image(f'cave/HeroKnight_Fall_{i}.png') for i in range(self.FALL_LAST + 1)]


        self.frame = 0.0
        self.fps = 10

        self.base_scale = 2.0
        self.scale = self.base_scale

        self.x, self.y = 320, 80
        self.prev_time = get_time()

        self.dir = 0
        self.face_dir = 1
        self.left_bound, self.right_bound = 30, 770

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

        self.hit_timer = 0.0
        self.knockback_timer = 0.0
        self.knockback_dir = 0
        self.knockback_speed = HIT_KNOCKBACK_SPEED_PPS

        self.guard_max = 4
        self.guard_current = self.guard_max
        self.guard_recharge_delay = 3.0
        self.guard_recharge_timer = 0.0

        self.awakened = False
        self.speed_scale = 1.0

        self.death_done = False

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)
        self.ROLL = Roll(self)
        self.ATTACK = Attack(self)
        self.BLOCK = Block(self)
        self.DIE = Die(self)

        # 상태 머신 전이 규칙은 HeroKnight 자체 입력 위주로만 사용되며
        # 낙하 착지는 play_mode.resolve_ground에서 이벤트를 보내 처리한다.
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
            self.ATTACK: {},
            self.BLOCK: {},
            self.DIE: {},
        }

        self.state_machine = StateMachine(self.IDLE, self.rules)

    def draw_current_frame(self):
        # 이 메서드는 현재 애니메이션 프레임 한 장을 그리며
        # 모든 상태의 draw()에서 공통으로 호출된다.
        fi = int(self.frame) % self.max_frames
        img = self.anim[fi]
        w, h = img.w, img.h
        tw, th = int(w * self.scale), int(h * self.scale)

        if self.face_dir == 1:
            img.draw(self.x, self.y, tw, th)
        else:
            img.composite_draw(0, 'h', self.x, self.y, tw, th)

    def get_bb(self):
        # 이 메서드는 몸통 히트박스를 계산하며
        # play_mode.resolve_body_block, resolve_attack, stage_background.CaveStalactites에서 사용된다.
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
        # 이 메서드는 공격 중일 때만 검 사용 히트박스를 반환하며
        # play_mode.resolve_attack에서 사용된다.
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

    def start_hit_effect(self, knockback_dir=None):
        # 이 메서드는 피격 시 깜빡임과 넉백을 설정하며
        # play_mode.resolve_attack에서 호출된다.
        self.hit_timer = HIT_EFFECT_DURATION
        self.knockback_timer = HIT_KNOCKBACK_DURATION
        self.knockback_speed = HIT_KNOCKBACK_SPEED_PPS

        if knockback_dir is not None:
            self.knockback_dir = knockback_dir
        else:
            self.knockback_dir = -self.face_dir

    def apply_damage(self, amount, knockback_dir=None):
        # 이 메서드는 실제 HP를 깎고 피격 연출을 시작하며
        # 낙하 물체나 EvilKnight의 공격에 공통으로 사용된다.
        if self.hp <= 0:
            return
        if self.hit_timer > 0.0:
            return

        self.hp = max(0, self.hp - amount)
        self.start_hit_effect(knockback_dir)

    def start_block_knockback(self, knockback_dir):
        # 이 메서드는 가드 성공 시의 짧은 넉백을 설정하며
        # consume_guard 내부에서 사용된다.
        if knockback_dir is None:
            knockback_dir = -self.face_dir
        self.knockback_dir = knockback_dir
        self.knockback_timer = HIT_KNOCKBACK_DURATION
        self.knockback_speed = BLOCK_KNOCKBACK_SPEED_PPS

    def consume_guard(self, knockback_dir, use_all=False):
        # 이 메서드는 방어 게이지를 소비하고 가드 넉백을 적용하며
        # play_mode.resolve_attack에서 호출된다.
        if self.guard_current <= 0:
            return False

        if use_all:
            self.guard_current = 0
        else:
            self.guard_current -= 1

        self.guard_recharge_timer = 0.0
        self.start_block_knockback(knockback_dir)
        return True

    def super_power(self):
        # 이 메서드는 HP가 일정 이하일 때 각성 상태로 전환하며
        # Boy.update에서 주기적으로 호출된다.
        if (not self.awakened) and self.hp < SUPER_THRESHOLD_HP:
            self.awakened = True
            self.speed_scale = SUPER_SPEED_SCALE
            self.scale = self.base_scale * SUPER_SCALE_FACTOR

    def handle_event(self, e):
        # 이 메서드는 play_mode.handle_events에서 SDL 이벤트를 전달받아
        # 상태 머신으로 넘기거나 구르기/방어 전용 입력을 처리한다.
        if self.hp <= 0:
            return

        cur_state = self.state_machine.cur_state

        # 방어 가능 여부: guard_current가 0이면 방어 입력을 무시하도록 사용한다.
        can_block = (self.guard_current > 0)

        # 스페이스 입력: 구르기
        if e.type == SDL_KEYDOWN and e.key == SDLK_SPACE:
            if (cur_state not in (self.JUMP, self.FALL, self.ROLL)
                    and self.roll_cool <= 0.0):
                self.state_machine.change_state(self.ROLL)
                self.roll_cool = ROLL_COOLTIME
                return

        # 공격 중 추가 입력 처리
        if isinstance(cur_state, Attack):
            if e.type == SDL_KEYDOWN:
                if e.key == SDLK_RIGHT:
                    self.face_dir = 1
                    cur_state.desired_dir = 1
                elif e.key == SDLK_LEFT:
                    self.face_dir = -1
                    cur_state.desired_dir = -1
                elif e.key == SDLK_s:
                    # 방어 게이지가 남아 있을 때만 공격 후 방어 예약이 가능하다.
                    if can_block:
                        cur_state.queued_block = True
            return

        # 방어 상태에서의 입력 처리
        if isinstance(cur_state, Block):
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

        # 일반 이동 입력 처리
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

        # 방어 게이지가 0일 때는 S 키 입력을 상태 머신에 전달하지 않는다.
        if e.type == SDL_KEYDOWN and e.key == SDLK_s and not can_block:
            return

        self.state_machine.handle_state_event(('INPUT', e))

    def update(self):
        # 이 메서드는 한 프레임 동안의 피격, 넉백, 각성, 가드 회복, 상태 머신 로직을 처리하며
        # play_mode.update에서 매 프레임 호출된다.
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

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

        self.super_power()

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
        # 이 메서드는 피격 깜빡임 효과를 적용한 뒤
        # 현재 상태의 스프라이트를 그린다.
        visible = True
        if self.hit_timer > 0.0:
            elapsed = HIT_EFFECT_DURATION - self.hit_timer
            if int(elapsed * 20) % 2 == 0:
                visible = False

        if visible:
            self.state_machine.draw()
