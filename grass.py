from pico2d import *
import os

BASE = os.path.dirname(__file__)

# 케니(kenney) 타일 경로용 헬퍼
def kenny_path(*names):
    # 실제 폴더 구조: kenney_platformer-pack-redux / PNG / ...
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', *names)


class Grass:
    def __init__(self):
        # 1스테이지 땅: PNG/Ground/Grass/grass.png
        self.tile = load_image(kenny_path('Ground', 'Grass', 'grass.png'))

    def get_bb(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h
        left = 0
        bottom = 0
        right = cw
        top = h
        return left, bottom, right, top

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        w, h = self.tile.w, self.tile.h
        y = h // 2
        x = w // 2
        while x < cw:
            self.tile.draw(x, y)
            x += w
