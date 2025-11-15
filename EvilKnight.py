from pico2d import *
import os
import game_framework
from state_machine import StateMachine



BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, '120x80_PNGSheets', *names)



TIME_PER_ACTION   = 0.5
ACTION_PER_TIME   = 1.0 / TIME_PER_ACTION
IDLE_FRAMES       = 10
MAX_DT            = 1.0 / 30.0

class Idle:
    def __init__(self, knight):
        self.knight = knight

    def enter(self, e):
        self.knight.frame = 0.0
        self.knight.max_frames = IDLE_FRAMES
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


class EvilKnight:
    def __init__(self):

        self.idle_sheet = load_image(p('_Idle.png'))


        self.sheet_w, self.sheet_h = self.idle_sheet.w, self.idle_sheet.h
        self.max_frames = IDLE_FRAMES
        self.frame_w = self.sheet_w // self.max_frames
        self.frame_h = self.sheet_h


        self.frame = 0.0
        self.scale = 2.0
        self.x, self.y = 600, 80
        self.face_dir = -1

        # 나중에 AI가 쓸 수도 있는 값들
        self.dir = 0
        self.left_bound, self.right_bound = 30, 770
        self.ground_y = self.y


        self.IDLE = Idle(self)
        self.rules = {
            self.IDLE: {}
        }
        self.state_machine = StateMachine(self.IDLE, self.rules)

    def draw_current_frame(self):

        fi = int(self.frame) % self.max_frames
        sx = fi * self.frame_w
        sy = 0

        dw = int(self.frame_w * self.scale)
        dh = int(self.frame_h * self.scale)


        if self.face_dir == 1:
            self.idle_sheet.clip_draw(
                sx, sy, self.frame_w, self.frame_h,
                self.x, self.y, dw, dh
            )
        else:
            self.idle_sheet.clip_composite_draw(
                sx, sy, self.frame_w, self.frame_h,
                0, 'h',
                self.x, self.y, dw, dh
            )

    def handle_event(self, e):

        pass

    def update(self):

        self.state_machine.update()

    def draw(self):

        self.state_machine.draw()
