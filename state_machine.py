class StateMachine:
    def __init__(self, start_state, rules):
        self.cur_state = start_state
        self.rules = rules

    def handle_state_event(self, state_event):
        # 현재 상태에 대한 전이 규칙이 없으면 무시
        if self.cur_state not in self.rules:
            return
        for check_event in self.rules[self.cur_state].keys():
            if check_event(state_event):
                next_state = self.rules[self.cur_state][check_event]
                prev_state = self.cur_state
                prev_state.exit(state_event)
                self.cur_state = next_state
                self.cur_state.enter(state_event)
                print(f'{prev_state.__class__.__name__} -> {self.cur_state.__class__.__name__}')
                return

    def update(self):
        self.cur_state.do()

    def draw(self):
        self.cur_state.draw()

    def change_state(self, new_state):
        prev_state = self.cur_state
        prev_state.exit(('INTERNAL', None))
        self.cur_state = new_state
        self.cur_state.enter(('INTERNAL', None))
