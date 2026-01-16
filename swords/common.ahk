#Requires AutoHotkey v2.0

; ==============================================================================
; 🛠️ 공통 라이브러리 (Common Lib)
; 여러 스크립트에서 공통으로 사용하는 유틸리티 함수 모음입니다.
; ==============================================================================

; ------------------------------------------------------------------------------
; 📁 파일/경로 관련 함수
; ------------------------------------------------------------------------------

; 경로에서 파일명만 추출 (예: C:\Path\file.txt -> file.txt)
GetShortPath(path) {
    if (path = "")
        return ""
    SplitPath(path, &name)
    return name
}

; 지정된 폴더가 없으면 생성하고, 파일 선택 대화상자를 엽니다.
; Return: 선택된 파일 경로 (취소 시 "")
PickImageFile(baseDir, title := "이미지 선택") {
    ; 폴더가 없으면 생성
    if !DirExist(baseDir)
        DirCreate(baseDir)
    
    ; 파일 선택 창 열기 (시작 위치: baseDir)
    return FileSelect(1, baseDir, title, "이미지 파일 (*.png; *.jpg; *.bmp)")
}

; ------------------------------------------------------------------------------
; 🖥️ 화면/모니터 관련 함수
; ------------------------------------------------------------------------------

; 특정 모니터의 테두리를 깜빡여서 표시합니다.
; monitorIndex: 모니터 번호 (기본값: 주 모니터)
; color: 테두리 색상 (기본값: 녹색 00FF00)
FlashMonitorBorder(monitorIndex := "", color := "00FF00", count := 3) {
    if (monitorIndex = "")
        monitorIndex := MonitorGetPrimary()
        
    try {
        ; 모니터 정보 가져오기
        MonitorGet(monitorIndex, &L, &T, &R, &B)
        W := R - L
        
        borderGui := Gui("+AlwaysOnTop -Caption +ToolWindow")
        borderGui.BackColor := color
        
        Loop count {
            ; 상단 테두리 표시
            borderGui.Show("x" L " y" T " w" W " h8 NoActivate")
            Sleep 200
            borderGui.Hide()
            Sleep 150
        }
        borderGui.Destroy()
    } catch {
        MsgBox("모니터 정보를 가져올 수 없습니다.", "오류")
    }
}

; 주 모니터의 영역(좌, 상, 우, 하)을 반환합니다.
GetPrimaryMonitorRect(&L, &T, &R, &B) {
    primary := MonitorGetPrimary()
    MonitorGet(primary, &L, &T, &R, &B)
    return primary ; 모니터 번호 반환
}

; ------------------------------------------------------------------------------
; 🔐 캡차 해결 관련 함수
; ------------------------------------------------------------------------------

; 앵커 이미지를 찾아 상대 좌표로 캡차 영역을 계산하고 Python 스크립트를 실행하여 캡차를 해결합니다.
; anchorImagePath: 앵커 이미지 파일 경로 (예: "images/refresh_icon.png")
; offsetX: 앵커 기준 X 오프셋 (음수면 왼쪽)
; offsetY: 앵커 기준 Y 오프셋 (음수면 위쪽)
; captchaW: 캡차 영역 너비
; captchaH: 캡차 영역 높이
; pythonScript: Python 스크립트 경로 (기본값: "captcha_solver.py")
; Return: 인식된 캡차 코드 (실패 시 "FAIL")
SolveCaptchaFromAnchor(anchorImagePath, offsetX, offsetY, captchaW, captchaH, pythonScript := "captcha_solver.py") {
    ; 1. 앵커 이미지 찾기
    if !FileExist(anchorImagePath) {
        ; 앵커 이미지 없으면 패스 (캡차가 아닐 수 있으므로 조용히 실패)
        return "FAIL"
    }
    
    ; 주 모니터 영역 가져오기
    GetPrimaryMonitorRect(&L, &T, &R, &B)
    
    ; 이미지 검색
    if !ImageSearch(&foundX, &foundY, L, T, R, B, "*50 " anchorImagePath) {
        return "FAIL"  ; 앵커를 찾지 못함
    }
    
    ; 2. 캡차 영역 계산
    captchaX := foundX + offsetX
    captchaY := foundY + offsetY
    
    ; 3. Python 스크립트 실행 (좌표 전달)
    resultFile := A_ScriptDir "\captcha_result.txt"
    
    ; 기존 결과 파일 삭제
    if FileExist(resultFile)
        FileDelete(resultFile)
    
    ; Python 스크립트 경로 확인
    scriptPath := A_ScriptDir "\" pythonScript
    if !FileExist(scriptPath) {
        MsgBox("Python 스크립트를 찾을 수 없습니다: " scriptPath, "오류")
        return "FAIL"
    }
    
    ; Python 실행 (좌표 전달)
    ; 주의: Python이 시스템 PATH에 있어야 함
    cmd := "python `"" scriptPath "`" " captchaX " " captchaY " " captchaW " " captchaH " `"" resultFile "`""
    RunWait(cmd, A_ScriptDir, "Hide")
    
    ; 4. 결과 읽기
    if !FileExist(resultFile) {
        return "FAIL"
    }
    
    try {
        code := FileRead(resultFile, "UTF-8")
        code := Trim(code)
        return code
    } catch {
        return "FAIL"
    }
}

; 캡차 입력 영역에 코드를 입력하고 엔터를 칩니다.
; (참고: 이제 대부분의 로직은 pythonScript 내부로 위임되었습니다. 인자들은 무시될 수 있음)
; pythonScript: Python 스크립트 경로 (기본값: "captcha_solver.py")
; Return: true (실행 성공) / false (실패)
SolveAndInputCaptcha(pythonScript := "popup_handler.py") {
    
    ; 1. 모니터 정보 가져오기
    GetPrimaryMonitorRect(&L, &T, &R, &B)
    W := R - L
    H := B - T
    
    ; 2. Python 스크립트 실행
    ; 인자: 모니터X 모니터Y 모니터W 모니터H 결과파일
    ; (Python 내부에서 앵커 찾고, 좌표 계산하고, VLM 호출하고, 입력까지 다 함)
    
    scriptPath := A_ScriptDir "\" pythonScript
    if !FileExist(scriptPath) {
        MsgBox("Python 스크립트를 찾을 수 없습니다: " scriptPath, "오류")
        return false
    }
    
    resultFile := A_ScriptDir "\captcha_result.txt"
    cmd := "python `"" scriptPath "`" " L " " T " " W " " H " `"" resultFile "`""
    
    ; 팝업 핸들러를 비동기로 실행 (CMD 창 표시, 종료 대기 안 함)
    Run(cmd, A_ScriptDir)
    
    return true
}
