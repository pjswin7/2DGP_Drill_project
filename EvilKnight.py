from pico2d import *
import os
import game_framework
from state_machine import StateMachine

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, '120x80_PNGSheets', *names)


FRAME_W = 120
FRAME_H = 80

PIXEL_PER_METER = (10.0 / 0.3)

RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM  = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS  = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS  = (RUN_SPEED_MPS * PIXEL_PER_METER)

ROLL_SPEED_PPS   = RUN_SPEED_PPS * 2.0
ROLL_DURATION    = 0.45

ATTACK_DURATION  = 0.45   # 공격 1회 재생 시간

TIME_PER_ACTION   = 0.5
ACTION_PER_TIME   = 1.0 / TIME_PER_ACTION

GRAVITY_PPS2 = 1200.0
JUMP_SPEED_PPS = 560.0

MAX_DT = 1.0 / 30.0


class Idle:
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.sheet = self.knight.idle_sheet
        self.knight.max_frames = self.knight.idle_frames
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

        self.knight.x += self.knight.dir * RUN_SPEED_PPS * dt
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

        self.knight.x += self.move_dir * ROLL_SPEED_PPS * dt
        self.knight.x = max(self.knight.left_bound,
                            min(self.knight.x, self.knight.right_bound))

        if self.elapsed >= ROLL_DURATION:
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
        # 1번/2번 공격 중 하나를 한 번만 랜덤 선택
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
        self.knight.dir = 0          # 공격 중에는 이동 정지

        self.fps = self.knight.max_frames / ATTACK_DURATION

    def exit(self, e):
        # 끝나면 원래 이동 방향 복구
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
            # 공격이 끝나면 서 있거나(Idle), 달리거나(Run) 중 하나로 복귀
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
        self.knight.y  += self.knight.vy * dt

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
        self.knight.y  += self.knight.vy * dt

        if self.knight.y <= self.knight.ground_y:
            self.knight.y = self.knight.ground_y
            self.knight.vy = 0.0
            if self.knight.dir == 0:
                self.knight.state_machine.change_state(self.knight.IDLE)
            else:
                self.knight.state_machine.change_state(self.knight.RUN)

    def draw(self):
        self.knight.draw_current_frame()


class EvilKnight:
    def __init__(self):
        # 각 모션별 스프라이트 시트 로드
        self.idle_sheet   = load_image(p('_Idle.png'))
        self.run_sheet    = load_image(p('_Run.png'))
        self.roll_sheet   = load_image(p('_Roll.png'))
        self.jump_sheet   = load_image(p('_Jump.png'))
        self.fall_sheet   = load_image(p('_JumpFallInbetween.png'))
        self.attack1_sheet = load_image(p('_Attack.png'))
        self.attack2_sheet = load_image(p('_Attack2.png'))

        # 모든 시트는 120x80 기준의 프레임으로 잘려 있음
        self.frame_w = FRAME_W
        self.frame_h = FRAME_H

        # 각 모션별 프레임 개수(가로 길이에서 계산)
        self.idle_frames    = self.idle_sheet.w    // self.frame_w
        self.run_frames     = self.run_sheet.w     // self.frame_w
        self.roll_frames    = self.roll_sheet.w    // self.frame_w
        self.jump_frames    = self.jump_sheet.w    // self.frame_w
        self.fall_frames    = self.fall_sheet.w    // self.frame_w
        self.attack1_frames = self.attack1_sheet.w // self.frame_w
        self.attack2_frames = self.attack2_sheet.w // self.frame_w

        self.sheet = self.idle_sheet
        self.max_frames = self.idle_frames
        self.frame = 0.0

        self.body_w_ratio = 0.22
        self.body_h_ratio = 0.60
        self.bb_y_offset_ratio = 0.20
        self.bb_x_offset_ratio = 0.05

        self.scale = 2.0
        self.x, self.y = 600, 80
        self.face_dir = -1
        self.dir = 0
        self.left_bound, self.right_bound = 30, 770
        self.ground_y = self.y

        self.vy = 0.0
        self.prev_time = get_time()

        self.IDLE   = Idle(self)
        self.RUN    = Run(self)
        self.ROLL   = Roll(self)
        self.ATTACK = Attack(self)
        self.JUMP   = Jump(self)
        self.FALL   = Fall(self)

        # 아직 AI/입력 없음 → 규칙 비워둠
        self.rules = {
            self.IDLE:   {},
            self.RUN:    {},
            self.ROLL:   {},
            self.ATTACK: {},
            self.JUMP:   {},
            self.FALL:   {},
        }
        self.state_machine = StateMachine(self.IDLE, self.rules)

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

        offset_y = full_h * self.bb_y_offset_ratio
        cy = self.y - offset_y

        offset_x = full_w * self.bb_x_offset_ratio
        cx = self.x + offset_x

        left = cx - half_w
        bottom = cy - half_h
        right = cx + half_w
        top = cy + half_h
        return left, bottom, right, top

    def get_attack_bb(self):
        if not isinstance(self.state_machine.cur_state, Attack):
            return None

        full_w = self.frame_w * self.scale
        full_h = self.frame_h * self.scale

        body_w = full_w * self.body_w_ratio
        sword_w = body_w * 0.9
        sword_h = full_h * 0.5

        cx = self.x + self.face_dir * (body_w * 0.5 + sword_w * 0.5)
        cy = self.y + full_h * 0.1

        half_w = sword_w / 2
        half_h = sword_h / 2
        left   = cx - half_w
        bottom = cy - half_h
        right  = cx + half_w
        top    = cy + half_h
        return left, bottom, right, top


    def handle_event(self, e):
        # 아직 플레이어 입력 없음(나중에 AI에서 직접 state 변경 예정)
        pass

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)

        atk_bb = self.get_attack_bb()
        if atk_bb is not None:
            draw_rectangle(*atk_bb)

    # 나중에 테스트하거나 AI에서 호출하기 편하게 공격 트리거용 함수 하나 추가
    def start_attack(self):
        self.state_machine.change_state(self.ATTACK)
