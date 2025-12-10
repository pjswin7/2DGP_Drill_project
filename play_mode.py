from pico2d import *
from grass import Grass, CaveGround
from HeroKnight import Boy, Block, ROLL_COOLTIME
from EvilKnight import EvilKnight
from stage_background import Stage1Background, Stage2Background
from portal import Portal
import time
import game_framework
import title_mode
import os

# 이 모듈은 실제 전투가 일어나는 플레이 모드를 담당하며
# HeroKnight.Boy, EvilKnight.EvilKnight, 배경, 포탈, UI를 모두 조합한다.


def resolve_ground(obj, ground):
    # 이 함수는 캐릭터의 바닥 충돌을 처리하며
    # Boy, EvilKnight의 y 좌표와 낙하 상태 전환을 관리한다.
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


def rects_intersect(a, b):
    # 이 함수는 두 사각형 박스가 겹치는지 검사하며
    # 포탈 충돌, 몸통 충돌, 공격 판정에 공통으로 사용된다.
    al, ab, ar, at = a
    bl, bb, br, bt = b
    return not (ar <= bl or br <= al or at <= bb or bt <= ab)


def is_ignoring_body_block(obj):
    # 이 함수는 구르기/점프/낙하/죽는 중인 객체가
    # 몸통 충돌을 무시해야 하는지 판정한다.
    if not hasattr(obj, 'state_machine'):
        return False

    cur = obj.state_machine.cur_state

    if hasattr(obj, 'ROLL') and cur == obj.ROLL:
        return True

    if hasattr(obj, 'JUMP') and cur == obj.JUMP:
        return True

    if hasattr(obj, 'FALL') and cur == obj.FALL:
        return True

    if hasattr(obj, 'DIE') and cur == obj.DIE:
        return True

    return False


def resolve_body_block(a, b):
    # 이 함수는 Hero와 Evil이 서로 몸통으로 겹치지 않도록
    # x 방향으로 밀어내는 충돌 처리를 담당한다.
    if is_ignoring_body_block(a) or is_ignoring_body_block(b):
        return

    al, ab, ar, at = a.get_bb()
    bl, bb, br, bt = b.get_bb()

    if not rects_intersect((al, ab, ar, at), (bl, bb, br, bt)):
        return

    overlap_left = ar - bl
    overlap_right = br - al

    if overlap_left < overlap_right:
        dx = -overlap_left
    else:
        dx = overlap_right

    a.x += dx / 2
    b.x -= dx / 2


def place_on_ground(obj, ground):
    # 이 함수는 캐릭터를 바닥 위에 정확히 올려놓으며
    # 스테이지 시작 시 Boy, Evil의 초기 위치를 맞출 때 사용된다.
    l, b, r, t = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()
    dy = gt - b
    obj.y += dy


def resolve_attack(attacker, defender):
    # 이 함수는 공격자와 방어자 사이의 공격 충돌을 처리하며
    # 양쪽 캐릭터의 get_attack_bb와 get_bb, 가드/넉백/피격을 모두 담당한다.
    atk_bb = attacker.get_attack_bb()
    if atk_bb is None:
        return

    def_bb = defender.get_bb()
    if not rects_intersect(atk_bb, def_bb):
        return

    if getattr(attacker, 'did_hit', False):
        return

    if hasattr(defender, 'state_machine') and hasattr(defender, 'ROLL'):
        if defender.state_machine.cur_state == defender.ROLL:
            return

    if hasattr(attacker, 'x') and hasattr(defender, 'x'):
        if attacker.x < defender.x:
            knock_dir = 1
        else:
            knock_dir = -1
    else:
        knock_dir = -getattr(defender, 'face_dir', 1)

    is_awakened_attacker = getattr(attacker, 'awakened', False)
    damage = 15 if is_awakened_attacker else 10

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
                return

    if hasattr(defender, 'apply_damage'):
        defender.apply_damage(damage, knock_dir)
    else:
        defender.hp = max(0, defender.hp - damage)

    attacker.did_hit = True


BAR_TARGET_WIDTH = 260.0
BAR_HEIGHT_SCALE = 0.3
HP_SLOTS = 10


def draw_status_bars(boy, evil):
    # 이 함수는 화면 상단의 HP/구르기/가드 바를 그리며
    # play_mode.draw에서 호출된다.
    global health_bar_image, roll_bar_image, block_bar_image

    if health_bar_image is None:
        return

    cw = get_canvas_width()
    ch = get_canvas_height()

    side_margin = 40
    top_margin = 40
    line_margin = 0

    target_w = BAR_TARGET_WIDTH

    def target_h(img):
        if img is None or img.w == 0:
            return 10.0
        base_h = img.h * (target_w / img.w)
        return base_h * BAR_HEIGHT_SCALE

    def draw_bar(img, ratio, x_left, y_center):
        if img is None:
            return

        ratio = max(0.0, min(1.0, ratio))
        if ratio <= 0.0:
            return

        full_w = img.w
        full_h = img.h

        src_w = full_w * ratio
        dst_w = target_w * ratio
        dst_h = target_h(img)

        sx = 0
        sy = 0

        img.clip_draw(sx, sy, int(src_w), full_h,
                      x_left + dst_w / 2, y_center,
                      dst_w, dst_h)

    def draw_slot_bar(img, cur_slots, max_slots, x_left, y_center):
        if img is None:
            return

        cur_slots = max(0, min(cur_slots, max_slots))
        if cur_slots == 0:
            return

        full_w = img.w
        full_h = img.h

        slot_src_w = full_w / max_slots
        src_w = slot_src_w * cur_slots

        slot_dst_w = target_w / max_slots
        dst_w = slot_dst_w * cur_slots
        dst_h = target_h(img)

        sx = 0
        sy = 0

        img.clip_draw(sx, sy, int(src_w), full_h,
                      x_left + dst_w / 2, y_center,
                      dst_w, dst_h)

    hero_x = side_margin
    evil_x = cw - side_margin - BAR_TARGET_WIDTH

    cur_y = ch - top_margin

    draw_slot_bar(health_bar_image,
                  int(HP_SLOTS * boy.hp / boy.max_hp),
                  HP_SLOTS,
                  hero_x, cur_y)

    cur_y -= target_h(health_bar_image) + line_margin

    roll_ratio = 1.0 - min(boy.roll_cool / ROLL_COOLTIME, 1.0)
    draw_bar(roll_bar_image, roll_ratio, hero_x, cur_y)

    cur_y -= target_h(roll_bar_image) + line_margin

    if hasattr(boy, 'guard_max'):
        guard_slots = int(HP_SLOTS * boy.guard_current / boy.guard_max)
    else:
        guard_slots = 0
    draw_slot_bar(block_bar_image,
                  guard_slots,
                  HP_SLOTS,
                  hero_x, cur_y)

    enemy_hp_slots = int(HP_SLOTS * evil.hp / evil.max_hp)
    draw_slot_bar(health_bar_image,
                  enemy_hp_slots,
                  HP_SLOTS,
                  evil_x, ch - top_margin)


def reset_hero_for_stage(boy):
    # 이 함수는 스테이지 전환 시 플레이어의 HP/가드/각성/피격 상태를 초기화하며
    # init()과 2스테이지 진입 시에 사용된다.
    boy.hp = boy.max_hp
    boy.guard_current = boy.guard_max
    boy.awakened = False
    boy.speed_scale = 1.0
    boy.scale = boy.base_scale

    boy.roll_cool = 0.0
    boy.hit_timer = 0.0
    boy.knockback_timer = 0.0
    boy.knockback_dir = 0

    boy.death_done = False


stage = 1
background = None
grass = None
boy = None
evil = None
portal = None

health_bar_image = None
roll_bar_image = None
block_bar_image = None

lose_image = None
win_image = None

game_result = None

MAX_DT = 1.0 / 30.0
_current_time = 0.0


def init():
    # 이 함수는 플레이 모드의 리소스와 객체를 초기화하며
    # title_mode에서 게임 시작 혹은 재시작 시 호출된다.
    global stage, background, grass, boy, evil, portal, _current_time
    global health_bar_image, roll_bar_image, block_bar_image
    global lose_image, win_image, game_result

    stage = 1

    background = Stage1Background()
    grass = Grass()
    boy = Boy()
    evil = EvilKnight()

    reset_hero_for_stage(boy)

    evil.target = boy
    evil.stage = stage
    evil.bg = background

    place_on_ground(boy, grass)
    place_on_ground(evil, grass)

    portal = None

    base_dir = os.path.dirname(__file__)
    health_bar_image = load_image(os.path.join(base_dir, 'cave', 'health_bar.png'))
    roll_bar_image = load_image(os.path.join(base_dir, 'cave', 'roll_bar.png'))
    block_bar_image = load_image(os.path.join(base_dir, 'cave', 'block_bar.png'))

    lose_image = load_image(os.path.join(base_dir, 'cave', 'lose.png'))
    win_image = load_image(os.path.join(base_dir, 'cave', 'win.png'))

    _current_time = time.time()
    game_result = None


def finish():
    # 이 함수는 플레이 모드가 스택에서 제거될 때 호출되는 정리용 함수이다.
    print('play_mode finish')


def handle_events():
    # 이 함수는 SDL 이벤트를 처리하여
    # ESC로 타이틀 전환, 포탈 진입, 게임 재시작, 플레이어 입력을 담당한다.
    global stage, background, grass, boy, evil, portal, game_result

    events = get_events()
    for e in events:
        if e.type == SDL_QUIT:
            game_framework.quit()
            continue

        if game_result is not None:
            if e.type == SDL_KEYDOWN:
                init()
            continue

        if e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE:
            game_framework.change_mode(title_mode)

        elif e.type == SDL_KEYDOWN and e.key == SDLK_DOWN:
            if portal is not None:
                if rects_intersect(boy.get_bb(), portal.get_bb()):
                    if stage == 1:
                        stage = 2
                        background = Stage2Background()
                        grass = CaveGround()

                        portal = None
                        evil = EvilKnight()

                        boy.x = 120
                        reset_hero_for_stage(boy)
                        place_on_ground(boy, grass)
                        place_on_ground(evil, grass)

                        evil.target = boy
                        evil.stage = stage
                        evil.bg = background

                        boy.state_machine.change_state(boy.IDLE)
                        boy.dir = 0
                        boy.vy = 0.0
        else:
            boy.handle_event(e)


def update():
    # 이 함수는 한 프레임 동안의 전체 게임 로직을 담당하며
    # 시간 갱신, 객체 업데이트, 충돌 처리, 승패 판정을 모두 수행한다.
    global background, grass, boy, evil, portal, _current_time, stage, game_result

    now = time.time()
    dt = now - _current_time
    if dt > MAX_DT:
        dt = MAX_DT
    if dt < 0.0:
        dt = 0.0
    game_framework.frame_time = dt
    _current_time = now

    if game_result is not None:
        return

    background.update()
    grass.update()
    boy.update()
    evil.update()

    if stage == 1 and evil.hp <= 0 and portal is None:
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

    if game_result is None:
        if boy.hp <= 0 and getattr(boy, 'death_done', False):
            if not (stage == 2 and evil.hp <= 0):
                game_result = 'LOSE'
        elif stage == 2 and evil.hp <= 0 and getattr(evil, 'death_done', False):
            game_result = 'WIN'


def draw():
    # 이 함수는 배경, 바닥, 포탈, 캐릭터, 상태 바, 승패 이미지를 모두 그리며
    # game_framework.run의 메인 루프에서 호출된다.
    global game_result, lose_image, win_image
    clear_canvas()
    background.draw()
    grass.draw()

    if portal is not None:
        portal.draw()

    boy.draw()
    evil.draw()
    draw_status_bars(boy, evil)

    if game_result is not None:
        img = None
        if game_result == 'LOSE':
            img = lose_image
        elif game_result == 'WIN':
            img = win_image

        if img is not None:
            cw = get_canvas_width()
            ch = get_canvas_height()
            iw, ih = img.w, img.h
            scale = min(cw / iw, ch / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            img.draw(cw // 2, ch // 2, draw_w, draw_h)

    update_canvas()


def pause():
    # 이 함수는 모드 스택 일시 정지 시 호출된다
    pass


def resume():
    # 이 함수는 일시 정지된 플레이 모드가 다시 활성화될 때 호출된다.
    pass
