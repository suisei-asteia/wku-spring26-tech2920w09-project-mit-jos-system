#!/usr/bin/env python3
"""
JOS System Visual Demo GUI
JOS操作系统可视化演示界面

自动演示JOS系统的各项基础操作，覆盖Lab 1-6的全部功能模块。
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
import threading

class JOSDemoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JOS Operating System - Visual Demo")
        self.root.geometry("1280x820")
        self.root.minsize(1100, 700)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_styles()

        self.auto_running = False
        self.auto_thread = None
        self.current_lab = 0
        self.lab_names = [
            "Lab 1: Boot & Monitor",
            "Lab 2: Memory Management",
            "Lab 3: User Env & Syscalls",
            "Lab 4: SMP, COW Fork & IPC",
            "Lab 5: File System & Shell",
            "Lab 6: Network & HTTP Server",
        ]
        self.lab_funcs = [
            self._show_lab1, self._show_lab2, self._show_lab3,
            self._show_lab4, self._show_lab5, self._show_lab6,
        ]

        self._build_layout()
        self._show_welcome()

    def _setup_styles(self):
        self.style.configure("Title.TLabel", font=("Consolas", 18, "bold"), foreground="#00FF00", background="#1a1a2e")
        self.style.configure("Header.TFrame", background="#1a1a2e")
        self.style.configure("Sidebar.TFrame", background="#16213e")
        self.style.configure("LabBtn.TButton", font=("Consolas", 11), padding=8)
        self.style.configure("DemoBtn.TButton", font=("Consolas", 10), padding=5)
        self.style.configure("AutoBtn.TButton", font=("Consolas", 11, "bold"), padding=8)
        self.style.configure("ArchLabel.TLabel", font=("Consolas", 9), background="#0f3460", foreground="#e0e0e0")
        self.style.configure("OutputLabel.TLabel", font=("Consolas", 10, "bold"), background="#0d0d0d", foreground="#00FF00")

    def _build_layout(self):
        self.root.configure(bg="#0a0a1a")
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#0a0a1a", sashwidth=3)
        main_paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(main_paned, bg="#16213e", width=320)
        main_paned.add(self.left_frame, minsize=280)

        right_frame = tk.Frame(main_paned, bg="#0a0a1a")
        main_paned.add(right_frame)

        right_paned = tk.PanedWindow(right_frame, orient=tk.VERTICAL, bg="#0a0a1a", sashwidth=3)
        right_paned.pack(fill=tk.BOTH, expand=True)

        self.arch_frame = tk.Frame(right_paned, bg="#0f3460", height=280)
        right_paned.add(self.arch_frame, minsize=240)

        self.output_frame = tk.Frame(right_paned, bg="#0d0d0d")
        right_paned.add(self.output_frame)

        self._build_header()
        self._build_left_sidebar()
        self._build_arch_panel()
        self._build_output_panel()

    def _build_header(self):
        header = tk.Frame(self.root, bg="#1a1a2e", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="JOS (MIT 6.828) Operating System -- Visual Demonstration",
                 font=("Consolas", 16, "bold"), fg="#00FF00", bg="#1a1a2e").pack(pady=8)

    def _build_left_sidebar(self):
        container = tk.Frame(self.left_frame, bg="#16213e")
        container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        tk.Label(container, text=" Lab Modules ", font=("Consolas", 13, "bold"),
                 fg="#e94560", bg="#16213e").pack(pady=(10, 5))

        self.lab_frames = {}
        self.lab_info_btns = {}
        self.lab_run_btns = {}
        lab_colors = ["#1b4332", "#1b3a4b", "#2d1b69", "#5c4a07", "#4a0e4e", "#0d3b66"]
        lab_hover = ["#2d6a4f", "#2a5f7a", "#3d2596", "#7a6310", "#6a166e", "#145a8c"]
        lab_info = [
            "BIOS→Boot→Kernel→Monitor", "Page alloc, VM, pgdir_walk",
            "Env, Trap, Syscall, IDT", "SMP, COW Fork, IPC, Sched",
            "FS Server, Spawn, Shell, Pipe", "E1000, lwIP, HTTP Server",
        ]

        for i, (name, func) in enumerate(zip(self.lab_names, self.lab_funcs)):
            card = tk.Frame(container, bg="#0a1628", relief=tk.FLAT, bd=0,
                           highlightthickness=1, highlightbackground="#1e3a5f")
            card.pack(fill=tk.X, padx=8, pady=3, ipady=2)
            self.lab_frames[i] = card

            idx = tk.Label(card, text=f" {i+1} ", font=("Consolas", 12, "bold"),
                          fg="#00FF00", bg="#0a1628")
            idx.pack(side=tk.LEFT, padx=(6, 0), pady=4)

            info_frame = tk.Frame(card, bg="#0a1628")
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 2), pady=2)

            name_label = tk.Label(info_frame, text=name, font=("Consolas", 11, "bold"),
                                 fg="#e0e0e0", bg="#0a1628", anchor="w")
            name_label.pack(anchor="w")

            desc_label = tk.Label(info_frame, text=lab_info[i], font=("Consolas", 8),
                                 fg="#777", bg="#0a1628", anchor="w")
            desc_label.pack(anchor="w")

            run_btn = tk.Button(card, text="\u25b6 Run", command=lambda idx=i: self._run_lab(idx + 1),
                              font=("Consolas", 10, "bold"), bg=lab_colors[i], fg="white",
                              activebackground=lab_hover[i], activeforeground="white",
                              relief=tk.FLAT, cursor="hand2", padx=10, pady=4,
                              borderwidth=0)
            run_btn.pack(side=tk.RIGHT, padx=(0, 8), pady=4)
            self.lab_run_btns[i] = run_btn

            card.bind("<Enter>", lambda e, f=card: f.configure(highlightbackground="#00FF00"))
            card.bind("<Leave>", lambda e, f=card: f.configure(highlightbackground="#1e3a5f"))

        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        tk.Label(container, text=" Auto Demo ", font=("Consolas", 13, "bold"),
                 fg="#00FF00", bg="#16213e").pack(pady=(5, 5))

        self.auto_btn = tk.Button(container, text="\u25b6 Run Full Auto Demo",
                                 command=self._start_auto_demo,
                                 font=("Consolas", 12, "bold"), bg="#2d6a4f", fg="white",
                                 activebackground="#40916c", activeforeground="white",
                                 relief=tk.FLAT, cursor="hand2", pady=8)
        self.auto_btn.pack(fill=tk.X, padx=8, pady=2)

        self.stop_auto_btn = tk.Button(container, text="\u25a0 Stop Auto Demo",
                                      command=self._stop_auto_demo,
                                      font=("Consolas", 12, "bold"), bg="#9d0208", fg="white",
                                      activebackground="#6a040f", activeforeground="white",
                                      relief=tk.FLAT, cursor="hand2", pady=8, state=tk.DISABLED)
        self.stop_auto_btn.pack(fill=tk.X, padx=8, pady=2)

        self.progress = ttk.Progressbar(container, mode="determinate", length=280)
        self.progress.pack(fill=tk.X, padx=10, pady=10)

        self.status_label = tk.Label(container, text="Ready", font=("Consolas", 10),
                                     fg="#aaa", bg="#16213e")
        self.status_label.pack(pady=5)

        ttk.Separator(container, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        clr_frame = tk.Frame(container, bg="#16213e")
        clr_frame.pack(fill=tk.X, padx=8, pady=2)

        tk.Button(clr_frame, text="Clear Output", command=self._clear_output,
                 font=("Consolas", 10), bg="#333", fg="#ccc",
                 activebackground="#555", relief=tk.FLAT, cursor="hand2", pady=4).pack(
                     side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(clr_frame, text="Next Lab \u25b6", command=self._run_next_lab,
                 font=("Consolas", 10, "bold"), bg="#1e3a5f", fg="#00FF00",
                 activebackground="#2a5f7a", relief=tk.FLAT, cursor="hand2", pady=4).pack(
                     side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

    def _build_arch_panel(self):
        tk.Label(self.arch_frame, text=" System Architecture ",
                 font=("Consolas", 12, "bold"), fg="#00FF00", bg="#0f3460").pack(anchor=tk.W, padx=10, pady=(5, 0))

        arch_text = tk.Text(self.arch_frame, bg="#0f3460", fg="#e0e0e0",
                           font=("Consolas", 9), wrap=tk.NONE, height=14,
                           insertbackground="#00FF00", relief=tk.FLAT,
                           borderwidth=0, padx=10, pady=5)
        arch_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        arch_text.insert(tk.END, self._get_arch_text())
        arch_text.configure(state=tk.DISABLED)

    def _get_arch_text(self):
        return r"""
+--------------------------------------------------------------+
|                    JOS System Architecture                    |
+--------------------------------------------------------------+
|  User Space (用户空间)                                        |
|  +----------+ +-------+ +-------+ +-----------+ +---------+  |
|  |  shell   | |  ls   | |  cat  | | FS Server | |NS Server|  |
|  | (sh.c)   | |(ls.c) | |(cat.c)| |(fs/serv.c)| |(net/)   |  |
|  +----+-----+ +---+---+ +---+---+ +-----+-----+ +----+----+  |
|       +-----------+----------+-----------+-----------+       |
|                          | IPC |                              |
+--------------------------+-----+------------------------------+
|  Kernel Space (内核空间)                                      |
|  +------------+ +------------+ +---------------------------+  |
|  |   Memory   | |  Trap /    | |      Scheduler            |  |
|  |   Manager  | |  Syscall   | |      (sched.c)            |  |
|  | (pmap.c)   | | (trap.c)   | | Round-Robin + Big Kernel  |  |
|  +------------+ +------------+ | Lock (BKL)                |  |
|  +------------+ +------------+ +---------------------------+  |
|  |  Monitor   | |  Console   | |     E1000 Driver          |  |
|  |(monitor.c) | | (cons.c)   | |     (e1000.c)             |  |
|  +------------+ +------------+ +---------------------------+  |
+--------------------------------------------------------------+
| Boot Sequence:                                                |
| BIOS -> Boot Loader -> entry.S -> i386_init() -> sched_yield()|
+--------------------------------------------------------------+
| Key Data Structures:                                          |
|  Env (Process PCB), Page Table (pgdir), Trapframe, GDT/IDT    |
+--------------------------------------------------------------+
"""

    def _build_output_panel(self):
        toolbar = tk.Frame(self.output_frame, bg="#111")
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.cur_lab_label = tk.Label(toolbar, text="No lab running",
                                      font=("Consolas", 10, "bold"),
                                      fg="#888", bg="#111")
        self.cur_lab_label.pack(side=tk.LEFT, padx=5, pady=4)

        self.re_run_btn = tk.Button(toolbar, text="\u21ba Re-run", command=self._re_run_current_lab,
                                   font=("Consolas", 10, "bold"), bg="#1e3a5f", fg="#00FF00",
                                   activebackground="#2a5f7a", activeforeground="white",
                                   relief=tk.FLAT, cursor="hand2", padx=10, pady=3,
                                   state=tk.DISABLED, borderwidth=0)
        self.re_run_btn.pack(side=tk.RIGHT, padx=(4, 5), pady=2)

        self.next_lab_btn = tk.Button(toolbar, text="Next \u25b6", command=self._run_next_lab,
                                     font=("Consolas", 10, "bold"), bg="#1e3a5f", fg="#87CEEB",
                                     activebackground="#2a5f7a", activeforeground="white",
                                     relief=tk.FLAT, cursor="hand2", padx=10, pady=3,
                                     borderwidth=0)
        self.next_lab_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        ttk.Separator(self.output_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5)

        self.output_text = scrolledtext.ScrolledText(
            self.output_frame, bg="#0d0d0d", fg="#00FF00",
            font=("Consolas", 10), wrap=tk.WORD,
            insertbackground="#00FF00", relief=tk.FLAT,
            borderwidth=0)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.tag_configure("highlight", foreground="#FFD700", font=("Consolas", 10, "bold"))
        self.output_text.tag_configure("info", foreground="#87CEEB")
        self.output_text.tag_configure("error", foreground="#FF4444")
        self.output_text.tag_configure("success", foreground="#00FF00", font=("Consolas", 10, "bold"))
        self.output_text.tag_configure("header", foreground="#e94560", font=("Consolas", 11, "bold"))
        self.output_text.tag_configure("warn", foreground="#FFA500")

    def _show_welcome(self):
        self._append_output_header("JOS Operating System (MIT 6.828) - Visual Demo", "header")
        self._append_output("=" * 72, "info")
        self._append_output()
        self._append_output("Welcome to the JOS System Visual Demonstration!", "success")
        self._append_output()
        self._append_output("This tool demonstrates the key features of JOS across all 6 labs:", "info")
        self._append_output()
        self._append_output("  Lab 1: Boot Process, Kernel Monitor (kerninfo, backtrace)", "info")
        self._append_output("  Lab 2: Memory Management (page alloc, virtual memory)", "info")
        self._append_output("  Lab 3: User Environments, Interrupts, System Calls", "info")
        self._append_output("  Lab 4: SMP, COW Fork, IPC (pingpong, primes)", "info")
        self._append_output("  Lab 5: File System, Spawn, Shell (ls, cat, pipes)", "info")
        self._append_output("  Lab 6: Network Driver (E1000), HTTP Server", "info")
        self._append_output()
        self._append_output("Click any Lab button on the left to explore,", "info")
        self._append_output("or press 'Run Full Auto Demo' for a complete walkthrough.", "info")
        self._append_output()
        self._append_output("=" * 72, "info")

    def _clear_output(self):
        self.output_text.delete(1.0, tk.END)
        self.current_lab = 0
        self.root.after(0, self._reset_lab_indicator)
        self.current_lab = 0
        self.root.after(0, self._reset_lab_indicator)

    def _append_output(self, text="", tag=None):
        self.output_text.insert(tk.END, text + "\n", tag or "")
        self.output_text.see(tk.END)

    def _append_output_header(self, text, tag="header"):
        self._append_output()
        self._append_output("=" * 72, "info")
        self._append_output(f"  {text}", tag)
        self._append_output("=" * 72, "info")
        self._append_output()

    def _append_demo_step(self, step_num, description):
        self._append_output(f"[Step {step_num}] {description}", "highlight")
        self.output_text.see(tk.END)

    def _typewriter_effect(self, text, tag=None, delay=0.015):
        for char in text:
            self.output_text.insert(tk.END, char, tag or "")
            self.output_text.see(tk.END)
            self.output_text.update()
            time.sleep(delay)

    def _run_with_animation(self, steps_func, delay_between=0.8):
        def run():
            for i, (desc, text, tag) in enumerate(steps_func()):
                if not self.auto_running and i > 0:
                    break
                self._append_demo_step(i + 1, desc)
                if isinstance(text, list):
                    for line in text:
                        self._append_output(line, tag)
                else:
                    self._append_output(text, tag)
                self.output_text.see(tk.END)
                time.sleep(delay_between)
            self._update_progress_done()
        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _show_lab1(self):
        self._clear_output()
        self._append_output_header("Lab 1: Boot Process & Kernel Monitor", "header")

        steps = [
            ("PC Power-On: BIOS performs POST and loads boot sector to 0x7C00",
             "  [BIOS] Power-On Self Test (POST) completed.\n"
             "  [BIOS] Loading first bootable device sector (512 bytes) to 0x7C00...", "info"),

            ("Boot Loader: Switch to 32-bit Protected Mode (boot/boot.S)",
             "  [Boot] Entering 32-bit protected mode...\n"
             "  [Boot] A20 gate enabled.\n"
             "  [Boot] Temporary GDT loaded.\n"
             "  [Boot] Loading kernel ELF from disk to physical 0x100000...", "info"),

            ("Kernel Entry: Enable Paging (kern/entry.S)",
             "  [Kernel Entry] Setting up entry_pgdir...\n"
             "  [Kernel Entry] Virtual 0xF0000000 -> Physical 0x00000000 mapped.\n"
             "  [Kernel Entry] CR3 loaded, paging enabled.\n"
             "  [Kernel Entry] Jumping to i386_init()...", "info"),

            ("Kernel Init: i386_init() executes (kern/init.c)",
             "  [i386_init] cons_init()    - Console initialized.\n"
             "  6828 decimal is 15254 octal!\n"
             "  [i386_init] mem_init()     - Memory management initialized.\n"
             "  [i386_init] env_init()     - Environment array initialized.\n"
             "  [i386_init] trap_init()    - IDT (Interrupt Descriptor Table) set up.\n"
             "  [i386_init] mp_init()      - Multi-processor config detected.\n"
             "  [i386_init] lapic_init()   - Local APIC initialized.", "info"),

            ("Kernel Monitor: Welcome prompt appears (kern/monitor.c)",
             [
                 "",
                 "Welcome to the JOS kernel monitor!",
                 "Type 'help' for a list of commands.",
                 "K> ",
             ], "success"),

            ("Monitor Command: help - List all available commands",
             [
                 "K> help",
                 "help - Display this list of commands",
                 "kerninfo - Display information about the kernel",
                 "backtrace - Display the stack backtrace",
             ], "success"),

            ("Monitor Command: kerninfo - Show kernel memory layout",
             [
                 "K> kerninfo",
                 "Special kernel symbols:",
                 "  _start                  0010000c (phys)",
                 "  entry  f010000c (virt)  0010000c (phys)",
                 "  etext  f0101a75 (virt)  00101a75 (phys)",
                 "  edata  f020e000 (virt)  0010e000 (phys)",
                 "  end    f020f000 (virt)  0010f000 (phys)",
                 "Kernel executable memory footprint: 64KB",
             ], "success"),

            ("Monitor Command: backtrace - Show function call stack (kern/kdebug.c)",
             [
                 "K> backtrace",
                 "Stack backtrace:",
                 "  ebp f010ef58  eip f0100a6f  args 00000001 f010ef80 00000000 f0100f9f f0100f84 00000000",
                 "  ebp f010ef78  eip f0100a8b  args 00000000 00000000 00000000 f0100f9f f0100f84 00000000",
                 "  ebp f010efb8  eip f0100f9f  args 00000000 00000000 00000000 00000000 00000000 00000000",
                 "  ebp f010efd8  eip f010003e  args 00000000 00001aac 00000644 00000000 00000000 00000000",
                 "  ebp f010eff8  eip f0100045  args 00000000 00000000 00000000 00000000 00000000 00000000",
             ], "success"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _show_lab2(self):
        self._clear_output()
        self._append_output_header("Lab 2: Memory Management", "header")

        steps = [
            ("Physical Memory Detection",
             [
                 "Physical memory: 131072K available, base = 640K, extended = 130432K",
                 "",
                 "Memory Layout:",
                 "  0x00000000 - 0x00000FFF  : Reserved (Page 0, IDT/BIOS)",
                 "  0x00001000 - 0x0009EFFF  : Free (base memory, ~630KB)",
                 "  0x0009F000 - 0x0009FFFF  : MPENTRY_PADDR (AP startup code)",
                 "  0x000A0000 - 0x000FFFFF  : I/O Hole (384KB)",
                 "  0x00100000 - 0x07FFFFFF  : Extended memory (kernel + free)",
             ], "info"),

            ("boot_alloc(): Allocate kernel memory during boot",
             "  boot_alloc(0x100000) -> Allocated 1MB for kernel page directory\n"
             "  boot_alloc(PTSIZE)   -> Allocated 4MB for kernel page table\n"
             "  boot_alloc(NPAGES*sizeof(struct PageInfo)) -> Page descriptor array", "info"),

            ("page_init(): Initialize physical page free list",
             "  Marking page 0 as reserved (holds IDT/BIOS data)\n"
             "  Marking I/O hole pages (0xA0000-0xFFFFF) as reserved\n"
             "  Marking kernel pages (0x100000+) as allocated\n"
             "  Remaining pages added to page_free_list", "info"),

            ("page_alloc(): Allocate a single physical page",
             "  page_alloc(ALLOC_ZERO) -> Returns struct PageInfo* for a free page\n"
             "  Page content zeroed (if ALLOC_ZERO flag set)\n"
             "  page_free_list head updated to next free page", "info"),

            ("page_free(): Return a page to the free list",
             "  page_free(pp) -> Returns page to page_free_list\n"
             "  Assert: page's reference count is 0 before freeing", "info"),

            ("pgdir_walk(): Walk page directory to get PTE address",
             "  Given pgdir + virtual address -> returns &pte (page table entry)\n"
             "  If page table doesn't exist and 'create' flag set:\n"
             "    -> allocates new page table, clears it, maps into pgdir", "info"),

            ("page_insert(): Map a physical page at a virtual address",
             "  page_insert(pgdir, pp, va, perm) -> Maps pp at va with given permissions\n"
             "  Calls pgdir_walk() to find/create PTE, then sets PTE value.\n"
             "  If va was previously mapped, removes old mapping first (TLB invalidate).", "info"),

            ("page_lookup(): Find physical page mapped at virtual address",
             "  page_lookup(pgdir, va, pte_store) -> Returns PageInfo* for va\n"
             "  Walks page directory/table to find PTE, extracts physical address.\n"
             "  If pte_store != NULL, stores the PTE address for caller.", "info"),

            ("mem_init() Self-Checks: Verifying correctness",
             [
                 "check_page_free_list() succeeded!",
                 "check_page_alloc() succeeded!",
                 "check_page() succeeded!",
                 "check_kern_pgdir() succeeded!",
                 "check_page_installed_pgdir() succeeded!",
                 "",
                 "Virtual Memory Layout:",
                 "  KERNBASE  (0xF0000000) : Kernel space start",
                 "  UPAGES    (0xEF000000) : Read-only 'pages' array",
                 "  UENVS     (0xEEC00000) : Read-only 'envs' array",
                 "  UTOP      (0xEEC00000) : Top of user-writable space",
                 "  ULIM      (0xEF800000) : Kernel/user boundary",
             ], "success"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _show_lab3(self):
        self._clear_output()
        self._append_output_header("Lab 3: User Environments, Interrupts & System Calls", "header")

        steps = [
            ("env_init(): Initialize environment (process) array",
             "  Initializing NENV (1024) environment structures...\n"
             "  env_free_list built (linked list of free environments)\n"
             "  Each Env contains: trapframe, page directory, env_id, status, etc.", "info"),

            ("env_create(): Create a user environment from ELF binary",
             "  env_create(user_hello, ENV_TYPE_USER)\n"
             "  -> env_alloc() to get free Env\n"
             "  -> env_setup_vm() to create new page directory\n"
             "  -> load_icode() to load ELF binary into environment\n"
             "  -> Set env_status = ENV_RUNNABLE", "info"),

            ("load_icode(): Load ELF binary into environment memory",
             "  Parsing ELF header at binary start...\n"
             "  Mapping program segments (LOAD type) into environment's address space\n"
             "  Allocating user stack at USTACKTOP (0xEEC00000)\n"
             "  Setting eip = ELF entry point", "info"),

            ("env_run(): Switch to user environment",
             "  env_run(e) -> lcr3(e->env_pgdir) switches to environment's page directory\n"
             "  env_pop_tf(&e->env_tf) restores registers and jumps to user code\n"
             "  Environment starts executing in user mode (Ring 3)", "info"),

            ("Trap Handling: IDT initialization (kern/trapentry.S + trap.c)",
             "  trap_init() sets up 256 IDT entries:\n"
             "    - Entries 0-19:  x86 exceptions (Divide Error, Page Fault, etc.)\n"
             "    - Entries 32-47: Hardware IRQs (Timer, Keyboard, etc.)\n"
             "    - Entry 48 (0x30): System call (int $0x30)\n"
             "  TSS (Task State Segment) configured for ring transition", "info"),

            ("Demo: Divide by Zero Exception (user/divzero.c)",
             [
                 "K> divzero",
                 "",
                 "Incoming TRAP frame at 0xefffffbc",
                 "TRAP frame at 0xf.......",
                 "  trap 0x00000000 Divide error",
                 "  eip  0x008.....",
                 "  ss   0x----0023",
                 "[00001001] free env 00001001",
                 "",
                 "--> Kernel catches Division Error, prints trap frame, destroys env.",
             ], "error"),

            ("Demo: Page Fault Protection (user/faultread.c)",
             [
                 "K> faultread",
                 "",
                 "Incoming TRAP frame at 0xefffffbc",
                 "TRAP frame at 0xf.......",
                 "  trap 0x0000000e Page Fault",
                 "  err  0x00000004 (user read, page not present)",
                 "  fault va 0x00000000  eip 0x008.....",
                 "[00001002] user fault va 00000000 ip 008.....",
                 "[00001002] free env 00001002",
                 "",
                 "--> Dereferencing NULL pointer causes Page Fault.",
             ], "error"),

            ("Demo: User Program 'hello' (user/hello.c)",
             [
                 "Starting environment: user_hello",
                 "hello, world",
                 "i am environment 00001000",
                 "[00001000] exiting gracefully",
                 "[00001000] free env 00001000",
                 "",
                 "--> Success: user program prints, calls sys_env_destroy, exits.",
             ], "success"),

            ("System Call Flow: sys_cputs() -> console output",
             "  User code calls cprintf() in lib/printf.c\n"
             "  -> lib/syscall.c: sys_cputs(s, len)\n"
             "  -> int $0x30 (TRAP number T_SYSCALL = 48)\n"
             "  -> kern/trap.c: trap_dispatch() detects T_SYSCALL\n"
             "  -> kern/syscall.c: syscall() dispatches to sys_cputs()\n"
             "  -> kern/console.c: cprintf() writes to VGA display", "info"),

            ("Supported System Calls (kern/syscall.c)",
             [
                 "System Call Table:",
                 "  SYS_cputs       (0)  - Print string to console",
                 "  SYS_cgetc       (1)  - Read char from console",
                 "  SYS_getenvid    (2)  - Get current environment ID",
                 "  SYS_env_destroy (3)  - Destroy an environment",
                 "  SYS_yield       (4)  - Yield CPU to another env",
                 "  SYS_exofork     (5)  - Create child environment (COW)",
                 "  SYS_env_set_status (6) - Set env status",
                 "  SYS_page_alloc  (7)  - Allocate page in env",
                 "  SYS_page_map    (8)  - Map page between envs",
                 "  SYS_page_unmap  (9)  - Unmap page in env",
                 "  SYS_env_set_pgfault_upcall (10) - Set page fault handler",
                 "  SYS_ipc_try_send  (11) - Try IPC send",
                 "  SYS_ipc_recv    (12) - IPC receive",
                 "  SYS_env_set_trapframe (13) - Set env trapframe",
             ], "info"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _show_lab4(self):
        self._clear_output()
        self._append_output_header("Lab 4: Multiprocessor, COW Fork & IPC", "header")

        steps = [
            ("SMP Initialization: boot_aps() starts non-boot CPUs",
             [
                 "--> boot_aps() copies mpentry.S to MPENTRY_PADDR (0x9000)",
                 "    Sends Startup IPI via LAPIC to each AP...",
                 "",
                 "SMP: CPU 1 starting",
                 "SMP: CPU 2 starting",
                 "SMP: CPU 3 starting",
                 "",
                 "--> Each AP runs mp_main():",
                 "    lcr3(PADDR(kern_pgdir))  -- switch to kernel page directory",
                 "    lapic_init()             -- initialize per-CPU LAPIC",
                 "    env_init_percpu()        -- initialize per-CPU env pointers",
                 "    trap_init_percpu()       -- configure TSS for this CPU",
                 "    lock_kernel() + sched_yield() -- ready to schedule",
             ], "success"),

            ("Round-Robin Scheduler (kern/sched.c)",
             "  sched_yield() iterates envs array circularly:\n"
             "    for (i = 0; i < NENV; i++):\n"
             "      if envs[(curenv_idx + i) % NENV].status == ENV_RUNNABLE:\n"
             "        env_run(&envs[...])\n"
             "  Big Kernel Lock (BKL) ensures only 1 CPU runs kernel code at a time.", "info"),

            ("COW (Copy-On-Write) Fork: sys_exofork() + duppage()",
             "  fork() in lib/fork.c:\n"
             "    1. sys_exofork() creates child with ENV_NOT_RUNNABLE status\n"
             "    2. duppage() maps parent pages as PTE_COW (read-only for both)\n"
             "    3. Both parent & child share physical pages initially\n"
             "    4. On write attempt -> page fault -> pgfault handler:\n"
             "       alloc new page, copy data, remap as writable (unshare)\n"
             "    5. sys_env_set_status(child, ENV_RUNNABLE) starts child", "info"),

            ("Demo: forktree - Process Tree Visualization (user/forktree.c)",
             [
                 "K> forktree",
                 "1000: I am ''",
                 "1001: I am '0'",
                 "2002: I am '00'",
                 "2003: I am '01'",
                 "2004: I am '000'",
                 "2005: I am '001'",
                 "2006: I am '010'",
                 "2007: I am '011'",
                 "1008: I am '1'",
                 "2009: I am '10'",
                 "2010: I am '11'",
                 "...",
                 "",
                 "--> Creates binary tree of processes via fork().",
             ], "success"),

            ("Demo: dumbfork - Simple Fork (user/dumbfork.c)",
             [
                 "K> dumbfork",
                 "[00001000] dumbfork starting",
                 "[00001001] dumbfork: I'm the child!",
                 "[00001000] dumbfork: I'm the parent. Child PID: 00001001",
                 "[00001001] dumbfork: child exiting",
                 "[00001000] dumbfork: parent exiting",
                 "",
                 "--> Basic fork demonstration: parent creates child, both run.",
             ], "success"),

            ("IPC: Inter-Process Communication (lib/ipc.c)",
             "  IPC primitives:\n"
             "    ipc_send(envid, value, srcva, perm)\n"
             "      -> sys_ipc_try_send() loops until receiver is ready\n"
             "      -> Maps srcva page into receiver's address space\n"
             "    ipc_recv(from_env_store, dstva, perm)\n"
             "      -> sys_ipc_recv() blocks until sender sends\n"
             "      -> Accepts page mapping from sender\n"
             "  Uses: FS server, Network server communicate via IPC", "info"),

            ("Demo: pingpong - IPC Test (user/pingpong.c)",
             [
                 "K> pingpong",
                 "[00001000] pingpong starting...",
                 "[00001001] pingpong: sending 0 from child 00001001 to parent 00001000",
                 "[00001000] pingpong: got 0 from 00001001",
                 "[00001001] pingpong: got 1 from 00001000",
                 "[00001000] pingpong: got 2 from 00001001",
                 "...",
                 "[00001001] pingpong: got 9 from 00001000",
                 "[00001000] pingpong: got 10 from 00001001",
                 "[00001000] pingpong: exiting",
                 "",
                 "--> Two processes ping-pong messages 10 times via IPC.",
             ], "success"),

            ("Demo: primes - Prime Sieve using IPC Pipes (user/primes.c)",
             [
                 "K> primes",
                 "Pipe Prime Sieve (generating primes up to 50):",
                 "2 3 5 7 11 13 17 19 23 29 31 37 41 43 47",
                 "",
                 "--> Each prime gets its own process, chained via IPC pipes.",
                 "    Process filters multiples of its prime, passes others downstream.",
             ], "success"),

            ("Stress Test: stresssched - Scheduler Load Test (user/stresssched.c)",
             [
                 "K> stresssched",
                 "[00001000] stresssched: creating many forking environments...",
                 "[00001001] forking...",
                 "[00001002] forking...",
                 "...",
                 "--> Creates many concurrent environments to test round-robin scheduler.",
             ], "info"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _show_lab5(self):
        self._clear_output()
        self._append_output_header("Lab 5: File System, Spawn & Shell", "header")

        steps = [
            ("File System Server Initialization (fs/serv.c + fs/fs.c)",
             "  ENV_CREATE(fs_fs, ENV_TYPE_FS) creates FS server process\n"
             "  FS server opens 'fs/fs.img' virtual disk image\n"
             "  Superblock loaded: disk size, block count, root directory inode\n"
             "  Block cache (bc.c) initialized: cache blocks with LRU eviction\n"
             "  FS server waits for IPC requests from user processes", "info"),

            ("File System Layout on Disk",
             [
                 "Disk Layout (fs/fs.img):",
                 "  +--------+--------+--------+-----+--------+",
                 "  | Super  | Inode  | Data   | ... | Data   |",
                 "  | Block  | Blocks | Blocks |     | Blocks |",
                 "  | (1)    |        |        |     |        |",
                 "  +--------+--------+--------+-----+--------+",
                 "",
                 "  Superblock: magic=0x4A0530AE, nblocks=1024",
                 "  Inode: file type, size, direct[10] + indirect block pointers",
                 "  Directory: array of (filename, inode) entries",
             ], "info"),

            ("Spawn: Create Process from ELF File (lib/spawn.c)",
             "  spawn(prog, argv):\n"
             "    1. Open ELF file via FS server IPC\n"
             "    2. sys_exofork() to create child environment\n"
             "    3. Parse ELF header, map each LOAD segment to child's address space\n"
             "    4. init_stack() sets up argc/argv/USTACKTOP for child\n"
             "    5. sys_env_set_trapframe() sets child's entry eip\n"
             "    6. sys_env_set_status(child, ENV_RUNNABLE) starts child", "info"),

            ("Shell: Interactive Command Interpreter (user/sh.c)",
             "  Shell startup: reads commands from stdin, spawns programs\n"
             "  Features:\n"
             "    <  : Input redirection (read from file)\n"
             "    >  : Output redirection (write to file)\n"
             "    |  : Pipe (connect stdout of left to stdin of right)\n"
             "  Built-in: cd (change directory)", "info"),

            ("Demo: Shell ls - List Directory Contents",
             [
                 "$ ls",
                 "lorem        motd         newmotd      script",
                 "testshell.sh testshell.key",
                 "",
                 "--> Shows files in the JOS file system root directory.",
             ], "success"),

            ("Demo: Shell cat - Display File Contents",
             [
                 "$ cat lorem",
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                 "Ut enim ad minim veniam, quis nostrud exercitation ullamco.",
                 "...",
                 "",
                 "--> cat opens file via FS server, reads and displays contents.",
             ], "success"),

            ("Demo: Shell Output Redirection (>)",
             [
                 "$ cat lorem > newfile",
                 "$ cat newfile",
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "...",
                 "",
                 "--> Redirects output of 'cat lorem' into a new file 'newfile'.",
             ], "success"),

            ("Demo: Shell Input Redirection (<)",
             [
                 "$ cat < lorem",
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "...",
                 "",
                 "--> Reads input from file 'lorem' instead of stdin.",
             ], "success"),

            ("Demo: Shell Pipe (|)",
             [
                 "$ cat lorem | cat",
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                 "...",
                 "",
                 "--> Pipe connects stdout of first cat to stdin of second cat.",
                 "    Implemented using pipe() system call + dup2().",
             ], "success"),

            ("Demo: testfile - File System Test Suite (user/testfile.c)",
             [
                 "$ testfile",
                 "Testing basic file operations...",
                 "  Creating file 'testfile.txt'... OK",
                 "  Writing to file... OK",
                 "  Reading from file... OK",
                 "  Seeking within file... OK",
                 "  Closing file... OK",
                 "All file tests passed!",
                 "",
                 "--> Comprehensive test of file create/read/write/seek.",
             ], "success"),

            ("Demo: echo - Print Arguments",
             [
                 "$ echo Hello JOS World",
                 "Hello JOS World",
                 "",
                 "--> Simple echo program: prints its arguments.",
             ], "success"),

            ("Demo: num - Print Numbers",
             [
                 "$ num 10",
                 "1 2 3 4 5 6 7 8 9 10",
                 "",
                 "--> Prints numbers from 1 to N.",
             ], "success"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _show_lab6(self):
        self._clear_output()
        self._append_output_header("Lab 6: Network Driver & HTTP Server", "header")

        steps = [
            ("PCI Initialization: Scan for E1000 Network Card (kern/pci.c)",
             "  pci_init() scans PCI bus for devices...\n"
             "  Found: Vendor=0x8086 (Intel), Device=0x100E (82540EM Gigabit)\n"
             "  E1000 at bus=0, slot=3, func=0\n"
             "  BAR0 (MMIO base): 0xFEB00000\n"
             "  PCI command register written: bus mastering + MMIO enabled", "info"),

            ("E1000 Driver: Transmit Initialization (kern/e1000.c)",
             "  e1000_transmit_init():\n"
             "    Allocates transmit descriptor ring (TX_RING_SIZE=64)\n"
             "    Sets TDBAL/TDBAH (descriptor base address)\n"
             "    Sets TDLEN (descriptor ring length)\n"
             "    Sets TDH=0, TDT=0 (head/tail pointers)\n"
             "    Configures TCTL (transmit control register)\n"
             "    Enables TX via TCTL.EN bit", "info"),

            ("E1000 Driver: Receive Initialization (kern/e1000.c)",
             "  e1000_receive_init():\n"
             "    Allocates receive descriptor ring + packet buffers\n"
             "    Sets RDBAL/RDBAH (descriptor base address)\n"
             "    Sets RDLEN (descriptor ring length)\n"
             "    Sets RDH=0, RDT=N-1 (head/tail pointers)\n"
             "    Configures RCTL (receive control register)\n"
             "    Sets MAC address filter (RAR0/RAH0)\n"
             "    Enables RX via RCTL.EN bit", "info"),

            ("Network Service Initialization (net/serv.c)",
             [
                 "ns: 52:54:00:12:34:56 bound to static IP 10.0.2.15",
                 "NS: TCP/IP initialized.",
                 "",
                 "--> NS (Network Service) uses lwIP TCP/IP stack.",
                 "    Communicates with input/output helper processes via IPC.",
             ], "success"),

            ("Data Flow: Packet Receive Path",
             "  E1000 hardware -> RX interrupt -> e1000_receive() [kernel]\n"
             "    -> sys_pkt_try_receive() [syscall] -> input process (net/input.c)\n"
             "    -> ipc_send() to NS server [IPC] -> lwIP stack processes packet\n"
             "    -> Deliver to application socket (e.g. HTTP server)", "info"),

            ("Data Flow: Packet Transmit Path",
             "  Application (e.g. HTTP) -> socket send() -> lwIP stack [NS server]\n"
             "    -> ipc_send() to output process [IPC] -> output (net/output.c)\n"
             "    -> sys_pkt_try_send() [syscall] -> e1000_transmit() [kernel]\n"
             "    -> E1000 hardware -> network wire", "info"),

            ("HTTP Server Startup (user/httpd.c)",
             [
                 "--> HTTP server listening on port 80...",
                 "[00001003] httpd: starting HTTP server on port 80",
                 "[00001003] httpd: waiting for connections...",
             ], "success"),

            ("HTTP Request/Response Demo",
             [
                 "Browser requests: GET / HTTP/1.1",
                 "",
                 "HTTP/1.1 200 OK",
                 "Content-Type: text/html",
                 "",
                 "<html><body>",
                 "<h1>Welcome to JOS HTTP Server!</h1>",
                 "<p>This page is served by JOS (MIT 6.828).</p>",
                 "<p>Environment: user/httpd.c</p>",
                 "<p>Network stack: lwIP via E1000 driver</p>",
                 "</body></html>",
                 "",
                 "--> Access at http://localhost:26080/ (QEMU port forwarding)",
             ], "success"),

            ("echo Service (UDP port 7) (user/echosrv.c)",
             [
                 "--> echo server listening on UDP port 7",
                 "[00001004] echosrv: starting echo server on port 7",
                 "[00001004] echosrv: echo'd 13 bytes",
                 "",
                 "--> Test with: echo 'hello' | nc -u localhost 26087",
             ], "success"),

            ("Demo: testtime - Time System Call Test (user/testtime.c)",
             [
                 "$ testtime",
                 "Starting testtime...",
                 "sys_time_msec() returns: 12345 ms",
                 "sleeping 1 second...",
                 "sys_time_msec() returns: 13345 ms",
                 "Elapsed: 1000 ms (OK)",
                 "",
                 "--> sys_time_msec uses RTC (kern/kclock.c) for time measurement.",
             ], "success"),

            ("Full Network Stack Summary",
             [
                 "JOS Network Architecture:",
                 "",
                 "  +----------------+",
                 "  |  HTTP Server   |  (user/httpd.c, port 80)",
                 "  |  Echo Server   |  (user/echosrv.c, UDP port 7)",
                 "  +-------+--------+",
                 "          | socket API",
                 "  +-------+--------+",
                 "  |   NS Server    |  (net/serv.c, lwIP TCP/IP)",
                 "  +-------+--------+",
                 "          | IPC",
                 "  +-------+--------+",
                 "  | input / output |  (net/input.c, net/output.c)",
                 "  +-------+--------+",
                 "          | syscall",
                 "  +-------+--------+",
                 "  |  E1000 Driver  |  (kern/e1000.c)",
                 "  +-------+--------+",
                 "          | PCI/MMIO",
                 "  +-------+--------+",
                 "  |  E1000 Hardware|  (Intel 82540EM)",
                 "  +----------------+",
             ], "info"),
        ]
        self._run_with_animation(lambda: steps, delay_between=1.0)

    def _start_auto_demo(self):
        self.auto_running = True
        self.auto_btn.config(state=tk.DISABLED, bg="#555")
        self.stop_auto_btn.config(state=tk.NORMAL, bg="#9d0208")
        self._clear_output()
        self._append_output_header("AUTO DEMO: Full JOS System Walkthrough", "header")
        self._append_output("Running all 6 labs in sequence...\n", "warn")

        def auto_sequence():
            total = len(self.lab_funcs)
            self.root.after(0, lambda: setattr(self, '_progress_max', total))
            self.root.after(0, lambda: self.progress.configure(maximum=total))
            for i in range(total):
                if not self.auto_running:
                    break
                self.root.after(0, lambda v=i+1: self.progress.configure(value=v))
                self.root.after(0, lambda v=i+1: self.status_label.config(
                    text=f"Running Lab {v}/{total}...", fg="#FFD700"))
                self._run_lab(i + 1)
                time.sleep(2.0)
            if self.auto_running:
                self.root.after(0, lambda: self.progress.configure(value=total))
                self.root.after(0, lambda: self.status_label.config(text="Auto Demo Complete!", fg="#00FF00"))
                self._append_output()
                self._append_output("=" * 72, "info")
                self._append_output("  AUTO DEMO COMPLETE!", "success")
                self._append_output("  All 6 Labs demonstrated successfully.", "success")
                self._append_output("=" * 72, "info")
            self._stop_auto_demo_internal()

        self.auto_thread = threading.Thread(target=auto_sequence, daemon=True)
        self.auto_thread.start()

    def _stop_auto_demo(self):
        self.auto_running = False
        self._stop_auto_demo_internal()

    def _stop_auto_demo_internal(self):
        self.auto_running = False
        self.root.after(0, lambda: self.auto_btn.config(state=tk.NORMAL, bg="#2d6a4f"))
        self.root.after(0, lambda: self.stop_auto_btn.config(state=tk.DISABLED, bg="#555"))

    def _run_lab(self, lab_num):
        self.current_lab = lab_num
        self.root.after(0, self._update_current_lab_indicator)
        if 1 <= lab_num <= len(self.lab_funcs):
            self.lab_funcs[lab_num - 1]()

    def _re_run_current_lab(self):
        if self.current_lab < 1 or self.current_lab > len(self.lab_funcs):
            return
        self.root.after(0, lambda: self.status_label.config(
            text=f"Re-running Lab {self.current_lab}...", fg="#FFD700"))
        self.lab_funcs[self.current_lab - 1]()

    def _run_next_lab(self):
        next_lab = self.current_lab + 1 if self.current_lab > 0 else 1
        if next_lab > len(self.lab_funcs):
            next_lab = 1
        self._run_lab(next_lab)

    def _update_current_lab_indicator(self):
        if 1 <= self.current_lab <= len(self.lab_names):
            self.cur_lab_label.config(
                text=f"Running: {self.lab_names[self.current_lab - 1]}",
                fg="#FFD700")
            self.re_run_btn.config(state=tk.NORMAL)
            self.next_lab_btn.config(state=tk.NORMAL)
            for i, frame in self.lab_frames.items():
                if i == self.current_lab - 1:
                    frame.configure(highlightbackground="#00FF00", highlightthickness=2)
                else:
                    frame.configure(highlightbackground="#1e3a5f", highlightthickness=1)

    def _reset_lab_indicator(self):
        self.cur_lab_label.config(text="No lab running", fg="#888")
        self.re_run_btn.config(state=tk.DISABLED)
        self.next_lab_btn.config(state=tk.NORMAL)
        for frame in self.lab_frames.values():
            frame.configure(highlightbackground="#1e3a5f", highlightthickness=1)

    def _update_progress_done(self):
        self.root.after(0, self._update_current_lab_indicator)


def main():
    root = tk.Tk()
    app = JOSDemoGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
