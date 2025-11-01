from pico2d import *
import os



# self.vy(수직속도), self.g(중력), self.jump_speed(초기속도), self.ground_y(바닥 높이)
#  self.air_vx(공중에서 유지할 수평 속도),


from state_machine import StateMachine

BASE = os.path.dirname(__file__)
def p(*names):
    return os.path.join(BASE, 'Hero Knight', 'Sprites', *names)



def right_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_RIGHT
def right_up(e):    return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_RIGHT
def left_down(e):   return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_LEFT
def left_up(e):     return e[0] == 'INPUT' and e[1].type == SDL_KEYUP   and e[1].key == SDLK_LEFT

def space_down(e):  return e[0] == 'INPUT' and e[1].type == SDL_KEYDOWN and e[1].key == SDLK_SPACE
def jump_done(e):   return e[0] == 'JUMP_DONE'
def fall_done(e):   return e[0] == 'FALL_DONE'
def landed_run(e):   return e[0] == 'LANDED_RUN'     # 착지 + 이동중
def landed_idle(e):  return e[0] == 'LANDED_IDLE'    # 착지 + 정지


class Idle:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0
        self.boy.y = self.boy.ground_y
        self.boy.vy = 0
        self.boy.frame = 0
        self.boy.prev_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        # 프레임 진행(기존 Boy.update 내용)
        now = get_time()
        dt = now - self.boy.prev_time
        self.boy.prev_time = now
        self.boy.frame = (self.boy.frame + self.boy.fps * dt) % 8

    def draw(self):
        # 그리기(기존 Boy.draw 내용)
        image = self.boy.images[int(self.boy.frame)]
        w = int(image.w * self.boy.scale)
        h = int(image.h * self.boy.scale)
        if self.boy.face_dir == 1:  # 오른쪽을 보는 중
            image.draw(self.boy.x, self.boy.y, w, h)
        else:  # 왼쪽을 보는 중
            image.composite_draw(0, 'h', self.boy.x, self.boy.y, w, h)



class Run:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        if right_down(e):
            self.boy.dir = 1
            self.boy.face_dir = 1
        elif left_down(e):
            self.boy.dir = -1
            self.boy.face_dir = -1
        self.boy.y = self.boy.ground_y
        self.boy.vy = 0
        self.boy.frame = 0
        self.boy.prev_time = get_time()

    def exit(self, e):
        pass

    def do(self):
        now = get_time()
        dt = now - self.boy.prev_time
        if dt > 0.05: dt = 0.05  # 큰 프레임 간격 캡
        self.boy.prev_time = now

        # 초당 self.boy.fps 만큼 진행
        self.boy.frame = (self.boy.frame + self.boy.fps * dt) % len(self.boy.run_images)

        # 초당 run_px_per_sec 만큼 이동
        self.boy.x += self.boy.dir * self.boy.run_px_per_sec * dt
        self.boy.x = max(self.boy.left_bound, min(self.boy.x, self.boy.right_bound))

    def draw(self):
        image = self.boy.run_images[int(self.boy.frame)]
        w = int(image.w * self.boy.scale);
        h = int(image.h * self.boy.scale)
        # 좌/우 반전은 시트 레이아웃에 따라 필요 시 composite_draw로
        if self.boy.face_dir == 1:
            image.draw(self.boy.x, self.boy.y, w, h)
        else:
            image.composite_draw(0, 'h', self.boy.x, self.boy.y, w, h)




class Jump:
    def __init__(self, boy): self.boy = boy
    def enter(self, e):
        if space_down(e):               # Space로 진입했을 때만 프레임 리셋
            self.boy.jump_idx = 0
            self.boy.anim_acc = 0.0
            # 지상 체크 제거하고 항상 점프 시작 속도 부여 + 바닥에 스냅
            self.boy.y = self.boy.ground_y
            self.boy.vy = self.boy.jump_speed
        self.boy.prev_time = get_time()

        if right_down(e): self.boy.face_dir = 1
        if left_down(e):  self.boy.face_dir = -1

    def exit(self, e): pass
    def do(self):
        now = get_time()
        dt = now - self.boy.prev_time
        if dt > 0.05: dt = 0.05
        self.boy.prev_time = now


        self.boy.vy += self.boy.g * dt
        self.boy.y += self.boy.vy * dt

        # 마지막 컷에서 멈추기(이벤트 보내지 않음)
        self.boy.anim_acc += dt
        if self.boy.anim_acc >= 1.0 / self.boy.fps:
            self.boy.anim_acc = 0.0
            if self.boy.jump_idx < self.boy.JUMP_LAST:
                self.boy.jump_idx += 1


        # 정점 도달 시에만 낙하로 전환
        if self.boy.vy <= 0:
            self.boy.state_machine.handle_state_event(('JUMP_DONE', None))

    def draw(self):
        img = self.boy.jump_images[min(self.boy.jump_idx, self.boy.JUMP_LAST)]
        w = int(img.w * self.boy.scale); h = int(img.h * self.boy.scale)
        if self.boy.face_dir == 1: img.draw(self.boy.x, self.boy.y, w, h)
        else: img.composite_draw(0, 'h', self.boy.x, self.boy.y, w, h)



class Fall:
    def __init__(self, boy): self.boy = boy
    def enter(self, e):
        if jump_done(e):
            self.boy.fall_idx = 0
            self.boy.anim_acc = 0.0
        self.boy.prev_time = get_time()
        if right_down(e): self.boy.face_dir = 1
        if left_down(e):  self.boy.face_dir = -1
    def exit(self, e): pass
    def do(self):
        now = get_time()
        dt = now - self.boy.prev_time
        if dt > 0.05: dt = 0.05
        self.boy.prev_time = now

        # 낙하 중 수직 이동(중력만)
        self.boy.vy += self.boy.g * dt
        self.boy.y += self.boy.vy * dt

        if self.boy.y <= self.boy.ground_y:
            self.boy.y = self.boy.ground_y
            self.boy.vy = 0
            if self.boy.dir != 0:
                self.boy.state_machine.handle_state_event(('LANDED_RUN', None))
            else:
                self.boy.state_machine.handle_state_event(('LANDED_IDLE', None))
            return  # 여기서 끝 (아래 프레임 갱신 생략)

            # 애니 프레임 넘김 (공중일 때만)
        self.boy.anim_acc += dt
        if self.boy.anim_acc >= 1.0 / self.boy.fps:
            self.boy.anim_acc = 0.0
            self.boy.fall_idx = min(self.boy.fall_idx + 1, self.boy.FALL_LAST)


    def draw(self):
        img = self.boy.fall_images[min(self.boy.fall_idx, self.boy.FALL_LAST)]
        w = int(img.w * self.boy.scale); h = int(img.h * self.boy.scale)
        if self.boy.face_dir == 1: img.draw(self.boy.x, self.boy.y, w, h)
        else: img.composite_draw(0, 'h', self.boy.x, self.boy.y, w, h)






class Boy:
    def __init__(self):
        self.images = [load_image(p('HeroKnight', 'Idle', f'HeroKnight_Idle_{i}.png')) for i in range(8)]
        self.run_images = [load_image(p('HeroKnight', 'Run', f'HeroKnight_Run_{i}.png')) for i in range(10)]  #각 이미지들을 프레임 모음으로 만들기 위한 코드

        self.JUMP_LAST = 1
        self.FALL_LAST = 3
        self.jump_images = [load_image(p('HeroKnight', 'Jump', f'HeroKnight_Jump_{i}.png')) for i in range(self.JUMP_LAST + 1)]
        self.fall_images = [load_image(p('HeroKnight', 'Fall', f'HeroKnight_Fall_{i}.png')) for i in range(self.FALL_LAST + 1)]


        self.frame = 0.0
        self.fps = 10
        self.scale=2.0
        self.x, self.y = 320, 80
        self.prev_time = get_time()  # 시작 기준 시간


        self.dir = 0
        self.face_dir = 1
        self.left_bound, self.right_bound = 30, 770

        self.jump_idx = 0
        self.fall_idx = 0
        self.anim_acc = 0.0

        self.ground_y = self.y  # 시작 y를 바닥으로 사용
        self.vy = 0.0
        self.g = -1200.0  # 중력(픽셀/초^2) - 필요하면 숫자만 바꿔
        self.jump_speed = 600.0  # 점프 초기속도(픽셀/초)
        self.run_px_per_sec = 300.0

        #  상태 객체
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)

        #rules: 예시 스타일
        self.rules = {
            self.IDLE: {
                right_down: self.RUN, left_down: self.RUN,
                space_down: self.JUMP,
            },
            self.RUN: {
                right_up: self.IDLE, left_up: self.IDLE,
                right_down: self.RUN, left_down: self.RUN,
                space_down: self.JUMP,
            },
            self.JUMP: {
                right_down: self.JUMP, left_down: self.JUMP,
                jump_done: self.FALL,
            },
            self.FALL: {
                right_down: self.FALL, left_down: self.FALL,
                landed_run: self.RUN,
                landed_idle: self.IDLE,
            },
        }

        # [변경] 상태머신: 시작 상태 + rules 전달
        self.state_machine = StateMachine(self.IDLE, self.rules)



    def handle_event(self, e):
        self.state_machine.handle_state_event(('INPUT', e))
        if e.type == SDL_KEYUP:
            if e.key == SDLK_RIGHT and self.dir == 1: self.dir = 0
            if e.key == SDLK_LEFT and self.dir == -1: self.dir = 0
        pass

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()