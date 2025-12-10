import time

# 이 모듈은 게임 루프와 모드 전환을 담당하며
# main.py, title_mode.py, play_mode.py에서 공통으로 사용된다..

frame_time = 0.0

running = None
stack = None

TARGET_FPS = 120
MAX_DT = 1.0 / 30.0
MIN_DT = 0.0


def change_mode(mode):
    # 이 함수는 현재 모드를 종료하고 새 모드로 전환하며
    # title_mode.py와 play_mode.py에서 호출된다.
    global stack
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    # 이 함수는 기존 모드는 일시정지하고 새 모드를 위에 쌓으며
    # 필요 시 추가 서브 모드를 올릴 때 사용할 수 있다.
    global stack
    if len(stack) > 0:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    # 이 함수는 현재 모드를 종료하고 이전 모드를 다시 활성화하며
    # 모드 스택을 한 단계 내린다.
    global stack
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    if len(stack) > 0:
        stack[-1].resume()


def quit():
    # 이 함수는 게임 루프를 종료하며
    # title_mode.py, play_mode.py의 이벤트 처리에서 호출된다.
    global running
    running = False


def run(start_mode):
    # 이 함수는 전체 게임 루프를 돌리며
    # main.py에서 최초 호출되고 이후 frame_time을 갱신한다.
    global running, stack
    running = True
    stack = [start_mode]
    start_mode.init()

    global frame_time
    frame_time = 0.0
    current_time = time.time()

    target_spf = 1.0 / TARGET_FPS

    while running:
        stack[-1].handle_events()
        stack[-1].update()
        stack[-1].draw()

        raw_now = time.time()
        raw_dt = raw_now - current_time

        if raw_dt < target_spf:
            time.sleep(target_spf - raw_dt)
            raw_now = time.time()
            raw_dt = raw_now - current_time

        frame_time = raw_dt
        if frame_time > MAX_DT:
            frame_time = MAX_DT
        if frame_time < MIN_DT:
            frame_time = MIN_DT

        current_time = raw_now

    while len(stack) > 0:
        stack[-1].finish()
        stack.pop()
