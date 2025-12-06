from pico2d import *
import os
import game_framework
from state_machine import StateMachine

BASE = os.path.dirname(__file__)


def p(*names):
    return os.path.join(BASE, '120x80_PNGSheets', *names)


def cave_path(*names):
    return os.path.join(BASE, 'cave', *names)


FRAME_W = 120
FRAME_H = 80

PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

ROLL_SPEED_PPS = RUN_SPEED_PPS * 2.0
ROLL_DURATION = 0.45

ATTACK_DURATION = 0.45   # 공격 1회 재생 시간

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION

GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

MAX_DT = 1.0 / 30.0

# 피격 관련 상수
HIT_EFFECT_DURATION = 2.0
HIT_KNOCKBACK_DURATION = 0.2
HIT_KNOCKBACK_SPEED_PPS = 250.0

# 각성 관련 상수
SUPER_THRESHOLD_HP = 50
SUPER_SPEED_SCALE = 1.3
SUPER_SCALE_FACTOR = 1.4  # 캐릭터 크기 배율


class Idle:
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
            # 구르기 끝나면 다시 전투 판단을 위해 IDLE로
            self.knight.state_machine.change_state(self.knight.IDLE)

    def draw(self):
        self.knight.draw_current_frame()


class Attack:
    def __init__(self, knight):
        self.knight = knight
        self.fps = 0.0
        self.saved_dir = 0

    def enter(self, e):
        import random

        # AI가 다음 공격타입을 미리 정해놓았다면 우선 사용
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

        # 공격 중에는 제자리에서 휘두르도록
        self.saved_dir = self.knight.dir
        self.knight.dir = 0

        # 한 번만 맞도록 플래그 초기화
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
            # 공격 끝나면 다시 전투 판단을 위해 IDLE/ RUN 으로 돌아감
            if self.knight.dir == 0:
                self.knight.state_machine.change_state(self.knight.IDLE)
            else:
                self.knight.state_machine.change_state(self.knight.RUN)

    def draw(self):
        self.knight.draw_current_frame()


class Jump:
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

        if self.knight.y <= self.knight.ground_y:
            self.knight.y = self.knight.ground_y
            self.knight.vy = 0.0
            if self.knight.dir == 0:
                self.knight.state_machine.change_state(self.knight.IDLE)
            else:
                self.knight.state_machine.change_state(self.knight.RUN)

    def draw(self):
        self.knight.draw_current_frame()


class Die:
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.dir = 0
        self.knight.vy = 0.0

        self.knight.sheet = self.knight.dead_sheet
        self.knight.max_frames = self.knight.dead_frames
        self.knight.frame = 0.0
        self.knight.prev_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        self.knight.frame += self.knight.max_frames * ACTION_PER_TIME * dt
        if self.knight.frame >= self.knight.max_frames:
            self.knight.frame = self.knight.max_frames - 1

    def draw(self):
        self.knight.draw_current_frame()


class EvilKnight:
    def __init__(self):
        # 스프라이트 시트
        self.idle_sheet = load_image(p('_Idle.png'))
        self.run_sheet = load_image(p('_Run.png'))
        self.roll_sheet = load_image(p('_Roll.png'))
        self.jump_sheet = load_image(p('_Jump.png'))
        self.fall_sheet = load_image(p('_JumpFallInbetween.png'))
        self.attack1_sheet = load_image(p('_Attack.png'))
        self.attack2_sheet = load_image(p('_Attack2.png'))
        self.dead_sheet = load_image(p('_Death.png'))

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

        # 바디 히트박스 비율
        self.body_w_ratio = 0.20
        self.body_h_ratio = 0.50
        self.bb_y_offset_ratio = 0.25

        # 기본 크기와 현재 크기
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

        # 피격 효과
        self.hit_timer = 0.0
        self.knockback_timer = 0.0
        self.knockback_dir = 0

        # 각성 상태
        self.awakened = False
        self.speed_scale = 1.0

        # 공격/구르기 쿨타임
        self.attack_cool = 0.0
        self.roll_cool = 0.0

        # AI가 사용할 다음 공격 타입(1,2) – 0이면 랜덤
        self.next_attack_type = 0

        # AI가 참조할 대상 (Hero), 스테이지, 배경
        self.target = None
        self.stage = 1
        self.bg = None

        # 상태 객체
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
            self.FALL: {},
            self.DIE: {},
        }
        self.state_machine = StateMachine(self.IDLE, self.rules)

    # ---------------- 히트박스 계산 ----------------

    def draw_current_frame(self):
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
        from EvilKnight import Attack
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

    # ---------------- 피격/각성 ----------------

    def start_hit_effect(self, knockback_dir=None):
        self.hit_timer = HIT_EFFECT_DURATION
        self.knockback_timer = HIT_KNOCKBACK_DURATION

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

    # 각성 발동
    def super_power(self):
        if (not self.awakened) and self.hp < SUPER_THRESHOLD_HP:
            self.awakened = True
            self.speed_scale = SUPER_SPEED_SCALE
            # 각성 시 캐릭터 전체 크기 1.4배
            self.scale = self.base_scale * SUPER_SCALE_FACTOR

    # ---------------- AI 보조 함수 ----------------

    def is_on_ground(self):
        return abs(self.y - self.ground_y) < 1.0 and self.vy == 0.0

    def _find_stalactite_danger(self):
        """
        2스테이지에서 종유석이 바로 머리 위에 떨어질 위험이 있는지 검사.
        위험하면 그 종유석의 x와 피해야 하는 방향(+1/-1)을 돌려줌.
        """
        if self.stage != 2:
            return None
        if self.bg is None or not hasattr(self.bg, 'hazards'):
            return None

        hazards = self.bg.hazards
        stones = getattr(hazards, 'stones', [])
        for s in stones:
            if not getattr(s, 'active', False):
                continue
            # Evil의 바로 위 근처에 있고, 아직 어느 정도 위에 떠 있으면 위험으로 본다
            if abs(s.x - self.x) < 40 and s.y > self.y + 40:
                # 종유석 기준으로 한 칸 옆으로 피하도록 방향 선택
                side_dir = 1 if s.x <= self.x else -1
                return s.x, side_dir

        return None

    def ai_update(self):
        """
        간단한 전투 AI:
        1) 2스테이지에서 머리 위 종유석이 위험하면 먼저 피하고
        2) 그 외에는 Hero를 쫓아가거나 적당한 거리에서 공격
        """

        # 죽었거나 쓰러지는 중에는 AI 동작 안 함
        if self.hp <= 0:
            return
        cur = self.state_machine.cur_state
        if cur in (self.ATTACK, self.ROLL, self.JUMP, self.FALL, self.DIE):
            return

        target = self.target
        if target is None or getattr(target, 'hp', 0) <= 0:
            # 상대가 없으면 그냥 가만히
            if cur is not self.IDLE:
                self.dir = 0
                self.state_machine.change_state(self.IDLE)
            return

        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        # 쿨타임 감소
        if self.attack_cool > 0.0:
            self.attack_cool = max(0.0, self.attack_cool - dt)
        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - dt)

        # Hero 위치 기준 기본 정보
        dx = target.x - self.x
        dist = abs(dx)

        # 바라보는 방향은 항상 Hero 쪽
        if dist > 1.0:
            self.face_dir = 1 if dx > 0 else -1

        # ---------- 1단계 : 2스테이지에서는 종유석 회피를 우선 ----------
        # 너무 근접해서 이미 난투 중이면(거리 매우 가까움) 그냥 싸운다고 가정
        close_melee_dist = 80.0

        danger = self._find_stalactite_danger()
        if danger is not None and dist > close_melee_dist:
            stone_x, side_dir = danger
            # 위험 구역에서 한 칸 옆으로 빠르게 이동
            self.dir = side_dir
            if cur is not self.RUN:
                self.state_machine.change_state(self.RUN)
            return

        # ---------- 2단계 : 전투 기본 패턴 ----------
        attack_range = 110.0   # 이 안이면 공격
        chase_range = 450.0    # 이 안이면 쫓아감

        # 공격 각성 상태일수록 더 자주 휘두르게
        base_attack_cool = 1.0
        if self.awakened:
            base_attack_cool = 0.6

        # Hero와 적당히 붙었으면 공격
        if dist <= attack_range and self.is_on_ground():
            if self.attack_cool <= 0.0:
                # 약간 랜덤하게 콤보 연출
                import random
                if self.awakened and random.random() < 0.4:
                    self.next_attack_type = 2
                else:
                    self.next_attack_type = 1
                self.start_attack()
                self.attack_cool = base_attack_cool
                self.dir = 0
            else:
                # 쿨타임 중이면 살짝 뒤로 물러나는 느낌
                self.dir = -self.face_dir * 0.3
                if cur is not self.RUN:
                    self.state_machine.change_state(self.RUN)
            return

        # 아직 거리가 있으면 추격
        if dist <= chase_range:
            self.dir = 1 if dx > 0 else -1
            if cur is not self.RUN:
                self.state_machine.change_state(self.RUN)
            return

        # 너무 멀면 그냥 서있기
        self.dir = 0
        if cur is not self.IDLE:
            self.state_machine.change_state(self.IDLE)

    # ---------------- 기본 루프 ----------------

    def handle_event(self, e):
        # Evil은 플레이어 입력을 받지 않음 (AI 전용)
        pass

    def update(self):
        dt = game_framework.frame_time
        if dt > MAX_DT:
            dt = MAX_DT

        # 피격/넉백
        if self.hit_timer > 0.0:
            self.hit_timer = max(0.0, self.hit_timer - dt)
        if self.knockback_timer > 0.0:
            self.knockback_timer = max(0.0, self.knockback_timer - dt)
            self.x += self.knockback_dir * HIT_KNOCKBACK_SPEED_PPS * dt
            self.x = max(self.left_bound, min(self.x, self.right_bound))

        # 이미 죽었으면 죽는 애니메이션만 재생
        if self.hp <= 0:
            if self.state_machine.cur_state is not self.DIE:
                self.dir = 0
                self.vy = 0.0
                self.state_machine.change_state(self.DIE)
            self.state_machine.update()
            return

        # 각성 체크
        self.super_power()

        # 공격/구르기 쿨타임 감소 (ai_update 에서도 한 번 더 안전하게 감소)
        if self.attack_cool > 0.0:
            self.attack_cool = max(0.0, self.attack_cool - dt)
        if self.roll_cool > 0.0:
            self.roll_cool = max(0.0, self.roll_cool - dt)

        # AI 판단
        self.ai_update()

        # 현재 상태 동작
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

        # 디버그용 히트박스
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)

        atk_bb = self.get_attack_bb()
        if atk_bb is not None:
            draw_rectangle(*atk_bb)

    def start_attack(self):
        self.state_machine.change_state(self.ATTACK)
