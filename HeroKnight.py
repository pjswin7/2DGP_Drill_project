
from pico2d import *

IMG_IDLE = 'HeroKnight_Idle_0.png'

class Boy:
    def __init__(self):
        self.x, self.y = 320, 120
        try:
            self.image = load_image(IMG_IDLE)
        except:
            self.image = None

    def handle_event(self, e):
        # 나중에 ←/→ 이동, 점프 등을 붙일 자리
        pass

    def update(self):
        # 지금은 로직 없음
        pass

    def draw(self):
        if self.image:
            self.image.draw(self.x, self.y)
        else:
            # 이미지가 없을 때 화면에 사각형이라도 그려서 존재 표시
            draw_rectangle(self.x-16, self.y-16, self.x+16, self.y+16)
