from pico2d import *
from grass import Grass, CaveGround, CastleGround
from HeroKnight import Boy
from EvilKnight import EvilKnight
from stage_background import Stage1Background, Stage2Background, Stage3Background
from portal import Portal
import time
import game_framework


def resolve_ground(obj, ground):
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()

    # 수평으로 아예 안 겹치면 무시
    if or_ < gl or gr < ol:
        return

    # 캐릭터가 땅 안으로 파고들었을 때만 위로 밀어 올림
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

    # a가 b의 왼쪽에 있으면 왼쪽으로, 아니면 오른쪽으로 밀어냄
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

    # HP 감소 + 피격 연출 (무적 포함)
    if hasattr(defender, 'apply_damage'):
        defender.apply_damage(10)
    else:
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


# [NEW] 땅 히트박스에 맞게 캐릭터를 자동으로 올려놓는 함수
def place_on_ground(obj, ground):
    """obj의 발(bottom)이 ground의 top에 딱 닿도록 y를 조정하고,
    obj.ground_y도 함께 갱신한다."""
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()

    dy = gt - ob
    obj.y += dy

    if hasattr(obj, 'ground_y'):
        obj.ground_y = obj.y


open_canvas()

stage = 1

background = Stage1Background()
grass = Grass()
boy = Boy()
evil = EvilKnight()

# [NEW] 처음 시작할 때도 땅 위에 정확히 세우기
place_on_ground(boy, grass)
place_on_ground(evil, grass)

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
                    if stage == 1:
                        # -------- 스테이지 1 -> 2 (동굴) --------
                        stage = 2
                        background = Stage2Background()
                        grass = CaveGround()

                        portal = None

                        evil = EvilKnight()

                        # x 위치만 정해주고, y는 땅 히트박스로 자동 정렬
                        boy.x = 120
                        place_on_ground(boy, grass)
                        place_on_ground(evil, grass)

                        boy.state_machine.change_state(boy.IDLE)
                        boy.dir = 0
                        boy.vy = 0.0

                    elif stage == 2:
                        # -------- 스테이지 2 -> 3 (성+용암) --------
                        stage = 3
                        background = Stage3Background()
                        grass = CastleGround()

                        portal = None

                        evil = EvilKnight()

                        boy.x = 120
                        place_on_ground(boy, grass)
                        place_on_ground(evil, grass)

                        boy.state_machine.change_state(boy.IDLE)
                        boy.dir = 0
                        boy.vy = 0.0

        else:
            boy.handle_event(e)

    background.update()
    grass.update()
    boy.update()
    evil.update()

    # Evil이 죽으면 포탈 생성
    if evil.hp <= 0 and portal is None:
        portal_x = get_canvas_width() - 80
        # 포탈도 땅 위에서 시작
        portal_y_top = grass.top
        portal = Portal(portal_x, portal_y_top)

    if portal is not None:
        portal.update()

    # 여전히 안전용으로 충돌 보정은 둔다
    resolve_ground(boy, grass)
    resolve_ground(evil, grass)
    resolve_body_block(boy, evil)

    resolve_attack(boy, evil)  # Hero가 Evil을 때리는 경우
    resolve_attack(evil, boy)  # Evil이 Hero를 때리는 경우

    if stage == 2:
        background.handle_hazard_collision(boy, evil)

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
