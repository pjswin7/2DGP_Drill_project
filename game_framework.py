
import time


frame_time = 0.0


running = None
stack = None


TARGET_FPS = 120
MAX_DT = 1.0 / 30.0
MIN_DT = 0.0

def change_mode(mode):
    global stack
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    stack.append(mode)
    mode.init()

def push_mode(mode):
    global stack
    if len(stack) > 0:
        stack[-1].pause()
    stack.append(mode)
    mode.init()

def pop_mode():
    global stack
    if len(stack) > 0:
        stack[-1].finish()
        stack.pop()
    if len(stack) > 0:
        stack[-1].resume()

def quit():
    global running
    running = False

def run(start_mode):
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
