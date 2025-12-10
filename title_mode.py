from pico2d import *
import game_framework
import play_mode
import os

# 이 모듈은 타이틀 화면 모드를 담당하며
# main.py에서 시작 모드로 사용된다.

BASE = os.path.dirname(__file__)


def cave_path(*names):
    # 이 함수는 타이틀 이미지가 있는 cave 폴더 경로를 구성하며
    # init()에서 타이틀 이미지를 로드할 때 사용된다.
    return os.path.join(BASE, 'cave', *names)


image = None


def init():
    # 이 함수는 타이틀 모드의 리소스를 초기화하며
    # game_framework.run 시작 시 최초로 호출된다.
    global image
    image = load_image(cave_path('main_title.png'))


def finish():
    # 이 함수는 타이틀 모드가 종료될 때 이미지 자원을 정리한다.
    global image
    if image is not None:
        del image


def handle_events():
    # 이 함수는 키보드/창 이벤트를 처리하며
    # 아무 키나 누르면 play_mode로 전환한다.
    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            game_framework.quit()
        elif e.type == SDL_KEYDOWN:
            game_framework.change_mode(play_mode)


def update():
    # 이 함수는 타이틀 모드의 논리 업데이트를 담당하며
    # 현재는 고정 화면이라 내용이 없다.
    pass


def draw():
    # 이 함수는 타이틀 이미지를 화면 크기에 맞게 그리며
    # game_framework.run의 메인 루프에서 호출된다.
    clear_canvas()

    cw = get_canvas_width()
    ch = get_canvas_height()

    iw, ih = image.w, image.h
    scale = max(cw / iw, ch / ih)
    draw_w = iw * scale
    draw_h = ih * scale

    image.draw(cw // 2, ch // 2, draw_w, draw_h)

    update_canvas()


def pause():
    # 이 함수는 모드 스택이 변경될 때 일시 정지용으로 제공되며
    # 현재는 별도 동작이 필요 없어 비어 있다.
    pass


def resume():
    # 이 함수는 일시 정지된 타이틀 모드가 다시 활성화될 때 호출된다.
    pass
