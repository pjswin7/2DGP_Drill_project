from pico2d import *
from grass import Grass, CaveGround
from HeroKnight import Boy, Block, ROLL_COOLTIME
from EvilKnight import EvilKnight
from stage_background import Stage1Background, Stage2Background
from portal import Portal
import time
import game_framework
import title_mode   # ESC 눌렀을 때 타이틀로 돌아가기 위해
import os


def resolve_ground(obj, ground):
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()

    # 수평으로 아예 안 겹치면 무시
    if or_ < gl or gr < ol:
        return

    # 아래에서 땅에 닿는 경우만 처리
    if ob < gt:
        dy = gt - ob
        obj.y += dy
        if hasattr(obj, 'vy'):
            obj.vy = 0.0

        # 떨어지는 중이었다면 착지 상태로 전환
        if hasattr(obj, 'state_machine') and hasattr(obj, 'FALL'):
            cur = obj.state_machine.cur_state

            if cur == obj.FALL:
                if obj.dir == 0:
                    obj.state_machine.handle_state_event(('LANDED_IDLE', None))
                else:
                    obj.state_machine.handle_state_event(('LANDED_RUN', None))


def resolve_body_block(a, b):
    """캐릭터끼리 몸통끼리 겹치지 않도록 좌우로 밀어낸다."""
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
    """공격 히트박스와 몸 히트박스가 겹치면 데미지/가드 처리."""
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

    # 넉백 방향 : 공격자가 왼쪽에 있으면 +1, 오른쪽이면 -1
    if hasattr(attacker, 'x') and hasattr(defender, 'x'):
        if attacker.x < defender.x:
            knock_dir = 1
        else:
            knock_dir = -1
    else:
        knock_dir = -getattr(defender, 'face_dir', 1)

    # 공격력: 각성 여부에 따라 10 또는 15
    is_awakened_attacker = getattr(attacker, 'awakened', False)
    damage = 15 if is_awakened_attacker else 10

    # Hero가 Block 상태인 경우 가드로 막기 시도
    if isinstance(defender, Boy) and isinstance(defender.state_machine.cur_state, Block):
        front = False
        if hasattr(attacker, 'x'):
            if defender.face_dir == 1 and attacker.x >= defender.x:
                front = True
            elif defender.face_dir == -1 and attacker.x <= defender.x:
                front = True

        if front and getattr(defender, 'guard_current', 0) > 0:
            # 각성 상태 공격은 가드를 한 번에 다 날려버리게 하고 싶으면 True
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


# ===== 상태바 설정 =====
BAR_TARGET_WIDTH = 260.0   # 한 줄 가로 길이
BAR_HEIGHT_SCALE = 0.3     # 세로 크기를 원본의 30%로
HP_SLOTS = 10              # 체력바 칸 수(이미지 기준)


def draw_status_bars(boy, evil):
    """Hero : 체력 / 구르기 / 가드 3줄, Evil : 체력 1줄 그리기 (전부 상단)"""
    global health_bar_image, roll_bar_image, block_bar_image

    if health_bar_image is None:
        return

    cw = get_canvas_width()
    ch = get_canvas_height()

    side_margin = 40
    top_margin = 40
    line_margin = 0        # 바들 사이 여유 간격(픽셀)

    target_w = BAR_TARGET_WIDTH

    def target_h(img):
        """이미지 비율 유지 + 세로만 BAR_HEIGHT_SCALE 만큼 줄이기."""
        if img is None or img.w == 0:
            return 10.0
        base_h = img.h * (target_w / img.w)   # 비율 유지한 기본 높이
        return base_h * BAR_HEIGHT_SCALE      # 세로만 추가 축소

    def draw_bar(img, ratio, x_left, y_center):
        """연속 게이지(구르기) – 왼쪽에서 ratio 비율만큼 잘라서 그리기"""
        if img is None:
            return

        ratio = max(0.0, min(1.0, ratio))
        if ratio <= 0.0:
            return

        full_w = img.w
        full_h = img.h

        src_w = int(full_w * ratio)
        if src_w <= 0:
            src_w = 1

        dst_w = target_w * ratio
        dst_h = target_h(img)

        sx = 0
        sy = 0

        dx = x_left + dst_w * 0.5
        dy = y_center

        img.clip_draw(sx, sy, src_w, full_h, dx, dy, dst_w, dst_h)

    def draw_bar_slots(img, cur_slots, max_slots, x_left, y_center):
        """
        칸 단위 게이지(체력 / 가드).
        이미지 전체를 max_slots 칸이라고 보고,
        cur_slots 개 만큼만 왼쪽부터 채운다.
        """
        if img is None or max_slots <= 0:
            return

        cur_slots = max(0, min(cur_slots, max_slots))
        if cur_slots == 0:
            return

        full_w = img.w
        full_h = img.h

        # 소스 이미지에서 한 칸의 너비
        slot_src_w = full_w / max_slots
        src_w = slot_src_w * cur_slots

        # 화면에 그릴 때 한 칸의 너비
        slot_dst_w = target_w / max_slots
        dst_w = slot_dst_w * cur_slots
        dst_h = target_h(img)

        sx = 0
        sy = 0
        dx = x_left + dst_w * 0.5
        dy = y_center

        img.clip_draw(int(sx), int(sy), int(src_w), int(full_h), dx, dy, dst_w, dst_h)

    # 각 바의 실제 높이(비율 유지 + 30% 축소)
    hp_h = target_h(health_bar_image)
    roll_h = target_h(roll_bar_image)
    block_h = target_h(block_bar_image)

    # ----- Hero 쪽 : 상단에 3줄 -----
    hero_left = side_margin
    hero_hp_y = ch - top_margin
    hero_roll_y = hero_hp_y - ((hp_h + roll_h) / 2 + line_margin)
    hero_block_y = hero_roll_y - ((roll_h + block_h) / 2 + line_margin)

    # Hero HP (10칸)
    if boy.max_hp > 0:
        hero_hp_ratio = boy.hp / boy.max_hp
    else:
        hero_hp_ratio = 0.0

    hp_slots = int(hero_hp_ratio * HP_SLOTS)
    draw_bar_slots(health_bar_image, hp_slots, HP_SLOTS, hero_left, hero_hp_y)

    # Hero 구르기(연속 게이지)
    remain = getattr(boy, 'roll_cool', 0.0)
    if ROLL_COOLTIME > 0.0:
        roll_ratio = 1.0 - (remain / ROLL_COOLTIME)
    else:
        roll_ratio = 1.0
    roll_ratio = max(0.0, min(1.0, roll_ratio))

    draw_bar(roll_bar_image, roll_ratio, hero_left, hero_roll_y)

    # Hero 가드(칸 단위)
    guard_max = getattr(boy, 'guard_max', 1)
    guard_cur = getattr(boy, 'guard_current', 0)
    draw_bar_slots(block_bar_image, guard_cur, guard_max, hero_left, hero_block_y)

    # ----- Evil 체력 : 상단 오른쪽 HP 1줄 -----
    if evil and hasattr(evil, 'max_hp') and evil.max_hp > 0:
        evil_ratio = evil.hp / evil.max_hp
    else:
        evil_ratio = 0.0

    evil_slots = int(evil_ratio * HP_SLOTS)

    enemy_left = cw - side_margin - target_w
    enemy_hp_y = hero_hp_y  # 같은 높이
    draw_bar_slots(health_bar_image, evil_slots, HP_SLOTS, enemy_left, enemy_hp_y)


def place_on_ground(obj, ground):
    """객체를 현재 발 밑의 ground 위에 정확히 올려놓는다."""
    ol, ob, or_, ot = obj.get_bb()
    gl, gb, gr, gt = ground.get_bb()

    dy = gt - ob
    obj.y += dy

    if hasattr(obj, 'ground_y'):
        obj.ground_y = obj.y


def reset_hero_for_stage(boy):
    """
    스테이지 입장 시 Hero 상태 리셋:
    - HP 풀로
    - 가드 풀로
    - 각성 해제 / 크기 원래대로
    - 구르기 쿨 / 피격효과 초기화
    """
    boy.hp = boy.max_hp
    boy.guard_current = boy.guard_max
    boy.awakened = False
    boy.speed_scale = 1.0
    boy.scale = boy.base_scale

    boy.roll_cool = 0.0
    boy.hit_timer = 0.0
    boy.knockback_timer = 0.0
    boy.knockback_dir = 0


# ----------------------
# 여기서부터 게임 모드용 전역 변수
# ----------------------
stage = 1
background = None
grass = None
boy = None
evil = None
portal = None

# 상태바 이미지들
health_bar_image = None   # 체력 게이지
roll_bar_image = None     # 구르기 게이지
block_bar_image = None    # 방어/가드 게이지

MAX_DT = 1.0 / 30.0
_current_time = 0.0


def init():
    """타이틀에서 넘어올 때 한 번만 호출 – 게임 세계 초기화"""
    global stage, background, grass, boy, evil, portal, _current_time
    global health_bar_image, roll_bar_image, block_bar_image

    stage = 1

    background = Stage1Background()
    grass = Grass()
    boy = Boy()
    evil = EvilKnight()

    # Hero 상태 리셋
    reset_hero_for_stage(boy)

    # Evil AI에 타겟 / 스테이지 / 배경 연결
    evil.target = boy
    evil.stage = stage
    evil.bg = background

    place_on_ground(boy, grass)
    place_on_ground(evil, grass)

    portal = None

    # 상태바 이미지 로드
    base_dir = os.path.dirname(__file__)
    health_bar_image = load_image(os.path.join(base_dir, 'cave', 'health_bar.png'))
    roll_bar_image = load_image(os.path.join(base_dir, 'cave', 'roll_bar.png'))
    block_bar_image = load_image(os.path.join(base_dir, 'cave', 'block_bar.png'))

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

                        # Hero 위치 / 상태 리셋
                        boy.x = 120
                        reset_hero_for_stage(boy)
                        place_on_ground(boy, grass)

                        # Evil 위치 세팅
                        place_on_ground(evil, grass)

                        # Evil AI 연결
                        evil.target = boy
                        evil.stage = stage
                        evil.bg = background

                        boy.state_machine.change_state(boy.IDLE)
                        boy.dir = 0
                        boy.vy = 0.0
                    # stage == 2 인 상태에서의 추가 스테이지 진입은 없음 (2스테이지가 마지막)
        else:
            boy.handle_event(e)


def update():
    """매 프레임 게임 로직"""
    global background, grass, boy, evil, portal, _current_time, stage

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

    # Evil 사망 시 포탈 생성 (★ 1스테이지에서만 생성)
    if stage == 1 and evil.hp <= 0 and portal is None:
        portal_x = get_canvas_width() - 80
        portal_y_top = grass.top
        portal = Portal(portal_x, portal_y_top, stage=stage)

    if portal is not None:
        portal.update()

    resolve_ground(boy, grass)
    resolve_ground(evil, grass)
    resolve_body_block(boy, evil)

    resolve_attack(boy, evil)
    resolve_attack(evil, boy)

    if stage == 2:
        # 종유석 충돌(데미지만) + Evil AI는 background.hazards를 직접 보고 회피
        background.handle_hazard_collision(boy, evil)


def draw():
    clear_canvas()
    background.draw()
    grass.draw()

    if portal is not None:
        portal.draw()

    boy.draw()
    evil.draw()
    draw_status_bars(boy, evil)

    update_canvas()


def pause():
    pass


def resume():
    pass
