# title_mode.py
from pico2d import *
import game_framework
import play_mode
import os

# 이 모듈은 타이틀 화면 모드를 담당하며
# main.py에서 시작 모드로 사용된다.

BASE = os.path.dirname(__file__)


def cave_path(name):
    # cave 폴더 안의 타이틀 이미지 경로를 만들어 주는 함수
    # init()에서 main_title.png를 로드할 때 사용된다.
    return os.path.join(BASE, 'cave', name)


image = None  # 타이틀 화면 이미지


def init():
    # 타이틀 모드 진입 시 호출되며
    # 타이틀 배경 이미지를 로드한다.
    global image
    image = load_image(cave_path('main_title.png'))


def finish():
    # 타이틀 모드가 종료될 때 호출되는 정리용 함수
    # 현재는 별도 정리할 리소스가 없다.
    pass


def handle_events():
    # SDL 이벤트를 처리하며
    # ESC → 게임 종료, 그 외 아무 키 → play_mode로 전환한다.
    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN:
            if e.key == SDLK_ESCAPE:
                game_framework.quit()
            else:
                game_framework.change_mode(play_mode)


def update():
    # 타이틀 화면의 논리 업데이트를 담당한다.
    # 현재는 별다른 동작이 없다.
    pass


def draw():
    # 타이틀 이미지를 비율은 유지하면서
    # 화면을 여백 없이 꽉 채우도록 그린다 (잘리는 부분 허용).
    clear_canvas()
    if image is not None:
        cw = get_canvas_width()
        ch = get_canvas_height()

        iw, ih = image.w, image.h

        # 화면을 완전히 덮도록 하는 스케일 (cover 방식)
        scale = max(cw / iw, ch / ih)

        draw_w = int(iw * scale)
        draw_h = int(ih * scale)

        # 가운데를 기준으로 그리면 넘치는 부분은 자동으로 잘린다.
        image.draw(cw // 2, ch // 2, draw_w, draw_h)

    update_canvas()


def pause():
    # 모드 스택 일시 정지 시 호출된다.
    pass


def resume():
    # 일시 정지된 타이틀 모드가 다시 활성화될 때 호출된다.
    pass
