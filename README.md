# DRILL 11: 소년 자동 무적 런

검증 환경: Windows, Python 3.14. 패키지 버전은 `requirements.txt`에 기록되어 있다.

저장소 루트에서 설치하고 실행한다. 이미지 경로가 작업 디렉터리를 기준으로 하므로 이 위치에서 실행해야 한다.

```powershell
python -m pip install -r requirements.txt
python main.py
```

- 좌우 방향키: 일반 달리기. 화면 끝에서는 멈추며 자동 반전하지 않는다.
- IDLE에서 A: 빠르게 이동하고 확대되는 AUTORUN. 화면 끝에서 반전하며 5초 뒤 IDLE로 돌아간다. 방향키를 누르면 일반 달리기로 전환한다.
- IDLE에서 5초 무입력: SLEEP. 스페이스로 깨우며, 방향키로도 달리기를 시작할 수 있다.
- ESC 또는 창 닫기: 종료.

상태 전환은 [상태 다이어그램](state_diagram.png), 구현 계획과 검증 기록은 [PRD.md](PRD.md)를 참고한다.
