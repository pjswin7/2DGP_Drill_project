from pico2d import *
import os

from state_machine import StateMachine

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)


class Idle:
    def __init__(self, boy):
        self.boy = boy

    def do(self):
        # 프레임 진행(기존 Boy.update 내용)
        now = get_time()
        dt = now - self.boy.prev_time
        self.boy.prev_time = now
        self.boy.frame = (self.boy.frame + self.boy.fps * dt) % 8

    def draw(self):
        # 그리기(기존 Boy.draw 내용)
        image = self.boy.images[int(self.boy.frame)]
        w = int(image.w * self.boy.scale)
        h = int(image.h * self.boy.scale)
        image.draw(self.boy.x, self.boy.y, w, h)


class Boy:
    def __init__(self):
        self.images = [load_image(p('HeroKnight', 'Idle', f'HeroKnight_Idle_{i}.png')) for i in range(8)]  #각 이미지들을 프레임 모음으로 만들기 위한 코드
        self.frame = 0.0
        self.fps = 10
        self.scale=2.0
        self.x, self.y = 320, 80
        self.prev_time = get_time()  # 시작 기준 시간

        self.state_machine = StateMachine(Idle(self))

    def handle_event(self, e):
        pass

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()