import os
import sys
import threading
import shutil
from math import cos, sin
from tkinter import filedialog, messagebox
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from PIL import Image, ImageTk

# 检查TkinterDnD是否可用
TKDND_AVAILABLE = True
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TKDND_AVAILABLE = False
    print("TkinterDnD模块未安装，拖放功能将不可用")
    print("可使用 pip install tkinterdnd2 安装")

class ImageResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片批量缩放工具")
        self.root.geometry("1000x930")  # 稍微提高窗口高度
        self.root.minsize(800, 750)  # 相应提高最小高度
        self.root.configure(bg="#2A2A2A")  # 更深的背景色
        
        print("初始化ImageResizerApp...")
        
        # 创建自定义样式
        try:
            print("创建自定义样式...")
            self.create_custom_style()
            print("自定义样式创建完成")
        except Exception as e:
            print(f"创建自定义样式时出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 初始化状态变量
        self.selected_files = []
        self.current_preview_index = -1
        self.current_preview_file = None
        self.processed_images = []
        self.output_dir = None
        
        # 创建主界面
        try:
            print("创建主界面...")
            self.create_ui()
            print("主界面创建完成")
        except Exception as e:
            print(f"创建主界面时出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 设置拖放支持
        if TKDND_AVAILABLE:
            try:
                print("设置拖放支持...")
                self.setup_drag_drop()
                print("拖放支持设置完成")
            except Exception as e:
                print(f"设置拖放支持时出错: {e}")
                import traceback
                traceback.print_exc()
            
        # 窗口大小变化时更新预览图
        self.root.bind("<Configure>", self.on_window_resize)
        print("应用初始化完成")
        
    def create_custom_style(self):
        # 创建自定义样式
        self.button_style = {
            "bg": "#3498db",
            "fg": "#ffffff",
            "activebackground": "#2980b9",
            "activeforeground": "#ffffff",
            "font": ("Microsoft YaHei", 10),
            "relief": tk.FLAT,
            "borderwidth": 0,
            "padx": 15,
            "pady": 8,
        }
        
        self.danger_button_style = self.button_style.copy()
        self.danger_button_style.update({
            "bg": "#e74c3c",
            "activebackground": "#c0392b",
        })
        
        self.success_button_style = self.button_style.copy()
        self.success_button_style.update({
            "bg": "#2ecc71",
            "activebackground": "#27ae60",
        })
        
        self.warning_button_style = self.button_style.copy()
        self.warning_button_style.update({
            "bg": "#f39c12",
            "activebackground": "#d35400",
        })
        
        # 创建圆角按钮类
        class RoundedButton(tk.Canvas):
            def __init__(self, parent, text, command=None, radius=10, **kwargs):
                # 提取自定义属性
                bg_color = kwargs.pop("bg", "#3498db")
                fg_color = kwargs.pop("fg", "#ffffff")
                active_bg = kwargs.pop("activebackground", "#2980b9")
                self.font = kwargs.pop("font", ("Microsoft YaHei", 10)) if "font" in kwargs else ("Microsoft YaHei", 10)
                self.padx = kwargs.pop("padx", 15) if "padx" in kwargs else 15
                self.pady = kwargs.pop("pady", 8) if "pady" in kwargs else 8
                
                # 获取父组件的背景色，用于四角背景
                parent_bg = parent.cget("bg") if parent else "#2A2A2A"
                
                # 移除Canvas不支持的参数
                for param in ["activeforeground", "relief", "borderwidth"]:
                    if param in kwargs:
                        kwargs.pop(param)
                
                # 初始化Canvas，设置背景色与父组件一致
                kwargs["bg"] = parent_bg
                super().__init__(parent, highlightthickness=0, **kwargs)
                
                # 初始化属性
                self.bg = bg_color
                self.fg = fg_color
                self.activebackground = active_bg
                self.text = text
                self.command = command
                self.radius = radius
                self.state = tk.NORMAL
                self.current_bg = self.bg
                self.parent_bg = parent_bg
                
                # 设置默认尺寸
                if not "width" in kwargs and not "height" in kwargs:
                    width = 120
                    height = 30
                    self.configure(width=width, height=height)
                
                # 绘制按钮
                self.create_ui()
                
                # 绑定事件
                self.bind("<ButtonPress-1>", self.on_press)
                self.bind("<ButtonRelease-1>", self.on_release)
                self.bind("<Enter>", self.on_enter)
                self.bind("<Leave>", self.on_leave)
            
            def create_ui(self):
                # 计算尺寸
                width = self.winfo_reqwidth()
                height = self.winfo_reqheight()
                
                # 清空画布
                self.delete("all")
                
                # 绘制背景
                if self.state == tk.DISABLED:
                    bg_color = "#7f8c8d"  # 禁用状态的颜色
                elif self.state == "active":
                    bg_color = self.activebackground
                else:
                    bg_color = self.current_bg if hasattr(self, 'current_bg') and self.current_bg else self.bg
                
                # 创建圆角矩形，并标记为"bg_rect"
                self.rounded_rect = self.create_rounded_rectangle(0, 0, width, height, self.radius, fill=bg_color, tags="bg_rect")
                
                # 创建文本，并确保在矩形上方
                text_color = "#ffffff" if self.state != tk.DISABLED else "#cccccc"
                self.text_item = self.create_text(width//2, height//2, text=self.text, fill=text_color, font=self.font, tags="btn_text")
                
                # 确保文本在圆角矩形上层
                self.tag_raise("btn_text")
            
            def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
                """使用直接绘制的方式创建圆角矩形，减少锯齿"""
                # 提取参数
                fill = kwargs.pop('fill', '')
                outline = kwargs.pop('outline', '')
                tags = kwargs.pop('tags', '')
                
                # 清除之前的元素
                if tags:
                    self.delete(tags)
                
                # 创建主体矩形 (中间区域)
                rect_id = self.create_rectangle(x1+radius, y1, x2-radius, y2, 
                                              fill=fill, outline="", tags=tags)
                
                # 创建左右矩形 (左右两侧)
                left_rect = self.create_rectangle(x1, y1+radius, x1+radius, y2-radius, 
                                                fill=fill, outline="", tags=tags)
                right_rect = self.create_rectangle(x2-radius, y1+radius, x2, y2-radius, 
                                                 fill=fill, outline="", tags=tags)
                
                # 创建四个圆角
                # 左上角
                nw_arc = self.create_arc(x1, y1, x1+2*radius, y1+2*radius, 
                                       start=90, extent=90, style=tk.PIESLICE,
                                       fill=fill, outline="", tags=tags)
                # 右上角
                ne_arc = self.create_arc(x2-2*radius, y1, x2, y1+2*radius, 
                                       start=0, extent=90, style=tk.PIESLICE,
                                       fill=fill, outline="", tags=tags)
                # 左下角
                sw_arc = self.create_arc(x1, y2-2*radius, x1+2*radius, y2, 
                                       start=180, extent=90, style=tk.PIESLICE,
                                       fill=fill, outline="", tags=tags)
                # 右下角
                se_arc = self.create_arc(x2-2*radius, y2-2*radius, x2, y2, 
                                       start=270, extent=90, style=tk.PIESLICE,
                                       fill=fill, outline="", tags=tags)
                
                # 如果需要边框
                if outline:
                    # 绘制边框线段
                    top_line = self.create_line(x1+radius, y1, x2-radius, y1, 
                                              fill=outline, tags=tags)
                    bottom_line = self.create_line(x1+radius, y2, x2-radius, y2, 
                                                 fill=outline, tags=tags)
                    left_line = self.create_line(x1, y1+radius, x1, y2-radius, 
                                               fill=outline, tags=tags)
                    right_line = self.create_line(x2, y1+radius, x2, y2-radius, 
                                                fill=outline, tags=tags)
                    
                    # 绘制四个圆弧的边框
                    nw_arc_outline = self.create_arc(x1, y1, x1+2*radius, y1+2*radius, 
                                                   start=90, extent=90, style=tk.ARC, 
                                                   outline=outline, tags=tags)
                    ne_arc_outline = self.create_arc(x2-2*radius, y1, x2, y1+2*radius, 
                                                   start=0, extent=90, style=tk.ARC, 
                                                   outline=outline, tags=tags)
                    sw_arc_outline = self.create_arc(x1, y2-2*radius, x1+2*radius, y2, 
                                                   start=180, extent=90, style=tk.ARC, 
                                                   outline=outline, tags=tags)
                    se_arc_outline = self.create_arc(x2-2*radius, y2-2*radius, x2, y2, 
                                                   start=270, extent=90, style=tk.ARC, 
                                                   outline=outline, tags=tags)
                
                # 创建一个透明区域用于事件捕获
                return self.create_rectangle(x1, y1, x2, y2, fill="", outline="", tags=tags)
            
            def configure(self, **kwargs):
                # 处理特殊属性
                if "state" in kwargs:
                    self.state = kwargs.pop("state")
                if "text" in kwargs:
                    self.text = kwargs.pop("text")
                if "command" in kwargs:
                    self.command = kwargs.pop("command")
                if "bg" in kwargs:
                    self.bg = kwargs.pop("bg")
                
                # 让父类处理剩余属性
                super().configure(**kwargs)
                
                # 重绘UI
                self.after(10, self.create_ui)
            
            def config(self, **kwargs):
                return self.configure(**kwargs)
            
            def on_press(self, event):
                if self.state != tk.DISABLED:
                    self.state = "active"
                    self.create_ui()
            
            def on_release(self, event):
                if self.state != tk.DISABLED and self.command:
                    self.state = tk.NORMAL
                    self.create_ui()
                    self.command()
            
            def on_enter(self, event):
                if self.state != tk.DISABLED:
                    # 使用当前的activebackground颜色重新绘制按钮
                    self.current_bg = self.activebackground
                    self.create_ui()
            
            def on_leave(self, event):
                if self.state != tk.DISABLED:
                    # 恢复默认的背景颜色并重新绘制按钮
                    self.current_bg = self.bg
                    self.create_ui()
        
        # 保存按钮类供后续使用
        self.RoundedButton = RoundedButton
        
        # 不再添加方法到Canvas类，因为已经在main中添加了
        # tk.Canvas.create_rounded_rectangle = self.create_rounded_rectangle
        # print("已添加create_rounded_rectangle方法到Canvas类")
        
    def create_ui(self):
        # 顶部区域 - 拖放区域
        top_frame = tk.Frame(self.root, bg="#2A2A2A", padx=10, pady=10)
        top_frame.pack(fill=tk.X)
        
        # 拖放区域
        drop_area_frame = tk.Frame(top_frame, bg="#2A2A2A", height=120)  # 增加高度
        drop_area_frame.pack(fill=tk.X, padx=10, pady=10)
        drop_area_frame.pack_propagate(False)  # 固定高度
        
        # 文件选择区域
        self.drop_frame = tk.Frame(drop_area_frame, bg="#3c3c3c", 
                                  bd=0, relief=tk.FLAT)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # 添加圆角边框
        def create_rounded_frame(event):
            canvas = event.widget
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            canvas.delete("all")  # 删除所有内容
            
            # 绘制圆角矩形背景
            canvas.create_rounded_rectangle(2, 2, width-2, height-2, 10, 
                                          outline="#5c5c5c", width=2, 
                                          fill="#3c3c3c", tags="roundedrect")
            
            # 绘制文本
            canvas.create_text(width//2, height//2-10, text="拖放图片到此处", 
                             font=("Microsoft YaHei", 14), fill="#ffffff",
                             tags="text")
            canvas.create_text(width//2, height//2+15, text="或点击选择文件夹", 
                             font=("Microsoft YaHei", 12), fill="#cccccc",
                             tags="text")
        
        # 创建canvas作为圆角容器
        drop_canvas = tk.Canvas(self.drop_frame, bg="#3c3c3c", bd=0, highlightthickness=0)
        drop_canvas.pack(fill=tk.BOTH, expand=True)
        drop_canvas.bind("<Configure>", create_rounded_frame)
        drop_canvas.bind("<Button-1>", lambda e: self.browse_folder_direct())
        
        self.drop_label = drop_canvas
        
        # 中间区域 - 缩放控制和图片显示
        middle_frame = tk.Frame(self.root, bg="#2A2A2A", padx=10, pady=5)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=(5, 0))  # 顶部留少量间距，底部无间距
        
        # 缩放控制区域 - 包含两种缩放模式：系数和目标尺寸
        scale_control_frame = tk.Frame(middle_frame, bg="#2A2A2A")
        scale_control_frame.pack(fill=tk.X, pady=5)
        
        # 创建选项卡，分为系数缩放和目标尺寸缩放
        tab_frame = tk.Frame(scale_control_frame, bg="#2A2A2A")
        tab_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 定义当前选中的选项卡
        self.current_tab = tk.StringVar(value="scale")  # 默认选中系数缩放
        
        # 创建选项卡样式
        tab_style = {
            "active": {"bg": "#3c3c3c", "fg": "#ffffff", "relief": tk.SUNKEN, "borderwidth": 1},
            "inactive": {"bg": "#2A2A2A", "fg": "#aaaaaa", "relief": tk.FLAT, "borderwidth": 1}
        }
        
        # 系数缩放选项卡
        self.scale_tab = tk.Label(tab_frame, text="按比例缩放", font=("Microsoft YaHei", 11),
                                padx=15, pady=5, cursor="hand2", **tab_style["active"])
        self.scale_tab.pack(side=tk.LEFT, padx=(0, 2))
        
        # 目标尺寸选项卡
        self.target_size_tab = tk.Label(tab_frame, text="按目标尺寸", font=("Microsoft YaHei", 11),
                                      padx=15, pady=5, cursor="hand2", **tab_style["inactive"])
        self.target_size_tab.pack(side=tk.LEFT)
        
        # 绑定点击事件
        self.scale_tab.bind("<Button-1>", lambda e: self.switch_tab("scale"))
        self.target_size_tab.bind("<Button-1>", lambda e: self.switch_tab("target_size"))
        
        # 创建缩放系数控制框架
        self.scale_frame = tk.Frame(scale_control_frame, bg="#2A2A2A")
        self.scale_frame.pack(fill=tk.X, pady=5)
        
        scale_label = tk.Label(self.scale_frame, text="缩放系数:", 
                              font=("Microsoft YaHei", 12), 
                              bg="#2A2A2A", fg="#ffffff")
        scale_label.pack(side=tk.LEFT, padx=5)
        
        # 自定义滑块样式
        slider_style = ttk.Style()
        slider_style.configure("Modern.Horizontal.TScale", 
                             background="#2A2A2A",
                             troughcolor="#444444")
        
        self.scale_slider = ttk.Scale(self.scale_frame, from_=0.1, to=3.0, 
                                    orient=tk.HORIZONTAL,
                                    length=300, value=1.0,
                                    command=self.update_scale_value,
                                    style="Modern.Horizontal.TScale")
        self.scale_slider.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 创建圆角框架显示缩放值
        scale_value_frame = tk.Frame(self.scale_frame, bg="#3c3c3c", bd=0, padx=10, pady=5)
        scale_value_frame.pack(side=tk.LEFT, padx=5)
        
        self.scale_value_label = tk.Label(scale_value_frame, text="1.0", 
                                        font=("Microsoft YaHei", 12, "bold"), 
                                        bg="#3c3c3c", fg="#ffffff",
                                        width=3)
        self.scale_value_label.pack()
        
        # 创建目标尺寸控制框架（初始隐藏）
        self.target_size_frame = tk.Frame(scale_control_frame, bg="#2A2A2A")
        # 不立即pack，根据选项卡切换显示
        
        # 添加一系列预设的目标尺寸按钮
        preset_sizes = ["4096x4096", "2048x2048", "1024x1024", "512x512", "256x256", "128x128", "64x64", "32x32"]
        self.target_size_var = tk.StringVar(value="")
        
        size_label = tk.Label(self.target_size_frame, text="目标尺寸:", 
                            font=("Microsoft YaHei", 12), 
                            bg="#2A2A2A", fg="#ffffff")
        size_label.pack(side=tk.LEFT, padx=5)
        
        # 创建按钮容器
        size_buttons_frame = tk.Frame(self.target_size_frame, bg="#2A2A2A")
        size_buttons_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 添加尺寸按钮
        for i, size in enumerate(preset_sizes):
            btn = self.RoundedButton(size_buttons_frame, text=size, 
                                   command=lambda s=size: self.set_target_size(s),
                                   bg="#3c3c3c", fg="#ffffff",
                                   activebackground="#4e4e4e",
                                   width=90, height=30,
                                   radius=8, font=("Microsoft YaHei", 9))
            row, col = divmod(i, 4)  # 每行4个按钮
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            
            # 配置大小调整行为
            size_buttons_frame.grid_columnconfigure(col, weight=1)
        
        # 显示当前选择的尺寸
        self.selected_size_label = tk.Label(self.target_size_frame, text="当前选择: 无", 
                                         font=("Microsoft YaHei", 11), 
                                         bg="#2A2A2A", fg="#ffffff")
        self.selected_size_label.pack(side=tk.LEFT, padx=10)
        
        # 图片显示区域 - 左右分栏
        content_frame = tk.Frame(middle_frame, bg="#2A2A2A")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))  # 顶部留少量间距，底部无间距
        
        # 设置左右框架宽度相等，并确保占用完全相同的空间
        content_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        content_frame.grid_columnconfigure(1, weight=1, uniform="group1")
        
        # 左侧 - 原始图片区域
        left_frame = tk.Frame(content_frame, bg="#2A2A2A", height=500)  # 降低高度
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.pack_propagate(False)  # 防止子组件改变高度
        
        # 左侧标题
        tk.Label(left_frame, text="原始图片", 
               font=("Microsoft YaHei", 12), 
               bg="#2A2A2A", fg="#ffffff").pack(pady=(0, 5), anchor=tk.W)
        
        # 左侧缩略图容器框架
        thumb_container = tk.Frame(left_frame, bg="#2D2D30", bd=0, padx=5, pady=5)  # 减小padding
        thumb_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条和Canvas
        thumb_canvas = tk.Canvas(thumb_container, bg="#2D2D30", bd=0, 
                               highlightthickness=0, height=370)  # 减小高度
        
        # 自定义滚动条样式
        scrollbar = ttk.Scrollbar(thumb_container, orient=tk.VERTICAL, 
                                command=thumb_canvas.yview)
        
        # 配置Canvas
        thumb_canvas.configure(yscrollcommand=scrollbar.set)
        thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建缩略图容器框架 - 使用Frame
        self.thumbnail_frame = tk.Frame(thumb_canvas, bg="#2D2D30")
        # 网格布局的容器要设置好宽度
        self.thumbnail_frame.columnconfigure(0, weight=1)
        self.thumbnail_frame.columnconfigure(1, weight=1)
        self.thumbnail_frame.columnconfigure(2, weight=1)
        self.thumbnail_frame.columnconfigure(3, weight=1)
        
        thumb_canvas.create_window((0, 0), window=self.thumbnail_frame, 
                                 anchor=tk.NW, tags="thumbnail_frame", width=thumb_canvas.winfo_reqwidth())
        
        # 保存Canvas引用和行信息
        self.thumbnail_frame._parent_canvas = thumb_canvas
        self.thumbnail_row = 0
        self.thumbnail_col = 0
        self.max_cols = 4  # 每行最多4个缩略图
        
        # 配置Canvas滚动区域
        def configure_thumb_frame(event):
            # 更新滚动区域
            thumb_canvas.configure(scrollregion=thumb_canvas.bbox("all"))
            # 设置画布宽度等于缩略图框架宽度，确保填满可用空间
            canvas_width = event.width
            thumb_canvas.itemconfig("thumbnail_frame", width=canvas_width)
        
        self.thumbnail_frame.bind("<Configure>", configure_thumb_frame)
        thumb_canvas.bind("<Configure>", lambda e: configure_thumb_frame(e))
        
        # 添加鼠标滚轮事件处理
        def on_mousewheel(event):
            # Windows和Linux系统的滚轮事件不同
            if hasattr(event, 'num') and event.num == 4 or hasattr(event, 'delta') and event.delta > 0:  # 向上滚动
                thumb_canvas.yview_scroll(-1, "units")
            elif hasattr(event, 'num') and event.num == 5 or hasattr(event, 'delta') and event.delta < 0:  # 向下滚动
                thumb_canvas.yview_scroll(1, "units")
        
        # 触摸板滚动事件处理 (Windows)
        def on_touchpad_scroll(event):
            # event.delta用于Windows触摸板的垂直滚动手势
            if hasattr(event, 'delta'):
                # 计算滚动单位，delta可能是大量像素，需要缩放
                units = abs(event.delta) // 20  # 每20个像素滚动一个单位
                if units < 1:
                    units = 1
                if event.delta > 0:
                    thumb_canvas.yview_scroll(-int(units), "units")
                else:
                    thumb_canvas.yview_scroll(int(units), "units")
                
        # 绑定滚轮事件到Canvas和缩略图框架
        # Windows系统
        thumb_canvas.bind("<MouseWheel>", on_mousewheel)
        # 触摸板事件 (Windows)
        thumb_canvas.bind("<Motion>", lambda e: None)  # 激活触摸板跟踪
        thumb_canvas.bind("<B1-Motion>", on_touchpad_scroll)  # 触摸板单指滑动
        thumb_canvas.bind("<B2-Motion>", on_touchpad_scroll)  # 触摸板双指滑动
        # Linux系统
        thumb_canvas.bind("<Button-4>", on_mousewheel)
        thumb_canvas.bind("<Button-5>", on_mousewheel)
        
        # 确保缩略图内部的所有元素也能响应滚轮事件
        def bind_mousewheel_to_children(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)
            widget.bind("<Button-5>", on_mousewheel)
            # 添加触摸板事件支持
            widget.bind("<Motion>", lambda e: None)  # 激活触摸板跟踪
            widget.bind("<B1-Motion>", on_touchpad_scroll)
            widget.bind("<B2-Motion>", on_touchpad_scroll)
            for child in widget.winfo_children():
                bind_mousewheel_to_children(child)
                
        # 初始调用以绑定现有元素
        bind_mousewheel_to_children(self.thumbnail_frame)
        
        # 添加清空按钮到左侧框架底部
        clear_frame = tk.Frame(left_frame, bg="#2A2A2A", pady=5)
        clear_frame.pack(fill=tk.X)
        
        # 清空按钮
        clear_btn = self.RoundedButton(clear_frame, text="清空列表", 
                                      command=self.clear_all_images,
                                      bg="#e74c3c", 
                                      activebackground="#c0392b",
                                      fg="#ffffff",
                                      font=("Microsoft YaHei", 10),
                                      radius=8)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 单独设置clear_frame的背景色
        clear_frame.configure(bg="#2A2A2A")
        
        # 右侧 - 预览区域
        right_frame = tk.Frame(content_frame, bg="#2A2A2A", height=500)  # 降低高度
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.pack_propagate(False)  # 防止子组件改变高度
        
        # 预览标题
        tk.Label(right_frame, text="预览效果", 
               font=("Microsoft YaHei", 12), 
               bg="#2A2A2A", fg="#ffffff").pack(pady=(0, 5), anchor=tk.W)
        
        # 预览视图容器
        self.preview_container = tk.Frame(right_frame, bg="#2D2D30", 
                                        bd=0, padx=10, pady=5)  # 减小padding
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        # 预览图像视图区域
        self.preview_viewport = tk.Frame(self.preview_container, bg="#1E1E1E", height=350)  # 从380减少到350，为信息区域腾出空间
        self.preview_viewport.pack(fill=tk.BOTH, expand=True, pady=3)  # 减小padding
        self.preview_viewport.pack_propagate(False)  # 防止子组件改变高度
        
        # 空白占位图像
        self.preview_view = tk.Label(self.preview_viewport, bg="#1E1E1E")
        self.preview_view.pack(expand=True, fill=tk.BOTH)
        
        # 预览信息区域 - 增加高度以容纳更多信息
        info_bg = "#363636"
        self.preview_info = tk.Label(self.preview_container, 
                                   text="", 
                                   bg=info_bg, fg="#ffffff",
                                   justify=tk.LEFT, anchor=tk.W,
                                   font=("Microsoft YaHei", 10),
                                   padx=10, pady=8,  # 增加内边距
                                   height=5)  # 增加显示高度，从3行增加到5行，确保显示完整信息
        self.preview_info.pack(fill=tk.X, pady=5)  # 增加外边距
        
        # 添加导航按钮
        nav_frame = tk.Frame(self.preview_container, bg="#2D2D30")
        nav_frame.pack(fill=tk.X, pady=3)  # 减小外边距
        
        # 上一张按钮
        self.prev_btn = self.RoundedButton(nav_frame, text="上一张", 
                                         command=lambda: self.navigate_preview(-1),
                                         bg="#3498db", fg="#ffffff",
                                         activebackground="#2980b9",
                                         width=80, height=30,
                                         radius=8, font=("Microsoft YaHei", 10))
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        self.prev_btn.configure(state=tk.DISABLED)  # 初始禁用
        
        # 图片计数
        self.preview_counter = tk.Label(nav_frame, text="0/0", 
                                      bg="#2D2D30", fg="#ffffff",
                                      font=("Microsoft YaHei", 10))
        self.preview_counter.pack(side=tk.LEFT, expand=True)
        
        # 下一张按钮
        self.next_btn = self.RoundedButton(nav_frame, text="下一张", 
                                         command=lambda: self.navigate_preview(1),
                                         bg="#3498db", fg="#ffffff",
                                         activebackground="#2980b9",
                                         width=80, height=30,
                                         radius=8, font=("Microsoft YaHei", 10))
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        self.next_btn.configure(state=tk.DISABLED)  # 初始禁用
        
        # 单独设置nav_frame的背景色
        nav_frame.configure(bg="#2D2D30")
        
        # 底部 - 转换按钮，调整padding使按钮向上移动
        bottom_frame = tk.Frame(self.root, bg="#2A2A2A", padx=10, pady=5)  # 上部间距更小
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 15))  # 底部保持原有空间，上部无间距
        
        # 转换按钮容器
        button_container = tk.Frame(bottom_frame, bg="#2A2A2A", padx=10, pady=0)
        button_container.pack(side=tk.TOP)
        
        # 开始转换按钮 - 居中放置
        start_btn = self.RoundedButton(button_container, text="开始转换(替换原文件)", 
                                     command=self.start_processing_with_dialog,
                                     bg="#4CAF50",  # 使用更鲜明的绿色
                                     fg="#ffffff",
                                     activebackground="#388E3C",
                                     font=("Microsoft YaHei", 16, "bold"),  # 更大的字体
                                     padx=40, pady=15,  # 增加内边距
                                     width=280, height=60,  # 显式设置更大的尺寸，加宽按钮
                                     radius=20)  # 更大的圆角
        start_btn.pack(side=tk.TOP, padx=5, pady=0)  # 进一步减少外边距
        
    def setup_drag_drop(self):
        if not TKDND_AVAILABLE:
            return
        
        # 配置拖放区域
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop)
        
        # 鼠标移入移出事件绑定
        self.drop_frame.bind('<Enter>', self.on_enter_drop_area)
        self.drop_frame.bind('<Leave>', self.on_leave_drop_area)
    
    def on_enter_drop_area(self, event):
        """鼠标进入拖放区时改变视觉效果"""
        # 重绘圆角矩形，使用高亮颜色
        canvas = self.drop_label
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        canvas.delete("all")
        # 绘制高亮的圆角矩形
        canvas.create_rounded_rectangle(2, 2, width-2, height-2, 10, 
                                      outline="#5f9ea0", width=2,  # 高亮边框
                                      fill="#4a4a4a", tags="roundedrect")  # 稍亮的背景
        
        # 重绘文字
        canvas.create_text(width//2, height//2-10, text="拖放图片", 
                     font=("Microsoft YaHei", 11), fill="#ffffff", tags="text")
        canvas.create_text(width//2, height//2+10, text="或点击选择文件夹", 
                     font=("Microsoft YaHei", 9), fill="#cccccc", tags="text")
    
    def on_leave_drop_area(self, event):
        """鼠标离开拖放区时恢复视觉效果"""
        # 恢复原来的样式
        canvas = self.drop_label
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        canvas.delete("all")
        # 绘制普通的圆角矩形
        canvas.create_rounded_rectangle(2, 2, width-2, height-2, 10, 
                                      outline="#5c5c5c", width=2, 
                                      fill="#3c3c3c", tags="roundedrect")
        
        # 重绘文字
        canvas.create_text(width//2, height//2-10, text="拖放图片", 
                     font=("Microsoft YaHei", 11), fill="#ffffff", tags="text")
        canvas.create_text(width//2, height//2+10, text="或点击选择文件夹", 
                     font=("Microsoft YaHei", 9), fill="#cccccc", tags="text")
    
    def drop(self, event):
        """处理拖放事件 - 添加动画效果"""
        # 添加闪烁效果表示接收到文件
        canvas = self.drop_label
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        print(f"收到拖入文件: {event.data}")
        
        def flash(count=0):
            if count >= 6:  # 闪烁3次
                self.on_leave_drop_area(None)  # 恢复正常状态
                # 处理文件
                try:
                    files = self.parse_drop_data(event.data)
                    print(f"解析后的文件列表: {files}")
                    self.handle_selected_files(files)
                except Exception as e:
                    print(f"处理拖放文件时出错: {e}")
                    import traceback
                    traceback.print_exc()
                return
            
            if count % 2 == 0:
                # 亮色
                canvas.delete("all")
                canvas.create_rounded_rectangle(2, 2, width-2, height-2, 10, 
                                              outline="#3498db", width=2, 
                                              fill="#4a6984", tags="roundedrect")
                # 重绘文字
                canvas.create_text(width//2, height//2-10, text="接收文件中...", 
                                 font=("Microsoft YaHei", 11), fill="#ffffff", tags="text")
            else:
                # 暗色
                canvas.delete("all")
                canvas.create_rounded_rectangle(2, 2, width-2, height-2, 10, 
                                              outline="#5c5c5c", width=2, 
                                              fill="#3c3c3c", tags="roundedrect")
                # 重绘文字
                canvas.create_text(width//2, height//2-10, text="接收文件中...", 
                                 font=("Microsoft YaHei", 11), fill="#ffffff", tags="text")
            
            self.root.after(100, lambda: flash(count + 1))
        
        flash()
    
    def parse_drop_data(self, data):
        """解析拖放数据，支持Windows和Linux不同格式"""
        files = []
        # Windows格式: {C:/path/to/file.jpg} {C:/path/to/another.jpg}
        if '{' in data:
            file_paths = data.split('} {')
            for path in file_paths:
                path = path.replace('{', '').replace('}', '')
                if path and os.path.exists(path):
                    files.append(path)
        # Linux格式: file:///path/to/file.jpg file:///path/to/another.jpg
        elif 'file:' in data:
            file_paths = data.split()
            for path in file_paths:
                if path.startswith('file:///'):
                    path = path[8:]  # 去掉 'file:///'
                    if os.path.exists(path):
                        files.append(path)
        # 简单路径
        elif os.path.exists(data):
            files.append(data)
        # 空格分隔的多个路径
        else:
            for path in data.split():
                if os.path.exists(path):
                    files.append(path)
        
        return files
    
    def browse_files(self):
        """通过文件对话框选择图片"""
        files = filedialog.askopenfilenames(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            self.handle_selected_files(files)
    
    def handle_selected_files(self, files):
        """验证和处理选择的文件"""
        # 仅保留图像文件
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        
        valid_files = []
        for file in files:
            # 检查文件是否存在
            if not os.path.exists(file):
                print(f"文件不存在: {file}")
                continue
                
            # 检查扩展名
            ext = os.path.splitext(file)[1].lower()
            if ext not in valid_extensions:
                print(f"不支持的文件格式: {file}")
                continue
                
            # 检查是否已在列表中
            if file in self.selected_files:
                print(f"文件已在列表中: {file}")
                continue
                
            valid_files.append(file)
        
        # 添加到列表
        if valid_files:
            self.selected_files.extend(valid_files)
            # 更新界面
            for file in valid_files:
                try:
                    # 添加缩略图到左侧区域
                    self.add_thumbnail(file)
                    print(f"添加缩略图: {file}")
                except Exception as e:
                    print(f"添加缩略图时出错: {file}, 错误: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 默认选中第一个文件进行预览
            if len(self.selected_files) == len(valid_files):  # 如果之前没有文件
                try:
                    print(f"设置预览文件: {self.selected_files[0]}")
                    self.set_preview_file(self.selected_files[0])
                except Exception as e:
                    print(f"设置预览文件时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # 无需更新转换按钮状态，因为还未定义
    
    def add_thumbnail(self, file_path):
        """添加文件缩略图到左侧缩略图区域 - 简化版只显示图片，使用网格布局"""
        try:
            # 创建缩略图容器 - 使用更简洁的设计
            thumb_container = tk.Frame(self.thumbnail_frame, bg="#2D2D30", padx=2, pady=2)
            
            # 放置到当前行列位置
            thumb_container.grid(row=self.thumbnail_row, column=self.thumbnail_col, 
                               padx=3, pady=3, sticky="nsew")
            
            # 更新列计数，每行达到最大列数后换行
            self.thumbnail_col += 1
            if self.thumbnail_col >= self.max_cols:
                self.thumbnail_col = 0
                self.thumbnail_row += 1
            
            # 加载图像并创建缩略图
            original_img = Image.open(file_path)
            thumb_size = (80, 80)  # 稍微调大缩略图尺寸
            thumb_img = original_img.copy()
            thumb_img.thumbnail(thumb_size)
            
            # 将PIL图像转换为Tkinter可用的格式
            tk_img = ImageTk.PhotoImage(thumb_img)
            
            # 保存图像引用，防止垃圾回收
            thumb_container.tk_img = tk_img
            
            # 创建图像标签
            img_label = tk.Label(thumb_container, image=tk_img, bg="#2D2D30", bd=0)
            img_label.pack(padx=2, pady=(2, 1))
            
            # 获取并显示文件信息（文件大小）
            try:
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                size_str = self.format_size(file_size)
                
                # 创建一个专门的框架用于显示文件大小，确保有足够的宽度
                size_frame = tk.Frame(thumb_container, bg="#2D2D30")
                size_frame.pack(fill=tk.X, expand=True, pady=(0, 2))
                
                # 使用带有固定宽度的标签显示文件大小
                size_label = tk.Label(size_frame, text=size_str, bg="#2D2D30", fg="#cccccc", 
                                     font=("Microsoft YaHei", 8), width=10)
                size_label.pack(fill=tk.X)
            except Exception as e:
                print(f"获取文件大小失败: {e}")
            
            # 为缩略图添加边框和悬停效果
            thumb_container.config(highlightbackground="#444444", highlightthickness=1)
            
            # 绑定点击事件 - 选择图像预览
            img_label.bind("<Button-1>", lambda e, path=file_path: self.set_preview_file(path))
            thumb_container.bind("<Button-1>", lambda e, path=file_path: self.set_preview_file(path))
            
            # 悬停效果
            def on_enter(e):
                thumb_container.config(highlightbackground="#3498db", highlightthickness=2)
                
            def on_leave(e):
                thumb_container.config(highlightbackground="#444444", highlightthickness=1)
                
            thumb_container.bind("<Enter>", on_enter)
            thumb_container.bind("<Leave>", on_leave)
            img_label.bind("<Enter>", on_enter)
            img_label.bind("<Leave>", on_leave)
            
            # 右键菜单删除功能
            def show_context_menu(event):
                context_menu = tk.Menu(self.root, tearoff=0, bg="#2D2D30", fg="white", 
                                     activebackground="#3498db", activeforeground="white")
                context_menu.add_command(label="删除", 
                                       command=lambda: self.remove_file(file_path, thumb_container))
                context_menu.tk_popup(event.x_root, event.y_root)
                
            thumb_container.bind("<Button-3>", show_context_menu)
            img_label.bind("<Button-3>", show_context_menu)
            
            # 为新添加的缩略图绑定鼠标滚轮事件
            def on_thumb_mousewheel(event):
                # 将滚轮事件传递给画布
                if hasattr(self.thumbnail_frame, '_parent_canvas'):
                    canvas = self.thumbnail_frame._parent_canvas
                    if hasattr(event, 'num') and event.num == 4 or hasattr(event, 'delta') and event.delta > 0:  # 向上滚动
                        canvas.yview_scroll(-1, "units")
                    elif hasattr(event, 'num') and event.num == 5 or hasattr(event, 'delta') and event.delta < 0:  # 向下滚动
                        canvas.yview_scroll(1, "units")
            
            # 触摸板滚动事件处理 (Windows)
            def on_thumb_touchpad_scroll(event):
                if hasattr(self.thumbnail_frame, '_parent_canvas'):
                    canvas = self.thumbnail_frame._parent_canvas
                    # event.delta用于Windows触摸板的垂直滚动手势
                    if hasattr(event, 'delta'):
                        # 计算滚动单位，delta可能是大量像素，需要缩放
                        units = abs(event.delta) // 20  # 每20个像素滚动一个单位
                        if units < 1:
                            units = 1
                        if event.delta > 0:
                            canvas.yview_scroll(-int(units), "units")
                        else:
                            canvas.yview_scroll(int(units), "units")
            
            # 绑定滚轮事件到缩略图容器及其子元素
            thumb_container.bind("<MouseWheel>", on_thumb_mousewheel)
            thumb_container.bind("<Button-4>", on_thumb_mousewheel)
            thumb_container.bind("<Button-5>", on_thumb_mousewheel)
            # 触摸板事件
            thumb_container.bind("<Motion>", lambda e: None)  # 激活触摸板跟踪
            thumb_container.bind("<B1-Motion>", on_thumb_touchpad_scroll)
            thumb_container.bind("<B2-Motion>", on_thumb_touchpad_scroll)
            
            # 为标签和子元素也绑定相同的事件
            img_label.bind("<MouseWheel>", on_thumb_mousewheel)
            img_label.bind("<Button-4>", on_thumb_mousewheel)
            img_label.bind("<Button-5>", on_thumb_mousewheel)
            img_label.bind("<B1-Motion>", on_thumb_touchpad_scroll)
            img_label.bind("<B2-Motion>", on_thumb_touchpad_scroll)
            
            if 'size_label' in locals():
                size_label.bind("<MouseWheel>", on_thumb_mousewheel)
                size_label.bind("<Button-4>", on_thumb_mousewheel)
                size_label.bind("<Button-5>", on_thumb_mousewheel)
                size_label.bind("<B1-Motion>", on_thumb_touchpad_scroll)
                size_label.bind("<B2-Motion>", on_thumb_touchpad_scroll)
            
            # 更新缩略图区域滚动区域
            self.update_thumbnail_scroll_region()
            
            return thumb_container
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"创建缩略图出错: {str(e)}")
            if 'thumb_container' in locals() and thumb_container:
                thumb_container.destroy()
            return None
            
    def update_thumbnail_scroll_region(self):
        """更新缩略图区域的滚动区域"""
        self.thumbnail_frame.update_idletasks()
        if hasattr(self.thumbnail_frame, '_parent_canvas'):
            self.thumbnail_frame._parent_canvas.configure(scrollregion=self.thumbnail_frame._parent_canvas.bbox("all"))
        
    def format_size(self, size_bytes):
        """格式化文件大小显示"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def remove_file(self, file_path, container):
        # 移除文件对应的容器
        container.destroy()
        
        # 从文件列表中移除
        self.selected_files.remove(file_path)
        
        # 如果移除的是当前预览的文件
        if self.current_preview_file == file_path:
            if self.selected_files:
                self.set_preview_file(self.selected_files[0])
            else:
                self.clear_preview()
        # 如果移除的文件在当前预览之前，需要更新预览索引
        elif self.current_preview_index > self.selected_files.index(file_path):
            self.current_preview_index -= 1
            
        # 考虑重新排列缩略图?
        # 简单起见，目前只移除当前缩略图，不重新排列
        
    def clear_all_images(self):
        if not self.selected_files:
            return
        
        result = messagebox.askyesno("确认", "确定要清除所有图片吗？")
        if result:
            # 清空存储的文件
            self.selected_files = []
            
            # 清空预览区域
            self.clear_preview()
            
            # 清空缩略图区域
            for widget in self.thumbnail_frame.winfo_children():
                widget.destroy()
                
            # 重置行列计数
            self.thumbnail_row = 0
            self.thumbnail_col = 0
    
    def set_preview_file(self, file_path):
        if file_path in self.selected_files:
            self.current_preview_index = self.selected_files.index(file_path)
            self.current_preview_file = file_path
            
            try:
                # 加载和显示预览图片
                img = Image.open(file_path)
                
                # 获取原始尺寸
                original_width, original_height = img.size
                
                # 调整大小以适应预览区域，保持纵横比
                preview_width = self.preview_viewport.winfo_width() - 20
                preview_height = self.preview_viewport.winfo_height() - 20
                
                if preview_width <= 1:  # 初始化时可能无法获取正确的尺寸
                    preview_width = 400
                    preview_height = 300
                
                # 计算适合预览区域的图像尺寸，保持纵横比
                img_ratio = original_width / original_height
                view_ratio = preview_width / preview_height
                
                if img_ratio > view_ratio:  # 图片更宽
                    disp_width = preview_width
                    disp_height = int(preview_width / img_ratio)
                else:  # 图片更高
                    disp_height = preview_height
                    disp_width = int(preview_height * img_ratio)
                
                # 调整大小
                img_resized = img.copy()
                img_resized.thumbnail((disp_width, disp_height))
                
                # 创建PhotoImage对象并保存引用
                photo = ImageTk.PhotoImage(img_resized)
                self.preview_view.configure(image=photo)
                self.preview_view.image = photo
                
                # 更新缩放信息，根据当前的缩放模式
                if self.current_tab.get() == "scale":
                    self.update_scaled_size_info(original_width, original_height)
                else:  # target_size
                    self.update_target_size_info()
                
                # 更新导航按钮状态
                self.update_preview_controls()
                
                # 确保界面更新
                self.root.update_idletasks()
                
            except Exception as e:
                print(f"Error setting preview: {e}")
                import traceback
                traceback.print_exc()
    
    def update_scaled_size_info(self, original_width, original_height):
        """更新缩放系数下的预览信息"""
        # 获取当前文件大小
        try:
            file_size = os.path.getsize(self.current_preview_file)
            size_str = self.format_size(file_size)
            
            # 计算缩放后的文件大小估算值
            scale = self.scale_slider.get()
            scaled_width = round(original_width * scale)
            scaled_height = round(original_height * scale)
            
            # 估算缩放后的文件大小 (按照面积比例计算)
            area_ratio = (scaled_width * scaled_height) / (original_width * original_height)
            estimated_size = file_size * area_ratio
            estimated_size_str = self.format_size(estimated_size)
            
            # 更新信息文本，包含文件大小
            info_text = f"原始尺寸: {original_width} x {original_height} 像素\n原始大小: {size_str}\n缩放后: {scaled_width} x {scaled_height} 像素\n预计大小: {estimated_size_str}"
            self.preview_info.configure(text=info_text)
        except Exception as e:
            print(f"获取文件大小失败: {e}")
            # 退回到仅显示尺寸的模式
            scale = self.scale_slider.get()
            scaled_width = round(original_width * scale)
            scaled_height = round(original_height * scale)
            info_text = f"原始尺寸: {original_width} x {original_height} 像素\n缩放后: {scaled_width} x {scaled_height} 像素"
            self.preview_info.configure(text=info_text)
    
    def clear_preview(self):
        self.current_preview_index = -1
        self.current_preview_file = None
        self.preview_view.configure(image="")
        self.preview_info.configure(text="")
        self.update_preview_controls()  # 更新导航按钮状态
    
    def navigate_preview(self, direction):
        new_index = self.current_preview_index + direction
        if 0 <= new_index < len(self.selected_files):
            self.set_preview_file(self.selected_files[new_index])
    
    def update_preview_controls(self):
        """更新预览控制按钮状态"""
        total = len(self.selected_files)
        
        # 更新计数器
        if total > 0 and self.current_preview_index >= 0:
            self.preview_counter.configure(text=f"{self.current_preview_index + 1}/{total}")
        else:
            self.preview_counter.configure(text="0/0")
        
        # 更新按钮状态
        if total <= 1 or self.current_preview_index <= 0:
            self.prev_btn.configure(state=tk.DISABLED)
        else:
            self.prev_btn.configure(state=tk.NORMAL)
        
        if total <= 1 or self.current_preview_index >= total - 1 or self.current_preview_index < 0:
            self.next_btn.configure(state=tk.DISABLED)
        else:
            self.next_btn.configure(state=tk.NORMAL)
    
    def update_scale_value(self, value):
        value = float(value)
        self.scale_value_label.configure(text=f"{value:.1f}")
        
        # 更新当前预览图片的缩放信息
        if self.current_preview_file:
            try:
                img = Image.open(self.current_preview_file)
                original_width, original_height = img.size
                self.update_scaled_size_info(original_width, original_height)
            except Exception as e:
                print(f"Error updating scale: {e}")
    
    def update_image_count(self):
        # 我们不再需要单独更新计数，因为界面简化了
        pass
    
    def start_processing_with_dialog(self):
        """直接替换原始文件，不再弹出选择保存位置的对话框"""
        if not self.selected_files:
            messagebox.showwarning("警告", "请先选择图片")
            return
        
        # 创建临时输出目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(script_dir, "temp_output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 根据当前缩放模式获取缩放参数
        current_mode = self.current_tab.get()
        
        # 使用线程处理图片并直接替换原文件
        total_files = len(self.selected_files)
        
        # 创建进度条窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("处理中")
        progress_window.geometry("400x150")
        progress_window.configure(bg="#2A2A2A")
        progress_window.resizable(False, False)
        
        # 设置为模态窗口
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 添加进度条
        progress_label = tk.Label(progress_window, text="正在处理图片...", 
                                 bg="#2A2A2A", fg="#ffffff",
                                 font=("Microsoft YaHei", 12))
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, 
                                     length=350, mode='determinate')
        progress_bar.pack(pady=10, padx=20)
        
        status_label = tk.Label(progress_window, text="0/{} 已完成".format(total_files), 
                              bg="#2A2A2A", fg="#ffffff",
                              font=("Microsoft YaHei", 10))
        status_label.pack(pady=10)
        
        def process_thread():
            processed_count = 0
            copied_count = 0
            total_original_size = 0
            total_new_size = 0
            
            for file_info in self.selected_files:
                try:
                    # 获取原始文件大小
                    original_size = os.path.getsize(file_info)
                    total_original_size += original_size
                    
                    # 处理图片
                    img = Image.open(file_info)
                    original_width, original_height = img.size
                    
                    # 根据缩放模式计算新尺寸
                    if current_mode == "scale":
                        scale = self.scale_slider.get()
                        new_width = round(original_width * scale)
                        new_height = round(original_height * scale)
                    else:  # target_size
                        target_size = self.target_size_var.get()
                        if not target_size:
                            # 如果未选择目标尺寸，使用原始尺寸
                            new_width, new_height = original_width, original_height
                        else:
                            # 使用指定的目标尺寸
                            new_width, new_height = map(int, target_size.split('x'))
                    
                    # 调整大小并保持纵横比
                    if current_mode == "target_size" and target_size:
                        # 计算新的尺寸，保持纵横比
                        target_width, target_height = map(int, target_size.split('x'))
                        img_ratio = original_width / original_height
                        
                        # 图像适应目标尺寸，保持纵横比
                        if img_ratio > 1:  # 宽大于高的图片
                            new_width = target_width
                            new_height = int(target_width / img_ratio)
                        else:  # 高大于或等于宽的图片
                            new_height = target_height
                            new_width = int(target_height * img_ratio)
                    
                    # 调整大小并保存
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # 如果是目标尺寸模式且有选择尺寸，需要处理背景填充
                    if current_mode == "target_size" and target_size:
                        target_width, target_height = map(int, target_size.split('x'))
                        
                        # 创建带背景的图像
                        background = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
                        
                        # 计算位置让图像居中
                        offset = ((target_width - new_width) // 2, (target_height - new_height) // 2)
                        background.paste(resized_img, offset)
                        resized_img = background
                    
                    # 直接替换原始文件
                    output_path = file_info
                    _, ext = os.path.splitext(file_info)
                    
                    # 保存图像，使用合适的格式
                    if ext.lower() in ['.jpg', '.jpeg']:
                        # 如果是RGBA模式，转为RGB以便保存为JPG
                        if resized_img.mode == 'RGBA':
                            resized_img = resized_img.convert('RGB')
                        resized_img.save(output_path, quality=95)
                    else:
                        resized_img.save(output_path)
                    
                    # 获取新文件大小
                    new_size = os.path.getsize(output_path)
                    total_new_size += new_size
                    
                    copied_count += 1
                    
                    # 更新进度信息
                    orig_size_str = self.format_size(original_size)
                    new_size_str = self.format_size(new_size)
                    size_change_pct = ((new_size - original_size) / original_size) * 100
                    size_change_text = f"{'增加' if size_change_pct > 0 else '减少'} {abs(size_change_pct):.1f}%"
                    
                    status_label.configure(text=f"{processed_count+1}/{total_files} 已完成 | {orig_size_str} → {new_size_str} ({size_change_text})")
                    
                except Exception as e:
                    print(f"Error processing {file_info}: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    processed_count += 1
                    # 更新进度
                    progress = (processed_count / total_files) * 100
                    progress_bar['value'] = progress
                    progress_window.update()
            
            # 处理完成后显示总大小变化
            total_orig_size_str = self.format_size(total_original_size)
            total_new_size_str = self.format_size(total_new_size)
            total_change_pct = ((total_new_size - total_original_size) / total_original_size) * 100
            total_change_text = f"{'增加' if total_change_pct > 0 else '减少'} {abs(total_change_pct):.1f}%"
            
            # 处理完成后关闭进度窗口并显示完成消息
            progress_window.after(500, progress_window.destroy)
            messagebox.showinfo("处理完成", 
                              f"已成功处理并替换 {copied_count} 张原始图片\n\n"
                              f"总文件大小: {total_orig_size_str} → {total_new_size_str}\n"
                              f"({total_change_text})")
            
            # 清理临时目录
            try:
                shutil.rmtree(self.output_dir)
            except:
                pass
        
        # 确认是否要替换原始文件
        if messagebox.askyesno("确认", "确定要直接替换原始图片吗？此操作无法撤销。"):
            # 启动处理线程
            threading.Thread(target=process_thread, daemon=True).start()
        else:
            # 用户取消了替换操作
            return
    
    def on_window_resize(self, event):
        # 只有当窗口大小发生实质性变化并且有图片预览时才更新
        if event.widget == self.root and self.current_preview_file:
            # 防止频繁更新
            self.root.after(100, self.refresh_preview)
    
    def refresh_preview(self):
        if self.current_preview_index >= 0:
            self.set_preview_file(self.selected_files[self.current_preview_index])
    
    def switch_tab(self, tab_name):
        """切换缩放模式选项卡"""
        tab_style = {
            "active": {"bg": "#3c3c3c", "fg": "#ffffff", "relief": tk.SUNKEN, "borderwidth": 1},
            "inactive": {"bg": "#2A2A2A", "fg": "#aaaaaa", "relief": tk.FLAT, "borderwidth": 1}
        }
        
        if tab_name == "scale":
            # 激活系数缩放选项卡
            self.scale_tab.configure(**tab_style["active"])
            self.target_size_tab.configure(**tab_style["inactive"])
            # 显示系数缩放控制，隐藏目标尺寸控制
            self.target_size_frame.pack_forget()
            self.scale_frame.pack(fill=tk.X, pady=5)
            self.current_tab.set("scale")
            
            # 更新预览信息
            if self.current_preview_file:
                try:
                    img = Image.open(self.current_preview_file)
                    self.update_scaled_size_info(img.width, img.height)
                except Exception as e:
                    print(f"Error updating preview: {e}")
        
        elif tab_name == "target_size":
            # 激活目标尺寸选项卡
            self.scale_tab.configure(**tab_style["inactive"])
            self.target_size_tab.configure(**tab_style["active"])
            # 显示目标尺寸控制，隐藏系数缩放控制
            self.scale_frame.pack_forget()
            self.target_size_frame.pack(fill=tk.X, pady=5)
            self.current_tab.set("target_size")
            
            # 更新预览信息，如果有选择的目标尺寸
            if self.current_preview_file and self.target_size_var.get():
                try:
                    self.update_target_size_info()
                except Exception as e:
                    print(f"Error updating target size info: {e}")
    
    def set_target_size(self, size_str):
        """设置目标尺寸，并更新预览信息"""
        self.target_size_var.set(size_str)
        self.selected_size_label.configure(text=f"当前选择: {size_str}")
        
        # 如果有预览图片，更新信息
        if self.current_preview_file:
            self.update_target_size_info()
    
    def update_target_size_info(self):
        """更新目标尺寸调整下的预览信息"""
        try:
            # 获取原始图片尺寸
            img = Image.open(self.current_preview_file)
            original_width, original_height = img.width, img.height
            
            # 获取文件大小
            try:
                file_size = os.path.getsize(self.current_preview_file)
                size_str = self.format_size(file_size)
                
                # 获取目标尺寸
                target_size = self.target_size_var.get()
                if not target_size:
                    # 如果未选择目标尺寸，则显示原始尺寸和文件大小
                    self.preview_info.configure(text=f"原始尺寸: {original_width} x {original_height} 像素\n原始大小: {size_str}\n选择目标尺寸进行预览")
                    return
                    
                # 解析目标尺寸
                target_width, target_height = map(int, target_size.split('x'))
                
                # 计算实际的缩放尺寸(保持宽高比)
                img_ratio = original_width / original_height
                
                if img_ratio > 1:  # 宽大于高的图片
                    new_width = target_width
                    new_height = int(target_width / img_ratio)
                else:  # 高大于或等于宽的图片
                    new_height = target_height
                    new_width = int(target_height * img_ratio)
                
                # 估算缩放后的文件大小 (按照面积比例计算)
                area_ratio = (new_width * new_height) / (original_width * original_height)
                estimated_size = file_size * area_ratio
                estimated_size_str = self.format_size(estimated_size)
                
                # 更新预览信息
                info_text = f"原始尺寸: {original_width} x {original_height} 像素\n原始大小: {size_str}\n目标尺寸: {target_width} x {target_height} 像素\n实际尺寸: {new_width} x {new_height} 像素\n预计大小: {estimated_size_str}"
                self.preview_info.configure(text=info_text)
            except Exception as e:
                print(f"获取文件大小失败: {e}")
                # 退回到基本信息
                target_size = self.target_size_var.get()
                if not target_size:
                    self.preview_info.configure(text=f"原始尺寸: {original_width} x {original_height} 像素\n选择目标尺寸进行预览")
                    return
                    
                target_width, target_height = map(int, target_size.split('x'))
                info_text = f"原始尺寸: {original_width} x {original_height} 像素\n目标尺寸: {target_width} x {target_height} 像素"
                self.preview_info.configure(text=info_text)
                
        except Exception as e:
            print(f"Error updating target size info: {e}")
            self.preview_info.configure(text="图片信息加载错误")
    
    def browse_folder(self):
        """通过文件对话框选择文件夹，并递归查找其中的所有图片"""
        folder_path = filedialog.askdirectory(
            title="选择图片文件夹"
        )
        
        if not folder_path:
            return
            
        # 显示加载中对话框
        loading_window = tk.Toplevel(self.root)
        loading_window.title("加载中")
        loading_window.geometry("300x100")
        loading_window.configure(bg="#2A2A2A")
        loading_window.resizable(False, False)
        
        # 设置为模态窗口
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        # 添加加载提示
        loading_label = tk.Label(loading_window, text="正在扫描文件夹中的图片...", 
                                bg="#2A2A2A", fg="#ffffff",
                                font=("Microsoft YaHei", 12))
        loading_label.pack(pady=10)
        
        # 添加进度条
        progress_bar = ttk.Progressbar(loading_window, orient=tk.HORIZONTAL, 
                                     length=250, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20)
        progress_bar.start(10)  # 启动滚动效果
        
        # 更新GUI
        loading_window.update()
        
        # 使用线程执行耗时操作
        def scan_folder_thread():
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff']
            found_files = []
            
            # 递归获取所有匹配的文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in valid_extensions:
                        full_path = os.path.join(root, file)
                        if full_path not in self.selected_files:  # 避免重复添加
                            found_files.append(full_path)
            
            # 更新UI必须在主线程中进行
            self.root.after(10, lambda: self.finish_folder_scan(found_files, loading_window))
        
        # 启动线程
        threading.Thread(target=scan_folder_thread, daemon=True).start()
    
    def finish_folder_scan(self, found_files, loading_window):
        """完成文件夹扫描，添加找到的图片"""
        # 关闭加载窗口
        loading_window.destroy()
        
        if not found_files:
            messagebox.showinfo("结果", "未在所选文件夹中找到有效的图片文件")
            return
            
        # 显示找到的文件数量
        result = messagebox.askyesno("确认", f"在文件夹及其子文件夹中找到 {len(found_files)} 个图片文件。\n是否添加到处理列表？")
        if not result:
            return
            
        # 添加到选中文件列表
        self.selected_files.extend(found_files)
        
        # 创建新窗口显示进度
        progress_window = tk.Toplevel(self.root)
        progress_window.title("正在添加图片")
        progress_window.geometry("400x150")
        progress_window.configure(bg="#2A2A2A")
        progress_window.resizable(False, False)
        
        # 设置为模态窗口
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 添加进度条
        progress_label = tk.Label(progress_window, text="正在添加图片...", 
                                 bg="#2A2A2A", fg="#ffffff",
                                 font=("Microsoft YaHei", 12))
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient=tk.HORIZONTAL, 
                                     length=350, mode='determinate')
        progress_bar.pack(pady=10, padx=20)
        
        status_label = tk.Label(progress_window, text="0/{} 已添加".format(len(found_files)), 
                              bg="#2A2A2A", fg="#ffffff",
                              font=("Microsoft YaHei", 10))
        status_label.pack(pady=10)
        
        # 更新UI以确保窗口显示
        progress_window.update()
        
        # 使用线程添加图片缩略图
        def add_thumbnails_thread():
            added_count = 0
            
            for file_path in found_files:
                try:
                    # 在主线程中添加缩略图
                    self.root.after(0, lambda p=file_path: self.add_thumbnail(p))
                    added_count += 1
                    
                    # 更新进度
                    progress = (added_count / len(found_files)) * 100
                    self.root.after(0, lambda p=progress: progress_bar.configure(value=p))
                    self.root.after(0, lambda c=added_count, t=len(found_files): 
                                  status_label.configure(text=f"{c}/{t} 已添加"))
                except Exception as e:
                    print(f"添加缩略图时出错: {file_path}, 错误: {str(e)}")
            
            # 完成后关闭窗口
            self.root.after(100, progress_window.destroy)
            
            # 默认选中第一个文件进行预览（如果之前没有文件）
            if len(self.selected_files) == len(found_files):  # 如果之前没有文件
                self.root.after(200, lambda: self.set_preview_file(self.selected_files[0]))
        
        # 启动线程
        threading.Thread(target=add_thumbnails_thread, daemon=True).start()

    def show_file_options(self):
        """显示添加文件或文件夹的选项对话框"""
        # 创建一个小的弹出窗口
        options_window = tk.Toplevel(self.root)
        options_window.title("选择操作")
        options_window.geometry("240x120")
        options_window.configure(bg="#2A2A2A")
        options_window.resizable(False, False)
        
        # 设置为模态窗口
        options_window.transient(self.root)
        options_window.grab_set()
        
        # 在窗口中心位置
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (240 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (120 // 2)
        options_window.geometry(f"+{x}+{y}")
        
        # 添加选项按钮
        options_frame = tk.Frame(options_window, bg="#2A2A2A", padx=20, pady=15)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        add_files_btn = self.RoundedButton(options_frame, text="添加文件", 
                                          command=lambda: [options_window.destroy(), self.browse_files()],
                                          bg="#3498db", fg="#ffffff",
                                          activebackground="#2980b9",
                                          width=180, height=30,
                                          radius=8, font=("Microsoft YaHei", 10))
        add_files_btn.pack(pady=(0, 10))
        
        add_folder_btn = self.RoundedButton(options_frame, text="添加文件夹", 
                                           command=lambda: [options_window.destroy(), self.browse_folder()],
                                           bg="#9b59b6", fg="#ffffff",
                                           activebackground="#8e44ad",
                                           width=180, height=30,
                                           radius=8, font=("Microsoft YaHei", 10))
        add_folder_btn.pack()

    def browse_folder_direct(self):
        """直接浏览文件夹并添加所有图片，包括子文件夹中的图片"""
        folder_path = filedialog.askdirectory(
            title="选择图片文件夹"
        )
        
        if not folder_path:
            return
            
        # 显示加载中对话框
        loading_window = tk.Toplevel(self.root)
        loading_window.title("加载中")
        loading_window.geometry("300x100")
        loading_window.configure(bg="#2A2A2A")
        loading_window.resizable(False, False)
        
        # 设置为模态窗口
        loading_window.transient(self.root)
        loading_window.grab_set()
        
        # 添加加载提示
        loading_label = tk.Label(loading_window, text="正在扫描文件夹中的图片...", 
                                bg="#2A2A2A", fg="#ffffff",
                                font=("Microsoft YaHei", 12))
        loading_label.pack(pady=10)
        
        # 添加进度条
        progress_bar = ttk.Progressbar(loading_window, orient=tk.HORIZONTAL, 
                                     length=250, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20)
        progress_bar.start(10)  # 启动滚动效果
        
        # 更新GUI
        loading_window.update()
        
        # 使用线程执行耗时操作
        def scan_folder_thread():
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff']
            found_files = []
            
            # 递归获取所有匹配的文件
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in valid_extensions:
                        full_path = os.path.join(root, file)
                        if full_path not in self.selected_files:  # 避免重复添加
                            found_files.append(full_path)
            
            # 更新UI必须在主线程中进行
            self.root.after(10, lambda: self.finish_folder_scan(found_files, loading_window))
        
        # 启动线程
        threading.Thread(target=scan_folder_thread, daemon=True).start()

def main():
    print("程序开始初始化...")
    
    # 创建圆角矩形方法
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """使用直接绘制的方式创建圆角矩形，减少锯齿"""
        # 提取参数
        fill = kwargs.pop('fill', '')
        outline = kwargs.pop('outline', '')
        tags = kwargs.pop('tags', '')
        
        # 清除之前的元素
        if tags:
            self.delete(tags)
        
        # 创建主体矩形 (中间区域)
        rect_id = self.create_rectangle(x1+radius, y1, x2-radius, y2, 
                                      fill=fill, outline="", tags=tags)
        
        # 创建左右矩形 (左右两侧)
        left_rect = self.create_rectangle(x1, y1+radius, x1+radius, y2-radius, 
                                        fill=fill, outline="", tags=tags)
        right_rect = self.create_rectangle(x2-radius, y1+radius, x2, y2-radius, 
                                         fill=fill, outline="", tags=tags)
        
        # 创建四个圆角
        # 左上角
        nw_arc = self.create_arc(x1, y1, x1+2*radius, y1+2*radius, 
                               start=90, extent=90, style=tk.PIESLICE,
                               fill=fill, outline="", tags=tags)
        # 右上角
        ne_arc = self.create_arc(x2-2*radius, y1, x2, y1+2*radius, 
                               start=0, extent=90, style=tk.PIESLICE,
                               fill=fill, outline="", tags=tags)
        # 左下角
        sw_arc = self.create_arc(x1, y2-2*radius, x1+2*radius, y2, 
                               start=180, extent=90, style=tk.PIESLICE,
                               fill=fill, outline="", tags=tags)
        # 右下角
        se_arc = self.create_arc(x2-2*radius, y2-2*radius, x2, y2, 
                               start=270, extent=90, style=tk.PIESLICE,
                               fill=fill, outline="", tags=tags)
        
        # 如果需要边框
        if outline:
            # 绘制边框线段
            top_line = self.create_line(x1+radius, y1, x2-radius, y1, 
                                      fill=outline, tags=tags)
            bottom_line = self.create_line(x1+radius, y2, x2-radius, y2, 
                                                 fill=outline, tags=tags)
            left_line = self.create_line(x1, y1+radius, x1, y2-radius, 
                                               fill=outline, tags=tags)
            right_line = self.create_line(x2, y1+radius, x2, y2-radius, 
                                                fill=outline, tags=tags)
            
            # 绘制四个圆弧的边框
            nw_arc_outline = self.create_arc(x1, y1, x1+2*radius, y1+2*radius, 
                                           start=90, extent=90, style=tk.ARC, 
                                           outline=outline, tags=tags)
            ne_arc_outline = self.create_arc(x2-2*radius, y1, x2, y1+2*radius, 
                                           start=0, extent=90, style=tk.ARC, 
                                           outline=outline, tags=tags)
            sw_arc_outline = self.create_arc(x1, y2-2*radius, x1+2*radius, y2, 
                                           start=180, extent=90, style=tk.ARC, 
                                           outline=outline, tags=tags)
            se_arc_outline = self.create_arc(x2-2*radius, y2-2*radius, x2, y2, 
                                           start=270, extent=90, style=tk.ARC, 
                                           outline=outline, tags=tags)
        
        # 创建一个透明区域用于事件捕获
        return self.create_rectangle(x1, y1, x2, y2, fill="", outline="", tags=tags)
    
    # 添加方法到Canvas类
    tk.Canvas.create_rounded_rectangle = create_rounded_rectangle
    print("已添加create_rounded_rectangle方法到Canvas类")
    
    # 如果TkinterDnD可用，使用TkinterDnD.Tk代替普通的tk.Tk
    if TKDND_AVAILABLE:
        print("使用TkinterDnD.Tk初始化根窗口")
        root = TkinterDnD.Tk()
    else:
        print("使用标准tk.Tk初始化根窗口")
        root = tk.Tk()
        
    # 设置窗口图标
    try:
        # 尝试设置图标
        root.iconbitmap("icon.ico")  # 如果有图标文件，可以启用这一行
    except:
        print("未找到图标文件，使用默认图标")
        pass
    
    print("创建应用实例...")
    app = ImageResizerApp(root)
    print("进入主事件循环...")
    root.mainloop()

if __name__ == "__main__":
    main() 