from pico2d import *
import os

# 이 모듈은 스테이지의 바닥 타일을 그리며
# play_mode.py에서 충돌 처리와 함께 사용된다.

BASE = os.path.dirname(__file__)

GROUND_TOP_Y = 90       # 1스테이지 바닥의 화면 상 위치
CAVE_GROUND_DROP = 20   # 동굴 스테이지에서 실제 충돌 바닥이 시각적 바닥보다 내려가는 거리


def cave_path(name):
    # cave 폴더 안의 PNG 파일 경로를 구성하는 헬퍼 함수이다.
    return os.path.join(BASE, 'cave', name)


class Grass:
    # 이 클래스는 1스테이지의 초원 바닥을 그리며
    # play_mode.py에서 Boy, Evil의 착지 기준이 되는 충돌 박스를 제공한다.
    def __init__(self):
        self.tile = load_image(cave_path('grass.png'))
        self.top = GROUND_TOP_Y
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        # 이 메서드는 바닥 전체의 충돌 박스를 반환하며
        # play_mode.resolve_ground에서 사용된다.
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        # 이 메서드는 바닥의 논리 업데이트를 담당하며
        # 현재는 움직이지 않는 고정 바닥이라 내용이 없다.
        pass

    def draw(self):
        # 이 메서드는 화면 너비에 맞게 잔디 타일을 반복해서 그린다.
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h

        y = (self.bottom + self.top) / 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w


class CaveGround:
    # 이 클래스는 2스테이지의 동굴 바닥과 아래 배경을 그리며
    # play_mode.py에서 Boy, Evil의 착지 기준으로 사용된다.
    def __init__(self):
        self.tile = load_image(cave_path('cave_tile.png'))
        self.bottom_tile = load_image(cave_path('cave2_title.png'))

        # 화면에 보이는 바닥 위치와 실제 충돌 판정용 바닥 위치를 분리한다.
        self.visual_top = GROUND_TOP_Y
        self.top = self.visual_top - CAVE_GROUND_DROP
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        # 이 메서드는 동굴 바닥의 충돌 박스를 반환하며
        # play_mode.resolve_ground에서 사용된다.
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        # 이 메서드는 동굴 바닥의 논리 업데이트를 담당하며
        # 현재는 고정 바닥이므로 비어 있다.
        pass

    def draw(self):
        # 이 메서드는 화면 아래를 동굴 돌 배경으로 채우고
        # 맨 위 줄은 실제 발판 타일로 그린다.
        cw = get_canvas_width()

        # 아래쪽 채우는 타일
        bw, bh = self.bottom_tile.w, self.bottom_tile.h
        y = bh // 2
        while y < self.visual_top:
            x = bw // 2
            while x < cw + bw:
                self.bottom_tile.draw(x, y)
                x += bw
            y += bh

        # 실제 발판 타일
        w, h = self.tile.w, self.tile.h
        y = self.visual_top - h // 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w
