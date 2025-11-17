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

TIME_PER_ACTION   = 0.5
ACTION_PER_TIME   = 1.0 / TIME_PER_ACTION

# 중력/점프 속도 (HeroKnight와 동일 값)
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
        # 달리는 중이면 그 방향으로, 아니면 보고 있는 방향으로 굴러감
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
            # 이후에는 단순히 서 있게만 함(나중에 AI에서 수정 가능)
            self.knight.state_machine.change_state(self.knight.IDLE)

    def draw(self):
        self.knight.draw_current_frame()


class Jump:
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        # 점프 시작 시 위로 쏘아 올리는 초기 속도
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

        # 애니메이션 프레임 진행
        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        # 위로 올라갔다가, vy가 0이 되면 떨어지기 시작
        self.knight.vy -= GRAVITY_PPS2 * dt
        self.knight.y  += self.knight.vy * dt

        if self.knight.vy <= 0:
            # 상승이 끝나면 떨어지는 상태로
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

        # 애니메이션 프레임 진행
        self.knight.frame = (
            self.knight.frame
            + self.knight.max_frames * ACTION_PER_TIME * dt
        ) % self.knight.max_frames

        # 아래로 떨어지기
        self.knight.vy -= GRAVITY_PPS2 * dt
        self.knight.y  += self.knight.vy * dt

        # 바닥에 닿으면 멈추고 Idle/Run으로 복귀
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
        self.idle_sheet = load_image(p('_Idle.png'))
        self.run_sheet  = load_image(p('_Run.png'))
        self.roll_sheet = load_image(p('_Roll.png'))
        self.jump_sheet = load_image(p('_Jump.png'))
        self.fall_sheet = load_image(p('_JumpFallInbetween.png'))

        # 모든 시트는 120x80 기준의 프레임으로 잘려 있음
        self.frame_w = FRAME_W
        self.frame_h = FRAME_H

        # 각 모션별 프레임 개수(가로 길이에서 계산)
        self.idle_frames = self.idle_sheet.w // self.frame_w
        self.run_frames  = self.run_sheet.w  // self.frame_w
        self.roll_frames = self.roll_sheet.w // self.frame_w
        self.jump_frames = self.jump_sheet.w // self.frame_w
        self.fall_frames = self.fall_sheet.w // self.frame_w

        # 현재 재생 중인 시트/프레임 정보
        self.sheet = self.idle_sheet
        self.max_frames = self.idle_frames
        self.frame = 0.0

        # 위치/방향/크기
        self.scale = 2.0
        self.x, self.y = 600, 80
        self.face_dir = -1  # 왼쪽을 보고 시작
        self.dir = 0        # 수평 이동 방향
        self.left_bound, self.right_bound = 30, 770
        self.ground_y = self.y

        # 수직 속도
        self.vy = 0.0

        # 상태 객체들
        self.IDLE = Idle(self)
        self.RUN  = Run(self)
        self.ROLL = Roll(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)

        # 지금은 AI가 없으니 이벤트 기반 전이는 비워 둔다
        self.rules = {
            self.IDLE: {},
            self.RUN: {},
            self.ROLL: {},
            self.JUMP: {},
            self.FALL: {},
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

    def handle_event(self, e):
        # 아직 플레이어 입력을 받지 않음(나중에 AI에서 직접 상태 전환 예정)
        pass

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()
