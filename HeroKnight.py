from pico2d import *
import os

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)

class Boy:
    def __init__(self):
        self.images = [load_image(p('HeroKnight', 'Idle', f'HeroKnight_Idle_{i}.png')) for i in range(8)]  #각 이미지들을 프레임 모음으로 만들기 위한 코드
        self.frame = 0.0
        self.fps = 10
        self.scale=2.0
        self.x, self.y = 320, 80
        self.prev_time = get_time()  # 시작 기준 시간

    def handle_event(self, e):
        pass

    def update(self):
        now = get_time()
        dt = now - self.prev_time   # 지난 프레임에서 흐른 시간
        self.prev_time = now
        self.frame = (self.frame + self.fps * dt) % 8

    def draw(self):
        # 다른 파일 수정 없이도 캐릭터가 커져서 보임
        image = self.images[int(self.frame)]
        w = int(image.w * self.scale)
        h = int(image.h * self.scale)
        image.draw(self.x, self.y, w, h)