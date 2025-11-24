from pico2d import *
from grass import Grass
from HeroKnight import Boy
from EvilKnight import EvilKnight
from stage_background import Stage1Background
from portal import Portal
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


def rects_intersect(a, b):
    al, ab, ar, at = a
    bl, bb, br, bt = b
    return not (ar <= bl or br <= al or at <= bb or bt <= ab)


def resolve_attack(attacker, defender):
    # 공격 히트박스가 없으면 패스
    atk_bb = attacker.get_attack_bb()
    if atk_bb is None:
        return

    def_bb = defender.get_bb()
    if not rects_intersect(atk_bb, def_bb):
        return

    # 이번 공격에서 이미 한 번 때렸으면 더 이상 데미지 없음
    if getattr(attacker, 'did_hit', False):
        return

    # HP 10 감소 (최소 0)
    defender.hp = max(0, defender.hp - 10)
    attacker.did_hit = True

    print(f'Hit! {defender.__class__.__name__} HP = {defender.hp}')




def draw_hp_bars(boy, evil):
    cw = get_canvas_width()
    ch = get_canvas_height()

    bar_w = 100
    bar_h = 10
    margin = 20

    # ----- Hero HP (왼쪽 상단, 왼쪽→오른쪽으로 줄어듦) -----
    x1 = margin
    y2 = ch - margin
    x2 = x1 + bar_w
    y1 = y2 - bar_h
    draw_rectangle(x1, y1, x2, y2)
    if boy.hp > 0:
        cur_w = bar_w * boy.hp / boy.max_hp
        draw_rectangle(x1, y1, x1 + cur_w, y2)

    # ----- Evil HP (오른쪽 상단, 오른쪽→왼쪽으로 줄어듦) -----
    x2 = cw - margin
    x1 = x2 - bar_w
    y2 = ch - margin
    y1 = y2 - bar_h
    draw_rectangle(x1, y1, x2, y2)
    if evil.hp > 0:
        cur_w = bar_w * evil.hp / evil.max_hp
        draw_rectangle(x2 - cur_w, y1, x2, y2)

open_canvas()

background = Stage1Background()


grass = Grass()
boy = Boy()
evil = EvilKnight()

evil.y = boy.y + 29
evil.ground_y = boy.ground_y + 29

portal = None


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
        elif e.type == SDL_KEYDOWN and e.key == SDLK_DOWN:

            if portal is not None:
                if rects_intersect(boy.get_bb(), portal.get_bb()):
                    print("포탈 진입! (여기서 동굴 스테이지로 전환 예정)")
                    # TODO: 여기서 동굴 배경/땅으로 바꾸고, 새 스테이지 세팅해 줄 것
        else:
            boy.handle_event(e)


    background.update()
    grass.update()
    boy.update()
    evil.update()

    # Evil이 죽으면 포탈 생성
    if evil.hp <= 0 and portal is None:
        portal_x = get_canvas_width() - 80  # 오른쪽 끝 근처
        portal_y_top = grass.top  # 땅 위쪽(y값)
        portal = Portal(portal_x, portal_y_top)

    # 포탈이 있으면 애니메이션 업데이트
    if portal is not None:
        portal.update()

    resolve_ground(boy, grass)
    resolve_ground(evil, grass)
    resolve_body_block(boy, evil)

    resolve_attack(boy, evil)  # Hero가 Evil을 때리는 경우
    resolve_attack(evil, boy)  # Evil이 Hero를 때리는 경우

    clear_canvas()
    background.draw()
    grass.draw()

    if portal is not None:
        portal.draw()


    boy.draw()
    evil.draw()
    draw_hp_bars(boy, evil)
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
