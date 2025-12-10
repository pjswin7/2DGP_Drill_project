import time

# 이 모듈은 게임 루프와 모드 전환을 담당하며
# main.py, title_mode.py, play_mode.py에서 공통으로 사용된다.

frame_time = 0.0          # 각 프레임 사이의 시간 간격(초)
running = False           # 메인 루프 실행 여부
stack = []                # 모드 스택 (title_mode, play_mode 등)

TARGET_FPS = 120          # 목표 프레임 레이트
MAX_DT = 1.0 / 30.0       # 한 프레임에서 허용하는 최대 dt
MIN_DT = 0.0              # 최소 dt


def run(start_mode):
    # 이 함수는 게임의 시작 모드를 받아 메인 루프를 실행하며
    # main.py에서 최초로 호출된다.
    global running, stack, frame_time
    running = True
    stack = [start_mode]

    start_mode.init()
    current_time = time.time()

    while running and stack:
        # 프레임 시작 시각
        frame_start = time.time()

        # 현재 모드 하나만 동작
        top = stack[-1]
        top.handle_events()
        top.update()
        top.draw()

        # 시간 갱신
        now = time.time()
        raw_dt = now - current_time
        current_time = now

        frame_time = raw_dt
        if frame_time > MAX_DT:
            frame_time = MAX_DT
        if frame_time < MIN_DT:
            frame_time = MIN_DT

        # FPS 맞추기 위해 남는 시간 잠깐 sleep
        frame_duration = 1.0 / TARGET_FPS
        elapsed = time.time() - frame_start
        if elapsed < frame_duration:
            time.sleep(frame_duration - elapsed)

    # 루프가 끝나면 스택의 모드들을 정리
    while stack:
        mode = stack.pop()
        try:
            mode.finish()
        except AttributeError:
            pass


def change_mode(mode):
    # 이 함수는 현재 모드를 종료하고 새 모드로 교체하며
    # title_mode → play_mode 전환 등에 사용된다.
    global stack
    if not stack:
        stack = [mode]
        mode.init()
        return

    top = stack.pop()
    try:
        top.finish()
    except AttributeError:
        pass

    stack.append(mode)
    mode.init()


def push_mode(mode):
    # 이 함수는 현재 모드 위에 새 모드를 올려
    # 일시적으로 다른 화면(예: 메뉴)을 띄울 때 사용된다.
    global stack
    if stack:
        try:
            stack[-1].pause()
        except AttributeError:
            pass

    stack.append(mode)
    mode.init()


def pop_mode():
    # 이 함수는 현재 모드를 제거하고
    # 아래에 있던 모드를 다시 활성화할 때 사용된다.
    global stack, running
    if not stack:
        running = False
        return

    top = stack.pop()
    try:
        top.finish()
    except AttributeError:
        pass

    if not stack:
        running = False
        return

    try:
        stack[-1].resume()
    except AttributeError:
        pass


def quit():
    # 이 함수는 메인 루프를 종료하도록 플래그를 내려주며
    # SDL_QUIT 처리나 ESC 입력 처리에서 사용된다.
    global running
    running = False
