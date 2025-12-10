from pico2d import *
import os
import game_framework
from state_machine import StateMachine

# 이 모듈은 적 캐릭터 EvilKnight의 상태, AI, 피격 처리를 담당하며
# play_mode.py에서 플레이어와 싸우도록 사용된다.

BASE = os.path.dirname(__file__)


def cave_path(name):
    # cave 폴더 안의 PNG 파일 경로를 구성하는 헬퍼 함수이다.
    return os.path.join(BASE, 'cave', name)


FRAME_W = 120
FRAME_H = 80

PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

ROLL_SPEED_PPS = RUN_SPEED_PPS * 2.0
ROLL_DURATION = 0.45

ATTACK_DURATION = 0.45

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION

GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

MAX_DT = 1.0 / 30.0

HIT_EFFECT_DURATION = 2.0
HIT_KNOCKBACK_DURATION = 0.2
HIT_KNOCKBACK_SPEED_PPS = 250.0

SUPER_THRESHOLD_HP = 50
SUPER_SPEED_SCALE = 1.3
SUPER_SCALE_FACTOR = 1.4

EVIL_ATTACK_COOL_BASE = 1.2
EVIL_ATTACK_COOL_AWAKENED = 0.7
EVIL_ROLL_COOL = 2.0
EVIL_MAX_COMBO = 3
EVIL_EVADE_TIME = 0.8
EVIL_EVADE_JUMP_PROB = 0.25
EVIL_EVADE_ROLL_PROB = 0.5


def landed_run(e):
    # 이 함수는 낙하 후 착지하여 달리기 상태로 전이해야 할 때
    # play_mode.resolve_ground에서 발생시키는 이벤트 판정에 사용된다.
    return e[0] == 'LANDED_RUN'


def landed_idle(e):
    # 이 함수는 낙하 후 착지하여 대기 상태로 전이해야 할 때
    # play_mode.resolve_ground에서 발생시키는 이벤트 판정에 사용된다.
    return e[0] == 'LANDED_IDLE'


class Idle:
    # 이 상태는 Evil이 가만히 서 있는 상태이며
    # EvilKnight.update의 AI가 행동을 결정하지 않을 때 유지된다.
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.sheet = self.knight.idle_sheet
        self.knight.max_frames = self.knight.idle_frames
        self.knight.frame = 0.0
        self.knight.dir = 0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

    def draw(self):
        self.knight.draw_current_frame()


class Run:
    # 이 상태는 Evil이 좌우로 움직이는 상태이며
    # AI가 추격/회피를 결정할 때 사용된다.
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.sheet = self.knight.run_sheet
        self.knight.max_frames = self.knight.run_frames
        self.knight.frame = 0.0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        self.knight.x += self.knight.dir * RUN_SPEED_PPS * self.knight.speed_scale * dt
        self.knight.x = max(self.knight.left_bound,
                            min(self.knight.x, self.knight.right_bound))

    def draw(self):
        self.knight.draw_current_frame()


class Roll:
    # 이 상태는 Evil의 긴급 회피 구르기를 담당하며
    # 종유석 회피 및 근거리 회피 AI에서 사용된다.
    def __init__(self, knight):
        self.knight = knight
        self.elapsed = 0.0
        self.move_dir = 0

    def enter(self, e):
        self.knight.sheet = self.knight.roll_sheet
        self.knight.max_frames = self.knight.roll_frames
        self.knight.frame = 0.0
        self.elapsed = 0.0
        self.move_dir = self.knight.dir if self.knight.dir != 0 else self.knight.face_dir
        if self.move_dir != 0:
            self.knight.face_dir = self.move_dir

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.elapsed += dt
        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        self.knight.x += self.move_dir * ROLL_SPEED_PPS * self.knight.speed_scale * dt
        self.knight.x = max(self.knight.left_bound,
                            min(self.knight.x, self.knight.right_bound))

        if self.elapsed >= ROLL_DURATION:
            self.knight.state_machine.change_state(self.knight.IDLE)

    def draw(self):
        self.knight.draw_current_frame()


class Attack:
    # 이 상태는 Evil의 공격 애니메이션을 재생하며
    # play_mode.resolve_attack에서 검 히트박스를 사용한다.
    def __init__(self, knight):
        self.knight = knight
        self.fps = 0.0
        self.saved_dir = 0

    def enter(self, e):
        import random

        if self.knight.next_attack_type in (1, 2):
            pick = self.knight.next_attack_type
            self.knight.next_attack_type = 0
        else:
            pick = random.choice([1, 2])

        if pick == 1:
            self.knight.sheet = self.knight.attack1_sheet
            self.knight.max_frames = self.knight.attack1_frames
        else:
            self.knight.sheet = self.knight.attack2_sheet
            self.knight.max_frames = self.knight.attack2_frames

        self.knight.frame = 0.0
        self.knight.prev_time = get_time()

        self.saved_dir = self.knight.dir
        self.knight.dir = 0

        self.knight.did_hit = False

        self.fps = self.knight.max_frames / ATTACK_DURATION

    def exit(self, e):
        self.knight.dir = self.saved_dir

    def do(self):
        now = get_time()
        dt = now - self.knight.prev_time
        if dt > MAX_DT:
            dt = MAX_DT
        if dt < 0.0:
            dt = 0.0

        self.knight.prev_time = now
        self.knight.frame += self.fps * dt

        if self.knight.frame >= self.knight.max_frames:
            if self.knight.dir == 0:
                self.knight.state_machine.change_state(self.knight.IDLE)
            else:
                self.knight.state_machine.change_state(self.knight.RUN)

    def draw(self):
        self.knight.draw_current_frame()


class Jump:
    # 이 상태는 Evil의 점프 상승 구간을 처리하며
    # 회피 AI가 점프를 선택했을 때 사용된다.
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.vy = JUMP_SPEED_PPS
        self.knight.sheet = self.knight.jump_sheet
        self.knight.max_frames = self.knight.jump_frames
        self.knight.frame = 0.0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        self.knight.vy -= GRAVITY_PPS2 * dt
        self.knight.y += self.knight.vy * dt

        if self.knight.vy <= 0:
            self.knight.state_machine.change_state(self.knight.FALL)

    def draw(self):
        self.knight.draw_current_frame()


class Fall:
    # 이 상태는 Evil의 낙하 구간을 처리하며
    # play_mode.resolve_ground에서 착지 이벤트로 Idle/Run으로 전환된다.
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.sheet = self.knight.fall_sheet
        self.knight.max_frames = self.knight.fall_frames
        self.knight.frame = 0.0

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        self.knight.vy -= GRAVITY_PPS2 * dt
        self.knight.y += self.knight.vy * dt

    def draw(self):
        self.knight.draw_current_frame()


class Die:
    # 이 상태는 Evil이 사망 시 죽는 모션을 재생하며
    # play_mode.update에서 death_done 플래그를 보고 승리를 판정한다.
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.dir = 0
        self.knight.vy = 0.0

        self.knight.sheet = self.knight.dead_sheet
        self.knight.max_frames = self.knight.dead_frames
        self.knight.frame = 0.0
        self.knight.prev_time = get_time()

        self.knight.death_done = False

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame += self.knight.max_frames * ACTION_PER_TIME * dt
        if self.knight.frame >= self.knight.max_frames:
            self.knight.frame = self.knight.max_frames - 1
            self.knight.death_done = True

    def draw(self):
        self.knight.draw_current_frame()


class EvilKnight:
    # 이 클래스는 적의 전체 로직과 AI를 담당하며
    # play_mode.py에서 HeroKnight.Boy와 싸우게 된다.
    def __init__(self):
        self.idle_sheet = load_image('cave/_Idle.png')
        self.run_sheet = load_image('cave/_Run.png')
        self.roll_sheet = load_image('cave/_Roll.png')
        self.jump_sheet = load_image('cave/_Jump.png')
        self.fall_sheet = load_image('cave/_JumpFallInbetween.png')
        self.attack1_sheet = load_image('cave/_Attack.png')
        self.attack2_sheet = load_image('cave/_Attack2.png')
        self.dead_sheet = load_image('cave/_Death.png')

        self.frame_w = FRAME_W
        self.frame_h = FRAME_H

        self.idle_frames = self.idle_sheet.w // self.frame_w
        self.run_frames = self.run_sheet.w // self.frame_w
        self.roll_frames = self.roll_sheet.w // self.frame_w
        self.jump_frames = self.jump_sheet.w // self.frame_w
        self.fall_frames = self.fall_sheet.w // self.frame_w
        self.attack1_frames = self.attack1_sheet.w // self.frame_w
        self.attack2_frames = self.attack2_sheet.w // self.frame_w
        self.dead_frames = self.dead_sheet.w // self.frame_w

        self.sheet = self.idle_sheet
        self.max_frames = self.idle_frames
        self.frame = 0.0

        self.body_w_ratio = 0.20
        self.body_h_ratio = 0.50
        self.bb_y_offset_ratio = 0.25

        self.base_scale = 2.0
        self.scale = self.base_scale

        self.x, self.y = 600, 80
        self.face_dir = -1
        self.dir = 0
        self.left_bound, self.right_bound = 30, 770
        self.ground_y = self.y

        self.vy = 0.0
        self.prev_time = get_time()

        self.max_hp = 100
        self.hp = self.max_hp
        self.did_hit = False

        self.hit_timer = 0.0
        self.knockback_timer = 0.0
        self.knockback_dir = 0

        self.awakened = False
        self.speed_scale = 1.0

        self.attack_cool = 0.0
        self.roll_cool = 0.0

        self.combo_count = 0
        self.evade_timer = 0.0
        self.evade_dir = 0

        self.next_attack_type = 0

        self.target = None
        self.stage = 1
        self.bg = None

        self.death_done = False

        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.ROLL = Roll(self)
        self.ATTACK = Attack(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)
        self.DIE = Die(self)

        self.rules = {
            self.IDLE: {},
            self.RUN: {},
            self.ROLL: {},
            self.ATTACK: {},
            self.JUMP: {},
            self.FALL: {
                landed_run: self.RUN,
                landed_idle: self.IDLE,
            },
            self.DIE: {},
        }
        self.state_machine = StateMachine(self.IDLE, self.rules)

    def draw_current_frame(self):
        # 이 메서드는 EvilKnight의 현재 시트에서 한 프레임을 그리며
        # 모든 상태의 draw()에서 공통으로 사용된다.
        fi = int(self.frame) % self.max_frames
        sx = fi * self.frame_w
        sy = 0

        dw = int(self.frame_w * self.scale)
        dh = int(self.frame_h * self.scale)

        if self.face_dir == 1:
            self.sheet.clip_draw(
                sx, sy, self.frame_w, self.frame_h,
                self.x, self.y, dw, dh
            )
        else:
            self.sheet.clip_composite_draw(
                sx, sy, self.frame_w, self.frame_h,
                0, 'h',
                self.x, self.y, dw, dh
            )

    def get_bb(self):
        # 이 메서드는 Evil의 몸통 히트박스를 계산하며
        # play_mode.resolve_body_block, resolve_attack, stage_background.CaveStalactites에서 사용된다.
        full_w = self.frame_w * self.scale
        full_h = self.frame_h * self.scale

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
        # 이 메서드는 공격 중일 때만 검 히트박스를 반환하며
        # play_mode.resolve_attack에서 사용된다.
        if not isinstance(self.state_machine.cur_state, Attack):
            return None

        full_w = self.frame_w * self.scale
        full_h = self.frame_h * self.scale

        body_w = full_w * self.body_w_ratio

        sword_w = body_w * 2.0
        sword_h = full_h * 0.3

        cx = self.x + self.face_dir * (body_w * 0.5 + sword_w * 0.5)
        cy = self.y - full_h * 0.35

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

        if knockback_dir is not None:
            self.knockback_dir = knockback_dir
        else:
            self.knockback_dir = -self.face_dir

    def apply_damage(self, amount, knockback_dir=None):
        # 이 메서드는 Evil의 HP를 감소시키고 피격 연출을 시작하며
        # HeroKnight 공격과 종유석 모두 여기로 들어온다.
        if self.hp <= 0:
            return
        if self.hit_timer > 0.0:
            return

        self.hp = max(0, self.hp - amount)
        self.start_hit_effect(knockback_dir)

    def super_power(self):
        # 이 메서드는 Evil의 HP가 일정 이하일 때 각성 상태로 전환하며
        # EvilKnight.update에서 주기적으로 호출된다.
        if (not self.awakened) and self.hp < SUPER_THRESHOLD_HP:
            self.awakened = True
            self.speed_scale = SUPER_SPEED_SCALE
            self.scale = self.base_scale * SUPER_SCALE_FACTOR

    def is_on_ground(self):
        # 이 메서드는 Evil이 점프/낙하 상태가 아닌지 확인하여
        # 회피/공격 AI에서 조건으로 사용된다.
        return (self.vy == 0.0
                and self.state_machine.cur_state not in (self.JUMP, self.FALL))

    def _find_stalactite_danger(self):
        # 이 내부 메서드는 2스테이지에서 머리 위에 떨어지는 종유석이 있는지 확인하여
        # AI가 회피 행동을 결정할 때 사용된다.
        if self.stage != 2:
            return None
        if self.bg is None or not hasattr(self.bg, 'hazards'):
            return None

        hazards = self.bg.hazards
        stones = getattr(hazards, 'stones', [])
        for s in stones:
            if not getattr(s, 'active', False):
                continue
            if abs(s.x - self.x) < 40 and s.y > self.y + 40:
                side_dir = 1 if s.x <= self.x else -1
                return s.x, side_dir

        return None

    def ai_update(self):
        # 이 메서드는 Evil의 전체 전투 AI를 담당하며
        # EvilKnight.update에서 매 프레임 호출된다.
        if self.hp <= 0:
            return
        cur = self.state_machine.cur_state
        if cur in (self.ATTACK, self.ROLL, self.JUMP, self.FALL, self.DIE):
            return

        target = self.target
        if target is None or getattr(target, 'hp', 0) <= 0:
            if cur is not self.IDLE:
                self.dir = 0
                self.state_machine.change_state(self.IDLE)
            return

        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        if self.attack_cool > 0.0:
            self.attack_cool = max(0.0, self.attack_cool - dt)
        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - dt)

        dx = target.x - self.x
        dist = abs(dx)

        base_attack_cool = EVIL_ATTACK_COOL_AWAKENED if self.awakened else EVIL_ATTACK_COOL_BASE

        danger = self._find_stalactite_danger()
        if danger is not None and self.is_on_ground():
            import random
            stone_x, side_dir = danger

            if self.roll_cool <= 0.0 and random.random() < 0.7:
                self.dir = side_dir
                self.face_dir = side_dir
                self.evade_dir = side_dir
                self.roll_cool = EVIL_ROLL_COOL
                self.state_machine.change_state(self.ROLL)
            else:
                self.dir = side_dir
                self.face_dir = side_dir
                if cur is not self.RUN:
                    self.state_machine.change_state(self.RUN)
            return

        if self.evade_timer > 0.0:
            import random
            self.evade_timer = max(0.0, self.evade_timer - dt)

            move_dir = self.evade_dir if self.evade_dir != 0 else (-1 if dx > 0 else 1)

            if self.is_on_ground() and self.roll_cool <= 0.0 and random.random() < EVIL_EVADE_ROLL_PROB:
                self.dir = move_dir
                self.face_dir = move_dir
                self.roll_cool = EVIL_ROLL_COOL
                self.state_machine.change_state(self.ROLL)
                return

            self.dir = move_dir
            self.face_dir = move_dir
            if cur is not self.RUN:
                self.state_machine.change_state(self.RUN)
            return

        attack_range = 110.0
        chase_range = 450.0

        if dist <= attack_range and self.is_on_ground():
            import random

            if dist > 1.0:
                self.face_dir = 1 if dx > 0 else -1

            if self.attack_cool <= 0.0:
                if self.awakened and random.random() < 0.4:
                    self.next_attack_type = 2
                else:
                    self.next_attack_type = 1

                self.start_attack()
                self.attack_cool = base_attack_cool
                self.dir = 0
                self.combo_count += 1

                if self.combo_count >= EVIL_MAX_COMBO:
                    self.combo_count = 0
                    self.evade_timer = EVIL_EVADE_TIME
                    self.evade_dir = -self.face_dir
                return

            else:
                import random
                r = random.random()

                if self.roll_cool <= 0.0 and self.is_on_ground() and r < EVIL_EVADE_ROLL_PROB:
                    move_dir = -self.face_dir
                    self.dir = move_dir
                    self.face_dir = move_dir
                    self.evade_dir = move_dir
                    self.roll_cool = EVIL_ROLL_COOL
                    self.state_machine.change_state(self.ROLL)
                    return

                if self.is_on_ground() and r < EVIL_EVADE_ROLL_PROB + EVIL_EVADE_JUMP_PROB:
                    self.state_machine.change_state(self.JUMP)
                    return

                move_dir = -self.face_dir
                self.dir = move_dir
                self.face_dir = move_dir
                if cur is not self.RUN:
                    self.state_machine.change_state(self.RUN)
                return

        if dist <= chase_range:
            move_dir = 1 if dx > 0 else -1
            self.dir = move_dir
            self.face_dir = move_dir
            if cur is not self.RUN:
                self.state_machine.change_state(self.RUN)
            return

        self.dir = 0
        if cur is not self.IDLE:
            self.state_machine.change_state(self.IDLE)

    def handle_event(self, e):
        # 이 메서드는 Evil이 플레이어처럼 입력을 받지 않으므로
        # 현재는 구현되지 않은 자리이다.
        pass

    def update(self):
        # 이 메서드는 Evil의 피격, 넉백, 각성, AI, 상태 머신 업데이트를
        # 한 프레임 동안 처리하며 play_mode.update에서 호출된다.
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        if self.hit_timer > 0.0:
            self.hit_timer = max(0.0, self.hit_timer - dt)
        if self.knockback_timer > 0.0:
            self.knockback_timer = max(0.0, self.knockback_timer - dt)
            self.x += self.knockback_dir * HIT_KNOCKBACK_SPEED_PPS * dt
            self.x = max(self.left_bound, min(self.x, self.right_bound))

        if self.hp <= 0:
            if self.state_machine.cur_state is not self.DIE:
                self.dir = 0
                self.vy = 0.0
                self.state_machine.change_state(self.DIE)
            self.state_machine.update()
            return

        self.super_power()

        if self.attack_cool > 0.0:
            self.attack_cool = max(0.0, self.attack_cool - dt)
        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - dt)

        self.ai_update()

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

    def start_attack(self):
        # 이 메서드는 AI에서 공격을 시작할 때 상태를 ATTACK으로 전환한다.
        self.state_machine.change_state(self.ATTACK)
