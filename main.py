# main.py
from pico2d import *
import game_framework
import title_mode as start_mode  # 시작은 타이틀 모드부터.

open_canvas()
bgm = load_music('cave/Dance_of_curse.mp3')
bgm.set_volume(64)
bgm.repeat_play()
game_framework.run(start_mode)
close_canvas()
