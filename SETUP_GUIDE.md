# MCP Appium 설치 가이드

## 🚀 가장 쉬운 설치 방법

### macOS / Linux 사용자

터미널을 열고 다음 명령어를 **한 줄만** 복사해서 붙여넣으세요:

```bash
curl -sSL https://raw.githubusercontent.com/supremehyo/appium-mcp-claude-android/main/install-remote.sh | bash
```

끝! 이게 전부입니다.

### Windows 사용자

1. **PowerShell 또는 CMD 열기**

2. **다음 명령어 실행:**
```bash
git clone https://github.com/supremehyo/appium-mcp-claude-android.git
cd appium-mcp-claude-android
pip install -e .
python -m mcp_appium.installer
```

## 📋 설치가 하는 일

자동 설치 스크립트는 다음을 수행합니다:

1. ✅ 코드 다운로드 (GitHub에서)
2. ✅ Python 패키지 설치
3. ✅ Appium 자동 설치 (npm이 있다면)
4. ✅ Claude Code에 MCP 서버 자동 등록
5. ✅ 설치 완료!

**직접 할 필요가 없습니다.** 스크립트가 모두 자동으로 처리합니다.

## ✅ 설치 확인

### 1. MCP 서버 확인
```bash
claude mcp list
```

출력에 `appium`이 보여야 합니다:
```
appium - stdio server
```

### 2. Claude Code 재시작

Claude Code를 완전히 종료하고 다시 시작합니다.

### 3. 테스트

Claude Code에서:
```
"연결된 기기 확인해줘"
```

## 📱 기기 준비

### Android 실제 기기

1. **개발자 옵션 활성화**
   - 설정 > 휴대전화 정보 > 빌드 번호를 7번 탭

2. **USB 디버깅 활성화**
   - 설정 > 개발자 옵션 > USB 디버깅 켜기

3. **USB 연결**
   - 컴퓨터에 USB로 연결
   - "USB 디버깅 허용" 팝업에서 허용

4. **확인**
   ```bash
   adb devices
   ```
   기기가 "device" 상태로 표시되어야 합니다.

### Android 에뮬레이터

1. **Android Studio 실행**
2. **AVD Manager** 열기
3. **에뮬레이터 시작**
4. **확인**
   ```bash
   adb devices
   ```

## 🎯 첫 사용

Claude Code에서 다음과 같이 말하세요:

### 1단계: 기기 확인
```
"연결된 Android 기기 확인해줘"
```

### 2단계: 자동 설정
```
"Appium 설정하고 기기에 연결해줘"
```

이 명령 하나로:
- ✅ Appium 서버 자동 시작
- ✅ 기기 자동 감지
- ✅ 설정 자동 생성
- ✅ 연결 완료!

### 3단계: 테스트
```
"현재 화면에 뭐가 있는지 보여줘"
"설정 앱 열어줘"
"아래로 스크롤해줘"
```

## ❓ 문제 해결

### "claude: command not found"

Claude Code CLI가 설치되지 않았습니다.
- Claude Code를 재설치하거나
- 수동으로 MCP 서버 등록:
  ```bash
  claude mcp add --transport stdio appium -- python -m mcp_appium.server
  ```

### "adb: command not found"

Android SDK Platform-Tools가 필요합니다.

**macOS (Homebrew 사용 시):**
```bash
brew install android-platform-tools
```

**다른 방법:**
1. https://developer.android.com/studio/releases/platform-tools 에서 다운로드
2. 압축 해제
3. PATH에 추가:
   ```bash
   export PATH=$PATH:/path/to/platform-tools
   ```

### "appium: command not found"

Node.js와 Appium이 필요합니다.

**Node.js 설치:**
- https://nodejs.org/ 에서 다운로드

**Appium 설치:**
```bash
npm install -g appium
appium driver install uiautomator2
```

### "No devices found"

1. **USB 디버깅 확인**
   - 설정 > 개발자 옵션 > USB 디버깅이 켜져 있는지 확인

2. **연결 확인**
   ```bash
   adb devices
   ```
   기기가 보이지 않으면:
   - USB 케이블 재연결
   - 다른 USB 포트 시도
   - "USB 디버깅 허용" 다시 승인

3. **에뮬레이터 확인**
   - Android Studio AVD Manager에서 에뮬레이터가 실행 중인지 확인

### MCP 서버가 목록에 없음

```bash
# 수동 등록
python -m mcp_appium.installer

# 또는
claude mcp add --transport stdio appium -- python -m mcp_appium.server

# 확인
claude mcp list
```

## 🔄 업데이트

새 버전이 나왔을 때:

```bash
# 방법 1: 재설치
curl -sSL https://raw.githubusercontent.com/supremehyo/appium-mcp-claude-android/main/install-remote.sh | bash

# 방법 2: 수동 업데이트
cd ~/.mcp-appium  # 또는 설치된 디렉토리
git pull
pip install -e . --upgrade
```

## 🗑️ 제거

```bash
# MCP 서버 등록 해제
mcp-appium-install --uninstall

# 패키지 제거
pip uninstall mcp-appium

# 설치 디렉토리 제거 (선택)
rm -rf ~/.mcp-appium
```

## 💡 팁

1. **요구사항 확인**
   ```bash
   mcp-appium-install --check
   ```

2. **로그 확인**
   - Appium 로그: `appium.log` (프로젝트 루트)

3. **여러 기기 연결 시**
   - 첫 번째로 감지된 기기를 자동으로 사용합니다
   - 특정 기기 사용하려면 설정 파일 수정 가능

## 📚 더 알아보기

- **전체 문서**: [README.md](README.md)
- **상세 설치**: [INSTALL.md](INSTALL.md)
- **빠른 시작**: [QUICKSTART.md](QUICKSTART.md)

## 🆘 도움말

문제가 해결되지 않으면:
1. GitHub Issues: https://github.com/supremehyo/appium-mcp-claude-android/issues
2. 로그 확인: `appium.log`
3. 요구사항 재확인: `mcp-appium-install --check`
