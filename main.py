from pico2d import *
from grass import Grass
from HeroKnight import Boy
from EvilKnight import EvilKnight
import time
import game_framework



open_canvas()


grass = Grass()
boy = Boy()
evil = EvilKnight()


running = True

current_time = time.time()
MAX_DT = 1.0 / 30.0

while running:

    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            running = False
        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            running = False
        else:
            boy.handle_event(e)


    grass.update()
    boy.update()
    evil.update()


    clear_canvas()
    grass.draw()
    boy.draw()
    evil.draw()
    update_canvas()
    now = time.time()
    dt = now - current_time
    if dt > MAX_DT:
        dt = MAX_DT
    if dt < 0.0:
        dt = 0.0
    game_framework.frame_time = dt
    current_time = now





close_canvas()
