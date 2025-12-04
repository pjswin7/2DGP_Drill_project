# play_mode.py
from pico2d import *
from grass import Grass, CaveGround, CastleGround
from HeroKnight import Boy, Block
from EvilKnight import EvilKnight
from stage_background import Stage1Background, Stage2Background, Stage3Background
from portal import Portal
import time
import game_framework
import title_mode   # ESC 눌렀을 때 타이틀로 돌아가기 위해


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

    if ar <= bl or br <= al:
        return
    if at <= bb or bt <= ab:
        return

    # 롤링 중이면 몸 히트박스 통과
    if hasattr(a, 'state_machine') and hasattr(a, 'ROLL'):
        if a.state_machine.cur_state == a.ROLL:
            return
    if hasattr(b, 'state_machine') and hasattr(b, 'ROLL'):
        if b.state_machine.cur_state == b.ROLL:
            return

    # 롤링이 아닐 때만 수평 충돌 해결
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
    atk_bb = attacker.get_attack_bb()
    if atk_bb is None:
        return

    def_bb = defender.get_bb()
    if not rects_intersect(atk_bb, def_bb):
        return

    # 이미 한 번 맞춘 공격이면 중복 히트 방지
    if getattr(attacker, 'did_hit', False):
        return

    # 롤링 중인 수비자는 무적
    if hasattr(defender, 'state_machine') and hasattr(defender, 'ROLL'):
        if defender.state_machine.cur_state == defender.ROLL:
            return

    # 넉백 방향
    if hasattr(attacker, 'x') and hasattr(defender, 'x'):
        if attacker.x < defender.x:
            knock_dir = 1
        else:
            knock_dir = -1
    else:
        knock_dir = -getattr(defender, 'face_dir', 1)

    # 공격력: 각성 여부에 따라 10 or 15
    is_awakened_attacker = getattr(attacker, 'awakened', False)
    damage = 15 if is_awakened_attacker else 10

    # Hero가 Block 상태인 경우
    if isinstance(defender, Boy) and isinstance(defender.state_machine.cur_state, Block):
        front = False
        if hasattr(attacker, 'x'):
            if defender.face_dir == 1 and attacker.x >= defender.x:
                front = True
            elif defender.face_dir == -1 and attacker.x <= defender.x:
                front = True

        if front and getattr(defender, 'guard_current', 0) > 0:
            use_all = is_awakened_attacker
            if defender.consume_guard(knock_dir, use_all=use_all):
                attacker.did_hit = True
                print(f'Guard! {defender.__class__.__name__} guard = {defender.guard_current}')
                return

    # 실제 데미지 적용
    if hasattr(defender, 'apply_damage'):
        defender.apply_damage(damage, knock_dir)
    else:
        defender.hp = max(0, defender.hp - damage)

    attacker.did_hit = True
    print(f'Hit! {defender.__class__.__name__} HP = {defender.hp}')


def draw_hp_bars(boy, evil):
    cw = get_canvas_width()
    ch = get_canvas_height()

    bar_w = 100
    bar_h = 10
    margin = 20

    # Hero HP
    x1 = margin
    y2 = ch - margin
    x2 = x1 + bar_w
    y1 = y2 - bar_h
    draw_rectangle(x1, y1, x2, y2)
    if boy.hp > 0:
        cur_w = bar_w * boy.hp / boy.max_hp
        draw_rectangle(x1, y1, x1 + cur_w, y2)

    # Hero Guard 게이지
    if hasattr(boy, 'guard_max') and hasattr(boy, 'guard_current'):
        segments = boy.guard_max
        if segments > 0:
            guard_y2 = y1 - 5
            guard_y1 = guard_y2 - bar_h
            seg_w = bar_w / segments
            gap = 2

            for i in range(segments):
                gx1 = margin + i * seg_w
                gx2 = gx1 + seg_w - gap
                draw_rectangle(gx1, guard_y1, gx2, guard_y2)
                if i < boy.guard_current:
                    draw_rectangle(gx1 + 1, guard_y1 + 1, gx2 - 1, guard_y2 - 1)

    # Evil HP
    x2 = cw - margin
    x1 = x2 - bar_w
    y2 = ch - margin
    y1 = y2 - bar_h
    draw_rectangle(x1, y1, x2, y2)
    if evil.hp > 0:
        cur_w = bar_w * evil.hp / evil.max_hp
        draw_rectangle(x2 - cur_w, y1, x2, y2)


def place_on_ground(obj, ground):
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()

    dy = gt - ob
    obj.y += dy

    if hasattr(obj, 'ground_y'):
        obj.ground_y = obj.y


# ----------------------
# 여기서부터 게임 모드용 전역 변수
# ----------------------
stage = 1
background = None
grass = None
boy = None
evil = None
portal = None

MAX_DT = 1.0 / 30.0
_current_time = 0.0


def init():
    """타이틀에서 넘어올 때 한 번만 호출 – 게임 세계 초기화"""
    global stage, background, grass, boy, evil, portal, _current_time

    stage = 1

    background = Stage1Background()
    grass = Grass()
    boy = Boy()
    evil = EvilKnight()

    place_on_ground(boy, grass)
    place_on_ground(evil, grass)

    portal = None

    _current_time = time.time()
    print('play_mode init')


def finish():
    """게임 끝날 때 정리할 게 있으면 여기서"""
    print('play_mode finish')


def handle_events():
    global stage, background, grass, boy, evil, portal

    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()

        elif e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            # ESC 누르면 타이틀 화면으로 복귀
            game_framework.change_mode(title_mode)

        elif e.type == SDL_KEYDOWN and e.key == SDLK_DOWN:
            # 포탈 위에서 아래키 → 다음 스테이지
            if portal is not None:
                if rects_intersect(boy.get_bb(), portal.get_bb()):
                    if stage == 1:
                        stage = 2
                        background = Stage2Background()
                        grass = CaveGround()

                        portal = None
                        evil = EvilKnight()

                        boy.x = 120
                        place_on_ground(boy, grass)
                        place_on_ground(evil, grass)

                        boy.state_machine.change_state(boy.IDLE)
                        boy.dir = 0
                        boy.vy = 0.0

                    elif stage == 2:
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


def update():
    """매 프레임 게임 로직"""
    global background, grass, boy, evil, portal, _current_time

    # frame_time 계산
    now = time.time()
    dt = now - _current_time
    if dt > MAX_DT:
        dt = MAX_DT
    if dt < 0.0:
        dt = 0.0
    game_framework.frame_time = dt
    _current_time = now

    background.update()
    grass.update()
    boy.update()
    evil.update()

    # Evil 사망 시 포탈 생성
    if evil.hp <= 0 and portal is None:
        portal_x = get_canvas_width() - 80
        portal_y_top = grass.top
        portal = Portal(portal_x, portal_y_top)

    if portal is not None:
        portal.update()

    resolve_ground(boy, grass)
    resolve_ground(evil, grass)
    resolve_body_block(boy, evil)

    resolve_attack(boy, evil)
    resolve_attack(evil, boy)

    if stage == 2:
        background.handle_hazard_collision(boy, evil)


def draw():
    clear_canvas()
    background.draw()
    grass.draw()

    if portal is not None:
        portal.draw()

    boy.draw()
    evil.draw()
    draw_hp_bars(boy, evil)

    update_canvas()


def pause():
    pass


def resume():
    pass
