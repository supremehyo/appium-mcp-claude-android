# MCP Appium - Automated Mobile Testing with Model Context Protocol

MCP Appium은 Appium을 MCP(Model Context Protocol) 서버로 제공하여, AI 에이전트가 모바일 디바이스를 자동으로 제어하고 테스트할 수 있도록 합니다.

## 주요 기능

- **자동 서버 시작**: Appium 서버를 자동으로 시작 (GUI 불필요)
- **자동 기기 감지**: `adb devices`를 통해 연결된 Android 기기 자동 감지
- **자동 설정**: 감지된 기기 정보로 설정 파일 자동 생성
- **유연한 테스트**: 특정 앱에 제한되지 않고 기기의 모든 앱 자유롭게 테스트
- **MCP 통합**: Claude Code 등의 AI 에이전트와 완벽하게 통합
- **원클릭 설치**: 자동 설치 스크립트로 간편한 설치 및 MCP 등록

## 빠른 시작

### 1. 설치

**방법 1: 저장소 클론 후 설치 (추천)**
```bash
git clone https://github.com/supremehyo/appium-mcp-claude-android.git
cd appium-mcp-claude-android
./install.sh
```

**방법 2: 원격 설치 (홈 디렉토리에 설치됨)**
```bash
curl -sSL https://raw.githubusercontent.com/supremehyo/appium-mcp-claude-android/main/install-remote.sh | bash
# 설치 후: cd ~/.mcp-appium
```

### 2. Claude Code에서 열기

```bash
# 설치한 디렉토리에서
claude
# 또는 다른 방법으로 Claude Code를 해당 디렉토리에서 실행
```

Claude Code가 `.mcp.json`을 자동으로 감지하고 MCP 서버 승인을 요청합니다.

### 3. 사용

Claude Code에서:
```
"연결된 기기 확인해줘"  → list_devices
"Appium 설정하고 연결해줘"  → setup_appium_connection (자동 설정!)
"현재 화면 요소 보여줘"  → get_screen_elements
```

> 상세한 설치 방법은 [INSTALL.md](INSTALL.md)를 참조하세요.

## 필수 요구사항

### 1. Node.js 및 Appium 설치

```bash
# Node.js 설치 (https://nodejs.org/)

# Appium 전역 설치
npm install -g appium

# UiAutomator2 드라이버 설치
appium driver install uiautomator2
```

### 2. Android SDK 및 ADB 설치

- Android Studio 설치 후 SDK Platform-Tools 설치
- 또는 독립 실행형 Platform-Tools 다운로드: https://developer.android.com/studio/releases/platform-tools

환경변수 설정:
```bash
# macOS/Linux (.bashrc 또는 .zshrc에 추가)
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools

# Windows (시스템 환경 변수에 추가)
ANDROID_HOME=C:\Users\YourName\AppData\Local\Android\Sdk
Path=%Path%;%ANDROID_HOME%\platform-tools
```

### 3. Python 패키지 설치

```bash
pip install -r requirements.txt
```

## 기기 준비

### Android 실제 기기
1. USB 디버깅 활성화 (개발자 옵션)
2. USB로 컴퓨터에 연결
3. 디버깅 허용 승인
4. 터미널에서 확인: `adb devices`

### Android 에뮬레이터
1. Android Studio에서 AVD Manager로 에뮬레이터 생성 및 실행
2. 터미널에서 확인: `adb devices`

## 사용 방법

> **참고**: 위의 "빠른 시작"에서 설치 스크립트를 실행했다면 MCP 서버가 이미 등록되어 있습니다.

### 설치 확인

```bash
# MCP 서버 목록 확인
claude mcp list

# "appium"이 목록에 있어야 합니다
```

### 기본 워크플로우

1. **기기 연결 확인**
   ```
   list_devices 도구 사용
   ```

2. **Appium 자동 설정 및 연결**
   ```
   setup_appium_connection 도구 사용
   ```
   이 도구는 다음을 자동으로 수행합니다:
   - Appium 서버 시작
   - 연결된 기기 자동 감지
   - 설정 파일 자동 생성
   - 기기 연결

3. **화면 요소 확인**
   ```
   get_screen_elements 도구 사용
   ```

4. **액션 실행**
   ```
   execute_action 도구로 탭, 입력, 스와이프 등 수행
   ```

5. **자동화 시나리오 실행**
   ```
   run_test_scenario 도구로 자연어 시나리오 실행
   ```

## MCP 도구 목록

### 1. setup_appium_connection
Appium 서버를 시작하고 기기에 자동으로 연결합니다.

**파라미터**:
- `port` (선택): Appium 서버 포트 (기본값: 4723)

**예시**:
```
"Appium 설정하고 기기에 연결해줘"
```

### 2. list_devices
연결된 모든 Android 기기 목록을 표시합니다.

**예시**:
```
"연결된 기기 목록 보여줘"
```

### 3. start_appium_server
Appium 서버만 수동으로 시작합니다.

**파라미터**:
- `port` (선택): Appium 서버 포트 (기본값: 4723)

### 4. stop_appium_server
실행 중인 Appium 서버를 중지합니다.

### 5. get_screen_elements
현재 화면의 모든 UI 요소를 가져옵니다.

### 6. execute_action
모바일 기기에서 특정 액션을 실행합니다.

**지원 액션**:
- `tap`: 요소 탭
- `input_text`: 텍스트 입력
- `swipe`: 스와이프
- `long_press`: 길게 누르기
- `back`: 뒤로 가기
- `hide_keyboard`: 키보드 숨기기
- `scroll_down`: 아래로 스크롤
- `scroll_up`: 위로 스크롤

### 7. run_test_scenario
자연어로 작성된 테스트 시나리오를 자동으로 실행합니다.

**예시**:
```
"설정 앱을 열고 Wi-Fi 메뉴로 이동해줘"
"카카오톡을 열고 검색창에 '테스트' 입력해줘"
```

## 예시 사용 시나리오

### 시나리오 1: 기본 설정 및 테스트

```
User: "연결된 기기 확인해줘"
Claude: [list_devices 실행]

User: "Appium 설정하고 연결해줘"
Claude: [setup_appium_connection 실행]

User: "현재 화면에 뭐가 있는지 보여줘"
Claude: [get_screen_elements 실행]

User: "설정 아이콘 눌러줘"
Claude: [execute_action with tap 실행]
```

### 시나리오 2: 자동화 테스트

```
User: "갤러리 앱을 열고 첫 번째 사진을 선택한 다음 공유 버튼을 눌러줘"
Claude: [run_test_scenario 실행]
```

## 트러블슈팅

### "Appium not found" 에러
```bash
# Appium이 설치되어 있는지 확인
appium --version

# 없다면 설치
npm install -g appium
appium driver install uiautomator2
```

### "No devices found" 에러
```bash
# ADB로 기기 연결 확인
adb devices

# 기기가 보이지 않으면:
# 1. USB 디버깅 활성화 확인
# 2. USB 케이블 재연결
# 3. 에뮬레이터 재시작
```

### "Connection refused" 에러
- 방화벽 설정 확인
- 포트 4723이 사용 중인지 확인: `lsof -i :4723` (macOS/Linux)
- 다른 포트 사용: `setup_appium_connection` 호출 시 `port` 파라미터 지정

## 로그 확인

Appium 서버 로그는 `appium.log` 파일에 저장됩니다.

## 라이선스

MIT License
