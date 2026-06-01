import tkinter as tk
from tkinter import ttk
import math

# ============================================================
# Catppuccin Mocha Color Palette
# ============================================================
C = {
    "base":    "#1e1e2e", "mantle": "#181825", "crust":  "#11111b",
    "surface0":"#313244", "surface1":"#45475a", "surface2":"#585b70",
    "text":    "#cdd6f4", "subtext0":"#a6adc8", "subtext1":"#bac2de",
    "red":     "#f38ba8", "maroon":  "#eba0ac", "peach":  "#fab387",
    "yellow":  "#f9e2af", "green":   "#a6e3a1", "teal":   "#94e2d5",
    "sky":     "#89dceb", "sapphire":"#74c7ec", "blue":   "#89b4fa",
    "lavender":"#b4befe", "mauve":   "#cba6f7", "pink":   "#f5c2e7",
    "flamingo":"#f2cdcd","rosewater":"#f5e0dc",
}
LAB_COLORS = [C["mauve"],C["blue"],C["green"],C["yellow"],C["peach"],C["red"]]
FONT = ("Microsoft YaHei", 10)
FONT_B = ("Microsoft YaHei", 10, "bold")
FONT_H = ("Microsoft YaHei", 14, "bold")
FONT_M = ("Consolas", 9)
FONT_S = ("Consolas", 8)


class JOSDemoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JOS Operating System — Interactive Step-by-Step Demo")
        self.root.geometry("1320x860")
        self.root.configure(bg=C["crust"])
        self.root.minsize(1100, 700)

        self.lab_defs = [
            ("Lab 1: Booting & Bootloader","BIOS → Real Mode → Protected Mode → Kernel Entry"),
            ("Lab 2: Memory Management","Physical Pages · Page Tables · Virtual Address Space"),
            ("Lab 3: User Environments & Syscalls","Env Lifecycle · IDT/Trap · System Call Flow"),
            ("Lab 4: Multitasking & IPC","SMP · Round-Robin · COW Fork · Page-Level IPC"),
            ("Lab 5: File System & Shell","Disk Layout · FS Server · Spawn · Pipes & Redirect"),
            ("Lab 6: Network Driver","E1000 · Descriptor Rings · lwIP Stack · HTTP Server"),
        ]

        self._anim_jobs = []   # pending after() IDs
        self._anim_running = False
        self._auto_playing = False
        self._auto_job = None

        self.current_lab = None
        self.current_step = 0
        self.total_steps = 0

        self._build_layout()
        self._select_lab(0)

    # ── Layout ─────────────────────────────────────────────────────
    def _build_layout(self):
        # ── Sidebar ──
        self.sidebar = tk.Frame(self.root, bg=C["mantle"], width=210)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        hdr = tk.Frame(self.sidebar, bg=C["mantle"])
        hdr.pack(fill=tk.X, pady=(22, 8))
        tk.Label(hdr, text="JOS", bg=C["mantle"], fg=C["mauve"],
                 font=("Segoe UI", 24, "bold")).pack()
        tk.Label(hdr, text="Operating System Demo", bg=C["mantle"], fg=C["subtext0"],
                 font=("Microsoft YaHei", 7)).pack()
        tk.Label(hdr, text="MIT 6.828 / xv6", bg=C["mantle"], fg=C["surface2"],
                 font=("Consolas", 7)).pack(pady=(2,0))

        sep = tk.Frame(self.sidebar, bg=C["surface0"], height=1)
        sep.pack(fill=tk.X, padx=16, pady=(10, 14))

        self.lab_btns = []
        self._lab_sub = []   # subtitle labels for each button
        labs_cn = [
            ("  Boot & Init  ", "BIOS → Bootloader → Kernel"),
            ("  Memory Mgmt  ", "Pages · Page Tables · VM"),
            ("  User Envs    ", "IDT · Traps · System Calls"),
            ("  Multitasking ", "SMP · COW Fork · IPC"),
            ("  File System  ", "Disk · FS Server · Shell"),
            ("  Networking   ", "E1000 · lwIP · HTTP"),
        ]
        for i, (short, sub) in enumerate(labs_cn):
            card = tk.Frame(self.sidebar, bg=C["surface0"], cursor="hand2")
            card.pack(fill=tk.X, padx=10, pady=4, ipady=2)
            card.bind("<Button-1>", lambda e, idx=i: self._select_lab(idx))
            for ch in card.winfo_children():
                ch.bind("<Button-1>", lambda e, idx=i: self._select_lab(idx))

            dot = tk.Label(card, text="●", bg=C["surface0"], fg=LAB_COLORS[i],
                           font=("Segoe UI", 10))
            dot.pack(side=tk.LEFT, padx=(8, 2))

            num = tk.Label(card, text="Lab {}".format(i + 1), bg=C["surface0"],
                           fg=C["text"], font=("Segoe UI", 9, "bold"))
            num.pack(side=tk.LEFT)

            txt = tk.Label(card, text=short, bg=C["surface0"], fg=C["subtext0"],
                           font=("Microsoft YaHei", 8))
            txt.pack(side=tk.LEFT)

            self.lab_btns.append((card, dot, num, txt))

        sep2 = tk.Frame(self.sidebar, bg=C["surface0"], height=1)
        sep2.pack(fill=tk.X, padx=16, pady=(14, 10))

        # status indicator
        self.status_lbl = tk.Label(self.sidebar, text="  READY", bg=C["mantle"],
                                    fg=C["green"], font=("Consolas", 9, "bold"),
                                    anchor=tk.W)
        self.status_lbl.pack(fill=tk.X, padx=16)
        self.status_sub = tk.Label(self.sidebar, text="  Select a Lab to begin",
                                    bg=C["mantle"], fg=C["surface2"],
                                    font=("Microsoft YaHei", 7), anchor=tk.W)
        self.status_sub.pack(fill=tk.X, padx=16, pady=(2, 0))

        # ── Main area ──
        self.main = tk.Frame(self.root, bg=C["base"])
        self.main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Top bar ──
        top = tk.Frame(self.main, bg=C["mantle"], height=56)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        self.title_label = tk.Label(top, text="", bg=C["mantle"], fg=C["text"],
                                     font=FONT_H, anchor=tk.W)
        self.title_label.pack(side=tk.LEFT, padx=(18, 0), pady=6)
        self.desc_label = tk.Label(top, text="", bg=C["mantle"], fg=C["subtext0"],
                                    font=("Microsoft YaHei", 8), anchor=tk.W)
        self.desc_label.pack(side=tk.LEFT, padx=(18, 0), pady=6)

        self.step_indicator = tk.Label(top, text="", bg=C["mantle"], fg=C["mauve"],
                                        font=("Segoe UI", 11, "bold"))
        self.step_indicator.pack(side=tk.RIGHT, padx=20, pady=6)

        # ── Canvas ──
        self.canvas_frame = tk.Frame(self.main, bg=C["base"])
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 2))

        self.canvas = tk.Canvas(self.canvas_frame, bg=C["mantle"],
                                 highlightthickness=0, height=360)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.canvas.bind("<Configure>", self._on_resize)

        # ── Bottom panel: terminal + info ──
        self.bottom = tk.Frame(self.main, bg=C["base"])
        self.bottom.pack(fill=tk.X, padx=8, pady=(0, 4))

        # Terminal (simulated JOS console)
        self.term_frame = tk.Frame(self.bottom, bg=C["crust"])
        self.term_frame.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.term_canvas = tk.Canvas(self.term_frame, bg=C["crust"],
                                      highlightthickness=0, height=90)
        self.term_canvas.pack(fill=tk.X, padx=2, pady=2)
        self._term_lines = []
        self._term_offset = 0

        # Info text
        self.info_frame = tk.Frame(self.bottom, bg=C["surface0"])
        self.info_frame.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.info_text = tk.Label(self.info_frame, text="",
                                   bg=C["surface0"], fg=C["text"],
                                   font=FONT, wraplength=1200,
                                   justify=tk.LEFT, padx=14, pady=8)
        self.info_text.pack(fill=tk.X)

        # ── Navigation ──
        self.nav_frame = tk.Frame(self.main, bg=C["base"])
        self.nav_frame.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.speed_var = tk.StringVar(value="Medium")
        speed_menu = tk.OptionMenu(self.nav_frame, self.speed_var,
                                    "Slow", "Medium", "Fast",
                                    command=self._on_speed_change)
        speed_menu.configure(bg=C["surface1"], fg=C["text"],
                             font=("Microsoft YaHei", 8), relief=tk.FLAT,
                             highlightthickness=0, indicatoron=0)
        speed_menu["menu"].configure(bg=C["surface1"], fg=C["text"],
                                      font=("Microsoft YaHei", 8))
        speed_menu.pack(side=tk.LEFT, padx=4)

        self.auto_btn = tk.Button(self.nav_frame, text="  ▶ Auto Play",
                                  bg=C["surface1"], fg=C["text"],
                                  font=("Microsoft YaHei", 9),
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=14, pady=3, command=self._toggle_auto,
                                  activebackground=C["surface2"],
                                  activeforeground=C["text"])
        self.auto_btn.pack(side=tk.RIGHT, padx=4)

        self.next_btn = tk.Button(self.nav_frame, text="Next ▸",
                                  bg=C["mauve"], fg=C["crust"],
                                  font=("Segoe UI", 10, "bold"),
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=20, pady=4, command=self._next_step,
                                  activebackground=C["lavender"],
                                  activeforeground=C["crust"])
        self.next_btn.pack(side=tk.RIGHT, padx=4)

        self.prev_btn = tk.Button(self.nav_frame, text="◂ Prev",
                                  bg=C["surface1"], fg=C["text"],
                                  font=("Segoe UI", 10),
                                  relief=tk.FLAT, cursor="hand2",
                                  padx=20, pady=4, state=tk.DISABLED,
                                  command=self._prev_step,
                                  activebackground=C["surface2"],
                                  activeforeground=C["text"])
        self.prev_btn.pack(side=tk.RIGHT, padx=4)

        self.step_lbl = tk.Label(self.nav_frame, text="", bg=C["base"],
                                  fg=C["subtext0"], font=FONT)
        self.step_lbl.pack(side=tk.RIGHT, padx=12)

    # ── Speed ──────────────────────────────────────────────────────
    def _on_speed_change(self, v):
        pass  # used by anim delays

    def _anim_delay(self):
        return {"Slow": 600, "Medium": 350, "Fast": 150}.get(self.speed_var.get(), 350)

    # ── Selection ─────────────────────────────────────────────────
    def _select_lab(self, idx):
        self._cancel_anim()
        self._stop_auto()
        self.current_lab = idx
        self.current_step = 0
        for i, (card, dot, num, txt) in enumerate(self.lab_btns):
            if i == idx:
                card.configure(bg=C["mauve"])
                dot.configure(bg=C["mauve"], fg=C["crust"])
                num.configure(bg=C["mauve"], fg=C["crust"])
                txt.configure(bg=C["mauve"], fg=C["crust"])
            else:
                card.configure(bg=C["surface0"])
                dot.configure(bg=C["surface0"], fg=LAB_COLORS[i])
                num.configure(bg=C["surface0"], fg=C["text"])
                txt.configure(bg=C["surface0"], fg=C["subtext0"])
        title, desc = self.lab_defs[idx]
        self.title_label.configure(text=title)
        self.desc_label.configure(text=desc)
        self.total_steps = [5, 5, 5, 5, 5, 5][idx]
        self._update_nav()
        self._draw_current_step(animate=True)

    # ── Navigation ────────────────────────────────────────────────
    def _update_nav(self):
        s = self.current_step
        t = self.total_steps
        self.step_indicator.configure(text="STEP {}/{}".format(s + 1, t))
        self.step_lbl.configure(text="Step {} of {}".format(s + 1, t))
        self.prev_btn.configure(state=tk.NORMAL if s > 0 else tk.DISABLED)
        if s >= t - 1:
            self.next_btn.configure(text="Done ✓", bg=C["green"])
        else:
            self.next_btn.configure(text="Next ▸", bg=C["mauve"])

    def _prev_step(self):
        if self.current_step > 0 and not self._anim_running:
            self.current_step -= 1
            self._stop_auto()
            self._update_nav()
            self._draw_current_step(animate=True)

    def _next_step(self):
        if self.current_step < self.total_steps - 1 and not self._anim_running:
            self.current_step += 1
            self._update_nav()
            self._draw_current_step(animate=True)

    def _toggle_auto(self):
        if self._auto_playing:
            self._stop_auto()
        else:
            self._auto_playing = True
            self.auto_btn.configure(text="  ■ Stop", bg=C["red"], fg=C["crust"])
            self.status_lbl.configure(text="  AUTO", fg=C["yellow"])
            self._auto_advance()

    def _stop_auto(self):
        self._auto_playing = False
        self.auto_btn.configure(text="  ▶ Auto Play", bg=C["surface1"], fg=C["text"])
        self.status_lbl.configure(text="  READY", fg=C["green"])
        if self._auto_job:
            self.root.after_cancel(self._auto_job)
            self._auto_job = None

    def _auto_advance(self):
        if not self._auto_playing:
            return
        total_anim_time = self._anim_delay() * 6 + 2000
        wait = max(total_anim_time + 1200, 5000)

        def go():
            if not self._auto_playing:
                return
            if self.current_step < self.total_steps - 1:
                self.current_step += 1
                self._update_nav()
                self._draw_current_step(animate=True)
                self._auto_job = self.root.after(wait, self._auto_advance)
            else:
                self._stop_auto()
        self._auto_job = self.root.after(wait, go)

    def _on_resize(self, event):
        if not self._anim_running and self.current_lab is not None:
            self._draw_current_step(animate=False)

    # ── Animation control ─────────────────────────────────────────
    def _cancel_anim(self):
        for jid in self._anim_jobs:
            self.root.after_cancel(jid)
        self._anim_jobs.clear()
        self._anim_running = False

    def _schedule(self, ms, fn):
        jid = self.root.after(ms, fn)
        self._anim_jobs.append(jid)
        return jid

    def _anim_done(self):
        self._anim_running = False
        self._anim_jobs.clear()

    # ── Terminal simulation ───────────────────────────────────────
    def _clear_term(self):
        self._term_offset = 0
        self.term_canvas.delete("all")
        self._term_lines = []

    def _write_term(self, text, color=C["subtext0"], idx=0):
        """type one line to the simulated terminal"""
        y = 10 + self._term_offset * 18
        self.term_canvas.create_text(10, y, text=text, anchor=tk.W,
                                      fill=color, font=FONT_M)
        self._term_offset += 1
        self._term_lines.append((text, color))

    def _animate_term(self, lines, start_delay=200):
        """animate terminal lines appearing one by one"""
        self._clear_term()
        self._anim_running = True
        d = self._anim_delay()
        for i, (text, color) in enumerate(lines):
            self._schedule(start_delay + i * d,
                           lambda t=text, c=color, idx=i: self._write_term(t, c, idx))

    # ── Drawing helpers ───────────────────────────────────────────
    def _round_rect(self, x1, y1, x2, y2, r=10, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
               x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.canvas.create_polygon(pts, smooth=True, **kw)

    def _box(self, x, y, w, h, text, fill=C["surface0"], tc=C["text"],
             font=FONT_B, outline=None, tags=""):
        if outline is None:
            outline = fill
        r = self._round_rect(x, y, x+w, y+h, r=9, fill=fill, outline=outline, width=2, tags=tags)
        t = self.canvas.create_text(x+w//2, y+h//2, text=text, fill=tc, font=font, tags=tags)
        return r, t

    def _arrow(self, x1, y1, x2, y2, color=C["subtext0"], w=2, dash=(), tags=""):
        return self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST,
                                        fill=color, width=w, dash=dash,
                                        arrowshape=(13, 16, 7), tags=tags)

    def _hline(self, x1, x2, y, color=C["surface2"], dash=(), tags=""):
        self.canvas.create_line(x1, y, x2, y, fill=color, width=1, dash=dash, tags=tags)

    def _shadow_box(self, x, y, w, h, text, fill, tc, font=FONT_B):
        """box with drop shadow"""
        self._round_rect(x+3, y+3, x+w+3, y+h+3, r=9, fill=C["crust"], outline=C["crust"])
        self._box(x, y, w, h, text, fill, tc, font)

    def _glow_dot(self, x, y, r, color, tags=""):
        for i in range(3, 0, -1):
            alpha = int(0x30 / i)
            c = color
            self.canvas.create_oval(x-r-i*2, y-r-i*2, x+r+i*2, y+r+i*2,
                                     fill="", outline=color, width=1, tags=tags)
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color, tags=tags)

    # ═══════════════════════════════════════════════════════════════
    # MAIN DRAW DISPATCH
    # ═══════════════════════════════════════════════════════════════
    def _draw_current_step(self, animate=True):
        self._cancel_anim()
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50:
            w = 1000
        if h < 50:
            h = 340
        self._W, self._H = w, h

        if animate:
            self._anim_running = True
            self.status_lbl.configure(text="  ANIM", fg=C["blue"])
            self.status_sub.configure(text="  Drawing step...")
        else:
            self._anim_running = False

        labs = [self._lab1, self._lab2, self._lab3,
                self._lab4, self._lab5, self._lab6]
        lab = labs[self.current_lab]
        info_map = lab(self.current_step)

        if animate:
            self._animate_term(info_map.get("term", []), start_delay=100)
        else:
            self._clear_term()
            for t, c in info_map.get("term", []):
                self._write_term(t, c)

        self.info_text.configure(text=info_map.get("info", ""))

        if animate:
            draw_fn = info_map.get("draw")
            if draw_fn:
                # schedule the draw slightly after term starts
                self._schedule(150, lambda: draw_fn(self._W, self._H))

            total = len(info_map.get("term", [])) * self._anim_delay() + 500
            self._schedule(total + 400, self._anim_done)
            self._schedule(total + 500, lambda: self.status_lbl.configure(
                text="  READY", fg=C["green"]))
            self._schedule(total + 500, lambda: self.status_sub.configure(
                text="  Press Next or enable Auto Play"))
        else:
            draw_fn = info_map.get("draw")
            if draw_fn:
                draw_fn(w, h)
            self._anim_done()
            self.status_lbl.configure(text="  READY", fg=C["green"])

    # ═══════════════════════════════════════════════════════════════
    # LAB 1:  Boot & Init  (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab1(self, step):
        infos = [
            ("BIOS 上电自检 (POST)\n\n"
             "  • CPU 复位后从 0xFFFFFFF0 开始执行，跳转到 BIOS ROM\n"
             "  • BIOS 执行 POST：检测 CPU、内存、键盘等硬件\n"
             "  • BIOS 扫描引导设备，读取第一个可引导磁盘的引导扇区\n"
             "  • 512 字节的引导扇区被加载到物理地址 0x7C00\n"
             "  • BIOS 跳转到 0x7C00，CPU 进入实模式开始执行 Boot Loader"),
            ("Boot Loader：实模式 → 保护模式\n\n"
             "  • boot.S 首先关闭中断 (cli)，防止初始化过程被打断\n"
             "  • 开启 A20 地址线，突破 8086 的 1MB 寻址限制\n"
             "  • 加载全局描述符表 GDT (lgdt)，定义代码段和数据段\n"
             "  • 设置 CR0 控制寄存器的 PE 位 = 1，进入 32 位保护模式\n"
             "  • 执行远跳转 ljmp，刷新 CS 寄存器，正式进入保护模式"),
            ("加载内核 ELF 镜像\n\n"
             "  • boot/main.c 读取磁盘上的内核 ELF 文件头\n"
             "  • 解析 ELF Program Header Table\n"
             "  • 将每个 LOAD 段复制到物理内存 0x100000 (1MB) 处\n"
             "  • ELF 段包含：.text (代码) / .rodata (只读) / .data / .bss\n"
             "  • 跳转到 ELF 入口点 entry.S 开始执行内核代码"),
            ("内核入口：开启分页机制\n\n"
             "  • entry.S 加载临时页表 entry_pgdir 到 CR3 寄存器\n"
             "  • entry_pgdir 使用 4MB 大页，映射 VA 0xF0000000→PA 0x00000000\n"
             "  • 设置 CR0.PG = 1，CPU 开始使用分页机制\n"
             "  • 此时所有地址经过 MMU 转换，虚拟地址空间建立\n"
             "  • 设置内核栈 esp，跳转到 C 函数 i386_init()"),
            ("内核初始化 → 监视器就绪\n\n"
             "  • cons_init() — 初始化控制台 (VGA + 键盘)\n"
             "  • mem_init() — 初始化物理页管理和虚拟内存\n"
             "  • env_init() — 初始化环境 (进程) 数组\n"
             "  • trap_init() — 配置 IDT 中断描述符表\n"
             "  • 最后运行 monitor()，显示 K> 提示符等待命令"),
        ]
        terms = [
            [("BIOS: Power-On Self Test (POST)...", C["peach"]),
             ("BIOS: Scanning boot devices...", C["peach"]),
             ("BIOS: Loading boot sector (512B) to 0x7C00...", C["peach"]),
             ("BIOS: Jumping to 0x7C00...", C["green"])],
            [("boot.S: cli            # disable interrupts", C["blue"]),
             ("boot.S: Enable A20 address line...", C["blue"]),
             ("boot.S: lgdt gdtdesc   # load GDT", C["blue"]),
             ("boot.S: mov %cr0, eax; or $1, eax; mov eax, %cr0", C["mauve"]),
             ("boot.S: ljmp $SEL_KCODE, $1f  # enter 32-bit!", C["green"])],
            [("boot/main.c: Reading kernel ELF header...", C["blue"]),
             ("boot/main.c: .text  -> PA 0x100000", C["blue"]),
             ("boot/main.c: .data  -> PA 0x102000", C["blue"]),
             ("boot/main.c: Jumping to kernel entry point...", C["green"])],
            [("entry.S: mov $entry_pgdir, %cr3    # load page table", C["mauve"]),
             ("entry.S: mov %cr0, %eax; or $0x80000000, %eax", C["mauve"]),
             ("entry.S: mov %eax, %cr0             # enable paging!", C["green"]),
             ("entry.S: mov $bootstack, %esp       # set kernel stack", C["blue"]),
             ("entry.S: call i386_init              # enter C code", C["blue"])],
            [("i386_init(): cons_init()      # init console...", C["blue"]),
             ("i386_init(): mem_init()       # init memory mgmt...", C["blue"]),
             ("i386_init(): env_init()       # init env array...", C["blue"]),
             ("i386_init(): trap_init()      # init IDT...", C["blue"]),
             ("Welcome to the JOS kernel monitor!", C["green"]),
             ("Type 'help' for a list of commands.", C["subtext0"]),
             ("K> _", C["mauve"])],
        ]
        draws = [self._draw_l1_s0, self._draw_l1_s1, self._draw_l1_s2,
                 self._draw_l1_s3, self._draw_l1_s4]

        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l1_s0(self, W, H):
        self.canvas.create_text(W // 2, 16, text="BIOS 加电启动流程",
                                 fill=C["mauve"], font=FONT_H, tags="s0")
        # CPU + BIOS ROM
        cpu_x, bio_x = W // 2 - 200, W // 2 + 60
        for x, lbl, cl in [(cpu_x, "CPU\n0xFFFFFFF0", C["red"]),
                            (bio_x, "BIOS ROM\nPOST · 硬件检测", C["blue"])]:
            self._shadow_box(x, 55, 160, 50, lbl, cl, C["crust"])
        self._arrow(cpu_x + 160, 80, bio_x, 80, C["mauve"], 3, tags="s0")

        # Memory layout
        mem = [("0x00000  IVT/BDA", "#f38ba8"), ("0x00400  BIOS Data", "#fab387"),
               ("0x07C00  BOOT SECTOR ←", "#a6e3a1"), ("0x0F000  BIOS ROM", "#b4befe"),
               ("0x9FC00  Free Memory", "#89b4fa")]
        mx, my, mw, mh = W // 2 - 280, 130, 130, 190
        for addr, clr in mem:
            self._round_rect(mx, my, mx + mw, my + 28, 4, fill=clr, outline=clr, tags="s0")
            self.canvas.create_text(mx + mw // 2, my + 14, text=addr, fill=C["crust"],
                                     font=FONT_S, tags="s0")
            my += 32

        self.canvas.create_text(mx + mw // 2, my + 8, text="0xFFFFF (1MB)",
                                 fill=C["surface2"], font=FONT_S, tags="s0")
        self._arrow(W // 2 + 120, 105, mx + mw // 2, my - 90, C["yellow"], 2, tags="s0")

        tags_s0 = "s0"
        self._box(W // 2 - 150, 340, 300, 28,
                  "BIOS → 0x7C00 → Boot Loader",
                  C["mauve"], C["crust"], font=FONT_B, tags=tags_s0)

    def _draw_l1_s1(self, W, H):
        self.canvas.create_text(W // 2, 15, text="Boot Loader：实模式 → 32位保护模式",
                                 fill=C["mauve"], font=FONT_H)
        self._shadow_box(W // 2 - 300, 55, 140, 42, "实模式\nReal Mode (16-bit)",
                         C["red"], C["crust"])
        self._shadow_box(W // 2 + 160, 55, 140, 42, "保护模式\nProtected Mode (32-bit)",
                         C["green"], C["crust"])
        self._arrow(W // 2 - 155, 76, W // 2 + 155, 76, C["mauve"], 4)

        steps = ["① cli — 关中断", "② 开启 A20 地址线", "③ lgdt — 加载 GDT",
                 "④ mov CR0.PE = 1", "⑤ ljmp — 刷新 CS"]
        for i, s in enumerate(steps):
            self._box(W // 2 - 180, 120 + i * 38, 360, 30, s,
                      C["surface0"], C["text"], font=FONT_B)

    def _draw_l1_s2(self, W, H):
        self.canvas.create_text(W // 2, 15, text="从磁盘加载内核 ELF 镜像到物理内存",
                                 fill=C["mauve"], font=FONT_H)
        self._shadow_box(W // 2 - 320, 60, 130, 45, "磁盘\nkernel.img", C["yellow"], C["crust"])
        self._arrow(W // 2 - 185, 82, W // 2 - 95, 82, C["mauve"], 2)

        self._shadow_box(W // 2 - 90, 55, 150, 55, "ELF 解析\nboot/main.c → 复制 LOAD 段",
                         C["blue"], C["crust"])
        self._arrow(W // 2 + 65, 82, W // 2 + 155, 82, C["mauve"], 2)

        self._shadow_box(W // 2 + 160, 60, 130, 45, "物理内存\n0x100000 (1MB)",
                         C["green"], C["crust"])

        segs = [(".text  (代码)", C["red"]), (".rodata (只读)", C["peach"]),
                (".data  (数据)", C["yellow"]), (".bss   (BSS)", C["green"])]
        for i, (name, clr) in enumerate(segs):
            y = 140 + i * 30
            self._round_rect(W // 2 - 220, y, W // 2 - 180, y + 22, 5,
                             fill=clr, outline=clr)
            self.canvas.create_text(W // 2 - 200, y + 11, text=name[:3], fill=C["crust"],
                                     font=FONT_S)
            self.canvas.create_text(W // 2 - 165, y + 11, text=name, fill=C["text"],
                                     font=FONT, anchor=tk.W)

    def _draw_l1_s3(self, W, H):
        self.canvas.create_text(W // 2, 15, text="entry.S：加载 entry_pgdir 并开启分页",
                                 fill=C["mauve"], font=FONT_H)

        flow = ["entry.S", "加载\nentry_pgdir\n→ CR3", "CR0.PG = 1\n分页开启"]
        clrs = [C["mauve"], C["blue"], C["green"]]
        fx = W // 2 - 310
        for i, (txt, clr) in enumerate(zip(flow, clrs)):
            self._shadow_box(fx + i * 220, 55, 180, 50, txt, clr, C["crust"])
            if i < len(flow) - 1:
                self._arrow(fx + i * 220 + 180, 80, fx + (i + 1) * 220, 80, C["mauve"], 2)

        self.canvas.create_text(W // 2 - 180, 135, text="虚拟地址 (VA)", fill=C["mauve"], font=FONT_B)
        self.canvas.create_text(W // 2 + 180, 135, text="物理地址 (PA)", fill=C["green"], font=FONT_B)

        for i, (va, pa) in enumerate([("0xF0100000", "0x00100000"),
                                       ("0xF0101000", "0x00101000"),
                                       ("0xF0102000", "0x00102000")]):
            y = 165 + i * 36
            self._box(W // 2 - 320, y, 140, 28, va, C["surface0"], C["text"], font=FONT_M)
            self._arrow(W // 2 - 175, y + 14, W // 2 + 175, y + 14, C["mauve"], 3)
            self._box(W // 2 + 180, y, 140, 28, pa, C["surface0"], C["green"], font=FONT_M)

        self.canvas.create_text(W // 2, 295, text="entry_pgdir 使用 4MB 大页直映射：VA[31:22] → PDE → PA[31:22]",
                                 fill=C["surface2"], font=FONT_S)

    def _draw_l1_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="i386_init() 初始化流程 → 进入内核监视器",
                                 fill=C["mauve"], font=FONT_H)

        flow = [("cons_init", C["red"]), ("mem_init", C["peach"]), ("env_init", C["yellow"]),
                ("trap_init", C["green"]), ("monitor()", C["mauve"])]
        fx = W // 2 - 370
        for i, (name, clr) in enumerate(flow):
            self._shadow_box(fx + i * 155, 55, 135, 38, name, clr, C["crust"],
                             font=FONT_B)
            if i < len(flow) - 1:
                self._arrow(fx + i * 155 + 135, 74, fx + (i+1) * 155, 74, C["mauve"], 2)

        # Monitor terminal
        self._box(W // 2 - 320, 120, 640, 210, "", C["crust"], "", outline=C["mauve"])
        lines = [
            ("Welcome to the JOS kernel monitor!", C["green"]),
            ("Type 'help' for a list of commands.", C["subtext0"]),
            ("K> help", C["mauve"]),
            ("  help      - Display this list of commands", C["text"]),
            ("  kerninfo  - Display information about the kernel", C["text"]),
            ("  backtrace - Display the stack backtrace", C["text"]),
            ("K> kerninfo", C["mauve"]),
            ("Kernel executable memory footprint: 64KB", C["green"]),
        ]
        for i, (line, clr) in enumerate(lines):
            self.canvas.create_text(W // 2, 140 + i * 20, text=line, fill=clr,
                                     font=FONT_M if "K>" in line else FONT_S)

    # ═══════════════════════════════════════════════════════════════
    # LAB 2:  Memory Management  (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab2(self, step):
        infos = [
            ("物理内存探测与初始化\n\n"
             "  • BIOS INT 0x15 报告可用内存 (base memory + extended memory)\n"
             "  • JOS 将物理内存信息记录到全局变量 npages / npages_basemem\n"
             "  • boot_alloc(n) 在内核早期提供简单的线性内存分配\n"
             "  • page_init() 分析内存布局，建立 PageInfo 数组和空闲页面链表"),
            ("物理页管理：PageInfo 与空闲链表\n\n"
             "  • struct PageInfo { *pp_link, pp_ref } 为每个物理页维护元数据\n"
             "  • pp_link 将所有空闲页串成单向链表 (page_free_list)\n"
             "  • page_alloc(ALLOC_ZERO)：从链表头部取一页，可选清零\n"
             "  • page_free(pp) 和 page_decref(pp)：归还页面或减少引用"),
            ("虚拟内存：二级页表 VA→PA 转换\n\n"
             "  • x86 32位虚拟地址拆分：DIR[31:22] 10位 + TABLE[21:12] 10位 + OFFSET[11:0] 12位\n"
             "  • pgdir_walk(pgdir, va, create)：遍历二级页表，返回 PTE 指针\n"
             "  • page_insert()：建立 VA→PA 映射并管理引用计数\n"
             "  • page_lookup() / page_remove()：查询和删除映射"),
            ("JOS 虚拟地址空间完整布局\n\n"
             "  • KERNBASE (0xF0000000)：内核空间起始，以上映射所有物理内存\n"
             "  • ULIM (0xEF800000)：用户空间地址上限\n"
             "  • UVPT (0xEF400000)：用户只读页表 (实现用户态缺页处理)\n"
             "  • UPAGES (0xEF000000)：用户只读页面信息数组\n"
             "  • UENVS (0xEEC00000)：环境数组，用户只读"),
            ("内存管理自检验证\n\n"
             "  • check_page_free_list()：验证空闲链表结构完整性\n"
             "  • check_page_alloc()：验证分配/释放每个操作的正确性\n"
             "  • check_page()：验证 insert/lookup/remove 全流程\n"
             "  • check_kern_pgdir()：验证内核页表每个映射正确\n"
             "  • check_page_installed_pgdir()：验证页表切换后一致性\n"
             "  • 所有检查通过后，mem_init() 成功返回"),
        ]
        terms = [
            [("Physical memory: 131072K available", C["green"]),
             ("base = 640K, extended = 130432K", C["subtext0"]),
             ("boot_alloc(): allocating early kernel memory...", C["blue"]),
             ("page_init(): building PageInfo array...", C["blue"]),
             ("page_init(): free page list ready", C["green"])],
            [("struct PageInfo { pp_link, pp_ref }  // per physical page", C["mauve"]),
             ("page_free_list -> Page0 -> Page1 -> ... -> NULL", C["green"]),
             ('page_alloc(ALLOC_ZERO)  // take from head, zero it', C["blue"]),
             ('page_free(pp)            // insert at head', C["blue"]),
             ('page_decref(pp)          // pp_ref--; if 0 -> free', C["blue"])],
            [("pgdir_walk(pgdir, va, create=false)  -> PTE*", C["blue"]),
             ("page_insert(pgdir, pp, va, perm)      // map VA->PA", C["blue"]),
             ("boot_map_region(pgdir, va, size, pa, perm)  // batch map", C["blue"]),
             ("VA 0xF0100ABC -> DIR=0x3C0 TABLE=0x100 OFFSET=0xABC", C["subtext0"]),
             ("-> PA = PTE->ppn << 12 + OFFSET", C["green"])],
            [("KERNBASE = 0xF0000000  // kernel space", C["mauve"]),
             ("ULIM     = 0xEF800000  // user space limit", C["mauve"]),
             ("UTEXT    = 0x00800000  // user code start", C["subtext0"]),
             ("PGSIZE   = 0x1000 (4KB)", C["subtext0"]),
             ("NENV     = 1024         // max environments", C["subtext0"])],
            [("check_page_free_list()           ... PASS", C["green"]),
             ("check_page_alloc()               ... PASS", C["green"]),
             ("check_page()                     ... PASS", C["green"]),
             ("check_kern_pgdir()               ... PASS", C["green"]),
             ("check_page_installed_pgdir()     ... PASS", C["green"]),
             ("mem_init() completed successfully!", C["mauve"])],
        ]
        draws = [self._draw_l2_s0, self._draw_l2_s1, self._draw_l2_s2,
                 self._draw_l2_s3, self._draw_l2_s4]
        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l2_s0(self, W, H):
        self.canvas.create_text(W // 2, 14, text="物理内存布局探测",
                                 fill=C["mauve"], font=FONT_H)

        zones = [("0x00000-0x00FFF  Reserved", C["red"], 0.04),
                 ("0x01000-0x9EFFF  Base Memory (Free)", C["green"], 0.45),
                 ("0x9F000-0x9FFFF  MPENTRY_PADDR", C["peach"], 0.04),
                 ("0xA0000-0xFFFFF  I/O Hole", C["surface2"], 0.30),
                 ("0x100000+  Extended Memory", C["blue"], 3.0)]
        x0, y0, bw = W // 2 - 300, 55, 150
        cy = y0
        total = sum(z[2] for z in zones)
        bh = 260
        for lbl, clr, ratio in zones:
            sh = max(10, (ratio / total) * bh)
            self._round_rect(x0, cy, x0 + bw, cy + sh, 5, fill=clr, outline=clr)
            if sh > 20:
                self.canvas.create_text(x0 + bw // 2, cy + sh // 2, text=lbl,
                                         fill=C["crust"], font=("Microsoft YaHei", 7, "bold"))
            cy += sh

        rx = x0 + bw + 40
        self._shadow_box(rx, 70, 220, 40, "boot_alloc(n)\n早期线性分配器", C["mauve"], C["crust"])
        self._shadow_box(rx, 130, 220, 40, "page_init()\nPageInfo + 空闲链表", C["green"], C["crust"])
        self._shadow_box(rx, 200, 220, 50, "npages = 总物理页数\nnpages_basemem = 低端页数",
                         C["surface0"], C["text"])

    def _draw_l2_s1(self, W, H):
        self.canvas.create_text(W // 2, 14, text="PageInfo 结构体与空闲链表",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 350, 50, 160, 38, "struct PageInfo", C["mauve"], C["crust"])
        self.canvas.create_text(W // 2 - 270, 105, text="pp_link → 下一空闲页\npp_ref  → 引用计数",
                                 fill=C["text"], font=FONT_M)

        px = 80
        for i in range(6):
            st = "free" if i < 4 else "used"
            clr = C["green"] if i < 4 else C["red"]
            self._shadow_box(px + i * 150, 130, 135, 48,
                             "Page {}\n[{}]".format(i, st), clr, C["crust"])
        for i in range(3):
            self._arrow(px + i * 150 + 135, 154, px + (i+1) * 150, 154, C["green"], 2)

        chain = " -> ".join(["Page{}".format(i) for i in range(4)])
        self.canvas.create_text(W // 2, 115, text="page_free_list → {} → NULL".format(chain),
                                 fill=C["green"], font=FONT_M)

        self._box(W // 2 - 250, 210, 500, 60,
                  "page_alloc(ALLOC_ZERO) — 从链表取头，可选清零\npage_free(pp) — 插回链表头部\npage_decref(pp) — 减少引用计数，为 0 则释放",
                  C["surface0"], C["text"], font=FONT_M)

    def _draw_l2_s2(self, W, H):
        self.canvas.create_text(W // 2, 14, text="x86 二级页表：VA → PA 转换流程",
                                 fill=C["mauve"], font=FONT_H)

        self._box(W // 2 - 300, 50, 80, 32, "VA (32-bit)", C["mauve"], C["crust"])
        self._arrow(W // 2 - 215, 66, W // 2 - 155, 66, C["mauve"], 2)

        for lbl, clr, bw in [("[31:22] DIR", C["red"], 90),
                              ("[21:12] TABLE", C["peach"], 90),
                              ("[11:0] OFFSET", C["yellow"], 90)]:
            self._box(W // 2 - 150 if lbl.startswith("[31") else
                      W // 2 - 60 if lbl.startswith("[21") else
                      W // 2 + 30, 42, bw, 52, lbl, clr, C["crust"], font=FONT_B)

        self.canvas.create_text(W // 2, 115, text="CR3 → 页目录 (PDE)", fill=C["red"], font=FONT_B)
        self._box(W // 2 - 80, 130, 160, 28, "PDE → 页表基址", C["red"], C["text"], font=FONT_M)
        self.canvas.create_text(W // 2, 175, text="页表 (PTE)", fill=C["peach"], font=FONT_B)
        self._box(W // 2 - 80, 190, 160, 28, "PTE → 物理页基址", C["peach"], C["text"], font=FONT_M)
        self.canvas.create_text(W // 2, 235, text="+ OFFSET", fill=C["yellow"], font=FONT_B)
        self._arrow(W // 2, 255, W // 2 + 50, 280, C["green"], 2)
        self._shadow_box(W // 2 + 55, 272, 160, 30, "→ 物理地址 PA", C["green"], C["crust"],
                         font=FONT_B)

        self.canvas.create_text(W // 2, 330, text="pgdir_walk(pgdir, va, create) 遍历二级页表，返回 PTE 指针",
                                 fill=C["surface2"], font=FONT_S)

    def _draw_l2_s3(self, W, H):
        self.canvas.create_text(W // 2, 14, text="JOS 虚拟地址空间完整布局 (4GB)",
                                 fill=C["mauve"], font=FONT_H)

        x0, x1, y0 = W // 2 - 240, W // 2 - 20, 48
        bh = 285
        regions = [
            ("0xF0000000  KERNBASE", "内核空间 (RW/--)", 0.0, 0.07, C["mauve"]),
            ("0xEF800000  ULIM", "MMIO (4MB)", 0.07, 0.05, C["blue"]),
            ("0xEF400000  UVPT", "用户只读页表 (4MB)", 0.12, 0.06, C["peach"]),
            ("0xEF000000  UPAGES", "页面信息 (4MB)", 0.18, 0.06, C["yellow"]),
            ("0xEEC00000  UENVS", "环境数组 (4MB)", 0.24, 0.06, C["green"]),
            ("", "用户异常栈", 0.30, 0.03, C["teal"]),
            ("USTACKTOP", "用户栈 (4KB) RW/RW", 0.33, 0.05, C["sky"]),
            ("", "程序数据 & 堆", 0.38, 0.28, C["surface1"]),
            ("0x00800000  UTEXT", "用户代码 R-/R-", 0.66, 0.10, C["green"]),
        ]
        for lbl, desc, sr, sz, clr in regions:
            y = y0 + sr * bh
            sh = max(5, sz * bh)
            tc = C["crust"] if clr != C["surface1"] else C["text"]
            self._round_rect(x0, y, x1, y + sh, 4, fill=clr, outline=clr)
            if sh > 25:
                self.canvas.create_text((x0 + x1) // 2, y + sh // 2,
                                         text=desc, fill=tc,
                                         font=("Microsoft YaHei", 7, "bold"))
            if lbl:
                self.canvas.create_text(x1 + 10, y + sh // 2, text=lbl,
                                         fill=C["subtext1"], font=FONT_S, anchor=tk.W)

    def _draw_l2_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="内存管理自检验证 — 全部通过",
                                 fill=C["mauve"], font=FONT_H)

        checks = [
            ("check_page_free_list()", "✓ 空闲链表结构完整"),
            ("check_page_alloc()", "✓ 分配/释放正确"),
            ("check_page()", "✓ 映射操作正确定"),
            ("check_kern_pgdir()", "✓ 内核页表映射"),
            ("check_page_installed_pgdir()", "✓ 页表切换一致性"),
        ]
        for i, (name, result) in enumerate(checks):
            y = 65 + i * 52
            self._shadow_box(W // 2 - 260, y, 520, 42,
                             "{}      {}".format(name, result),
                             C["green"] if i < 4 else C["mauve"], C["crust"],
                             font=FONT_M)

    # ═══════════════════════════════════════════════════════════════
    # LAB 3:  User Environments & Syscalls  (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab3(self, step):
        infos = [
            ("环境 (Env) 结构体 — JOS 的进程抽象\n\n"
             "  • struct Env 包含：页目录、陷阱帧、状态、父子关系\n"
             "  • env_tf (Trapframe) 保存完整寄存器快照\n"
             "  • env_pgdir 指向环境的独立页目录\n"
             "  • env_status：FREE / DYING / RUNNABLE / RUNNING / NOT_RUNNABLE\n"
             "  • ENV_CREATE(binary, type) 宏便捷创建环境"),
            ("环境生命周期状态机\n\n"
             "  • FREE：环境槽位空闲，等待 env_alloc() 分配\n"
             "  • NOT_RUNNABLE：已分配但不可运行 (如刚 fork 的子进程)\n"
             "  • RUNNABLE：就绪态，由调度器 sched_yield() 选中执行\n"
             "  • RUNNING：当前正在 CPU 上执行 (curenv 指向它)\n"
             "  • DYING：已销毁或异常终止，等待回收"),
            ("中断描述符表 (IDT) 与陷阱处理\n\n"
             "  • trap_init() 使用 SETGATE 宏配置 256 条目 IDT\n"
             "  • 异常 0-19 号：除零、断点、GP 故障、页面错误等\n"
             "  • T_SYSCALL (0x30)：系统调用门，DPL=3 允许用户态触发\n"
             "  • Trapframe 在栈上保存完整上下文\n"
             "  • trap_dispatch(tf) 根据 tf_trapno 分发到具体 handler"),
            ("系统调用完整流程\n\n"
             "  ① 用户程序调用 sys_cputs() (lib/syscall.c)\n"
             "  ② 系统调用号放入 eax，参数放入 edx/ecx/ebx/edi/esi\n"
             "  ③ 执行 int $T_SYSCALL → CPU 切换到内核栈\n"
             "  ④ trap_dispatch() 识别 T_SYSCALL → 调用 syscall()\n"
             "  ⑤ syscall() 根据调用号 switch 分派到具体内核函数\n"
             "  ⑥ 返回值存入 tf->reg_eax，iret 返回用户态"),
            ("用户程序执行与异常处理\n\n"
             "  • user/hello.c 通过 cprintf → sys_cputs 输出 \"hello, world\"\n"
             "  • 除零异常：int a = 1/0 → CPU Divide Error → env_destroy()\n"
             "  • 页面错误：*(int*)0xBAD → Page Fault → page_fault_handler()\n"
             "  • user_mem_assert() 验证所有用户态指针合法性\n"
             "  • 内核通过 env_destroy() 安全终止异常环境"),
        ]
        terms = [
            [("ENV_CREATE(user_hello, ENV_TYPE_USER);", C["blue"]),
             ("ENV_CREATE(fs_fs,     ENV_TYPE_FS);", C["blue"]),
             ("ENV_CREATE(net_ns,    ENV_TYPE_NS);", C["blue"]),
             ("sched_yield();  // start scheduling", C["mauve"]),
             ("hello, world", C["green"]),
             ("i am environment 00001000", C["subtext0"])],
            [("env_alloc() -> Env 00001001 created", C["green"]),
             ("env_status: NOT_RUNNABLE", C["subtext0"]),
             ("sys_env_set_status(RUNNABLE)", C["blue"]),
             ("sched_yield() -> env_run(00001001)", C["mauve"]),
             ("Env 00001001 now RUNNING on CPU 0", C["green"])],
            [("trap_init(): configuring 256 IDT entries...", C["blue"]),
             ("SETGATE(idt[T_DIVIDE], 0, GD_KT, divide_handler, 0)", C["mauve"]),
             ("SETGATE(idt[T_SYSCALL], 0, GD_KT, syscall_handler, 3)", C["mauve"]),
             ("SETGATE(idt[T_PGFLT], 0, GD_KT, pgflt_handler, 0)", C["mauve"]),
             ("IDT register loaded (lidt)", C["green"])],
            [("User: mov $SYS_cputs, %eax", C["subtext0"]),
             ("User: int $0x30           # TRAP!", C["red"]),
             ("Kernel: trap_dispatch() -> T_SYSCALL", C["blue"]),
             ("Kernel: syscall() -> sys_cputs()", C["blue"]),
             ("Kernel: cputchar('h') cputchar('e') cputchar('l') ...", C["blue"]),
             ("Kernel: iret -> back to user mode", C["green"])],
            [("user/hello.c: cprintf(\"hello, world\\n\");", C["blue"]),
             ("  -> lib/syscall.c: sys_cputs(s, 13)", C["subtext0"]),
             ("  -> int $0x30 -> trap -> sys_cputs()", C["subtext0"]),
             ("hello, world", C["green"]),
             ("divzero: int a = 1/0;", C["red"]),
             ("  !! Divide Error (trap 0) -> env destroyed", C["red"])],
        ]
        draws = [self._draw_l3_s0, self._draw_l3_s1, self._draw_l3_s2,
                 self._draw_l3_s3, self._draw_l3_s4]
        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l3_s0(self, W, H):
        self.canvas.create_text(W // 2, 14, text="Env 结构体 — JOS 的进程模型",
                                 fill=C["mauve"], font=FONT_H)
        self._shadow_box(W // 2 - 350, 50, 180, 36, "struct Env", C["mauve"], C["crust"])

        fields = [("env_tf (Trapframe)", "寄存器快照", C["red"]),
                  ("env_pgdir (pde_t*)", "页目录物理地址", C["peach"]),
                  ("env_id / env_parent_id", "唯一ID / 父环境ID", C["yellow"]),
                  ("env_status", "FREE/DYING/RUNNABLE/RUNNING", C["green"]),
                  ("env_type", "USER / FS / NS", C["blue"]),
                  ("env_pgfault_upcall", "用户态缺页回调", C["mauve"])]
        for i, (fld, desc, clr) in enumerate(fields):
            y = 100 + i * 25
            self._round_rect(W // 2 - 350, y, W // 2 - 160, y + 20, 4, fill=clr, outline=clr)
            self.canvas.create_text(W // 2 - 255, y + 10, text=fld, fill=C["crust"], font=FONT_S)
            self.canvas.create_text(W // 2 - 145, y + 10, text=desc, fill=C["text"],
                                     font=("Microsoft YaHei", 7), anchor=tk.W)

        self._box(W // 2 + 40, 80, 310, 110, "",
                  C["surface0"], "", outline=C["mauve"])
        code = ("ENV_CREATE(user_hello, ENV_TYPE_USER);\n"
                "ENV_CREATE(fs_fs,     ENV_TYPE_FS);\n"
                "ENV_CREATE(net_ns,    ENV_TYPE_NS);\n"
                "sched_yield();  // begin scheduling")
        self.canvas.create_text(W // 2 + 195, 140, text=code, fill=C["green"], font=FONT_M)

    def _draw_l3_s1(self, W, H):
        self.canvas.create_text(W // 2, 14, text="环境生命周期状态机",
                                 fill=C["mauve"], font=FONT_H)

        states = [("FREE", 100, 80, C["surface1"]),
                  ("NOT_RUNNABLE", 330, 48, C["red"]),
                  ("RUNNABLE", 330, 180, C["yellow"]),
                  ("RUNNING", 100, 260, C["green"]),
                  ("DYING", 560, 180, C["peach"])]
        for name, x, y, clr in states:
            self._shadow_box(x, y, 120, 40, name, clr, C["crust"], font=FONT_B)

        edges = [(160, 100, 330, 68, "env_alloc()", C["mauve"]),
                 (390, 88, 390, 180, "set_status()", C["green"]),
                 (390, 200, 220, 280, "env_run()", C["blue"]),
                 (220, 280, 160, 100, "sched_yield()", C["yellow"]),
                 (390, 200, 560, 200, "env_destroy()", C["red"])]
        for x1, y1, x2, y2, lbl, clr in edges:
            self._arrow(x1, y1, x2, y2, clr, 2)
            self.canvas.create_text((x1 + x2) // 2 + 15, (y1 + y2) // 2 - 6,
                                     text=lbl, fill=clr, font=("Microsoft YaHei", 7))

    def _draw_l3_s2(self, W, H):
        self.canvas.create_text(W // 2, 14, text="IDT 中断描述符表与陷阱处理流程",
                                 fill=C["mauve"], font=FONT_H)

        entries = [("0", "Divide Error", C["red"]), ("3", "Breakpoint", C["peach"]),
                   ("13", "GP Fault", C["yellow"]), ("14", "Page Fault", C["green"]),
                   ("0x30", "SYSCALL", C["mauve"])]
        x0 = W // 2 - 360
        for i, (num, name, clr) in enumerate(entries):
            y = 55 + i * 35
            self._round_rect(x0, y, x0 + 60, y + 27, 4, fill=clr, outline=clr)
            self.canvas.create_text(x0 + 30, y + 13, text=num, fill=C["crust"],
                                     font=FONT_B)
            self.canvas.create_text(x0 + 75, y + 13, text=name, fill=C["text"],
                                     font=FONT, anchor=tk.W)

        rx = x0 + 220
        self._box(rx, 55, 170, 34, "trapentry.S\n256 个汇编入口", C["surface0"], C["text"], font=FONT_M)
        self._arrow(x0 + 60, 68, rx, 72, C["mauve"], 2)
        self._box(rx, 118, 170, 34, "trap() [trap.c]\n保存 Trapframe", C["surface0"], C["text"], font=FONT_M)
        self._arrow(rx + 85, 89, rx + 85, 118, C["mauve"], 2)
        self._box(rx, 182, 170, 34, "trap_dispatch()\n按类型分派", C["surface0"], C["text"], font=FONT_M)
        self._arrow(rx + 85, 152, rx + 85, 182, C["mauve"], 2)

        for name, y in [("syscall()", 235), ("page_fault_handler()", 275)]:
            self._box(rx, y, 170, 28, name, C["mauve"], C["crust"], font=FONT_M)

    def _draw_l3_s3(self, W, H):
        self.canvas.create_text(W // 2, 14, text="系统调用完整执行流程",
                                 fill=C["mauve"], font=FONT_H)

        steps = [("① User\ncall sys_cputs", C["red"], 40),
                 ("② eax=call#\nargs→regs", C["peach"], 155),
                 ("③ int $0x30\nCPU 切换栈", C["yellow"], 270),
                 ("④ trap_dispatch\n→ syscall()", C["green"], 385),
                 ("⑤ switch(#)\n内核函数", C["blue"], 500),
                 ("⑥ iret\n返回用户", C["mauve"], 615)]
        for lbl, clr, x in steps:
            self._shadow_box(x, 55, 110, 48, lbl, clr, C["crust"])

        for i in range(len(steps) - 1):
            self._arrow(steps[i][3] + 110, 79, steps[i + 1][3], 79, C["mauve"], 2)

        self._box(W // 2 - 200, 150, 400, 90, "", C["surface0"], "", outline=C["mauve"])
        syscalls = [
            "SYS_cputs(0) → sys_cputs()    控制台输出",
            "SYS_cgetc(1) → sys_cgetc()    读取字符",
            "SYS_getenvid(2) → sys_getenvid()  环境ID",
            "SYS_page_alloc(5) → sys_page_alloc()  分配页",
            "SYS_exofork(8) → sys_exofork()   创建子环境",
        ]
        for i, line in enumerate(syscalls):
            self.canvas.create_text(W // 2, 168 + i * 17, text=line,
                                     fill=C["text"] if "→" not in line else C["green"],
                                     font=FONT_S)

    def _draw_l3_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="用户程序运行与异常处理演示",
                                 fill=C["mauve"], font=FONT_H)

        self._box(W // 2 - 350, 50, 340, 160, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2 - 180, 68, text="user/hello.c 执行路径",
                                 fill=C["mauve"], font=FONT_B)
        lines = ['cprintf("hello, world\\n");', "  -> lib/printf.c: vcprintf()",
                 "  -> lib/syscall.c: sys_cputs(s, len)", "  -> int $0x30  (SYSCALL!)",
                 "  -> kern/syscall.c: sys_cputs()", "  -> kern/console.c: cputchar()"]
        for i, l in enumerate(lines):
            cl = C["green"] if "->" in l else C["text"]
            self.canvas.create_text(W // 2 - 335, 90 + i * 18, text=l, fill=cl,
                                     font=FONT_S, anchor=tk.W)

        self._box(W // 2 + 30, 50, 320, 160, "", C["surface0"], "", outline=C["red"])
        self.canvas.create_text(W // 2 + 190, 68, text="异常演示",
                                 fill=C["red"], font=FONT_B)
        exc = ["除零异常:  int a = 1/0;", "  -> CPU: Divide Error (trap 0)",
               "  -> trap_dispatch -> env_destroy()", "",
               "页面错误:  *(int*)0xBAD = 1;", "  -> CPU: Page Fault (trap 14)",
               "  -> page_fault_handler()", "  -> env_destroy() (无 handler)"]
        for i, l in enumerate(exc):
            self.canvas.create_text(W // 2 + 45, 90 + i * 18, text=l, fill=C["text"],
                                     font=FONT_S, anchor=tk.W)

    # ═══════════════════════════════════════════════════════════════
    # LAB 4: Multitasking & IPC (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab4(self, step):
        infos = [
            ("SMP：对称多处理器架构\n\n"
             "  • mp_init() 检测 MP 配置表获取 CPU 数量和 APIC 信息\n"
             "  • boot_aps() 通过 LAPIC 发送 INIT-SIPI IPI 依次启动 AP\n"
             "  • 每个 CPU 拥有独立的内核栈 (KSTACKSIZE=64KB) 和 TSS\n"
             "  • 大内核锁 (Big Kernel Lock)：全局自旋锁保护内核临界区\n"
             "  • BSP 和所有 AP 初始化完成后各自调用 sched_yield()"),
            ("轮转调度算法 (Round-Robin)\n\n"
             "  • sched_yield() 从当前 env 之后的位置开始轮询\n"
             "  • 找到第一个 env_status==RUNNABLE 的环境执行 env_run()\n"
             "  • env_run(e)：设置 curenv、切换页目录 (lcr3)、恢复寄存器\n"
             "  • 无就绪环境 → sched_halt()：释放大内核锁、sti; hlt\n"
             "  • 最多支持 NENV=1024 个环境，每个运行一个时间片"),
            ("Copy-on-Write Fork 写时复制\n\n"
             "  • sys_exofork()：创建子环境 (标记为 NOT_RUNNABLE)\n"
             "  • duppage()：将父子可写页标记 PTE_COW + 只读\n"
             "  • 子进程写入 COW 页 → CPU 触发 Page Fault (trap 14)\n"
             "  • pgfault handler 检测 PTE_COW 标志 → 分配新物理页\n"
             "  • 复制原页数据 → 重映射为可写 (清除 COW 位) → 父子独立"),
            ("页面级进程间通信 (IPC)\n\n"
             "  • JOS 实现独特的页面级 IPC：发送方映射一整页到接收方\n"
             "  • sys_ipc_try_send(envid, value, srcva, perm)：尝试发送\n"
             "  • sys_ipc_recv(dstva)：阻塞等待接收 IPC\n"
             "  • 内核检查接收方 env_ipc_recving==true 时完成传递\n"
             "  • FS Server 和 NS Server 通过 IPC 提供服务"),
            ("IPC 应用示例\n\n"
             "  • pingpong：两个环境通过 IPC 互相发送消息\n"
             "  • primes：埃拉托色尼筛法，通过 IPC 管道实现素数筛选\n"
             "  • forktree：创建多层进程树，展示 COW Fork 正确性\n"
             "  • FS Server Request-Response 模式：ipc_send → ipc_recv"),
        ]
        terms = [
            [("mp_init(): scanning MP configuration table...", C["blue"]),
             ("SMP: CPU 0 (BSP) starting", C["green"]),
             ("SMP: CPU 1 starting", C["green"]),
             ("SMP: CPU 2 starting", C["green"]),
             ("SMP: CPU 3 starting", C["green"])],
            [("sched_yield(): scanning envs[] from index 1...", C["blue"]),
             ("  envs[2].env_status = RUNNABLE", C["green"]),
             ("env_run(envs[2]): lcr3(pgdir) -> env_pop_tf()", C["mauve"]),
             ("curenv = envs[2]", C["subtext0"]),
             ("No runnable -> sched_halt(): unlock, sti, hlt", C["yellow"])],
            [("sys_exofork(): child Env 00002001 created", C["blue"]),
             ("duppage(): marking pages PTE_COW for parent & child", C["blue"]),
             ("child: write to COW page -> PAGE FAULT!", C["red"]),
             ("pgfault: detected PTE_COW, allocating new page...", C["mauve"]),
             ("pgfault: page copied, remapped writable", C["green"])],
            [("sys_ipc_recv(dstva): env_ipc_recving = true, block", C["blue"]),
             ("sys_ipc_try_send(to, value=42, srcva, perm)", C["mauve"]),
             ("Kernel: env_ipc_recving == true -> delivering IPC", C["green"]),
             ("Kernel: page mapped to dstva, value=42 delivered", C["green"]),
             ("Receiver: sys_ipc_recv returns (from=..., value=42)", C["subtext0"])],
            [("forktree: I am '0'   (env 1001)", C["green"]),
             ("forktree: I am '00'  (env 1002)", C["green"]),
             ("forktree: I am '01'  (env 1003)", C["green"]),
             ("pingpong: 0 received ping from 1", C["blue"]),
             ("pingpong: 1 received pong from 0", C["blue"])],
        ]
        draws = [self._draw_l4_s0, self._draw_l4_s1, self._draw_l4_s2,
                 self._draw_l4_s3, self._draw_l4_s4]
        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l4_s0(self, W, H):
        self.canvas.create_text(W // 2, 14, text="SMP 对称多处理器架构",
                                 fill=C["mauve"], font=FONT_H)
        for i in range(4):
            cx = 120 + i * 220
            lbl = "CPU {} (BSP)".format(i) if i == 0 else "CPU {} (AP)".format(i)
            self._shadow_box(cx, 55, 190, 60, lbl, C["mauve"], C["crust"])
            self._shadow_box(cx, 130, 190, 26, "Kernel Stack [{}] (64KB)".format(i),
                             C["surface0"], C["text"], font=FONT_S)
            self._shadow_box(cx, 162, 190, 26, "TSS [{}] (per-CPU)".format(i),
                             C["surface0"], C["text"], font=FONT_S)

        self._shadow_box(W // 2 - 160, 215, 320, 45,
                         "spin_lock(&kernel_lock);    // enter\nspin_unlock(&kernel_lock);  // leave",
                         C["red"], C["crust"], font=FONT_S)
        self.canvas.create_text(W // 2, 280, text="Big Kernel Lock — 全局自旋锁保护内核临界区",
                                 fill=C["peach"], font=FONT_B)

    def _draw_l4_s1(self, W, H):
        self.canvas.create_text(W // 2, 14, text="Round-Robin 轮转调度算法",
                                 fill=C["mauve"], font=FONT_H)
        sts = ["RUNNABLE", "RUNNING", "RUNNABLE", "DYING", "RUNNABLE"]
        clrs = [C["green"], C["yellow"], C["green"], C["peach"], C["green"]]
        for i in range(5):
            self._shadow_box(60 + i * 170, 65, 150, 50,
                             "Env {}\n[{}]".format(i, sts[i]),
                             clrs[i], C["crust"], font=FONT_B)

        self._arrow(210, 90, 230, 90, C["mauve"], 2)
        self._arrow(380, 90, 480, 110, C["mauve"], 2, dash=(4, 4))

        self._box(W // 2 - 220, 155, 440, 60, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2, 172, text="sched_yield(): for i in 0..NENV → find RUNNABLE → env_run(e)",
                                 fill=C["text"], font=FONT_M)
        self.canvas.create_text(W // 2, 195, text="No RUNNABLE? sched_halt() → unlock + sti + hlt (waiting for interrupt)",
                                 fill=C["yellow"], font=FONT_S)

    def _draw_l4_s2(self, W, H):
        self.canvas.create_text(W // 2, 14, text="Copy-on-Write Fork 写时复制原理",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 340, 50, 130, 38, "父进程", C["mauve"], C["crust"])
        self._shadow_box(W // 2 + 210, 50, 130, 38, "子进程", C["green"], C["crust"])

        for i, (px, clr) in enumerate([(W // 2 - 330, C["red"]),
                                         (W // 2 - 200, C["peach"]),
                                         (W // 2 - 70, C["yellow"])]):
            self._shadow_box(px, 102, 110, 42, "Page {}\nPTE_COW".format(chr(65+i)),
                             clr, C["crust"], font=FONT_S)
            self._shadow_box(px + 540, 102, 110, 42, "Page {}'\n(same PA)".format(chr(65+i)),
                             clr, C["crust"], font=FONT_S)
            self._arrow(px + 55, 144, px + 540 + 55, 144, C["surface2"], 1, dash=(4, 4))

        self._box(W // 2 - 220, 175, 440, 105, "", C["surface0"], "", outline=C["green"])
        flow = ["1. duppage(): 所有可写页标记 PTE_COW，父子均只读",
                "2. 子进程写入 → CPU Page Fault!", "3. pgfault handler 检测 PTE_COW",
                "4. 分配新物理页 → 复制数据 → 重映射为可写", "5. 父子进程拥有各自独立页面副本"]
        for i, line in enumerate(flow):
            self.canvas.create_text(W // 2, 192 + i * 18, text=line,
                                     fill=C["text"], font=FONT_S)

    def _draw_l4_s3(self, W, H):
        self.canvas.create_text(W // 2, 14, text="页面级 IPC：进程间通信",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 330, 50, 140, 45, "发送方 Env A", C["mauve"], C["crust"])
        self._shadow_box(W // 2 + 190, 50, 140, 45, "接收方 Env B", C["green"], C["crust"])

        self._box(W // 2 - 330, 115, 140, 42,
                  "sys_ipc_try_send(\n  envid, value,\n  srcva, perm)",
                  C["red"], C["text"], font=FONT_S)
        self._box(W // 2 + 190, 115, 140, 42,
                  "sys_ipc_recv(dstva)\n阻塞等待",
                  C["green"], C["text"], font=FONT_S)

        self._arrow(W // 2 - 185, 136, W // 2 + 185, 136, C["mauve"], 3)
        self.canvas.create_text(W // 2, 98, text="value + 页面映射", fill=C["yellow"], font=FONT_B)

        self._box(W // 2 - 280, 180, 560, 130, "", C["surface0"], "", outline=C["mauve"])
        ipc = ["1. Env B: sys_ipc_recv() → env_ipc_recving=true → 阻塞",
               "2. Env A: sys_ipc_try_send(B, val, srcva, perm)",
               "3. Kernel: env_ipc_recving == true? → 传递",
               "4. Kernel: 页面映射到 B 的 dstva, ipc_value=val",
               "5. Kernel: 唤醒 B (RUNNABLE), A 返回 0",
               "6. Env B: sys_ipc_recv() 返回，获得 value 和映射"]
        for i, line in enumerate(ipc):
            self.canvas.create_text(W // 2, 197 + i * 18, text=line,
                                     fill=C["text"], font=FONT_S)

    def _draw_l4_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="IPC 应用：微内核服务模式",
                                 fill=C["mauve"], font=FONT_H)

        demos = [("pingpong", "双向 IPC\n消息交换", C["red"]),
                 ("primes", "埃拉托色尼\n素数筛 IPC", C["peach"]),
                 ("forktree", "进程树\nCOW Fork 测试", C["yellow"]),
                 ("FS Server", "文件系统\nIPC 请求响应", C["green"])]
        for i, (name, desc, clr) in enumerate(demos):
            self._shadow_box(100 + i * 230, 60, 200, 80,
                             "{}\n{}".format(name, desc), clr, C["crust"],
                             font=("Microsoft YaHei", 9, "bold"))

        self._box(W // 2 - 280, 180, 560, 90, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2, 196, text="FS Server IPC 请求-响应模式",
                                 fill=C["mauve"], font=FONT_B)
        fsr = ["apps -> ipc_send(fs_env, REQ_OPEN, &fsipcbuf, perm)",
               "FS Server -> ipc_recv() -> serve_open() -> … -> ipc_send(result)",
               "apps -> ipc_recv() 获得返回值"]
        for i, l in enumerate(fsr):
            self.canvas.create_text(W // 2, 215 + i * 18, text=l, fill=C["text"], font=FONT_S)

    # ═══════════════════════════════════════════════════════════════
    # LAB 5: File System & Shell (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab5(self, step):
        infos = [
            ("文件系统架构与磁盘布局\n\n"
             "  • 微内核设计：FS 作为用户态服务进程运行 (ENV_TYPE_FS)\n"
             "  • 用户程序 ↔ FS Server (IPC) ↔ IDE 磁盘驱动\n"
             "  • 磁盘布局：Block0(Boot) | Block1(Super) | Block2+(Bitmap) | Data\n"
             "  • Super Block 包含：s_magic(FS_MAGIC), s_nblocks, s_root\n"
             "  • File 结构：f_name[128], f_size, f_type, f_direct[10], f_indirect"),
            ("核心文件与目录操作函数\n\n"
             "  • alloc_block()：在 bitmap 中扫描空闲块，设置标记并返回块号\n"
             "  • file_block_walk(f, blockno, alloc)：定位文件第 N 个块指针\n"
             "  • file_get_block(f, blockno)：获取文件块（按需分配、按需读取）\n"
             "  • dir_lookup(dir, name, *file)：在目录 entry 中遍历查找文件名\n"
             "  • file_read() / file_write()：跨块读写，通过 file_get_block"),
            ("FS Server 文件系统服务协议\n\n"
             "  • FSREQ_OPEN：打开文件，返回文件描述符 FD\n"
             "  • FSREQ_READ：从 FD 读取指定字节数\n"
             "  • FSREQ_WRITE：向 FD 写入数据\n"
             "  • FSREQ_STAT：获取文件元信息 (大小、类型)\n"
             "  • FSREQ_FLUSH：将脏块缓存写回磁盘\n"
             "  • fsipcbuf 共享内存页：用户与 FS Server 的数据交换区"),
            ("Spawn：从文件系统加载进程\n\n"
             "  • spawn(prog, argv)：加载磁盘上的 ELF 可执行文件创建新环境\n"
             "  • 流程：sys_exofork() → init_stack(argc/argv) → map_segment(ELF 段)\n"
             "  • copy_shared_pages() → set_trapframe(eip) → set_status(RUNNABLE)\n"
             "  • 与 fork() 区别：Spawn 加载新程序，不需要 COW\n"
             "  • Shell 通过 spawn() 来运行用户输入的命令"),
            ("Shell 功能：管道与重定向\n\n"
             "  • 内置命令：ls / cat / echo / mkdir / rm 等\n"
             "  • 输入重定向 < ：cat < file → 打开 file 为 stdin (FD 0)\n"
             "  • 输出重定向 > ：cat > file → 打开 file 为 stdout (FD 1)\n"
             "  • 管道 | ：fork 两个进程 → pipe() → stdout→写端 / stdin←读端\n"
             "  • 两个子进程并行执行，通过 pipe buffer 传递数据"),
        ]
        terms = [
            [("fs_init(): reading super block...", C["blue"]),
             ("Super: s_magic=0x4D5F53, s_nblocks=1024", C["green"]),
             ("fs_init(): bitmap loaded", C["green"]),
             ("Root dir: 'lorem', 'newfile', 'httpd' ...", C["subtext0"])],
            [("alloc_block(bitmap) -> block 42", C["green"]),
             ("file_block_walk(f, 0, alloc=true) -> &f_direct[0]", C["blue"]),
             ("file_get_block(f, 1) -> block 128 (from indirect)", C["blue"]),
             ("dir_lookup(root, \"lorem\", &file) -> found!", C["green"])],
            [("User: ipc_send(fs_env, FSREQ_OPEN, \"lorem\", perm)", C["blue"]),
             ("FS:   ipc_recv() -> req_type=FSREQ_OPEN", C["blue"]),
             ("FS:   serve_open() -> FD 3", C["green"]),
             ("FS:   ipc_send(user, FD=3)", C["green"]),
             ("User: ipc_recv() got FD=3", C["subtext0"])],
            [("Shell: spawn(\"echo\", [\"echo\", \"hello\"])", C["blue"]),
             ("  sys_exofork() -> child env 00003001", C["subtext0"]),
             ("  init_stack(): argc=2, argv=[\"echo\", \"hello\"]", C["subtext0"]),
             ("  map_segment(): loading ELF .text/.data", C["subtext0"]),
             ("  set_trapframe(entry_eip=0x800020)", C["subtext0"]),
             ("  set_status(RUNNABLE) -> child starts!", C["green"])],
            [("$ ls", C["mauve"]),
             ("lorem  newfile  httpd  test", C["subtext0"]),
             ("$ cat lorem | cat", C["mauve"]),
             ("  -> fork: pipe created (fds 3 & 4)", C["blue"]),
             ("  -> child1: stdout->pipe write end", C["blue"]),
             ("  -> child2: stdin<-pipe read end", C["blue"]),
             ("  (two children running in parallel)", C["subtext0"])],
        ]
        draws = [self._draw_l5_s0, self._draw_l5_s1, self._draw_l5_s2,
                 self._draw_l5_s3, self._draw_l5_s4]
        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l5_s0(self, W, H):
        self.canvas.create_text(W // 2, 14, text="文件系统架构：微内核 + FS Server",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 350, 50, 160, 38, "用户程序", C["mauve"], C["crust"])
        self._arrow(W // 2 - 185, 69, W // 2 - 95, 69, C["mauve"], 2)
        self._shadow_box(W // 2 - 90, 45, 180, 48, "FS Server\n(用户态服务进程)", C["blue"], C["crust"])
        self.canvas.create_text(W // 2, 82, text="IPC 页面级通信", fill=C["yellow"], font=FONT)
        self._arrow(W // 2 + 5, 104, W // 2 + 75, 112, C["mauve"], 2)
        self._shadow_box(W // 2 + 80, 102, 160, 35, "IDE 磁盘驱动 (内核)", C["green"], C["crust"])

        self._hline(W // 2 - 350, W // 2 + 240, 155)

        disk = [("Block 0\nBoot", 50, C["red"], W // 2 - 320),
                ("Block 1\nSuper", 50, C["peach"], W // 2 - 260),
                ("Block 2+\nBitmap", 65, C["yellow"], W // 2 - 200),
                ("...\nData Blocks\n(Files + Dirs)", 200, C["green"], W // 2 - 125)]
        for lbl, wb, clr, x in disk:
            self._shadow_box(x, 175, wb, 58, lbl, clr, C["crust"], font=FONT_S)

        self._box(W // 2 - 280, 265, 560, 30,
                  "struct File { f_name[128], f_size, f_type, f_direct[10], f_indirect }",
                  C["surface0"], C["text"], font=FONT_M)

    def _draw_l5_s1(self, W, H):
        self.canvas.create_text(W // 2, 14, text="核心文件与目录操作函数",
                                 fill=C["mauve"], font=FONT_H)

        funcs = [("alloc_block()", "扫描 bitmap 找空闲块", C["red"]),
                 ("file_block_walk(f,n,alloc)", "定位文件第 n 个块指针", C["peach"]),
                 ("file_get_block(f,n)", "获取/分配第 n 块", C["yellow"]),
                 ("dir_lookup(dir,name,&f)", "目录中按名查找文件", C["green"]),
                 ("file_read(f,buf,n,off)", "跨块读取 n 字节", C["blue"]),
                 ("file_write(f,buf,n,off)", "跨块写入 n 字节", C["mauve"])]
        x0 = W // 2 - 380
        for i, (name, desc, clr) in enumerate(funcs):
            x = x0 + (i % 3) * 265
            y = 55 + (i // 3) * 120
            self._shadow_box(x, y, 240, 95, "{}\n{}".format(name, desc),
                             clr, C["crust"], font=FONT_M)

    def _draw_l5_s2(self, W, H):
        self.canvas.create_text(W // 2, 14, text="FS Server IPC 服务协议",
                                 fill=C["mauve"], font=FONT_H)

        ops = [("FSREQ_OPEN", "打开文件 → FD", C["red"]),
               ("FSREQ_READ", "从 FD 读取", C["peach"]),
               ("FSREQ_WRITE", "向 FD 写入", C["yellow"]),
               ("FSREQ_STAT", "获取文件状态", C["green"]),
               ("FSREQ_FLUSH", "刷新脏块到磁盘", C["blue"]),
               ("FSREQ_REMOVE", "删除文件", C["mauve"])]
        x0 = W // 2 - 380
        for i, (op, desc, clr) in enumerate(ops):
            x = x0 + (i % 3) * 265
            y = 55 + (i // 3) * 100
            self._shadow_box(x, y, 240, 72, "{}\n{}".format(op, desc),
                             clr, C["crust"], font=FONT_B)

        self._box(W // 2 - 260, 275, 520, 28,
                  "flush_block(): 脏块写回 IDE  |  bc_pgfault(): 缺页驱动的按需磁盘读取",
                  C["surface0"], C["text"], font=FONT_M)

    def _draw_l5_s3(self, W, H):
        self.canvas.create_text(W // 2, 14, text="Spawn：从文件系统加载并创建进程",
                                 fill=C["mauve"], font=FONT_H)

        steps_s = [("sys_exofork()", C["red"]), ("init_stack()", C["peach"]),
                   ("map_segment()", C["yellow"]), ("copy_shared()", C["green"]),
                   ("set_trapframe()", C["blue"]), ("set_status()", C["mauve"])]
        for i, (name, clr) in enumerate(steps_s):
            x = 40 + i * 140
            self._shadow_box(x, 55, 125, 48, name, clr, C["crust"], font=FONT_B)
            if i < len(steps_s) - 1:
                self._arrow(x + 125, 79, x + 140, 79, C["mauve"], 2)

        self._box(W // 2 - 220, 130, 440, 110, "", C["surface0"], "", outline=C["green"])
        sl = ["Spawn vs Fork:", "  Fork: 复制当前进程 (代码+数据+栈+页表), 需要 COW",
              "  Spawn: 从磁盘加载新的 ELF 可执行文件", "  Spawn: 新地址空间，无需 COW，设置全新栈",
              "  Shell 通过 spawn() 运行用户输入的命令"]
        for i, l in enumerate(sl):
            self.canvas.create_text(W // 2, 148 + i * 18, text=l, fill=C["text"], font=FONT_S)

    def _draw_l5_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="Shell：管道与重定向",
                                 fill=C["mauve"], font=FONT_H)

        self._box(W // 2 - 370, 48, 290, 260, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2 - 225, 66, text="Shell 命令", fill=C["mauve"], font=FONT_B)
        cmds = ["$ ls", "$ cat lorem", "$ echo hello", "$ mkdir test",
                "$ rm file", "$ testfile", "$ forktree", "$ pingpong", "$ primes"]
        for i, cmd in enumerate(cmds):
            self.canvas.create_text(W // 2 - 355, 88 + i * 20, text=cmd,
                                     fill=C["green"], font=FONT_M, anchor=tk.W)

        self._box(W // 2 - 60, 48, 430, 260, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2 + 155, 66, text="管道与重定向", fill=C["mauve"], font=FONT_B)
        pl = ["输入重定向:  cat < lorem", "  -> open lorem 作为 stdin (FD 0)", "",
              "输出重定向:  cat lorem > newfile", "  -> open newfile 作为 stdout (FD 1)", "",
              "管道:  cat lorem | cat", "  -> fork 两个子进程", "  -> pipe() 创建一对 FD",
              "  -> 左边 stdout → pipe[1]", "  -> 右边 stdin  ← pipe[0]", "  -> 两进程并行执行"]
        for i, l in enumerate(pl):
            self.canvas.create_text(W // 2 - 42, 88 + i * 20, text=l,
                                     fill=C["text"], font=FONT_S, anchor=tk.W)

    # ═══════════════════════════════════════════════════════════════
    # LAB 6: Network Driver (5 steps)
    # ═══════════════════════════════════════════════════════════════
    def _lab6(self, step):
        infos = [
            ("网络子系统整体架构\n\n"
             "  • PCI 总线扫描 → 检测 Intel E1000 网卡 (Vendor: 0x8086)\n"
             "  • 数据流：外部网络 ↔ QEMU NAT ↔ E1000 ↔ input/output ↔ NS ↔ HTTP\n"
             "  • NS (Network Server)：用户态服务，集成了 lwIP TCP/IP 协议栈\n"
             "  • 网络处理完全在用户态运行，内核只提供最小的包收发系统调用"),
            ("E1000 网卡驱动：描述符环形缓冲区\n\n"
             "  • pci_init() 扫描 PCI 总线，找到 E1000 并映射 BAR 寄存器\n"
             "  • TX Descriptor Ring：发包环形缓冲区 + 描述符链表\n"
             "  • RX Descriptor Ring：收包环形缓冲区 + 描述符链表\n"
             "  • e1000_transmit(pkt, len)：写入发送环，更新 TDT\n"
             "  • e1000_receive(pkt, &len)：从接收环读取，更新 RDT\n"),
            ("网络数据包流转路径\n\n"
             "  • Input 进程：循环调用 sys_pkt_recv() 从 E1000 收包\n"
             "  • Input → NS：通过 IPC NSREQ_INPUT 将包递给 lwIP 协议栈\n"
             "  • NS 服务：lwIP 处理 TCP/IP 协议，解包到 socket\n"
             "  • HTTP Server：通过 socket API 接收/发送应用数据\n"
             "  • Output 进程：通过 IPC NSREQ_OUTPUT 从 NS 获取要发送的包"),
            ("lwIP 轻量级 TCP/IP 协议栈\n\n"
             "  • NS 服务启动时初始化 lwIP 协议栈\n"
             "  • 协议栈分层：ARP(链路) → IP(网络) → TCP/UDP(传输) → Socket(应用)\n"
             "  • 提供标准 BSD Socket API：socket/bind/listen/accept/send/recv\n"
             "  • DHCP 自动获取 IP 地址：MAC=52:54:00:12:34:56 → IP=10.0.2.15"),
            ("HTTP Web 服务器\n\n"
             "  • user/httpd.c：简单的 HTTP/1.0 Web 服务器\n"
             "  • socket() → bind(80) → listen() → accept() 循环\n"
             "  • 解析 GET 请求 → 打开对应文件 → 构建 HTTP 200 响应\n"
             "  • QEMU 端口转发：外部 TCP 26080 → JOS 内部 80\n"
             "  • 浏览器访问 http://localhost:26080/ 查看 JOS 服务的内容"),
        ]
        terms = [
            [("pci_init(): scanning PCI bus...", C["blue"]),
             ("PCI: found Intel E1000 (vendor=0x8086, dev=0x100E)", C["green"]),
             ("E1000: BAR0 mapped, MAC=52:54:00:12:34:56", C["green"]),
             ("e1000_transmit_init(): TX ring ready", C["subtext0"]),
             ("e1000_receive_init(): RX ring ready", C["subtext0"])],
            [("e1000_transmit_init(): 64 TX descriptors", C["blue"]),
             ("e1000_receive_init(): 128 RX descriptors", C["blue"]),
             ("TX ring: circular buffer, TDH/TDT registers", C["subtext0"]),
             ("RX ring: packet buffers + descriptors", C["subtext0"])],
            [("input process: sys_pkt_recv() -> packet!", C["green"]),
             ("input -> NS: ipc_send(NSREQ_INPUT, pkt)", C["blue"]),
             ("NS: lwIP processes packet (ARP/IP/TCP)...", C["mauve"]),
             ("NS -> HTTP: socket recv() returns data", C["green"]),
             ("HTTP -> NS: socket send() response", C["green"]),
             ("NS -> output: ipc_send(NSREQ_OUTPUT, pkt)", C["blue"]),
             ("output -> E1000: sys_pkt_send(pkt)", C["blue"])],
            [("NS: lwIP stack initialized", C["green"]),
             ("NS: DHCP discover -> IP 10.0.2.15 assigned", C["green"]),
             ("lwIP layers: ARP -> IP -> TCP -> Socket", C["subtext0"]),
             ("NS: TCP/IP initialized. Ready for connections.", C["green"])],
            [("httpd: socket() -> bind(0.0.0.0:80) -> listen()", C["blue"]),
             ("httpd: accept() -> new connection!", C["green"]),
             ("httpd: GET /index.html HTTP/1.0", C["subtext0"]),
             ("httpd: HTTP/1.0 200 OK (serving file)", C["green"]),
             ("httpd: connection closed", C["subtext0"]),
             ("Browser: http://localhost:26080/  -> JOS serves HTML!", C["mauve"])],
        ]
        draws = [self._draw_l6_s0, self._draw_l6_s1, self._draw_l6_s2,
                 self._draw_l6_s3, self._draw_l6_s4]
        return {"info": infos[step], "term": terms[step], "draw": draws[step]}

    def _draw_l6_s0(self, W, H):
        self.canvas.create_text(W // 2, 14, text="网络子系统：从硬件到应用的全栈架构",
                                 fill=C["mauve"], font=FONT_H)

        layers = [("外部网络 (Internet)", C["surface2"]),
                  ("QEMU 端口转发 (NAT)", C["surface1"]),
                  ("E1000 网卡驱动 (内核)", C["red"]),
                  ("input / output 进程", C["peach"]),
                  ("NS 网络服务 (lwIP)", C["yellow"]),
                  ("HTTP 服务 (httpd.c)", C["green"]),
                  ("外部浏览器", C["mauve"])]
        lx = W // 2 - 180
        for i, (name, clr) in enumerate(layers):
            y = 38 + i * 35
            self._shadow_box(lx, y, 360, 30, name, clr, C["crust"],
                             font=("Microsoft YaHei", 8, "bold"))
            if i < len(layers) - 1:
                self._arrow(lx + 180, y + 30, lx + 180, y + 35, C["mauve"], 2)

        self.canvas.create_text(W // 2, 320, text="QEMU: -net user -net nic,model=e1000 -redir tcp:26080::80",
                                 fill=C["surface2"], font=FONT_S)

    def _draw_l6_s1(self, W, H):
        self.canvas.create_text(W // 2, 14, text="E1000 网卡驱动：描述符环形缓冲区",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 350, 52, 150, 38, "PCI 扫描\npci_init()", C["mauve"], C["crust"])
        self._arrow(W // 2 - 195, 71, W // 2 - 85, 71, C["mauve"], 2)
        self._shadow_box(W // 2 - 80, 52, 150, 38, "BAR 映射\nE1000 寄存器", C["blue"], C["crust"])

        self._shadow_box(W // 2 - 340, 115, 280, 55,
                         "TX Descriptor Ring\n环形缓冲区 (64 描述符)",
                         C["red"], C["crust"], font=FONT_B)
        self._shadow_box(W // 2 + 60, 115, 280, 55,
                         "RX Descriptor Ring\n环形缓冲区 (128 描述符)",
                         C["green"], C["crust"], font=FONT_B)

        self._box(W // 2 - 220, 200, 440, 30,
                  "e1000_transmit(pkt, len): write TX ring -> update TDT",
                  C["surface0"], C["text"], font=FONT_M)
        self._box(W // 2 - 220, 240, 440, 30,
                  "e1000_receive(pkt, &len): read RX ring -> update RDT",
                  C["surface0"], C["text"], font=FONT_M)

    def _draw_l6_s2(self, W, H):
        self.canvas.create_text(W // 2, 14, text="网络数据包收发完整路径",
                                 fill=C["mauve"], font=FONT_H)

        nodes = [("E1000\nNIC", 100, 55, C["red"]), ("input\n进程", 260, 105, C["peach"]),
                 ("NS\n(lwIP)", 430, 185, C["mauve"]), ("HTTP\nServer", 260, 265, C["green"]),
                 ("output\n进程", 100, 305, C["blue"])]
        for name, x, y, clr in nodes:
            self._shadow_box(x, y, 85, 42, name, clr, C["crust"],
                             font=("Microsoft YaHei", 7, "bold"))

        # RX path (solid)
        rxe = [(142, 92, 260, 118, "收包", C["green"], False),
               (302, 118, 430, 185, "IPC IN", C["mauve"], False),
               (472, 200, 302, 260, "socket\nrecv", C["green"], False)]
        for x1, y1, x2, y2, lbl, clr, dash in rxe:
            d = (4, 4) if dash else ()
            self._arrow(x1, y1, x2, y2, clr, 2, dash=d)
            self.canvas.create_text((x1 + x2) // 2 - 12, (y1 + y2) // 2 - 4,
                                     text=lbl, fill=clr, font=("Microsoft YaHei", 6))

        # TX path (dashed)
        txe = [(302, 282, 430, 215, "socket\nsend", C["peach"], True),
               (472, 210, 200, 305, "IPC OUT", C["red"], True),
               (200, 316, 142, 92, "发包", C["blue"], True)]
        for x1, y1, x2, y2, lbl, clr, dash in txe:
            d = (4, 4) if dash else ()
            self._arrow(x1, y1, x2, y2, clr, 2, dash=d)
            self.canvas.create_text((x1 + x2) // 2 - 12, (y1 + y2) // 2 - 4,
                                     text=lbl, fill=clr, font=("Microsoft YaHei", 6))

        self.canvas.create_text(W // 2, 348, text="所有网络处理均在用户态！内核只提供最小的包收发系统调用",
                                 fill=C["subtext0"], font=FONT_S)

    def _draw_l6_s3(self, W, H):
        self.canvas.create_text(W // 2, 14, text="lwIP 轻量级 TCP/IP 协议栈分层",
                                 fill=C["mauve"], font=FONT_H)

        self._box(W // 2 - 340, 48, 680, 280, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2, 66, text="lwIP Protocol Stack",
                                 fill=C["mauve"], font=FONT_B)

        layers = [("Application Layer (HTTP, Echo)", 85, C["green"]),
                  ("BSD Socket API (socket/bind/listen/accept)", 120, C["blue"]),
                  ("Transport Layer (TCP / UDP)", 160, C["yellow"]),
                  ("Network Layer (IP / ICMP)", 200, C["peach"]),
                  ("Link Layer (ARP)", 240, C["red"]),
                  ("E1000 Driver (Hardware)", 280, C["mauve"])]
        for name, y, clr in layers:
            self._shadow_box(W // 2 - 200, y, 400, 32, name, clr, C["crust"],
                             font=("Microsoft YaHei", 8, "bold"))

        self.canvas.create_text(W // 2, 340, text="NS: MAC=52:54:00:12:34:56 | IP=10.0.2.15 (DHCP)",
                                 fill=C["surface2"], font=FONT_S)

    def _draw_l6_s4(self, W, H):
        self.canvas.create_text(W // 2, 14, text="HTTP Web 服务器请求处理流程",
                                 fill=C["mauve"], font=FONT_H)

        self._shadow_box(W // 2 - 340, 52, 220, 35, "Browser\nhttp://localhost:26080/",
                         C["mauve"], C["crust"])
        self._arrow(W // 2 - 115, 69, W // 2 - 20, 69, C["mauve"], 2)
        self._shadow_box(W // 2 - 15, 52, 220, 35, "QEMU Port Fwd\n26080 → JOS:80",
                         C["blue"], C["crust"])
        self._arrow(W // 2 + 210, 69, W // 2 + 305, 69, C["mauve"], 2)
        self._shadow_box(W // 2 + 310, 52, 220, 35, "user/httpd.c\nhandle GET request",
                         C["green"], C["crust"])

        self._box(W // 2 - 280, 110, 560, 210, "", C["surface0"], "", outline=C["mauve"])
        self.canvas.create_text(W // 2, 128, text="HTTP 请求处理完整流程",
                                 fill=C["mauve"], font=FONT_B)
        httpf = ["1. httpd: socket() -> bind(0.0.0.0:80) -> listen()",
                 "2. httpd: accept() 等待客户端连接 (阻塞)",
                 "3. httpd: read() 收到 GET /index.html HTTP/1.0",
                 "4. httpd: 解析路径 -> 打开对应文件 (e.g. index.html)",
                 "5. httpd: send() HTTP/1.0 200 OK + Content-Length + body",
                 "6. httpd: close() 关闭连接",
                 "7. Browser: 解析 HTTP 响应，渲染 HTML 页面"]
        for i, l in enumerate(httpf):
            self.canvas.create_text(W // 2, 151 + i * 18, text=l, fill=C["text"], font=FONT_S)

        self.canvas.create_text(W // 2, 340,
            text="JOS HTTP Server running! Visit http://localhost:26080/ in your browser",
            fill=C["green"], font=FONT_B)


def main():
    root = tk.Tk()
    app = JOSDemoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()