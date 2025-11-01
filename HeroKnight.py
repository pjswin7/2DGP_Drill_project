from pico2d import *
import os


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



class Idle:
    def __init__(self, boy):
        self.boy = boy

    def enter(self, e):
        self.boy.dir = 0

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

    def exit(self, e):
        pass

    def do(self):
        #  달리기 프레임은 run_images 개수 기준으로
        self.boy.frame = (self.boy.frame + 1) % len(self.boy.run_images)
        # 이동(고정 스텝)
        self.boy.x += self.boy.dir * 5
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
        if right_down(e): self.boy.face_dir = 1
        if left_down(e):  self.boy.face_dir = -1
    def exit(self, e): pass
    def do(self):
        now = get_time()
        dt = now - self.boy.prev_time
        self.boy.prev_time = now

        # 간단한 타이머로 프레임 넘김(고급 물리 없음)
        self.boy.anim_acc += dt
        if self.boy.anim_acc >= 1.0 / self.boy.fps:
            self.boy.anim_acc = 0.0
            self.boy.jump_idx += 1
            if self.boy.jump_idx > self.boy.JUMP_LAST:
                # Jump 애니메이션 종료 → Fall로 넘어가도록 내부 이벤트 발생
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
        if right_down(e): self.boy.face_dir = 1
        if left_down(e):  self.boy.face_dir = -1
    def exit(self, e): pass
    def do(self):
        now = get_time()
        dt = now - self.boy.prev_time
        self.boy.prev_time = now

        self.boy.anim_acc += dt
        if self.boy.anim_acc >= 1.0 / self.boy.fps:
            self.boy.anim_acc = 0.0
            self.boy.fall_idx += 1
            if self.boy.fall_idx > self.boy.FALL_LAST:
                # 달리는 중이면 Run, 아니면 Idle
                self.boy.state_machine.handle_state_event(('FALL_DONE', None))
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

        #  상태 객체
        self.IDLE = Idle(self)
        self.RUN = Run(self)
        self.JUMP = Jump(self)
        self.FALL = Fall(self)

        #rules: 예시 스타일
        self.rules = {
            self.IDLE: {right_down: self.RUN, left_down: self.RUN},
            self.RUN: {right_up: self.IDLE, left_up: self.IDLE,
                       right_down: self.RUN, left_down: self.RUN},# 누른 방향으로 계속 RUN 유지(방향만 바뀜)
            self.JUMP: {
                right_down: self.JUMP, left_down: self.JUMP,  # 공중에서 얼굴만 전환
                jump_done: self.FALL,  # Jump 끝나면 Fall 시작
            },
            self.FALL: {
                right_down: self.FALL, left_down: self.FALL,
                # 낙하가 끝났을 때: dir이 0이 아니면 Run, 0이면 Idle로 복귀
                fall_done: self.RUN if self.dir != 0 else self.IDLE,
            },
        }

        # [변경] 상태머신: 시작 상태 + rules 전달
        self.state_machine = StateMachine(self.IDLE, self.rules)



    def handle_event(self, e):
        self.state_machine.handle_state_event(('INPUT', e))
        pass

    def update(self):
        self.state_machine.update()

    def draw(self):
        self.state_machine.draw()