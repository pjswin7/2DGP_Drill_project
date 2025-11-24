from pico2d import *
import os
import game_framework

BASE = os.path.dirname(__file__)

TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION


class Portal:
    def __init__(self, x, ground_top):
        self.image = load_image(os.path.join(BASE, 'cave', 'portal.png'))

        # 스프라이트 시트: 가로 여러 칸 × 세로 3줄
        self.rows = 3
        self.frame_h = self.image.h // self.rows

        # 프레임이 정사각형이라고 가정
        self.cols = self.image.w // self.frame_h     # 한 줄 프레임 수
        self.frame_w = self.image.w // self.cols

        self.max_frames = self.cols

        self.frame = 0.0
        self.scale = 2.0

        # 실제 인덱싱: 0 = 맨 아래, 1 = 가운데, 2 = 맨 위
        # 너가 원하는 매핑:
        #   - 가운데 줄(2번째) : 처음 열릴 때 1번만 재생
        #   - 맨 위 줄(1번째)   : 그 다음 계속 반복
        self.open_row = 1       # 가운데 줄
        self.idle_row = 2       # 맨 위 줄
        self.cur_row = self.open_row

        self.opening = True     # 처음엔 열리는 중

        self.x = x
        self.ground_top = ground_top
        self.y = ground_top + (self.frame_h * self.scale) / 2.0

    def update(self):
        dt = game_framework.frame_time
        if dt < 0.0:
            dt = 0.0

        if self.opening:
            # 가운데 줄(열리는 애니메이션)을 1번만 재생
            self.frame += self.max_frames * ACTION_PER_TIME * dt
            if self.frame >= self.max_frames:
                self.frame = 0.0
                self.opening = False
                self.cur_row = self.idle_row
        else:
            # 열린 상태 유지: 맨 위 줄을 계속 반복
            self.frame = (self.frame
                          + self.max_frames * ACTION_PER_TIME * dt) % self.max_frames

    def draw(self):
        fi = int(self.frame) % self.max_frames
        col = fi
        row = self.cur_row

        sx = col * self.frame_w
        sy = row * self.frame_h    # sy=0 이 맨 아래 줄

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
