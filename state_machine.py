
class StateMachine:
    def __init__(self, start_state):
        self.cur_state = start_state

    def update(self):
        # 매 프레임 상태의 로직 실행
        self.cur_state.do()

    def draw(self):
        # 그리기도 상태에 맡김
        self.cur_state.draw()

    def change(self, new_state):
        # 나중에 Run/Jump 같은 걸로 갈아끼울 때 사용
        self.cur_state = new_state
