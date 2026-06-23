#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生死狙击2 - 瞄准小球 自动连点器
自动识别并高速连续点击游戏区域内的小球

使用方法:
  直接运行 -> GUI模式
  --cli    -> 命令行模式
  --debug  -> 显示小球检测可视化窗口（调试用）
"""

import os
import sys
import time
import threading
import ctypes

# ── DPI 感知设置：避免高DPI下坐标缩放导致点击偏移 ──
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PerMonitorV2
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from collections import deque

import cv2
import numpy as np
import win32gui
import win32api
import win32con
import win32ui
from PIL import ImageGrab

# ==================== 配置参数 ====================
class Config:
    # 窗口标题关键词
    WINDOW_TITLE_KEYWORD = "生死狙击2"
    
    # 小球检测参数 (HSV色彩空间)
    SATURATION_THRESHOLD = 60      # 饱和度阈值
    VALUE_THRESHOLD = 120          # 亮度阈值
    
    # 小球大小范围（像素）
    MIN_BALL_RADIUS = 8
    MAX_BALL_RADIUS = 60
    
    # 轮廓面积下限（像素²）— 排除残留光晕碎片
    MIN_CONTOUR_AREA = 60
    
    # 圆形度阈值
    MIN_CIRCULARITY = 0.55
    
    # 去重距离
    MIN_BALL_DISTANCE = 15
    
    # 热键 (MOD_ALT=1, MOD_CONTROL=2, MOD_SHIFT=4, MOD_WIN=8)
    HOTKEY_ID_START = 1
    HOTKEY_ID_STOP = 2
    HOTKEY_START_KEY = win32con.VK_F6       # F6
    HOTKEY_STOP_KEY = win32con.VK_F7        # F7
    HOTKEY_MOD = 0                          # 无修饰键
    
    # 快速模式点击时序（秒）
    FAST_MOVE_SETTLE = 0.010       # 移动后等待鼠标稳定
    FAST_CLICK_HOLD = 0.030        # 按住时间，确保游戏注册
    FAST_CLICK_RELEASE = 0.010     # 释放后间隔
    FAST_BALL_GAP = 0.030          # 球与球之间的间隔
    # 检测循环间隔
    DETECT_INTERVAL = 0.05
    # 调试慢速模式
    SLOW_MODE = False                    # --slow 参数开启
    SLOW_MOVE_STEPS = 40                 # 平滑移动步数
    SLOW_MOVE_DURATION = 0.25            # 移动总时长(秒)
    SLOW_CLICK_HOLD = 0.15               # 按下持续时长(秒)
    SLOW_DELAY_BEFORE = 0.2              # 点击前延迟(秒)
    SLOW_DELAY_AFTER = 0.4               # 点击后间隔(秒)

    # 检测区域边距（占客户区比例，范围0-1），限定小球检测范围
    # 这些值根据游戏截图红框区域估算
    DETECT_LEFT = 0.14     # 左侧菜单栏
    DETECT_RIGHT = 0.22    # 右侧好友排行面板
    DETECT_TOP = 0.18      # 顶部连击/时间UI
    DETECT_BOTTOM = 0.22   # 底部开始按钮/得分UI


# ==================== 窗口管理 ====================
class WindowManager:
    def __init__(self):
        self.hwnd = None
        self.window_rect = None
        self.client_rect = None
        self.game_area = None
        self.detect_offset = (0, 0)   # (dx, dy)：检测子区域在截图内的偏移
        
    def find_window(self) -> bool:
        windows = []
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    title = win32gui.GetWindowText(hwnd)
                    if Config.WINDOW_TITLE_KEYWORD in title:
                        windows.append(hwnd)
                except:
                    pass
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        if not windows:
            return False
        
        self.hwnd = windows[0]
        self._update_rects()
        return True
    
    def _update_rects(self):
        if self.hwnd is None:
            return
        try:
            self.window_rect = win32gui.GetWindowRect(self.hwnd)
            self.client_rect = win32gui.GetClientRect(self.hwnd)
            
            left_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
            client_width = self.client_rect[2]
            client_height = self.client_rect[3]
            
            # 完整客户区 = 游戏区域（靠HSV过滤排除UI）
            self.game_area = (
                left_top[0],
                left_top[1],
                left_top[0] + client_width,
                left_top[1] + client_height
            )
            
            # 检测子区域偏移（红框范围）
            self.detect_offset = (
                int(client_width * Config.DETECT_LEFT),
                int(client_height * Config.DETECT_TOP)
            )
            detect_w = client_width - int(client_width * Config.DETECT_LEFT) - int(client_width * Config.DETECT_RIGHT)
            detect_h = client_height - int(client_height * Config.DETECT_TOP) - int(client_height * Config.DETECT_BOTTOM)
            
            print(f"[INFO] 窗口Rect={self.window_rect} 客户区={self.client_rect}")
            print(f"[INFO] 客户区屏幕坐标: ({left_top[0]},{left_top[1]}) 尺寸={client_width}x{client_height}")
            print(f"[INFO] 检测区域: 偏移({self.detect_offset[0]},{self.detect_offset[1]}) 尺寸={detect_w}x{detect_h}")
        except Exception:
            self.game_area = None
            self.detect_offset = (0, 0)
    
    def is_window_valid(self) -> bool:
        if self.hwnd is None:
            return False
        try:
            return bool(win32gui.IsWindow(self.hwnd) and win32gui.IsWindowVisible(self.hwnd))
        except:
            return False
    
    def get_game_screenshot(self):
        if self.game_area is None:
            return None
        try:
            x1, y1, x2, y2 = self.game_area
            if x1 >= x2 or y1 >= y2:
                return None
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception:
            return None
    
    def game_to_screen_coords(self, game_x, game_y):
        if self.game_area is None:
            return game_x, game_y
        return game_x + self.game_area[0], game_y + self.game_area[1]


# ==================== 小球检测器 ====================
class BallDetector:
    def __init__(self):
        self.kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        self.kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
    def detect(self, screenshot):
        if screenshot is None or screenshot.size == 0:
            return []
        
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        _, s, v = cv2.split(hsv)
        
        # 高饱和度 + 高亮度区域
        mask_s = cv2.threshold(s, Config.SATURATION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        mask_v = cv2.threshold(v, Config.VALUE_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
        mask = cv2.bitwise_and(mask_s, mask_v)
        
        # 形态学处理 — 仅 1 次 close，避免把消失球残留光晕连成虚影
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel_close, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel_open, iterations=1)
        
        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        balls = []
        h_img, w_img = screenshot.shape[:2]
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < Config.MIN_CONTOUR_AREA:
                continue
            
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            radius = int(radius)
            
            if radius < Config.MIN_BALL_RADIUS or radius > Config.MAX_BALL_RADIUS:
                continue
            
            # 圆形度
            circle_area = np.pi * radius * radius
            if circle_area <= 0:
                continue
            circularity = area / circle_area
            if circularity < Config.MIN_CIRCULARITY:
                continue
            
            # 中心点在mask内
            cxi, cyi = int(cx), int(cy)
            if 0 <= cxi < w_img and 0 <= cyi < h_img:
                if mask[cyi, cxi] == 0:
                    continue
                # 中心点饱和度二次验证：原始 S 通道必须足够高
                if s[cyi, cxi] < Config.SATURATION_THRESHOLD:
                    continue
            
            balls.append((cxi, cyi, radius))
        
        balls = self._deduplicate(balls)
        return balls
    
    def _deduplicate(self, balls):
        if len(balls) <= 1:
            return balls
        balls = sorted(balls, key=lambda b: b[2], reverse=True)
        result = []
        for ball in balls:
            dup = False
            for existing in result:
                dx = ball[0] - existing[0]
                dy = ball[1] - existing[1]
                if (dx * dx + dy * dy) ** 0.5 < Config.MIN_BALL_DISTANCE:
                    dup = True
                    break
            if not dup:
                result.append(ball)
        return result


# ==================== SendInput 结构定义（模块级，供 FastClicker 使用）====================
class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT)]

class _SENDINPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", _INPUT_UNION),
    ]

# ==================== 快速点击器 ====================
class FastClicker:
    """高速鼠标点击 - 使用 SendInput API，兼容 DirectInput 游戏"""
    
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_ABSOLUTE = 0x8000
    
    _screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    _screen_h = ctypes.windll.user32.GetSystemMetrics(1)
    
    @classmethod
    def _send_input(cls, flags, dx=0, dy=0):
        """发送单个鼠标输入事件"""
        inp = _SENDINPUT()
        inp.type = cls.INPUT_MOUSE
        inp.union.mi.dx = dx
        inp.union.mi.dy = dy
        inp.union.mi.mouseData = 0
        inp.union.mi.dwFlags = flags
        inp.union.mi.time = 0
        inp.union.mi.dwExtraInfo = None
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    
    @classmethod
    def _move_to(cls, screen_x, screen_y):
        """移动鼠标到绝对屏幕坐标（瞬时）"""
        abs_x = int(screen_x * 65535 / cls._screen_w)
        abs_y = int(screen_y * 65535 / cls._screen_h)
        cls._send_input(cls.MOUSEEVENTF_MOVE | cls.MOUSEEVENTF_ABSOLUTE, abs_x, abs_y)
    
    @classmethod
    def _move_to_slow(cls, target_x, target_y):
        """平滑移动鼠标到目标位置（慢速调试用，全部SendInput）"""
        # 使用 win32api 获取鼠标位置（比 ctypes.wintypes.POINT 可靠）
        start_x, start_y = win32api.GetCursorPos()
        print(f"[SLOW]   GetCursorPos=({start_x},{start_y}) target=({target_x},{target_y})", flush=True)

        total_dist = ((target_x - start_x) ** 2 + (target_y - start_y) ** 2) ** 0.5
        print(f"[SLOW]   距离={total_dist:.0f}px  screen={cls._screen_w}x{cls._screen_h}", flush=True)
        if total_dist < 2:
            abs_x = int(target_x * 65535 / cls._screen_w)
            abs_y = int(target_y * 65535 / cls._screen_h)
            print(f"[SLOW]   距离太短，直接 SendInput ABS ({abs_x},{abs_y})", flush=True)
            cls._send_input(cls.MOUSEEVENTF_MOVE | cls.MOUSEEVENTF_ABSOLUTE, abs_x, abs_y)
            return

        steps = Config.SLOW_MOVE_STEPS
        step_time = Config.SLOW_MOVE_DURATION / steps
        print(f"[SLOW]   开始 {steps} 步平滑移动, 每步 {step_time:.4f}s", flush=True)

        for i in range(1, steps + 1):
            t = i / steps
            ease = 1 - (1 - t) ** 3
            cur_x = int(start_x + (target_x - start_x) * ease)
            cur_y = int(start_y + (target_y - start_y) * ease)
            abs_x = int(cur_x * 65535 / cls._screen_w)
            abs_y = int(cur_y * 65535 / cls._screen_h)
            cls._send_input(cls.MOUSEEVENTF_MOVE | cls.MOUSEEVENTF_ABSOLUTE, abs_x, abs_y)
            if i == 1:
                print(f"[SLOW]   第1步 SendInput({abs_x},{abs_y})", flush=True)
            time.sleep(step_time)
        print(f"[SLOW]   平滑移动完成, 最终位置=({cur_x},{cur_y})", flush=True)

    @classmethod
    def _click_slow(cls, screen_x, screen_y):
        """慢速点击（人眼可观察，全部使用SendInput）"""
        print(f"[SLOW] 移动到 ({screen_x}, {screen_y}) 并点击...", flush=True)
        time.sleep(Config.SLOW_DELAY_BEFORE)
        cls._move_to_slow(screen_x, screen_y)
        cls._send_input(cls.MOUSEEVENTF_LEFTDOWN)
        time.sleep(Config.SLOW_CLICK_HOLD)
        cls._send_input(cls.MOUSEEVENTF_LEFTUP)
        time.sleep(Config.SLOW_DELAY_AFTER)
    
    @classmethod
    def click_at(cls, screen_x, screen_y):
        """在屏幕坐标执行一次点击"""
        if Config.SLOW_MODE:
            cls._click_slow(screen_x, screen_y)
        else:
            cls._move_to(screen_x, screen_y)
            time.sleep(Config.FAST_MOVE_SETTLE)
            cls._send_input(cls.MOUSEEVENTF_LEFTDOWN)
            time.sleep(Config.FAST_CLICK_HOLD)
            cls._send_input(cls.MOUSEEVENTF_LEFTUP)
            time.sleep(Config.FAST_CLICK_RELEASE)
    
    @staticmethod
    def click_balls(balls, window_manager):
        for i, (x, y, _) in enumerate(balls):
            sx, sy = window_manager.game_to_screen_coords(x, y)
            FastClicker.click_at(sx, sy)
            if i < len(balls) - 1:
                time.sleep(Config.FAST_BALL_GAP)


# ==================== 主控制器 ====================
class AutoBallClicker:
    def __init__(self):
        self.window_manager = WindowManager()
        self.ball_detector = BallDetector()
        self.running = False
        self.thread = None
        self.stats = {
            'total_clicks': 0,
            'total_detections': 0,
            'balls_per_scan': deque(maxlen=50),
            'fps': deque(maxlen=30),
        }
        self.debug_mode = False
        
    def start(self) -> bool:
        if self.running:
            return False
        
        if not self.window_manager.find_window():
            print("[ERROR] 未找到游戏窗口")
            return False
        
        title = win32gui.GetWindowText(self.window_manager.hwnd)
        ga = self.window_manager.game_area
        print(f"[INFO] 窗口: {title}")
        print(f"[INFO] 游戏区域: ({ga[0]},{ga[1]}) - ({ga[2]},{ga[3]})")
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[INFO] 自动点击已启动")
        return True
    
    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        print(f"[INFO] 已停止 - 总点击: {self.stats['total_clicks']}")
    
    def _run_loop(self):
        while self.running:
            try:
                if not self.window_manager.is_window_valid():
                    print("[WARN] 游戏窗口已关闭")
                    self.running = False
                    break
                
                screenshot = self.window_manager.get_game_screenshot()
                if screenshot is None:
                    time.sleep(0.05)
                    continue

                # 裁剪到检测区域（红框范围），排除四周UI
                h, w = screenshot.shape[:2]
                dx = int(w * Config.DETECT_LEFT)
                dy = int(h * Config.DETECT_TOP)
                det_w = w - dx - int(w * Config.DETECT_RIGHT)
                det_h = h - dy - int(h * Config.DETECT_BOTTOM)
                if det_w > 0 and det_h > 0:
                    detect_img = screenshot[dy:dy+det_h, dx:dx+det_w]
                    balls = self.ball_detector.detect(detect_img)
                    # 球坐标从检测子区域 → 全截图空间
                    balls = [(bx + dx, by + dy, r) for (bx, by, r) in balls]
                else:
                    balls = []
                
                if Config.SLOW_MODE:
                    if balls:
                        print(f"[SLOW] 检测到 {len(balls)} 个小球", flush=True)
                    else:
                        print(f"[SLOW] .", end="", flush=True)  # 心跳点
                
                if self.debug_mode and balls:
                    debug_img = screenshot.copy()
                    for x, y, r in balls:
                        cv2.circle(debug_img, (x, y), r, (0, 255, 0), 2)
                        cv2.circle(debug_img, (x, y), 2, (0, 0, 255), -1)
                    cv2.imshow('Ball Detection', debug_img)
                    cv2.waitKey(1)
                
                if balls:
                    FastClicker.click_balls(balls, self.window_manager)
                    self.stats['total_detections'] += 1
                    self.stats['total_clicks'] += len(balls)
                    self.stats['balls_per_scan'].append(len(balls))
                
                self.stats['fps'].append(1.0 / max(time.time() - time.time() + Config.DETECT_INTERVAL, 0.001))
                time.sleep(Config.DETECT_INTERVAL)
                
            except Exception as e:
                import traceback
                print(f"[ERROR] {e}", flush=True)
                print(traceback.format_exc(), flush=True)
                time.sleep(0.1)


# ==================== 全局热键管理器 ====================
class GlobalHotkeyManager:
    """
    全局热键监听 - 使用 GetAsyncKeyState 轮询方式
    无需管理员权限，不依赖窗口类注册，简单可靠
    """
    
    def __init__(self, on_f6=None, on_f7=None):
        self.on_f6 = on_f6        # F6 回调 (切换启动/停止)
        self.on_f7 = on_f7        # F7 回调 (停止)
        self.running = False
        self.thread = None
        
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        return True
    
    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
    
    def _poll_loop(self):
        """轮询 GetAsyncKeyState 检测按键"""
        was_f6 = False
        was_f7 = False
        while self.running:
            try:
                # GetAsyncKeyState: bit 15 = currently pressed
                f6_now = bool(ctypes.windll.user32.GetAsyncKeyState(win32con.VK_F6) & 0x8000)
                f7_now = bool(ctypes.windll.user32.GetAsyncKeyState(win32con.VK_F7) & 0x8000)
                
                # 检测上升沿（按下瞬间触发一次）
                if f6_now and not was_f6:
                    if self.on_f6:
                        threading.Thread(target=self.on_f6, daemon=True).start()
                
                if f7_now and not was_f7:
                    if self.on_f7:
                        threading.Thread(target=self.on_f7, daemon=True).start()
                
                was_f6 = f6_now
                was_f7 = f7_now
                
            except Exception:
                pass
            
            time.sleep(0.05)  # 50ms 轮询间隔


# ==================== GUI界面 ====================
def create_gui():
    import tkinter as tk
    from tkinter import ttk
    
    root = tk.Tk()
    root.title("Auto Ball Clicker")
    root.geometry("400x480")
    root.resizable(False, False)
    root.configure(bg='#1a1a2e')
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TFrame', background='#1a1a2e')
    style.configure('TLabel', background='#1a1a2e', foreground='#cdd6f4', font=('Microsoft YaHei', 10))
    style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'), foreground='#89b4fa')
    style.configure('Sub.TLabel', font=('Microsoft YaHei', 9), foreground='#6c7086')
    style.configure('TButton', font=('Microsoft YaHei', 11, 'bold'), padding=8)
    style.configure('Green.TButton', foreground='#a6e3a1')
    style.configure('Red.TButton', foreground='#f38ba8')
    
    main = ttk.Frame(root, padding=20)
    main.pack(fill='both', expand=True)
    
    ttk.Label(main, text='Auto Ball Clicker', style='Title.TLabel').pack(pady=(0, 3))
    ttk.Label(main, text='生死狙击2 - 瞄准小球辅助', style='Sub.TLabel').pack(pady=(0, 18))
    
    # 状态
    status_frame = ttk.Frame(main)
    status_frame.pack(fill='x', pady=(0, 12))
    
    status_label = ttk.Label(status_frame, text='状态:', font=('Microsoft YaHei', 11))
    status_label.pack(side='left')
    status_value = ttk.Label(status_frame, text='已停止', font=('Microsoft YaHei', 11, 'bold'), foreground='#f38ba8')
    status_value.pack(side='left', padx=(5, 0))
    
    ttk.Separator(main, orient='horizontal').pack(fill='x', pady=10)
    
    # 统计
    ttk.Label(main, text='实时统计', font=('Microsoft YaHei', 11, 'bold'), foreground='#a6e3a1').pack(anchor='w', pady=(0, 8))
    
    stats_frame = ttk.Frame(main)
    stats_frame.pack(fill='x')
    
    stat_texts = ['总点击:', '扫描次数:', '平均小球/次:', '窗口状态:']
    stat_values = {}
    for i, text in enumerate(stat_texts):
        ttk.Label(stats_frame, text=text).grid(row=i, column=0, sticky='w', pady=2, padx=(0, 10))
        sv = ttk.Label(stats_frame, text='-' if i < 3 else '未检测', foreground='#f5c2e7')
        sv.grid(row=i, column=1, sticky='w', pady=2)
        stat_values[text] = sv
    
    ttk.Separator(main, orient='horizontal').pack(fill='x', pady=10)
    
    # 快捷键说明
    ttk.Label(main, text='快捷键', font=('Microsoft YaHei', 11, 'bold'), foreground='#fab387').pack(anchor='w', pady=(0, 5))
    for h in ['F6 — 启动 / 停止', 'F7 — 停止']:
        ttk.Label(main, text=h, style='Sub.TLabel').pack(anchor='w', pady=1)
    
    ttk.Label(main, text='请先启动游戏并进入小游戏', style='Sub.TLabel', foreground='#f9e2af').pack(anchor='w', pady=(8, 12))
    
    # 按钮
    btn_frame = ttk.Frame(main)
    btn_frame.pack(fill='x')
    
    clicker = AutoBallClicker()
    hotkey_mgr = GlobalHotkeyManager(
        on_f6=lambda: root.after(0, toggle_clicker),
        on_f7=lambda: root.after(0, do_stop)
    )
    
    def toggle_clicker():
        if clicker.running:
            do_stop()
        else:
            do_start()
    
    def do_start():
        if clicker.start():
            status_value.config(text='运行中', foreground='#a6e3a1')
            start_btn.config(text='停止 (F6)')
            update_stats()
    
    def do_stop():
        clicker.stop()
        status_value.config(text='已停止', foreground='#f38ba8')
        start_btn.config(text='启动 (F6)')
    
    def update_stats():
        s = clicker.stats
        stat_values['总点击:'].config(text=str(s['total_clicks']))
        stat_values['扫描次数:'].config(text=str(s['total_detections']))
        avg = 0
        if s['total_detections'] > 0:
            avg = s['total_clicks'] / s['total_detections']
        stat_values['平均小球/次:'].config(text=f"{avg:.1f}")
        
        if clicker.window_manager.hwnd:
            try:
                t = win32gui.GetWindowText(clicker.window_manager.hwnd)[:25]
            except:
                t = "已连接"
            stat_values['窗口状态:'].config(text=t, foreground='#a6e3a1')
        else:
            stat_values['窗口状态:'].config(text='未检测', foreground='#f38ba8')
        
        if clicker.running:
            root.after(300, update_stats)
    
    start_btn = ttk.Button(btn_frame, text='启动 (F6)', command=toggle_clicker)
    start_btn.pack(side='left', padx=(0, 10))
    
    exit_btn = ttk.Button(btn_frame, text='退出', command=lambda: cleanup())
    exit_btn.pack(side='left')
    
    ttk.Label(main, text='v1.0 | WorkBuddy', style='Sub.TLabel').pack(side='bottom', pady=(18, 0))
    
    hotkey_mgr.start()
    
    def cleanup():
        clicker.stop()
        hotkey_mgr.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", cleanup)
    return root


# ==================== 命令行模式 ====================
def run_cli():
    print("=" * 50)
    print("  Auto Ball Clicker v1.0")
    print("  生死狙击2 - 瞄准小球 辅助工具")
    print("=" * 50)
    
    clicker = AutoBallClicker()
    
    if not clicker.start():
        input("按回车退出...")
        sys.exit(1)
    
    print("\n命令: s=停止, q=退出, Enter=统计\n")
    
    try:
        while clicker.running:
            cmd = input("> ").strip().lower()
            if cmd in ('s', 'stop'):
                clicker.stop()
                break
            elif cmd in ('q', 'quit', 'exit'):
                clicker.stop()
                break
            elif cmd == '':
                s = clicker.stats
                avg = s['total_clicks'] / max(s['total_detections'], 1)
                print(f"  总点击:{s['total_clicks']}  扫描:{s['total_detections']}  平均:{avg:.1f}/次")
    except KeyboardInterrupt:
        clicker.stop()


# ==================== 主入口 ====================
if __name__ == '__main__':
    # 慢速调试模式
    if '--slow' in sys.argv:
        Config.SLOW_MODE = True
        Config.DETECT_INTERVAL = 0.5  # 降低扫描频率便于观察
        print("[DEBUG] Slow mode ON - mouse movement will be visible")
    
    if '--cli' in sys.argv or '-c' in sys.argv:
        run_cli()
    else:
        import tkinter as tk
        try:
            root = create_gui()
            root.mainloop()
        except Exception as e:
            print(f"GUI启动失败: {e}")
            run_cli()
