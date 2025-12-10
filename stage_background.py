from pico2d import *
import os
import random
import game_framework

# 이 모듈은 각 스테이지의 배경과 동굴 종유석(낙하 물체) 로직을 담당하며
# play_mode.py에서 배경 업데이트 및 충돌 처리에 사용된다.

BASE = os.path.dirname(__file__)


def kenny_bg(*names):
    # 이 함수는 케니 배경 이미지 경로를 구성하며
    # Stage1Background에서만 사용된다.
    return os.path.join(BASE, 'kenney_platformer-pack-redux', 'PNG', 'Backgrounds', *names)


class Stalactite:
    # 이 클래스는 2스테이지의 낙하하는 종유석 하나를 표현하며
    # CaveStalactites에서 여러 개를 관리한다.
    image = None
    FALL_SPEED_PPS = 350.0

    def __init__(self, x, y):
        if Stalactite.image is None:
            Stalactite.image = load_image(os.path.join(BASE, 'cave', 'cave_crystal.png'))
        self.x = x
        self.y = y
        self.active = True

    def update(self):
        # 이 메서드는 종유석을 아래로 떨어뜨리며
        # 화면 밖으로 나가면 비활성화한다.
        if not self.active:
            return

        self.y -= Stalactite.FALL_SPEED_PPS * game_framework.frame_time

        if self.y < -Stalactite.image.h:
            self.active = False

    def draw(self):
        # 이 메서드는 활성 상태의 종유석만 화면에 그린다.
        if self.active:
            Stalactite.image.draw(self.x, self.y)

    def get_bb(self):
        # 이 메서드는 종유석의 충돌 박스를 반환하며
        # CaveStalactites.handle_collision에서 Hero/Evil과의 충돌 검사에 사용된다.
        half_w = Stalactite.image.w * 0.25
        half_h = Stalactite.image.h * 0.5
        left = self.x - half_w
        right = self.x + half_w
        bottom = self.y - half_h
        top = self.y + half_h
        return left, bottom, right, top


class CaveStalactites:
    # 이 클래스는 동굴 천장에서 랜덤하게 떨어지는 종유석들을 관리하며
    # Stage2Background에서 소유하고 play_mode에서 충돌 처리에 사용된다.
    def __init__(self):
        self.stones = []
        self.spawn_timer = 0.0

    def update(self):
        # 이 메서드는 일정 시간마다 새로운 종유석을 생성하고
        # 기존 종유석들의 위치를 업데이트한다.
        self.spawn_timer -= game_framework.frame_time
        if self.spawn_timer <= 0.0:
            self.spawn_one()
            self.spawn_timer = random.uniform(1.0, 2.0)

        for s in self.stones:
            s.update()

        self.stones = [s for s in self.stones if s.active]

    def spawn_one(self):
        # 이 메서드는 화면 상단에서 새로운 종유석 하나를 생성한다.
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
        # 이 메서드는 관리 중인 모든 종유석을 그린다.
        for s in self.stones:
            s.draw()

    def handle_collision(self, *targets):
        # 이 메서드는 Hero와 Evil을 동시에 받아
        # 종유석과의 충돌 시 HP를 깎고 피격 처리를 수행한다.
        for s in self.stones:
            if not s.active:
                continue

            sl, sb, sr, st = s.get_bb()
            hit_any = False

            for obj in targets:
                if getattr(obj, 'hp', 0) <= 0:
                    continue

                # 롤링 상태일 때는 종유석도 무시하여 무적 판정을 유지한다.
                if hasattr(obj, 'state_machine') and hasattr(obj, 'ROLL'):
                    if obj.state_machine.cur_state == obj.ROLL:
                        continue

                ol, ob, or_, ot = obj.get_bb()
                if sl > or_ or sr < ol or sb > ot or st < ob:
                    continue

                if hasattr(obj, 'apply_damage'):
                    obj.apply_damage(15)
                else:
                    obj.hp -= 15

                hit_any = True

            if hit_any:
                s.active = False


class Stage1Background:
    # 이 클래스는 1스테이지의 초원 배경을 그리고
    # play_mode.update와 draw에서 사용된다.
    def __init__(self):
        self.image = load_image(kenny_bg('colored_land.png'))

    def update(self):
        # 이 메서드는 배경의 논리 업데이트를 담당한다.
        pass

    def draw(self):
        # 이 메서드는 화면 전체에 맞게 배경 이미지를 그린다.
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2)


class Stage2Background:
    # 이 클래스는 2스테이지의 동굴 배경과 종유석 Hazard를 관리하며
    # play_mode.update와 play_mode.update의 hazard 충돌 처리에서 사용된다..
    def __init__(self):
        self.image = load_image(os.path.join(BASE, 'cave', 'cave_background.png'))
        self.hazards = CaveStalactites()

    def update(self):
        # 이 메서드는 동굴 배경 위의 종유석들을 업데이트한다.
        self.hazards.update()

    def draw(self):
        # 이 메서드는 동굴 배경을 화면 크기에 맞게 그리고
        # 그 위에 종유석들을 그린다.
        cw = get_canvas_width()
        ch = get_canvas_height()
        self.image.draw(cw // 2, ch // 2, cw, ch)
        self.hazards.draw()

    def handle_hazard_collision(self, *targets):
        # 이 메서드는 play_mode.update에서 호출되며
        # Hero와 Evil이 종유석에 맞았는지 검사한다.
        self.hazards.handle_collision(*targets)
