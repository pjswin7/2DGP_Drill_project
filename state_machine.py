# 이 모듈은 단순 상태 머신을 제공하며
# HeroKnight.py의 Boy와 EvilKnight.py의 EvilKnight가 공유해서 사용한다.

class StateMachine:
    def __init__(self, start_state, rules):
        # start_state: 시작 상태 객체
        # rules: {state: {event_predicate: next_state}} 형태의 전이 테이블
        self.cur_state = start_state
        self.rules = rules

    def handle_state_event(self, state_event):
        # 이 메서드는 외부 입력/이벤트를 받아 적절한 상태로 전이하며
        # HeroKnight.Boy.handle_event, play_mode.resolve_ground 등에서 호출된다.
        if self.cur_state not in self.rules:
            return

        for check_event in self.rules[self.cur_state].keys():
            if check_event(state_event):
                next_state = self.rules[self.cur_state][check_event]
                prev_state = self.cur_state
                prev_state.exit(state_event)
                self.cur_state = next_state
                self.cur_state.enter(state_event)
                return

    def update(self):
        # 이 메서드는 현재 상태의 do()를 호출하며
        # HeroKnight.Boy.update, EvilKnight.EvilKnight.update에서 사용된다.
        self.cur_state.do()

    def draw(self):
        # 이 메서드는 현재 상태의 draw()를 호출하며
        # HeroKnight.Boy.draw, EvilKnight.EvilKnight.draw에서 사용된다.
        self.cur_state.draw()

    def change_state(self, new_state):
        # 이 메서드는 내부적으로 강제 상태 전환할 때 사용되며
        # 점프 → 낙하, 구르기 종료 등에서 직접 호출된다.
        prev_state = self.cur_state
        prev_state.exit(('INTERNAL', None))
        self.cur_state = new_state
        self.cur_state.enter(('INTERNAL', None))
