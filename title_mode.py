# title_mode.py
from pico2d import *
import game_framework
import play_mode     # 나중에 만들 play_mode.py (지금의 main 내용이 들어갈 파일)

import os

BASE = os.path.dirname(__file__)


def cave_path(*names):
    return os.path.join(BASE, 'cave', *names)


image = None


def init():
    global image
    # D:\GitHub\2DGP_Drill_project\2DGP_Drill_project\cave\main_title.png
    image = load_image(cave_path('main_title.png'))


def finish():
    global image
    if image is not None:
        del image


def handle_events():
    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            game_framework.quit()
        # 아무 키나 누르면 플레이 모드로 전환
        elif e.type == SDL_KEYDOWN:
            game_framework.change_mode(play_mode)


def update():
    # 타이틀 화면은 움직이는 거 없으면 그냥 패스
    pass


def draw():
    clear_canvas()
    # 타이틀 이미지를 화면 중앙에 그리기
    cw = get_canvas_width()
    ch = get_canvas_height()
    image.draw(cw // 2, ch // 2)
    update_canvas()


def pause():
    pass


def resume():
    pass
