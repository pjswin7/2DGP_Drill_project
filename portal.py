from pico2d import *
import os
import game_framework

BASE = os.path.dirname(__file__)

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION


class Portal:
    def __init__(self, x, ground_top, stage=1):
        self.image = load_image(os.path.join(BASE, 'cave', 'portal.png'))

        self.rows = 3
        self.frame_h = self.image.h // self.rows

        self.cols = self.image.w // self.frame_h     # 한 줄 프레임 수
        self.frame_w = self.image.w // self.cols

        self.max_frames = self.cols

        self.frame = 0.0
        self.scale = 2.0

        self.open_row = 1
        self.idle_row = 2
        self.cur_row = self.open_row

        self.opening = True

        self.x = x
        self.ground_top = ground_top
        self.y = ground_top + (self.frame_h * self.scale) / 2.0

        # ★ 이 포탈이 속한 스테이지 (1일 때만 동작)
        self.stage = stage

    def update(self):
        # ★ 1스테이지가 아니면 아예 동작 안 함
        if self.stage != 1:
            return

        dt = game_framework.frame_time
        if dt < 0.0:
            dt = 0.0

        if self.opening:
            self.frame += self.max_frames * ACTION_PER_TIME * dt
            if self.frame >= self.max_frames:
                self.frame = 0.0
                self.opening = False
                self.cur_row = self.idle_row
        else:
            self.frame = (self.frame
                          + self.max_frames * ACTION_PER_TIME * dt) % self.max_frames

    def draw(self):
        # ★ 1스테이지가 아니면 그리지 않음
        if self.stage != 1:
            return

        fi = int(self.frame) % self.max_frames
        col = fi
        row = self.cur_row

        sx = col * self.frame_w
        sy = row * self.frame_h

        dw = int(self.frame_w * self.scale)
        dh = int(self.frame_h * self.scale)

        self.image.clip_draw(sx, sy, self.frame_w, self.frame_h,
                             self.x, self.y, dw, dh)

        l, b, r, t = self.get_bb()
        draw_rectangle(l, b, r, t)

    def get_bb(self):
        dw = self.frame_w * self.scale
        dh = self.frame_h * self.scale

        half_w = dw * 0.25
        hit_h = dh * 0.8

        left = self.x - half_w
        right = self.x + half_w
        bottom = self.ground_top
        top = bottom + hit_h
        return left, bottom, right, top
