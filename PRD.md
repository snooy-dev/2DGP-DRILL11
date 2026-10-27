# DRILL 11 자동 무적 런(AUTORUN) 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** IDLE에서 A 키로 진입하는 5초짜리 AUTORUN 상태를 추가한다.

**Architecture:** `boy.py`에 `AutoRun` 상태 클래스를 추가해 진입·이탈·시간·이동·그리기를 담당하게 한다. 기존 `Boy`와 `transitions.Machine`은 상태 전환과 입력을 관리하며 AUTORUN의 갱신·그리기를 이 클래스에 위임한다. 기존 이벤트 전달과 게임 루프를 유지하며 새 런타임 모듈이나 의존성은 추가하지 않는다.

**Tech Stack:** Python, pico2d, transitions, time.monotonic, unittest.

**Spec:** [PRE-PRD.md](PRE-PRD.md)

## 공통 제약

- 키조작 없이 좌우 이동, 속도 증가, 크기 확대, 화면 끝 자동 반전, 5초 이상 경과 시 IDLE 복귀를 모두 구현한다.
- AUTORUN 중 방향키를 누르면 취소하고 기존 RUN으로 전환한다.
- 반드시 `AutoRun` 상태 클래스를 추가한다. Machine에 `AUTORUN` 상태 이름만 등록하는 구현은 허용하지 않는다.
- 점진적으로 개발하고 각 단계의 검증 후 커밋한다. 커밋 메시지는 한글로 작성하며 영어 말머리는 허용한다.
- 기존 IDLE·RUN·SLEEP, 좌우 동시 입력, 스페이스 깨우기, ESC·창 닫기 동작을 유지한다.
- 이번 문서 작성에서는 제품 코드 변경과 커밋을 수행하지 않는다. 아래 체크박스는 후속 구현 작업이다.

## 현재 코드와 변경 범위

| 파일 | 현재 역할 | 구현 시 작업 |
| --- | --- | --- |
| `boy.py` | 상태 머신, 키 입력, 이동, 애니메이션, 렌더링 | `AutoRun` 상태 클래스와 Boy의 전환·위임 연결 추가 |
| `tests/test_boy.py` | 현재 없음 | 표준 `unittest` 기반 회귀 테스트 추가 |
| `main.py` | 이벤트 전달, 월드 초기화·갱신·렌더링 | 변경 없이 통합 실행으로 확인 |
| `grass.py` | 잔디 렌더링 | 변경 없음 |
| `animation_sheet.png` | 현재 소년 스프라이트 | 기존 RUN 프레임 재사용 |

`Boy` 호출자는 `main.py`의 `reset_world()`, `handle_events()`, 월드 갱신·렌더링이다. `Boy()`와 `handle_event(event)`, `update()`, `draw()`의 호출 규약을 유지한다. 현재 테스트·패키지 설정·공개 export는 없으며 새 설정 파일은 필요하지 않다.

### AutoRun 클래스와 Boy의 연결

- `AutoRun`은 같은 `boy.py`에 정의하고, `enter(boy: Boy) -> None`, `exit(boy: Boy) -> None`, `update(boy: Boy) -> None`, `draw(boy: Boy) -> None`을 정적 메서드로 제공한다. 별도 상태 인스턴스나 공통 기반 클래스는 만들지 않는다.
- 좌표·방향·프레임·시각은 기존 `Boy` 객체에 저장한다. `AutoRun.enter()`는 `boy.autorun_started_at`을 기록하고, `AutoRun.exit()`는 `boy.last_input_time`을 갱신한다.
- Machine의 AUTORUN 진입·이탈 콜백은 각각 `lambda: AutoRun.enter(self)`, `lambda: AutoRun.exit(self)`로 연결한다. `Boy.update()`와 `Boy.draw()`의 AUTORUN 분기는 각각 `AutoRun.update(self)`, `AutoRun.draw(self)`에 위임한다.
- 입력과 전환 트리거는 `Boy`에 유지한다. `AutoRun.update()`는 시간 만료 시 `boy.finish_autorun()`을 호출한다. 기존 IDLE·RUN·SLEEP을 클래스로 바꾸는 작업은 포함하지 않는다.

## 구현 기준과 제안값

아래 수치와 모호한 입력 처리는 PRE-PRD에 명시되지 않은 구현 제안이다. 5초 지속 시간은 원문 요구사항이다.

| 항목 | 기준 |
| --- | --- |
| 진입 | `IDLE`에서 `SDL_KEYDOWN + SDLK_a` |
| 최초 이동 방향 | 진입 직전 `face_dir` 유지. 초기값은 기존과 같은 오른쪽 |
| 속도 | 기존 RUN은 업데이트당 3px, AUTORUN은 6px(2배) |
| 크기 | 기존 100×100에서 AUTORUN 150×150(1.5배) |
| 애니메이션 | RUN의 8프레임과 방향별 행(오른쪽 100, 왼쪽 0) 재사용 |
| 좌우 경계 | `get_canvas_width()`를 사용하고 확대 사각형 절반인 75px를 고려해 중심 x를 `[75, 너비-75]`로 제한 |
| 반전 | 이동 후 경계에 닿거나 넘으면 해당 경계로 보정하고 `face_dir`을 안쪽으로 변경 |
| 확대 위치 | `self.y`를 변경하지 않고 그리기 중심 y에 25px를 더해 기존 100px 프레임의 아래쪽 기준 유지 |
| 시간 | `monotonic()`으로 진입 시각 기록, 경과 시간이 `>= 5.0`이면 이동 전에 IDLE 전환 |
| 종료 | 다음 그리기부터 기존 크기, 위치 기준, IDLE/RUN 애니메이션 사용 |

이동량은 현재 코드와 동일하게 업데이트 횟수에 의존한다. 이번 작업에 delta-time 기반 이동 개편은 포함하지 않는다. 확대 프레임 아래쪽 정렬이 실제 이미지의 발 위치에도 맞는지는 화면에서 확인한다.

게임에는 체력·피격·적·충돌 시스템이 없다. 따라서 이 작업의 “무적”은 PRE-PRD에 나열된 이동·확대 효과를 뜻하며, 별도의 피해 무효화 시스템을 만들지 않는다.

## 상태와 입력 규칙

| 현재 상태 | 조건 | 다음 상태 | 처리 |
| --- | --- | --- | --- |
| IDLE | A 키 누름 | AUTORUN | 시작 시각 기록, 기존 방향 유지 |
| RUN / SLEEP | A 키 누름 | 유지 | AUTORUN 진입 안 함 |
| AUTORUN | 진입 후 5초 미만 | 유지 | 자동 이동·반전·확대 |
| AUTORUN | 진입 후 5초 이상 | IDLE | 종료, `last_input_time`을 현재 시각으로 갱신 |
| AUTORUN | 왼쪽/오른쪽 키 누름 | RUN | 누른 키 집합과 `move_dir` 갱신 후 즉시 취소 |
| AUTORUN | 방향키 해제 | 유지 | 키 집합만 갱신, 자동 이동은 계속 |
| AUTORUN | A 반복 입력 또는 기타 키 | 유지 | 시작 시각을 갱신하지 않음 |

방향키는 현재 이동 방향과 같아도 취소한다. 양쪽 키를 누른 결과 `move_dir == 0`이어도 방향키 KEYDOWN으로 취소했다면 RUN에 진입한다. 이후 키 해제에 따른 RUN/IDLE 전환은 기존 입력 규칙을 따른다. `face_dir`은 이동 방향이 0이 아닐 때만 입력 방향으로 갱신한다.

AUTORUN의 이동 방향은 `face_dir`, 수동 이동 방향은 기존 `move_dir`을 사용한다. 자동 이동을 위해 `pressed_keys`에 가짜 키를 넣지 않는다. 시간 만료 후에는 IDLE의 기존 무입력 5초를 새로 계산해 즉시 SLEEP으로 넘어가지 않게 한다.

## 중점 검토 항목

1. A 키 반복 입력: 지속 시간이 연장되지 않아야 한다. 단계 1에서 검증한다.
2. 타이머 경계: 4.999초에는 유지하고 5.000초 이상에는 종료하며, 다음 업데이트에서도 IDLE이어야 한다. 단계 1에서 검증한다.
3. 방향키 취소: 같은 방향, 반대 방향, 양쪽 동시 입력과 키 해제가 상태 오류를 만들지 않아야 한다. 단계 2에서 검증한다.
4. 화면 경계: 양쪽 끝과 경계 밖 위치에서 좌표를 보정하고 안쪽으로 이동해야 한다. 단계 3에서 검증한다.
5. 효과 해제: 시간 만료와 방향키 취소 모두 확대가 해제되고 기존 이동·SLEEP 동작이 유지되어야 한다. 단계 3에서 검증한다.

## 단계별 구현

### 1. AUTORUN 진입과 시간 만료

**파일:** 수정 `boy.py`, 생성 `tests/test_boy.py`.

**인터페이스:** 기존 Boy 메서드 시그니처 유지. Machine에 `AUTORUN`, `start_autorun: IDLE → AUTORUN`, `finish_autorun: AUTORUN → IDLE` 추가. `AutoRun.enter(boy: Boy) -> None`, `AutoRun.exit(boy: Boy) -> None`, `AutoRun.update(boy: Boy) -> None`을 구현하고 위 연결 규칙에 따라 진입·이탈 콜백과 갱신을 연결한다. 이 단계의 `AutoRun.update()`는 시간 만료를 처리한다.

- [ ] `unittest`에서 실제 `transitions.Machine`을 사용한다. 테스트에서 `boy`를 import하기 전에 `pico2d`를 필요한 상수·이미지 로더·캔버스 너비 함수가 있는 가짜 모듈로 대체해 창을 열지 않는다. `boy.monotonic`과 이미지 객체도 mock으로 제어한다.
- [ ] 실패 테스트 작성: `test_a_starts_autorun_only_from_idle`, `test_repeated_a_does_not_restart_timer`, `test_autorun_timeout_boundary`, `test_timeout_restarts_idle_sleep_timer`. 시각 100에 진입하여 104.999에는 AUTORUN, 105에는 IDLE, 105.01에도 IDLE, 110에는 SLEEP인지 확인한다. 105.1에서 첫 갱신하는 지연 사례도 종료되어야 한다.
- [ ] `python -m unittest discover -s tests -v`로 신규 요구사항의 실패를 확인한다.
- [ ] `AutoRun` 클래스, `SDLK_a` 입력과 위 상태·콜백·타이머를 구현한다. 테스트는 `Boy.handle_event()`와 `Boy.update()`를 통해 실행해 클래스 연결까지 검증한다. RUN/SLEEP의 A 입력과 AUTORUN의 A 반복 입력으로 잘못된 전환을 호출하지 않는다.
- [ ] 같은 명령으로 모든 테스트 통과를 확인한다.
- [ ] 관련 파일만 커밋: `feat: 자동 달리기 상태 진입과 시간 종료 추가`.

### 2. 자동 이동과 방향키 취소

**파일:** 수정 `boy.py`, `tests/test_boy.py`.

**인터페이스:** 기존 `start_run` 전환의 출발 상태에 AUTORUN 추가. 단계 1의 `AutoRun.exit()` 이탈 콜백을 그대로 사용하고 `AutoRun.update()`에 이동을 추가한다. `Boy.handle_event(event)`는 방향키 KEYDOWN으로 AUTORUN을 취소하는 처리를 `move_dir`의 참/거짓 판단보다 먼저 수행한다.

- [ ] 실패 테스트 작성: `test_autorun_moves_in_facing_direction`은 키 없이 좌우 각각 6px 이동, RUN은 3px 이동을 확인한다.
- [ ] 실패 테스트 작성: `test_arrow_keydown_cancels_autorun`은 같은 방향·반대 방향 모두 즉시 RUN 전환하고 후속 업데이트에서 수동 속도로 이동하는지 확인한다.
- [ ] 실패 테스트 작성: `test_zero_net_direction_still_cancels`, `test_arrow_keyup_does_not_cancel`, `test_other_keys_do_not_cancel`. 양쪽 키가 눌린 입력 상태도 구성해 `move_dir == 0`인 취소와 후속 키 해제 처리를 확인한다.
- [ ] `python -m unittest discover -s tests -v`로 신규 사례의 실패를 확인한다.
- [ ] `AutoRun.update()`에 자동 이동·프레임 갱신을, `Boy.handle_event()`에 방향키 취소를 구현한다. 기존 키 집합을 재사용하고 취소 시 이를 임의로 비우지 않는다.
- [ ] 같은 명령으로 기존 테스트와 신규 테스트 통과를 확인한다.
- [ ] 관련 파일만 커밋: `feat: 자동 이동과 방향키 취소 처리 추가`.

### 3. 경계 반전·확대와 통합 확인

**파일:** 수정 `boy.py`, `tests/test_boy.py`. `main.py`는 실행 검증만 수행한다.

**인터페이스:** `AutoRun.update()`는 캔버스 너비와 확대 크기로 좌우 경계를 계산한다. `AutoRun.draw(boy: Boy) -> None`을 추가해 RUN 프레임을 150×150으로 그리고 `Boy.draw()`의 AUTORUN 분기에서 위임한다. 속도·크기·지속 시간은 `boy.py` 내부 상수로 정의하며 설정 파일은 만들지 않는다.

- [ ] 실패 테스트 작성: `test_autorun_bounces_at_edges`는 너비 800에서 오른쪽 x=724 → 725·왼쪽 방향, 왼쪽 x=76 → 75·오른쪽 방향을 확인한다. 정확한 경계와 경계 밖에서 시작하는 사례도 포함한다.
- [ ] 실패 테스트 작성: `test_autorun_draws_scaled_run_frames`는 양 방향의 스프라이트 행, 목적 크기 150×150, 그리기 y=`self.y + 25`, `self.y` 원본 유지를 확인한다.
- [ ] 실패 테스트 작성: `test_autorun_exit_restores_normal_draw`는 시간 만료·방향키 취소 후 일반 크기와 기존 y로 그리는지 확인한다. `test_existing_idle_run_sleep_flow`는 IDLE 무입력 SLEEP, 스페이스 깨우기, 방향키 RUN, 양쪽 동시 입력·해제 동작을 확인한다.
- [ ] `python -m unittest discover -s tests -v`로 신규 사례의 실패를 확인한다.
- [ ] `AutoRun.update()`에 경계 보정·반전, `AutoRun.draw()`에 확대 그리기를 구현한다. 그리기 테스트도 `Boy.draw()`를 통해 위임을 검증한다. 자동 이동 종료 후 별도 복구가 필요 없도록 일반 좌표·크기를 덮어쓰지 않는다.
- [ ] `python -m unittest discover -s tests -v`로 전체 통과를 확인한다.
- [ ] `python -m py_compile boy.py main.py grass.py`의 종료 코드 0을 확인한다.
- [ ] pico2d·transitions가 설치된 환경에서 저장소 루트를 작업 디렉터리로 하여 `python main.py`를 실행한다. 양쪽 방향 진입, 빠른 이동·확대, 양끝 반전, 약 5초 후 복귀, 방향키 취소를 확인한다. 특히 발 위치, 경계에서의 잘림·떨림, 기존 SLEEP 렌더링, ESC·창 닫기를 확인한다.
- [ ] 관련 파일만 커밋: `feat: 자동 달리기 경계 반전과 확대 렌더링 완성`.

## 완료 기준

- [ ] `AutoRun` 상태 클래스가 실제 진입·이탈·갱신·그리기에 사용되며, Machine 상태 이름만 추가하거나 빈 클래스로 남겨두지 않는다.
- [ ] PRE-PRD의 다섯 가지 효과와 IDLE에서 A 키 진입이 모두 동작한다.
- [ ] 지속 시간은 실제 경과 시간으로 판정하고, 키 반복 입력으로 연장되지 않는다.
- [ ] 취소·만료 직후 정상 크기와 해당 상태의 이동 규칙으로 복귀한다.
- [ ] 자동 테스트·문법 검사·실행 화면 확인을 통과한다. 실행 환경 문제로 확인하지 못한 항목은 완료로 표시하지 않고 이유를 기록한다.
- [ ] 기존 IDLE·RUN·SLEEP과 종료 입력에 회귀가 없고, 단계별 한글 커밋이 남아 있다.

## 범위에서 제외한 작업

피격 판정, 적·장애물, 무적 이펙트·음향, 새로운 이미지, 남은 시간 UI, 속도 조절 메뉴, 게임 루프 재설계는 추가하지 않는다. 신규 의존성을 추가하지 않으며, pico2d·transitions 설치와 실제 화면 검증은 구현 시 실행 환경에서 확인한다.
