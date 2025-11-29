from pico2d import *
import os

BASE = os.path.dirname(__file__)

# 화면 기준 1/3쯤 되는 높이 – 1,3스테 땅 윗면 기준
GROUND_TOP_Y = 90

# 2스테이지(동굴)에서 "충돌선"을 그림보다 얼마나 아래로 내릴지 (픽셀)
# 캐릭터가 여전히 떠 보이면 이 값을 더 키우고,
# 너무 파묻혀 보이면 값을 줄이면 된다.
CAVE_GROUND_DROP = 20


def kenny_path(*names):
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', *names)


class Grass:
    def __init__(self):
        self.tile = load_image(kenny_path('Ground', 'Grass', 'grass.png'))

        self.top = GROUND_TOP_Y
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h

        y = (self.bottom + self.top) / 2

        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w

        # 바닥 충돌 박스 확인용
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)


class CaveGround:
    def __init__(self):
        self.tile = load_image(os.path.join(BASE, 'cave', 'cave_tile.png'))
        self.bottom_tile = load_image(os.path.join(BASE, 'cave', 'cave2_title.png'))

        # 그림상 윗면 위치는 그대로 90 근처에 두고,
        # 충돌선만 CAVE_GROUND_DROP 만큼 아래로 내린다.
        self.visual_top = GROUND_TOP_Y          # 타일 그림의 윗면 근처
        self.top = self.visual_top - CAVE_GROUND_DROP  # 실제 충돌용 윗면
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()

        # 아래쪽 꽉 채우는 타일 (cave2_title)
        bw, bh = self.bottom_tile.w, self.bottom_tile.h
        y = bh // 2
        # 그림은 예전처럼 visual_top까지 채운다
        while y < self.visual_top:
            x = bw // 2
            while x < cw + bw:
                self.bottom_tile.draw(x, y)
                x += bw
            y += bh

        # 실제 바닥 타일 한 줄 (cave_tile)
        w, h = self.tile.w, self.tile.h
        # 그림은 visual_top 기준으로 그린다 (전과 같은 위치)
        y = self.visual_top - h // 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w

        # 충돌 박스는 내려간 top/bottom 기준으로 그림
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)


class CastleGround:
    def __init__(self):
        # 3스테이지 땅 타일 (cave_tile.png 재사용)
        self.tile = load_image(os.path.join(BASE, 'cave', 'cave_tile.png'))

        self.top = GROUND_TOP_Y
        self.bottom = self.top - self.tile.h

    def get_bb(self):
        cw = get_canvas_width()
        left = 0
        right = cw
        return left, self.bottom, right, self.top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h

        # 공중에 떠 있는 한 줄만 그리기
        y = (self.bottom + self.top) / 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w

        # 충돌 박스 (땅 한 줄만)
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)
