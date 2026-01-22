"""
🎫 티켓 자동화 시스템
Python tkinter 기반 UI 애플리케이션
"""

import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

# 설정 파일 경로
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    """설정 파일 로드"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    """설정 파일 저장"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"설정 저장 오류: {e}")

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ticket_entry import TicketEntry
from modules.seat_selection import SeatSelection
from modules.payment import Payment
from modules.popup_watcher import PopupWatcher


class TicketAutomationApp:
    """티켓 자동화 메인 애플리케이션"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🎫 티켓 자동화 시스템")
        self.root.geometry("900x720")
        self.root.resizable(False, False)
        
        # 다크 테마 색상
        self.colors = {
            'bg': '#1a1a2e',
            'card': '#16213e',
            'accent': '#0f3460',
            'highlight': '#e94560',
            'text': '#ffffff',
            'text_dim': '#a0a0a0',
            'success': '#00ff88',
            'warning': '#ffcc00',
            'input_bg': '#252a40',  # 입력 필드 배경색
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 스타일 설정
        self._setup_styles()
        
        # 체크박스 변수
        self.entry_enabled = tk.BooleanVar(value=True)
        self.seat_enabled = tk.BooleanVar(value=True)
        self.payment_enabled = tk.BooleanVar(value=False)
        
        # 모듈 인스턴스
        self.ticket_entry = TicketEntry(
            callback=self.update_status,
            on_complete=self._on_ticket_entry_complete
        )
        self.seat_selection = SeatSelection(callback=self.update_status)
        self.payment = Payment(callback=self.update_status)
        self.popup_watcher = PopupWatcher(callback=self.update_status)
        
        # 이미지 관련
        self.target_image_path = None
        self.image_preview = None
        
        # UI 생성
        self._create_header()
        self._create_main_content()
        self._create_status_bar()
        
        # 모니터 정보 설정
        self._setup_monitor()
        
        # 마지막 이미지 로드
        self._load_last_image()
    
    def _setup_styles(self):
        """ttk 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 체크버튼 스타일
        style.configure('Card.TCheckbutton',
            background=self.colors['card'],
            foreground=self.colors['text'],
            font=('맑은 고딕', 12, 'bold'))
        
        # 프레임 스타일
        style.configure('Card.TFrame', background=self.colors['card'])
        
        # 레이블 스타일
        style.configure('Card.TLabel',
            background=self.colors['card'],
            foreground=self.colors['text'],
            font=('맑은 고딕', 10))
        
        style.configure('Header.TLabel',
            background=self.colors['bg'],
            foreground=self.colors['highlight'],
            font=('맑은 고딕', 18, 'bold'))
    
    def _setup_monitor(self):
        """모니터 정보 설정"""
        # 기본값: 전체 화면
        self.ticket_entry.set_monitor_region(0, 0, 1920, 1080)
        self.seat_selection.set_monitor_region(0, 0, 1920, 1080)
        self.popup_watcher.set_monitor_region(0, 0, 1920, 1080)
    
    def _create_header(self):
        """헤더 생성"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg'])
        header_frame.pack(fill='x', padx=20, pady=15)
        
        # 타이틀
        title = tk.Label(header_frame,
            text="🎫 티켓 자동화 시스템",
            font=('맑은 고딕', 20, 'bold'),
            fg=self.colors['highlight'],
            bg=self.colors['bg'])
        title.pack()
        
        # 서브타이틀
        subtitle = tk.Label(header_frame,
            text="예매입장 → 좌석선택 → 결재 자동화",
            font=('맑은 고딕', 10),
            fg=self.colors['text_dim'],
            bg=self.colors['bg'])
        subtitle.pack()
    
    def _create_main_content(self):
        """메인 컨텐츠 (3컬럼) 생성"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 3개 컬럼
        self._create_entry_column(main_frame)
        self._create_seat_column(main_frame)
        self._create_payment_column(main_frame)
        
        # 팝업 감시 섹션 (하단)
        self._create_popup_watcher_section()
    
    def _create_card_frame(self, parent, title, var, column):
        """카드 프레임 생성"""
        # 카드 컨테이너
        card = tk.Frame(parent, bg=self.colors['card'], bd=0)
        card.grid(row=0, column=column, padx=8, pady=5, sticky='nsew')
        parent.grid_columnconfigure(column, weight=1)
        
        # 카드 내부 패딩
        inner = tk.Frame(card, bg=self.colors['card'])
        inner.pack(fill='both', expand=True, padx=15, pady=15)
        
        # 체크박스 헤더
        header = tk.Checkbutton(inner,
            text=title,
            variable=var,
            font=('맑은 고딕', 14, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card'],
            selectcolor=self.colors['accent'],
            activebackground=self.colors['card'],
            activeforeground=self.colors['text'],
            indicatoron=True,
            width=12,
            anchor='w')
        header.pack(anchor='w')
        
        # 구분선
        sep = tk.Frame(inner, bg=self.colors['accent'], height=2)
        sep.pack(fill='x', pady=10)
        
        return inner
    
    def _create_entry_column(self, parent):
        """예매입장 컬럼"""
        inner = self._create_card_frame(parent, "예매입장", self.entry_enabled, 0)
        
        # 이미지 섹션
        img_label = tk.Label(inner,
            text="📷 버튼 이미지",
            font=('맑은 고딕', 10, 'bold'),
            fg=self.colors['warning'],
            bg=self.colors['card'])
        img_label.pack(anchor='w', pady=(5, 5))
        
        # 이미지 미리보기
        self.preview_frame = tk.Frame(inner, bg=self.colors['accent'], width=200, height=80)
        self.preview_frame.pack(fill='x', pady=5)
        self.preview_frame.pack_propagate(False)
        
        self.preview_label = tk.Label(self.preview_frame,
            text="이미지 없음",
            fg=self.colors['text_dim'],
            bg=self.colors['accent'])
        self.preview_label.pack(expand=True)
        
        # 이미지 선택 버튼
        img_btn = tk.Button(inner,
            text="📁 이미지 선택",
            command=self._select_image,
            font=('맑은 고딕', 9),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            relief='flat',
            cursor='hand2')
        img_btn.pack(fill='x', pady=5)
        
        # 시간 설정 섹션
        time_label = tk.Label(inner,
            text="⏰ 오픈 시간",
            font=('맑은 고딕', 10, 'bold'),
            fg=self.colors['warning'],
            bg=self.colors['card'])
        time_label.pack(anchor='w', pady=(15, 5))
        
        # 시간 입력
        time_frame = tk.Frame(inner, bg=self.colors['card'])
        time_frame.pack(fill='x', pady=5)
        
        self.hour_var = tk.StringVar(value="20")
        self.min_var = tk.StringVar(value="00")
        self.sec_var = tk.StringVar(value="00")
        
        for i, (var, label) in enumerate([(self.hour_var, "시"), (self.min_var, "분"), (self.sec_var, "초")]):
            entry = tk.Entry(time_frame, textvariable=var, width=4, 
                font=('맑은 고딕', 14), justify='center',
                bg=self.colors['accent'], fg=self.colors['text'],
                insertbackground=self.colors['text'])
            entry.pack(side='left', padx=2)
            
            lbl = tk.Label(time_frame, text=label, 
                font=('맑은 고딕', 10),
                fg=self.colors['text_dim'], bg=self.colors['card'])
            lbl.pack(side='left', padx=(0, 8))
        
        # 현재 시간 버튼
        now_btn = tk.Button(inner,
            text="🕐 현재 시간",
            command=self._set_current_time,
            font=('맑은 고딕', 9),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            relief='flat',
            cursor='hand2')
        now_btn.pack(fill='x', pady=5)
        
        # 시작 버튼들
        btn_frame = tk.Frame(inner, bg=self.colors['card'])
        btn_frame.pack(fill='x', pady=(15, 5))
        
        self.wait_btn = tk.Button(btn_frame,
            text="⏳ 대기 시작",
            command=self._toggle_wait,
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['highlight'],
            fg=self.colors['text'],
            relief='flat',
            cursor='hand2',
            width=12)
        self.wait_btn.pack(side='left', padx=2, expand=True, fill='x')
        
        self.watch_btn = tk.Button(btn_frame,
            text="🔍 즉시 감시",
            command=self._toggle_watch,
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text'],
            relief='flat',
            cursor='hand2',
            width=12)
        self.watch_btn.pack(side='left', padx=2, expand=True, fill='x')
    
    def _create_seat_column(self, parent):
        """좌석선택 컬럼"""
        inner = self._create_card_frame(parent, "좌석선택", self.seat_enabled, 1)
        
        # 옵션 섹션
        opt_label = tk.Label(inner,
            text="🪑 좌석 옵션",
            font=('맑은 고딕', 10, 'bold'),
            fg=self.colors['warning'],
            bg=self.colors['card'])
        opt_label.pack(anchor='w', pady=(5, 10))
        
        # 체크박스 옵션들
        self.center_var = tk.BooleanVar(value=True)
        center_cb = tk.Checkbutton(inner,
            text="중앙 좌석 우선",
            variable=self.center_var,
            font=('맑은 고딕', 10),
            fg=self.colors['text'],
            bg=self.colors['card'],
            selectcolor=self.colors['accent'],
            activebackground=self.colors['card'])
        center_cb.pack(anchor='w', pady=2)
        
        self.auto_zoom_var = tk.BooleanVar(value=True)
        zoom_cb = tk.Checkbutton(inner,
            text="자동 확대",
            variable=self.auto_zoom_var,
            font=('맑은 고딕', 10),
            fg=self.colors['text'],
            bg=self.colors['card'],
            selectcolor=self.colors['accent'],
            activebackground=self.colors['card'])
        zoom_cb.pack(anchor='w', pady=2)

        # 좌석 색상 선택 (콤보박스)
        color_frame = tk.Frame(inner, bg=self.colors['card'])
        color_frame.pack(fill='x', pady=2)
        
        tk.Label(color_frame, 
            text="좌석 색상:", 
            font=('맑은 고딕', 10),
            fg=self.colors['text'],
            bg=self.colors['card']).pack(side='left')
        
        # seat_colors 폴더에서 색상 파일 목록 로드
        import os
        color_options = ["All Colors"]
        seat_colors_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seat_colors")
        if os.path.exists(seat_colors_dir):
            for f in sorted(os.listdir(seat_colors_dir)):
                if f.endswith(('.png', '.jpg', '.bmp')):
                    color_options.append(f.replace('.png', '').replace('.jpg', '').replace('.bmp', ''))
        
        self.color_select_var = tk.StringVar(value="All Colors")
        self.color_select_combo = ttk.Combobox(color_frame,
            textvariable=self.color_select_var,
            values=color_options,
            state='readonly',
            width=15,
            font=('맑은 고딕', 10))
        self.color_select_combo.pack(side='left', padx=5)
        
        # 좌석 수량
        count_frame = tk.Frame(inner, bg=self.colors['card'])
        count_frame.pack(fill='x', pady=(5, 0))
        
        tk.Label(count_frame, 
            text="좌석 수량:", 
            font=('맑은 고딕', 10),
            fg=self.colors['text'],
            bg=self.colors['card']).pack(side='left')
            
        self.seat_count_var = tk.StringVar(value="1")
        self.seat_count_spin = tk.Spinbox(count_frame,
            from_=1, to=5,
            textvariable=self.seat_count_var,
            width=3,
            font=('맑은 고딕', 10),
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            relief='flat')
        self.seat_count_spin.pack(side='left', padx=5)
        
        tk.Label(count_frame, 
            text="석 (연속)", 
            font=('맑은 고딕', 10),
            fg=self.colors['text_dim'],
            bg=self.colors['card']).pack(side='left')
        
        # VLM 옵션
        vlm_label = tk.Label(inner,
            text="🤖 VLM 설정",
            font=('맑은 고딕', 10, 'bold'),
            fg=self.colors['warning'],
            bg=self.colors['card'])
        vlm_label.pack(anchor='w', pady=(20, 10))
        
        self.vlm_var = tk.StringVar(value="LM_STUDIO")
        for vlm in ["LM_STUDIO", "GROQ"]:
            rb = tk.Radiobutton(inner,
                text=vlm,
                variable=self.vlm_var,
                value=vlm,
                font=('맑은 고딕', 10),
                fg=self.colors['text'],
                bg=self.colors['card'],
                selectcolor=self.colors['accent'],
                activebackground=self.colors['card'])
            rb.pack(anchor='w', pady=2)
        
        # 시작 버튼
        self.seat_btn = tk.Button(inner,
            text="▶️ 작업 시작",
            command=self._toggle_seat_selection,
            font=('맑은 고딕', 11, 'bold'),
            bg=self.colors['highlight'],
            fg=self.colors['text'],
            relief='flat',
            cursor='hand2')
        self.seat_btn.pack(fill='x', pady=(30, 5))
    
    def _create_payment_column(self, parent):
        """결재 컬럼"""
        inner = self._create_card_frame(parent, "결재자동화", self.payment_enabled, 2)
        
        # Placeholder
        placeholder = tk.Label(inner,
            text="💳 결재 자동화\n\n(추후 구현 예정)",
            font=('맑은 고딕', 11),
            fg=self.colors['text_dim'],
            bg=self.colors['card'],
            justify='center')
        placeholder.pack(expand=True, pady=50)
        
        # 비활성화 버튼
        self.payment_btn = tk.Button(inner,
            text="💳 결재 시작",
            command=self._toggle_payment,
            font=('맑은 고딕', 11, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['text_dim'],
            relief='flat',
            state='disabled')
        self.payment_btn.pack(fill='x', pady=(20, 5))
    
    def _create_status_bar(self):
        """상태바 생성"""
        status_frame = tk.Frame(self.root, bg=self.colors['accent'])
        status_frame.pack(fill='x', side='bottom')
        
        self.status_label = tk.Label(status_frame,
            text="📡 대기 중...",
            font=('맑은 고딕', 10),
            fg=self.colors['text'],
            bg=self.colors['accent'],
            anchor='w',
            padx=15,
            pady=8)
        self.status_label.pack(fill='x')
    
    def update_status(self, message):
        """상태 업데이트"""
        def _update():
            self.status_label.config(text=f"📡 {message}")
        self.root.after(0, _update)
    
    def _select_image(self):
        """이미지 선택"""
        images_dir = os.path.join(os.path.dirname(__file__), "images")
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        filepath = filedialog.askopenfilename(
            initialdir=images_dir,
            title="버튼 이미지 선택",
            filetypes=[("Image files", "*.png *.jpg *.bmp"), ("All files", "*.*")])
        
        if filepath:
            self._set_image(filepath, save=True)
    
    def _set_image(self, filepath, save=False):
        """이미지 설정 (내부용)"""
        if not os.path.exists(filepath):
            self.update_status(f"이미지 파일 없음: {filepath}")
            return
        
        self.target_image_path = filepath
        self.ticket_entry.set_target_image(filepath)
        
        # 미리보기 업데이트
        try:
            img = Image.open(filepath)
            img.thumbnail((180, 70))
            self.image_preview = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.image_preview, text="")
        except Exception as e:
            self.preview_label.config(text=os.path.basename(filepath))
        
        # 설정 저장
        if save:
            config = load_config()
            config['last_image'] = filepath
            save_config(config)
    
    def _load_last_image(self):
        """마지막 사용 이미지 로드"""
        config = load_config()
        last_image = config.get('last_image')
        if last_image and os.path.exists(last_image):
            self._set_image(last_image, save=False)
            self.update_status(f"✅ 이전 이미지 로드: {os.path.basename(last_image)}")
    
    def _set_current_time(self):
        """다음 정시로 시간 설정"""
        from datetime import datetime
        now = datetime.now()
        
        # 다음 시간 계산
        next_hour = now.hour + 1
        if next_hour >= 24:
            next_hour = 0
        
        self.hour_var.set(f"{next_hour:02d}")
        self.min_var.set("00")
        self.sec_var.set("00")
        self.update_status(f"다음 오픈 시간: {next_hour:02d}:00:00")
    
    def _toggle_wait(self):
        """대기 시작/중지"""
        if self.ticket_entry.is_running:
            self.ticket_entry.stop()
            self.wait_btn.config(text="⏳ 대기 시작")
        else:
            try:
                h = int(self.hour_var.get())
                m = int(self.min_var.get())
                s = int(self.sec_var.get())
                self.ticket_entry.set_target_time(h, m, s)
                
                if self.ticket_entry.start_waiting():
                    self.wait_btn.config(text="⏹️ 중지")
            except ValueError:
                messagebox.showerror("오류", "시간을 올바르게 입력하세요!")
    
    def _toggle_watch(self):
        """즉시 감시 시작/중지"""
        if self.ticket_entry.is_running:
            self.ticket_entry.stop()
            self.watch_btn.config(text="🔍 즉시 감시")
        else:
            if self.ticket_entry.start_watching():
                self.watch_btn.config(text="⏹️ 중지")
    
    def _on_ticket_entry_complete(self, success: bool):
        """예매입장 완료 시 콜백"""
        def _update():
            # 버튼 상태 리셋
            self.wait_btn.config(text="⏳ 대기 시작")
            self.watch_btn.config(text="🔍 즉시 감시")
            
            if success:
                self.update_status("🎉 예매입장 성공!")
                
                # 좌석선택이 체크되어 있으면 자동 시작
                if self.seat_enabled.get():
                    self.update_status("→ 좌석선택 자동 시작...")
                    self._start_seat_selection()
            else:
                self.update_status("❌ 예매입장 실패")
        
        # UI 스레드에서 실행
        self.root.after(100, _update)
    
    def _start_seat_selection(self):
        """좌석 선택 시작 (내부용)"""
        # 옵션 적용
        self.seat_selection.prefer_center = self.center_var.get()
        self.seat_selection.auto_zoom = self.auto_zoom_var.get()
        self.seat_selection.selected_color = self.color_select_var.get()
        try:
            self.seat_selection.seat_count = int(self.seat_count_var.get())
        except:
            self.seat_selection.seat_count = 1
        
        # VLM 설정 변경
        from modules import vlm_handler
        vlm_handler.USE_PROVIDER = self.vlm_var.get()
        
        # 별도 스레드에서 실행
        def run():
            self.seat_selection.start()
            self.root.after(0, lambda: self.seat_btn.config(text="▶️ 작업 시작"))
        
        self.seat_btn.config(text="⏹️ 중지")
        threading.Thread(target=run, daemon=True).start()
    
    def _toggle_seat_selection(self):
        """좌석 선택 시작/중지"""
        if self.seat_selection.is_running:
            self.seat_selection.stop()
            self.seat_btn.config(text="▶️ 작업 시작")
        else:
            # 옵션 적용
            self.seat_selection.prefer_center = self.center_var.get()
            self.seat_selection.auto_zoom = self.auto_zoom_var.get()
            self.seat_selection.selected_color = self.color_select_var.get()
            try:
                self.seat_selection.seat_count = int(self.seat_count_var.get())
            except:
                self.seat_selection.seat_count = 1
            
            # VLM 설정 변경
            from modules import vlm_handler
            vlm_handler.USE_PROVIDER = self.vlm_var.get()
            
            # 별도 스레드에서 실행
            def run():
                self.seat_selection.start()
                self.root.after(0, lambda: self.seat_btn.config(text="🪑 좌석 선택 시작"))
            
            self.seat_btn.config(text="⏹️ 중지")
            threading.Thread(target=run, daemon=True).start()
    
    def _toggle_payment(self):
        """결재 시작/중지 (미구현)"""
        messagebox.showinfo("알림", "결재 자동화는 추후 구현 예정입니다.")
    
    def _create_popup_watcher_section(self):
        """팝업 감시 섹션 생성"""
        popup_frame = tk.Frame(self.root, bg=self.colors['card'])
        popup_frame.pack(fill='x', padx=28, pady=(0, 10))
        
        inner = tk.Frame(popup_frame, bg=self.colors['card'])
        inner.pack(fill='x', padx=15, pady=10)
        
        # 왼쪽: 제목과 설명
        left_frame = tk.Frame(inner, bg=self.colors['card'])
        left_frame.pack(side='left', fill='x', expand=True)
        
        title_label = tk.Label(left_frame,
            text="👁️ 팝업 자동 처리",
            font=('맑은 고딕', 12, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card'])
        title_label.pack(side='left')
        
        desc = tk.Label(left_frame,
            text="  (CAPTCHA, 확인창, 안내창 자동 처리)",
            font=('맑은 고딕', 9),
            fg=self.colors['text_dim'],
            bg=self.colors['card'])
        desc.pack(side='left')
        
        # 오른쪽: 버튼들
        right_frame = tk.Frame(inner, bg=self.colors['card'])
        right_frame.pack(side='right')
        
        self.popup_btn = tk.Button(right_frame,
            text="▶ 시작",
            command=self._toggle_popup_watcher,
            font=('맑은 고딕', 10, 'bold'),
            bg=self.colors['success'],
            fg=self.colors['bg'],
            relief='flat',
            cursor='hand2',
            width=8)
        self.popup_btn.pack(side='left', padx=5)
    
    def _toggle_popup_watcher(self):
        """팝업 감시 시작/중지"""
        if self.popup_watcher.is_running:
            self.popup_watcher.stop()
            self.popup_btn.config(text="▶ 시작", bg=self.colors['success'])
        else:
            self.popup_watcher.start()
            self.popup_btn.config(text="⏹ 정지", bg=self.colors['highlight'])


def main():
    root = tk.Tk()
    app = TicketAutomationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
