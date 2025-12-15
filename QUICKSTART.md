# Quick Start Guide

## 5분 만에 시작하기

### 1단계: 설치 (1분)

```bash
# 저장소 클론
git clone <your-repo-url>
cd mcp-appium

# 자동 설치
./install.sh
```

설치 스크립트가 자동으로:
- ✅ Python 패키지 설치
- ✅ Node.js/npm 설치 시도 (가능한 경우)
- ✅ Appium + uiautomator2 설치 (가능한 경우)
- ✅ Claude Code MCP 서버 등록

### 2단계: Claude Code 재시작 (10초)

Claude Code를 완전히 종료하고 다시 시작합니다.

### 3단계: 기기 연결 (1분)

**실제 Android 기기:**
1. USB 디버깅 활성화
2. USB 연결
3. 터미널에서 확인: `adb devices`

**에뮬레이터:**
1. Android Studio에서 에뮬레이터 시작
2. 터미널에서 확인: `adb devices`

### 4단계: 사용 시작! (2분)

Claude Code에서 다음과 같이 말하세요:

**1. 기기 확인**
```
"연결된 Android 기기 확인해줘"
```

**2. 자동 설정 및 연결**
```
"Appium 설정하고 기기에 연결해줘"
```

이 명령 하나로:
- ✅ Appium 서버 자동 시작
- ✅ 기기 자동 감지
- ✅ 설정 자동 생성
- ✅ 기기 연결 완료!

**3. 테스트 시작**
```
"현재 화면에 뭐가 있는지 보여줘"
"설정 앱 열어줘"
"갤러리 앱을 열고 첫 번째 사진을 선택해줘"
```

## 예시 시나리오

### 시나리오 1: 기본 탐색
```
User: "연결된 기기 확인해줘"
Claude: [list_devices 실행] → 기기 목록 표시

User: "Appium 설정하고 연결해줘"
Claude: [setup_appium_connection 실행] → 자동 설정 완료!

User: "현재 화면 요소들 보여줘"
Claude: [get_screen_elements 실행] → 화면의 모든 요소 나열

User: "설정 아이콘 눌러줘"
Claude: [execute_action 실행] → 설정 앱 열림
```

### 시나리오 2: 자동화 테스트
```
User: "갤러리 앱을 열고 첫 번째 사진을 선택한 다음 공유 버튼을 눌러줘"
Claude: [run_test_scenario 실행] → 자동으로 모든 단계 수행!
```

### 시나리오 3: 앱 테스트
```
User: "카카오톡을 열고 검색창에 '테스트' 입력해줘"
Claude: [자동으로 앱 실행 및 텍스트 입력]

User: "아래로 스크롤해줘"
Claude: [execute_action: scroll_down]

User: "첫 번째 채팅방 눌러줘"
Claude: [execute_action: tap]
```

## 문제 해결

### MCP 서버가 목록에 없음
```bash
# 수동으로 등록
claude mcp add --transport stdio appium -- python -m mcp_appium.server

# 확인
claude mcp list
```

### Appium 서버 시작 실패
```bash
# Appium이 설치되어 있는지 확인
appium --version

# 없다면 자동 설치(권장)
# macOS/Linux
mcp-appium-install --install-node --install-appium

# Windows
mcp-appium-install --install-deps -y

# 또는 수동 설치
# npm install -g appium
# appium driver install uiautomator2
```

### 기기가 감지되지 않음
```bash
# ADB로 기기 확인
adb devices

# 기기가 없다면:
# 1. USB 디버깅 활성화 확인
# 2. USB 케이블 재연결
# 3. 에뮬레이터 재시작
```

## 다음 단계

- 📖 자세한 사용법: [README.md](README.md)
- 🔧 고급 설정: [INSTALL.md](INSTALL.md)
- 🚀 더 많은 예시: README의 "예시 사용 시나리오" 섹션

## 도움말

- MCP 도구 목록 보기: Claude Code에서 "사용 가능한 Appium 도구 목록 보여줘"
- 요구사항 확인: `mcp-appium-install --check`
- 제거: `mcp-appium-install --uninstall`

## 팁

1. **특정 앱에 제한 없음**: 어떤 앱이든 자유롭게 테스트할 수 있습니다!
2. **자연어 사용**: "버튼 눌러줘", "아래로 스크롤해줘" 등 자연어로 명령
3. **여러 단계 한 번에**: 복잡한 시나리오도 한 번에 요청 가능
4. **화면 먼저 확인**: 액션 전에 `get_screen_elements`로 화면 확인하면 정확도 향상
