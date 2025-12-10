# main.py
from pico2d import *
import game_framework
import title_mode as start_mode  # 시작은 타이틀 모드부터.

open_canvas()
game_framework.run(start_mode)
close_canvas()