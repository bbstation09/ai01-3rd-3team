; ========================================
; 🎫 클릭 매크로 v3.0 - GUI 버전
; ========================================
; [기능]
; - 지정한 오픈 시간까지 자동 대기
; - 오픈 시간 되면 자동 새로고침 + 버튼 클릭
; - GUI로 편리한 설정 및 제어
; ========================================
#Requires AutoHotkey v2.0
#SingleInstance Force

; 📦 공통 모듈 포함
#Include common.ahk

; ========== 전역 설정 ==========
; 좌표계를 전체 화면 절대 좌표(Screen)로 통일 (매우 중요!)
CoordMode "Pixel", "Screen"
CoordMode "Mouse", "Screen"
CoordMode "ToolTip", "Screen"

; ========== 전역 변수 ==========
global isRunning := false
global currentMode := ""  ; "wait" 또는 "watch"

; 스크립트 이름 기반 이미지 경로 설정 (예: time_click_1.png)
global g_ScriptNameNoExt := ""
SplitPath(A_ScriptName, , , , &g_ScriptNameNoExt)

; 이미지 경로를 'images' 하위 폴더로 지정 (prefix: 실행파일명 + _1)
global imgPath := A_ScriptDir "\images\" g_ScriptNameNoExt "_1.png"
global mainGui := ""
global statusText := ""
global imgPreview := ""
global waitBtn := ""
global watchBtn := ""
global hourEdit := ""
global minEdit := ""
global secEdit := ""
global imgPathText := ""
global watchLoopCounter := 0

; ========== GUI 생성 ==========
CreateMainGui()

CreateMainGui() {
    global mainGui, statusText, imgPreview, waitBtn, watchBtn
    global hourEdit, minEdit, secEdit, imgPath, imgPathText
    
    ; 메인 윈도우
    mainGui := Gui("+AlwaysOnTop", "🎫 클릭 매크로 v3.0")
    mainGui.BackColor := "1a1a2e"
    mainGui.SetFont("s10 cFFFFFF", "맑은 고딕")
    
    ; ========== 프로그램 설명 ==========
    mainGui.SetFont("s12 c00FFFF")
    mainGui.Add("Text", "x20 y15 w360 Center", "🎫 티켓팅 자동 클릭 매크로")
    
    mainGui.SetFont("s9 cC0C0C0")
    mainGui.Add("Text", "x20 y45 w360 Center", "지정한 시간에 자동으로 새로고침하고")
    mainGui.Add("Text", "x20 y65 w360 Center", "등록한 버튼 이미지를 찾아 클릭합니다.")
    
    ; 감시 화면 정보 표시
    mainGui.SetFont("s8 cFFFF00 Bold")
    mainGui.Add("Text", "x20 y85 w360 Center", "⚠️ 감시 시작 시 녹색 깜박이는 화면만 감시합니다!")
    
    ; 주 모니터 정보 정확히 가져오기
    primaryMonitor := MonitorGetPrimary()
    MonitorGet(primaryMonitor, &monLeft, &monTop, &monRight, &monBottom)
    monWidth := monRight - monLeft
    monHeight := monBottom - monTop
    
    mainGui.SetFont("s8 c00FF00")
    mainGui.Add("Text", "x20 y100 w360 Center", "🖥️ 주 모니터: " monWidth "x" monHeight " (모니터 #" primaryMonitor ")")
    
    ; 구분선
    mainGui.Add("Text", "x20 y120 w360 h2 Background333355")





    
    ; ========== 버튼 이미지 섹션 ==========
    ; 기존 설정된 파일이 없으면 다른 확장자 검사
    if !FileExist(imgPath) {
        basePath := A_ScriptDir "\images\" g_ScriptNameNoExt "_1"
        
        if FileExist(basePath ".bmp")
            imgPath := basePath ".bmp"
        else if FileExist(basePath ".jpg")
            imgPath := basePath ".jpg"
    }

    mainGui.SetFont("s10 cFFFF00")
    mainGui.Add("Text", "x20 y135", "📷 버튼 이미지")
    
    mainGui.SetFont("s9 cFFFFFF")
    
    ; 이미지 미리보기 영역 (배경)
    mainGui.Add("Text", "x20 y160 w200 h80 Background222244 Center", "")
    
    ; 이미지 미리보기
    if FileExist(imgPath) {
        imgPreview := mainGui.Add("Picture", "x25 y165 w190 h70", imgPath)
    } else {
        imgPreview := mainGui.Add("Text", "x25 y190 w190 h30 c808080 Center", "이미지 없음")
    }
    
    ; 이미지 등록 버튼
    imgSelectBtn := mainGui.Add("Button", "x240 y160 w140 h35", "📁 이미지 선택")
    imgSelectBtn.OnEvent("Click", SelectImage)
    
    ; 이미지 경로 표시
    imgPathText := mainGui.Add("Text", "x240 y200 w140 h40 c808080", GetShortPath(imgPath))
    
    ; 구분선
    mainGui.Add("Text", "x20 y250 w360 h2 Background333355")


    
    ; ========== 오픈 시간 설정 ==========
    mainGui.SetFont("s10 cFFFF00")
    mainGui.Add("Text", "x20 y265", "⏰ 오픈 시간 설정")
    
    mainGui.SetFont("s12 cFFFF00 Bold")
    
    ; 시간 입력 (UpDown 컨트롤 포함)
    mainGui.Add("Text", "x20 y295", "시간:")
    hourEdit := mainGui.Add("Edit", "x70 y292 w60 h28 Center Number Background2a2a4a")
    hourEdit.Value := "20"
    mainGui.Add("UpDown", "Range0-23", 20).OnEvent("Change", (*) => ValidateHour())
    mainGui.Add("Text", "x135 y295", "시")
    
    mainGui.Add("Text", "x165 y295", "분:")
    minEdit := mainGui.Add("Edit", "x205 y292 w60 h28 Center Number Background2a2a4a")
    minEdit.Value := "00"
    mainGui.Add("UpDown", "Range0-59", 0).OnEvent("Change", (*) => ValidateMin())
    mainGui.Add("Text", "x270 y295", "분")
    
    mainGui.Add("Text", "x300 y295", "초:")
    secEdit := mainGui.Add("Edit", "x340 y292 w60 h28 Center Number Background2a2a4a")
    secEdit.Value := "00"
    mainGui.Add("UpDown", "Range0-59", 0).OnEvent("Change", (*) => ValidateSec())
    
    ; 현재 시간 자동 입력 버튼
    mainGui.SetFont("s9 c000000")
    nowBtn := mainGui.Add("Button", "x20 y325 w380 h30", "🕐 현재 시간으로 설정")
    nowBtn.OnEvent("Click", SetCurrentTime)
    
    mainGui.SetFont("s10 cFFFFFF")
    
    ; 구분선
    mainGui.Add("Text", "x20 y365 w360 h2 Background333355")


    
    ; ========== 제어 버튼 ==========
    mainGui.SetFont("s10 cFFFF00")
    mainGui.Add("Text", "x20 y380", "🎮 제어")
    
    ; 대기 버튼 (오픈 시간까지 대기 후 감시)
    mainGui.SetFont("s10 c000000")
    waitBtn := mainGui.Add("Button", "x20 y405 w170 h45", "⏳ 대기 시작")
    waitBtn.OnEvent("Click", ToggleWait)
    
    ; 감시 버튼 (즉시 감시 시작)
    watchBtn := mainGui.Add("Button", "x210 y405 w170 h45", "🔍 즉시 감시")
    watchBtn.OnEvent("Click", ToggleWatch)

    
    ; 구분선
    mainGui.Add("Text", "x20 y460 w360 h2 Background333355")
    
    ; ========== 상태 표시 ==========
    mainGui.SetFont("s10 cFFFF00")
    mainGui.Add("Text", "x20 y475", "📊 상태")
    
    mainGui.SetFont("s10 c00FF00")
    statusText := mainGui.Add("Text", "x20 y500 w360 h50 Background222244 Center", "준비 완료 - 버튼을 눌러 시작하세요")

    
    ; ========== 단축키 안내 ==========
    mainGui.SetFont("s8 c808080")
    mainGui.Add("Text", "x20 y560 w360 Center", "단축키: [ESC] 종료")
    
    ; 윈도우 닫기 이벤트
    mainGui.OnEvent("Close", (*) => ExitApp())
    
    ; GUI 표시
    mainGui.Show("w400 h585")



}

; ========== 이미지 선택 ==========
SelectImage(*) {
    global imgPath, imgPreview, imgPathText, mainGui
    
    ; images 폴더를 기본 경로로 하여 파일 선택
    imagesDir := A_ScriptDir "\images"
    selectedFile := PickImageFile(imagesDir, "버튼 이미지 선택")
    
    if (selectedFile != "") {
        ; 선택한 파일의 확장자 추출
        SplitPath(selectedFile, , , &ext)
        
        ; 기존 파일 삭제 (확장자가 다를 수 있으므로)
        if FileExist(imgPath)
            FileDelete(imgPath)
            
        ; 새 경로 설정 (images 폴더 내, 스크립트명_1.확장자 사용)
        imgPath := imagesDir "\" g_ScriptNameNoExt "_1." ext
        
        ; 선택한 이미지를 복사 (만약 images 폴더 내 파일을 선택했다면 자기 복사가 되지만 FileCopy 플래그 1로 덮어쓰기 무방하거나, 경로 비교 가능)
        try {
            if (selectedFile != imgPath) ; 같은 파일이면 복사 생략
                FileCopy(selectedFile, imgPath, 1)
            
            ; 미리보기 업데이트
            imgPreview.Value := imgPath
            imgPathText.Value := GetShortPath(imgPath)
            
            UpdateStatus("✅ 이미지 등록 완료!")
        } catch as err {
            MsgBox("이미지 복사 실패: " err.Message, "오류", "Icon!")
        }
    }
}


; ========== 시간 유효성 검증 ==========
ValidateHour(*) {
    global hourEdit
    val := Integer(hourEdit.Value)
    if (val < 0)
        hourEdit.Value := 0
    else if (val > 23)
        hourEdit.Value := 23
}

ValidateMin(*) {
    global minEdit
    val := Integer(minEdit.Value)
    if (val < 0)
        minEdit.Value := 0
    else if (val > 59)
        minEdit.Value := 59
}

ValidateSec(*) {
    global secEdit
    val := Integer(secEdit.Value)
    if (val < 0)
        secEdit.Value := 0
    else if (val > 59)
        secEdit.Value := 59
}

; ========== 현재 시간으로 설정 ==========
SetCurrentTime(*) {
    global hourEdit, minEdit, secEdit
    hourEdit.Value := A_Hour
    minEdit.Value := A_Min
    secEdit.Value := A_Sec
    UpdateStatus("✅ 현재 시간으로 설정됨: " . FormatTime(, "HH:mm:ss"))
}


; ========== 대기 토글 ==========
ToggleWait(*) {
    global isRunning, currentMode, waitBtn, watchBtn, watchLoopCounter, mainGui, imgPath
    
    if (isRunning && currentMode = "wait") {
        ; 정지
        StopAll()
    } else if (!isRunning) {
        ; 시작 전 체크
        if !FileExist(imgPath) {
            MsgBox("이미지 파일을 먼저 등록해주세요!", "오류", "Icon!")
            return
        }
        
        watchLoopCounter := 0  ; 카운터 초기화
        mainGui.Opt("+AlwaysOnTop")
        
        ; 오탐지 방지: 미리보기 이미지 숨기기
        imgPreview.Visible := false
        
        ; 감시 영역 즉시 표시 (사용자 피드백)
        FlashMonitorBorder()
        
        currentMode := "wait"
        isRunning := true
        waitBtn.Text := "⏹️ 정지"
        waitBtn.Enabled := false
        SetTimer(TimedWatchLoop, 100) ; 시간 대기는 0.1초 단위도 충분
    }
}

; ========== 감시 토글 ==========
ToggleWatch(*) {
    global isRunning, currentMode, waitBtn, watchBtn, watchLoopCounter, mainGui, imgPath, imgPreview
    
    if (isRunning && currentMode = "watch") {
        ; 정지
        StopAll()
    } else if (!isRunning) {
        ; 시작 전 체크
        if !FileExist(imgPath) {
            MsgBox("이미지 파일을 먼저 등록해주세요!", "오류", "Icon!")
            return
        }
        
        watchLoopCounter := 0  ; 카운터 초기화
        mainGui.Opt("+AlwaysOnTop")
        
        ; 오탐지 방지: 미리보기 이미지 숨기기
        imgPreview.Visible := false
        
        ; 감시 영역 즉시 표시 (사용자 피드백)
        FlashMonitorBorder()
        
        currentMode := "watch"
        isRunning := true
        waitBtn.Text := "⏹️ 정지"
        waitBtn.Enabled := false
        SetTimer(WatchLoop, 10) ; 🔥 10ms 고속 스캔!
    }
}

; ========== 모두 정지 ==========
StopAll() {
    global isRunning, currentMode, waitBtn, watchBtn, watchLoopCounter, imgPreview
    
    isRunning := false
    currentMode := ""
    watchLoopCounter := 0
    
    SetTimer(TimedWatchLoop, 0)
    SetTimer(WatchLoop, 0)
    
    ; 미리보기 이미지 복원
    imgPreview.Visible := true
    
    waitBtn.Text := "⏳ 대기 시작"
    waitBtn.Enabled := true
    watchBtn.Text := "🔍 즉시 감시"
    watchBtn.Enabled := true
    
    UpdateStatus("⏹️ 정지됨 - 다시 시작할 수 있습니다")
    ToolTip()
}


; ========== 상태 업데이트 ==========
UpdateStatus(msg) {
    global statusText
    statusText.Value := msg
}

; ========== 오픈 시간 대기 루프 ==========
TimedWatchLoop() {
    global isRunning, hourEdit, minEdit, secEdit, imgPath, watchLoopCounter
    
    if !isRunning
        return
    
    h := Integer(hourEdit.Value)
    m := Integer(minEdit.Value)
    s := Integer(secEdit.Value)
    
    openTime := Format("{:02d}:{:02d}:{:02d}", h, m, s)
    now := A_Hour . A_Min . A_Sec
    target := Format("{:02d}{:02d}{:02d}", h, m, s)
    
    ; 남은 시간 계산
    remaining := CalcRemaining(h, m, s)
    
    statusMsg := "🎫 오픈 대기 중...`n"
             . "오픈: " openTime " | 현재: " FormatTime(, "HH:mm:ss") "`n"
             . "남은 시간: " remaining
    
    UpdateStatus(statusMsg)
    ToolTip(statusMsg, 100, 100)
    
    ; 오픈 시간 도달
    if (now >= target) {
        UpdateStatus("🚀 오픈! 새로고침 중...")
        ToolTip("🚀 오픈! 새로고침 중...", 100, 100)
        Send "{F5}"
        Sleep 500
        
        ; 감시 모드로 전환
        watchLoopCounter := 0  ; 카운터 초기화
        SetTimer(TimedWatchLoop, 0)
        SetTimer(WatchLoop, 10) ; 🔥 10ms 고속 스캔!
    }
}

; ========== 버튼 감시 루프 ==========
WatchLoop() {
    global isRunning, imgPath, watchLoopCounter, mainGui
    
    if !isRunning
        return
    
    ; 주 모니터 정보 가져오기
    try {
        primaryMonitor := MonitorGetPrimary()
        MonitorGet(primaryMonitor, &monLeft, &monTop, &monRight, &monBottom)
    } catch {
        UpdateStatus("❌ 모니터 정보를 가져올 수 없습니다!")
        return
    }
    
    watchLoopCounter++
    
    ; 60초(10ms * 6000회) 경과 시 중단
    if (watchLoopCounter > 6000) { 
        UpdateStatus("❌ 시간 초과`n버튼을 찾지 못했습니다.")
        ToolTip()
        StopAll()
        return
    }
    
    ; 상태 메세지 업데이트는 0.1초(10회)마다 (사용자 피드백 강화)
    if (Mod(watchLoopCounter, 10) = 0) {
        ToolTip("🔍 스캔 중... (" watchLoopCounter ")`n영역: " monLeft "," monTop " - " monRight "," monBottom)
    }
    
    ; ===== 디버그: 1, 100, 200, ... 회차마다 화면 캡처 저장 (사용자 요청으로 주석 처리) =====
    ; if (watchLoopCounter = 1 || Mod(watchLoopCounter, 100) = 0) {
    ;     ; 비동기 실행 (AHK 성능 저하 최소화)
    ;     capScript := A_ScriptDir "\capture_screen.py"
    ;     Run("python `"" capScript "`" " monLeft " " monTop " " (monRight-monLeft) " " (monBottom-monTop) " " watchLoopCounter, , "Hide")
    ; }
    
    try {
        UpdateStatus(imgPath)
        ; 주 모니터에서만 이미지 검색 (정확한 좌표 사용)
        ; *60 옵션: 오차 허용 대폭 상향 (인식률 우선)
        if ImageSearch(&foundX, &foundY, monLeft, monTop, monRight, monBottom, "*60 " imgPath) {
            ; 발견 로그 출력
            UpdateStatus("✨ 버튼 발견! (" foundX ", " foundY ") 클릭 시도...")
            
            ; 발견 즉시 한 번만 정확하게 클릭
            MouseMove foundX + 10, foundY + 10
            Sleep 10 ; 딜레이 최소화
            Click
            SoundBeep(750, 100) ; 발견 알림음
            
            ; 클릭 후 성공 처리
            UpdateStatus("🎉 예매 버튼 클릭 완료! 팝업 처리 대기 중...")
            ToolTip() ; 툴팁 제거
            
            ; 팝업창 가림 방지를 위해 AlwaysOnTop 해제
            mainGui.Opt("-AlwaysOnTop")
            
            ; ===== 캡차 해결 시도 (옵션) =====
            ; 캡차/팝업이 있다면 해결 (없으면 무시)
            ; 인자: (무시됨), 파이썬스크립트
            ; * VLM 기반 팝업 핸들러 사용
            SolveAndInputCaptcha("popup_handler.py")

            
            ; if (didCaptcha) {
            ;     UpdateStatus("✔ 팝업/캡차 처리 완료")
            ;      MsgBox("🎉 예매 버튼 클릭 및 팝업 처리 성공!", "성공")
            ; } else {
            ;      MsgBox("🎉 예매 버튼 클릭 완료! (팝업 없음)", "성공")
            ; }
            
            StopAll()
        }
    } catch as err {
        ; ImageSearch 내부 에러 발생 시 로그 출력 (단순히 못 찾은 경우는 에러가 아님)
        ; ImageSearch는 못 찾으면 False를 반환하고, 파일이 없거나 파라미터가 잘못된 경우에만 에러 발생 가능
        UpdateStatus("⚠️ 이미지 검색 오류: " err.Message)
    }
}



; ========== 남은 시간 계산 ==========
CalcRemaining(h, m, s) {
    targetSec := h * 3600 + m * 60 + s
    nowSec := A_Hour * 3600 + A_Min * 60 + A_Sec
    diff := targetSec - nowSec
    
    if (diff < 0)
        return "오픈 시간 지남!"
    
    hh := Floor(diff / 3600)
    mm := Floor(Mod(diff, 3600) / 60)
    ss := Mod(diff, 60)
    
    return Format("{:02d}:{:02d}:{:02d}", hh, mm, ss)
}

; ========== 단축키 ==========
ESC:: ExitApp()