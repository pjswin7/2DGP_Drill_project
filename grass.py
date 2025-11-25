from pico2d import *
import os

BASE = os.path.dirname(__file__)


def kenny_path(*names):

    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', *names)


class Grass:
    def __init__(self):

        self.tile = load_image(kenny_path('Ground', 'Grass', 'grass.png'))


        self.top = 90
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

        self.top = 90
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

        bw, bh = self.bottom_tile.w, self.bottom_tile.h
        y = bh // 2
        while y < self.top:
            x = bw // 2
            while x < cw + bw:
                self.bottom_tile.draw(x, y)
                x += bw
            y += bh


        w, h = self.tile.w, self.tile.h
        y = (self.bottom + self.top) / 2
        x = w // 2
        while x < cw + w:
            self.tile.draw(x, y)
            x += w
        left, bottom, right, top = self.get_bb()
        draw_rectangle(left, bottom, right, top)




class CastleGround:
    def __init__(self):
        # 3스테이지 땅 타일 (두 번째 사진: cave_tile.png 재사용)
        self.tile = load_image(os.path.join(BASE, 'cave', 'cave_tile.png'))

        self.top = 90
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