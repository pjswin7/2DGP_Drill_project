from pico2d import *
import os
import game_framework

# 이 모듈은 1스테이지에서 Evil 처치 후 등장하는 포탈 애니메이션과
# 충돌 박스를 제공하며 play_mode.py에서 사용된다.

BASE = os.path.dirname(__file__)


def cave_path(name):
    # 이 함수는 cave 폴더 안의 포탈 스프라이트 경로를 구성하며
    # Portal.__init__에서 사용된다.
    return os.path.join(BASE, 'cave', name)


TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION


class Portal:
    # 이 클래스는 포탈 스프라이트를 애니메이션시키고
    # Hero와의 충돌 박스를 제공한다.
    def __init__(self, x, ground_top):
        self.image = load_image('cave/portal.png')

        # 스프라이트 시트는 세로 3줄, 가로 여러 프레임 구조라고 가정한다.
        self.rows = 3
        self.frame_h = self.image.h // self.rows

        self.cols = self.image.w // self.frame_h
        self.frame_w = self.image.w // self.cols

        self.max_frames = self.cols

        self.frame = 0.0
        self.scale = 2.0

        # 포탈의 각 행(row)의 의미: 1행 오픈, 2행 대기 등으로 사용.
        self.open_row = 1
        self.idle_row = 2
        self.cur_row = self.open_row

        self.opening = True

        self.x = x
        self.ground_top = ground_top
        self.y = ground_top + (self.frame_h * self.scale) / 2.0

    def update(self):
        # 이 메서드는 포탈의 애니메이션 프레임을 갱신하며
        # play_mode.update에서 호출된다.
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
        # 이 메서드는 포탈 스프라이트 한 프레임을 그리며
        # play_mode.draw에서 호출된다.
        fi = int(self.frame) % self.max_frames
        col = fi
        row = self.cur_row

        sx = col * self.frame_w
        sy = row * self.frame_h

        dw = int(self.frame_w * self.scale)
        dh = int(self.frame_h * self.scale)

        self.image.clip_draw(sx, sy, self.frame_w, self.frame_h,
                             self.x, self.y, dw, dh)

    def get_bb(self):
        # 이 메서드는 Hero가 포탈에 닿았는지 확인하기 위한
        # 충돌 박스를 반환하며 play_mode.handle_events에서 사용된다.
        dw = self.frame_w * self.scale
        dh = self.frame_h * self.scale

        half_w = dw * 0.25
        hit_h = dh * 0.8

        left = self.x - half_w
        right = self.x + half_w
        bottom = self.ground_top
        top = bottom + hit_h
        return left, bottom, right, top
