
class StateMachine:
    def __init__(self, start_state, rules):
        self.cur_state = start_state
        self.rules = rules

    def handle_state_event(self, state_event):
        # 첫 번째 방식(직접 인덱싱) 사용: 현재 상태의 전이 줄만 검사
        for check_event in self.rules[self.cur_state].keys():
            if check_event(state_event):
                next_state = self.rules[self.cur_state][check_event]
                prev_state = self.cur_state
                prev_state.exit(state_event)
                self.cur_state = next_state
                self.cur_state.enter(state_event)
                print(f'{prev_state.__class__.__name__} -> {self.cur_state.__class__.__name__}')
                return
        # 처리 못했을 때 메시지(선택)
        # print('처리되지 않은 이벤트')

    def update(self):
        # 매 프레임 상태의 로직 실행
        self.cur_state.do()

    def draw(self):
        # 그리기도 상태에 맡김
        self.cur_state.draw()

    def change_state(self, new_state):
        prev_state = self.cur_state
        prev_state.exit(('INTERNAL', None))
        self.cur_state = new_state
        self.cur_state.enter(('INTERNAL', None))