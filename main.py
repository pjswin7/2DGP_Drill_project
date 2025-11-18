from pico2d import *
from grass import Grass
from HeroKnight import Boy
from EvilKnight import EvilKnight
import time
import game_framework


def resolve_ground(obj, ground):
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()


    if or_ < gl or gr < ol:
        return


    if ob < gt:
        dy = gt - ob
        obj.y += dy
        if hasattr(obj, 'vy'):
            obj.vy = 0.0

        if hasattr(obj, 'state_machine') and hasattr(obj, 'FALL'):
            cur = obj.state_machine.cur_state

            if cur == obj.FALL:
                if obj.dir == 0:
                    obj.state_machine.handle_state_event(('LANDED_IDLE', None))
                else:
                    obj.state_machine.handle_state_event(('LANDED_RUN', None))


def resolve_body_block(a, b):
    al, ab, ar, at = a.get_bb()
    bl, bb, br, bt = b.get_bb()

    # 둘이 안 겹치면 아무것도 하지 않음
    if ar <= bl or br <= al:
        return
    if at <= bb or bt <= ab:
        return


    if a.x < b.x:
        shift = bl - ar
    else:
        shift = br - al
    a.x += shift


open_canvas()


grass = Grass()
boy = Boy()
evil = EvilKnight()

evil.y = boy.y + 29
evil.ground_y = boy.ground_y + 29


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

    resolve_ground(boy, grass)
    resolve_ground(evil, grass)
    resolve_body_block(boy, evil)

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
