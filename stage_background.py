from pico2d import *
import os
import random
import game_framework

BASE = os.path.dirname(__file__)


def kenny_bg(*names):
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', 'Backgrounds', *names)


class Stalactite:
    image = None
    FALL_SPEED_PPS = 350.0  # 떨어지는 속도(픽셀/초)

    def __init__(self, x, y):
        if Stalactite.image is None:
            Stalactite.image = load_image(os.path.join(BASE, 'cave', 'cave_crystal.png'))
        self.x = x
        self.y = y
        self.active = True

    def update(self):
        if not self.active:
            return

        self.y -= Stalactite.FALL_SPEED_PPS * game_framework.frame_time

        if self.y < -Stalactite.image.h:
            self.active = False

    def draw(self):
        if self.active:
            Stalactite.image.draw(self.x, self.y)

    def get_bb(self):
        half_w = Stalactite.image.w * 0.25
        half_h = Stalactite.image.h * 0.5
        left   = self.x - half_w
        right  = self.x + half_w
        bottom = self.y - half_h
        top    = self.y + half_h
        return left, bottom, right, top


class CaveStalactites:
    def __init__(self):
        self.stones = []
        self.spawn_timer = 0.0

    def update(self):
        self.spawn_timer -= game_framework.frame_time
        if self.spawn_timer <= 0.0:
            self.spawn_one()
            self.spawn_timer = random.uniform(1.0, 2.0)

        for s in self.stones:
            s.update()

        self.stones = [s for s in self.stones if s.active]

    def spawn_one(self):
        cw = get_canvas_width()
        ch = get_canvas_height()

        margin = 40
        x = random.randint(margin, cw - margin)

        if Stalactite.image is not None:
            y = ch + Stalactite.image.h // 2
        else:
            y = ch + 50

        self.stones.append(Stalactite(x, y))

    def draw(self):
        for s in self.stones:
            s.draw()

    def handle_collision(self, *targets):
        # hero, evil 같이 넣어줄 예정
        for s in self.stones:
            if not s.active:
                continue

            sl, sb, sr, st = s.get_bb()
            hit_any = False

            for obj in targets:
                # 이미 죽은 애는 굳이 또 깎을 필요 없음
                if getattr(obj, 'hp', 0) <= 0:
                    continue

                # --- 롤링 중이면 종유석에도 무적 ---
                if hasattr(obj, 'state_machine') and hasattr(obj, 'ROLL'):
                    if obj.state_machine.cur_state == obj.ROLL:
                        continue

                ol, ob, or_, ot = obj.get_bb()
                # AABB 충돌 체크
                if sl > or_ or sr < ol or sb > ot or st < ob:
                    continue

                # 맞으면 HP 15 깎기 + 피격 연출
                if hasattr(obj, 'apply_damage'):
                    obj.apply_damage(15)
                else:
                    obj.hp -= 15

                hit_any = True

            # 누군가라도 맞았으면 이 종유석은 사라짐
            if hit_any:
                s.active = False


class Stage1Background:
    def __init__(self):
        self.image = load_image(kenny_bg('colored_land.png'))

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2)


class Stage2Background:
    def __init__(self):
        self.image = load_image(os.path.join(BASE, 'cave', 'cave_background.png'))

        # 동굴 종유석 객체 생성
        self.hazards = CaveStalactites()

    def update(self):
        self.hazards.update()

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        # 동굴 배경 먼저 그림
        self.image.draw(cw // 2, ch // 2, cw, ch)
        # 그 위에 종유석들 그림
        self.hazards.draw()

    def handle_hazard_collision(self, *targets):
        self.hazards.handle_collision(*targets)


class Stage3Background:
    def __init__(self):
        self.image = load_image(os.path.join(BASE, 'cave', 'rava_castle.png'))

    def update(self):
        pass

    def draw(self):
        cw = get_canvas_width()
        ch = get_canvas_height()
        # 화면을 꽉 채우도록 스케일
        self.image.draw(cw // 2, ch // 2, cw, ch)
