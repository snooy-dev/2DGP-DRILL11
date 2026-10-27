from math import pi
from time import monotonic

from pico2d import load_image, get_canvas_width, SDL_KEYDOWN, SDL_KEYUP, SDLK_SPACE, SDLK_LEFT, SDLK_RIGHT, SDLK_a
from transitions import Machine

AUTORUN_DURATION = 5.0
AUTORUN_SPEED = 6
AUTORUN_SIZE = 150
# shortcut: 현재 RUN 16프레임의 불투명 x 범위, 스프라이트 교체 시 다시 측정.
RUN_VISIBLE_X = (18, 84)


class AutoRun:
    @staticmethod
    def enter(boy):
        boy.autorun_started_at = monotonic()

    @staticmethod
    def exit(boy):
        boy.last_input_time = monotonic()

    @staticmethod
    def update(boy):
        if monotonic() - boy.autorun_started_at >= AUTORUN_DURATION:
            boy.finish_autorun()
            return
        boy.frame = (boy.frame + 1) % 8
        boy.x += boy.face_dir * AUTORUN_SPEED
        scale = AUTORUN_SIZE / 100
        left_edge = (50 - RUN_VISIBLE_X[0]) * scale
        right_edge = get_canvas_width() - (RUN_VISIBLE_X[1] - 50) * scale
        if boy.x <= left_edge:
            boy.x, boy.face_dir = left_edge, 1
        elif boy.x >= right_edge:
            boy.x, boy.face_dir = right_edge, -1

    @staticmethod
    def draw(boy):
        row = 100 if boy.face_dir == 1 else 0
        draw_y = boy.y + (AUTORUN_SIZE - 100) / 2
        boy.image.clip_draw(boy.frame * 100, row, 100, 100, boy.x, draw_y, AUTORUN_SIZE, AUTORUN_SIZE)


class Boy:
    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_keys = set()
        self.move_dir = 0
        self.image = load_image('animation_sheet.png')
        self.last_input_time = monotonic()
        self.machine = Machine(model=self, states=['IDLE', 'SLEEP', 'RUN', {
            'name': 'AUTORUN',
            'on_enter': lambda: AutoRun.enter(self),
            'on_exit': lambda: AutoRun.exit(self),
        }], initial='IDLE', auto_transitions=False)
        self.machine.add_transition('sleep', 'IDLE', 'SLEEP')
        self.machine.add_transition('wake', 'SLEEP', 'IDLE')
        self.machine.add_transition('start_run', ['IDLE', 'SLEEP', 'AUTORUN'], 'RUN')
        self.machine.add_transition('stop_run', 'RUN', 'IDLE')
        self.machine.add_transition('start_autorun', 'IDLE', 'AUTORUN')
        self.machine.add_transition('finish_autorun', 'AUTORUN', 'IDLE')

    def handle_event(self, event):
        if event.type in (SDL_KEYDOWN, SDL_KEYUP):
            self.last_input_time = monotonic()
            if self.state == 'IDLE' and event.type == SDL_KEYDOWN and event.key == SDLK_a:
                self.start_autorun()
            if self.state == 'SLEEP' and event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
                self.wake()
            if event.key in (SDLK_LEFT, SDLK_RIGHT):
                if event.type == SDL_KEYDOWN:
                    self.pressed_keys.add(event.key)
                else:
                    self.pressed_keys.discard(event.key)
                self.move_dir = (SDLK_RIGHT in self.pressed_keys) - (SDLK_LEFT in self.pressed_keys)
                if self.state == 'AUTORUN':
                    if event.type == SDL_KEYDOWN:
                        if self.move_dir:
                            self.face_dir = self.move_dir
                        self.start_run()
                    return
                if self.move_dir:
                    self.face_dir = self.move_dir
                    if self.state != 'RUN':
                        self.start_run()
                elif self.state == 'RUN':
                    self.stop_run()

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if monotonic() - self.last_input_time >= 5:
                self.sleep()
        elif self.state == 'RUN':
            self.frame = (self.frame + 1) % 8
            self.x += self.move_dir * 3
        elif self.state == 'AUTORUN':
            AutoRun.update(self)

    def draw(self):
        if self.state == 'IDLE':
            if self.face_dir == 1:
                self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
            else:
                self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
        elif self.state == 'RUN':
            row = 100 if self.face_dir == 1 else 0
            self.image.clip_draw(self.frame * 100, row, 100, 100, self.x, self.y)
        elif self.state == 'AUTORUN':
            AutoRun.draw(self)
        elif self.state == 'SLEEP':
            row = 300 if self.face_dir == 1 else 200
            # Align the rotated sprite's opaque bottom with the standing feet.
            sleep_y = self.y - (28 if self.face_dir == 1 else 17)
            self.image.clip_composite_draw(0, row, 100, 100, self.face_dir * pi / 2, '', self.x, sleep_y, 100, 100)
