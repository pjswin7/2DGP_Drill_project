from pico2d import *
import os
import game_framework

BASE = os.path.dirname(__file__)

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION


class Portal:
    def __init__(self, x, ground_top):

        self.image = load_image(os.path.join(BASE, 'cave', 'portal.png'))


        self.max_frames = 16
        self.frame_w = self.image.w // self.max_frames
        self.frame_h = self.image.h

        self.frame = 0.0
        self.scale = 2.0

        self.x = x
        self.ground_top = ground_top

        self.y = ground_top + (self.frame_h * self.scale) / 2.0

    def update(self):
        dt = game_framework.frame_time
        if dt < 0.0:
            dt = 0.0
        self.frame = (self.frame
                      + self.max_frames * ACTION_PER_TIME * dt) % self.max_frames

    def draw(self):
        fi = int(self.frame) % self.max_frames
        sx = fi * self.frame_w
        sy = 0

        dw = int(self.frame_w * self.scale)
        dh = int(self.frame_h * self.scale)

        self.image.clip_draw(sx, sy, self.frame_w, self.frame_h,
                             self.x, self.y, dw, dh)

        # 히트박스 확인용
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
