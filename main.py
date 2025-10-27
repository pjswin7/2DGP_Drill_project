from pico2d import *
from grass import Grass
from HeroKnight import Boy


open_canvas()


grass = Grass()
boy = Boy()


running = True
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


    clear_canvas()
    grass.draw()
    boy.draw()
    update_canvas()


    delay(0.03)


close_canvas()
