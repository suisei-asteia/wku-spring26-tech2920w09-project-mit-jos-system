# JOS 系统操作指南

> JOS (JOS Operating System) 是 MIT 6.828 操作系统工程课程的教学操作系统，基于 xv6 改写而成，运行在 x86 架构上。本文档整合了课程资料、源码分析及实验笔记，提供全面的操作指南。

---

## 目录

1. [JOS 系统概述](#1-jos-系统概述)
2. [环境搭建与构建运行](#2-环境搭建与构建运行)
3. [系统启动流程](#3-系统启动流程)
4. [内存管理](#4-内存管理)
5. [进程与环境管理](#5-进程与环境管理)
6. [中断、异常与系统调用](#6-中断异常与系统调用)
7. [多任务调度](#7-多任务调度)
8. [进程间通信 (IPC)](#8-进程间通信-ipc)
9. [文件系统](#9-文件系统)
10. [Shell 操作](#10-shell-操作)
11. [网络子系统](#11-网络子系统)
12. [内核监视器](#12-内核监视器)
13. [调试指南](#13-调试指南)
14. [Lab 实验体系](#14-lab-实验体系)
15. [常见问题与技巧](#15-常见问题与技巧)
16. [附录：关键数据结构速查](#16-附录关键数据结构速查)

---

## 1. JOS 系统概述

### 1.1 什么是 JOS

JOS 是 MIT 6.828 课程使用的教学操作系统。它是在 **xv6**（一个类 Unix V6 的简化教学操作系统）基础上改写而成的微型内核，提供了完成实验所需的基础框架。

- **xv6**：重实现的 Dennis Ritchie 和 Ken Thompson 的 Unix V6，为 x86 多处理器架构设计
- **JOS**：在 xv6 基础上改写，使得学生可以逐步实现 OS 各核心功能

### 1.2 系统架构

JOS 采用**微内核 + 服务进程**的架构设计：

```
┌──────────────────────────────────────────────┐
│              用户空间 (User Space)              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌─────────────┐ │
│  │ shell │ │  ls  │ │ cat  │ │ FS Server   │ │
│  │(sh.c) │ │(ls.c)│ │(cat.c│ │ (fs/serv.c) │ │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──────┬──────┘ │
│     │        │        │             │         │
│     └────────┴────────┴──────┬──────┘         │
│                              │ IPC            │
│     ┌────────────────────────┴──────────┐     │
│     │          NS Server (Network)       │     │
│     └────────────────────────────────────┘     │
├──────────────────────────────────────────────┤
│              内核空间 (Kernel Space)            │
│  ┌──────────┐ ┌────────┐ ┌────────────────┐ │
│  │  Memory  │ │  Trap/ │ │   Scheduler    │ │
│  │  Manager │ │  Syscall│ │   (sched.c)    │ │
│  │ (pmap.c) │ │(trap.c)│ │                │ │
│  └──────────┘ └────────┘ └────────────────┘ │
│  ┌──────────┐ ┌────────┐ ┌────────────────┐ │
│  │  Monitor │ │ Console│ │  E1000 Driver  │ │
│  │(monitor.c)│ │(cons.c)│ │  (e1000.c)    │ │
│  └──────────┘ └────────┘ └────────────────┘ │
└──────────────────────────────────────────────┘
```

### 1.3 课程结构 (MIT 6.828 Fall 2012)

| 实验 | 主题 | 内容 |
|------|------|------|
| Lab 1 | C, Assembly, Tools, Bootstrapping | PC引导、Boot loader、内核加载 |
| Lab 2 | Memory Management | 物理页管理、虚拟内存、内核地址空间 |
| Lab 3 | User-Level Environments | 用户环境、异常处理、系统调用 |
| Lab 4 | Preemptive Multitasking | 多处理器支持、写时复制Fork、IPC |
| Lab 5 | Spawn and Shell | 文件系统、进程生成、Shell |
| Lab 6 | Network Driver | E1000网卡驱动、网络服务器 |

### 1.4 关键源文件速查表

| 目录/文件 | 功能 |
|-----------|------|
| `boot/` | 引导代码 (boot.S, main.c) |
| `kern/init.c` | 内核初始化入口 |
| `kern/pmap.c` | 物理内存/虚拟内存管理 |
| `kern/env.c` | 环境(进程)管理 |
| `kern/trap.c` | 中断/异常/系统调用处理 |
| `kern/syscall.c` | 系统调用实现 |
| `kern/sched.c` | CPU调度器 |
| `kern/monitor.c` | 内核监视器(调试命令行) |
| `kern/e1000.c` | E1000网卡驱动 |
| `lib/` | 用户库函数 |
| `user/` | 用户程序 (sh, ls, cat, echo等) |
| `fs/` | 文件系统服务 (fs.c, serv.c) |
| `net/` | 网络服务 (input.c, output.c, ns.h) |
| `inc/` | 公共头文件 |

---

## 2. 环境搭建与构建运行

### 2.1 环境要求

- **虚拟机**：VMware Workstation 或 VirtualBox
- **操作系统**：Ubuntu 16.04+ (推荐)
- **模拟器**：QEMU（建议使用 MIT patch 版本）
- **交叉编译工具链**：`i386-jos-elf-*`

### 2.2 安装工具链

```bash
# Ubuntu 上安装必要的工具
sudo apt-get update
sudo apt-get install -y build-essential gdb git qemu
```

详细的工具链安装请参考 MIT 官方文档：[Tools Used in 6.828](https://pdos.csail.mit.edu/6.828/2018/tools.html)

### 2.3 构建系统

```bash
# 进入 lab 目录
cd lab/

# 编译整个系统
make

# 详细输出模式
make V=1

# 使用自定义工具链
make TOOLPREFIX=i386-jos-elf-
```

构建配置文件：
- `conf/lab.mk`：指定当前 Lab 编号（如 `LAB=6`）
- `conf/env.mk`：自定义环境变量（如 `GCCPREFIX`, `QEMU` 路径）
- `GNUmakefile`：主构建文件，使用 Peter Miller 的递归 Make 优化方案

### 2.4 运行 JOS

```bash
# 标准 QEMU 图形模式运行
make qemu

# 无图形模式运行
make qemu-nox

# QEMU + GDB 调试模式
make qemu-gdb   # 启动 QEMU 等待 GDB 连接
make gdb        # 在另一个终端启动 GDB

# 无图形 + GDB 调试
make qemu-nox-gdb
```

QEMU 启动参数说明：
```
-drive file=obj/kern/kernel.img,index=0    # 内核镜像（磁盘0）
-drive file=obj/fs/fs.img,index=1          # 文件系统镜像（磁盘1）
-serial mon:stdio                           # 串口输出到标准IO
-smp N                                      # 模拟 N 个CPU
-net user -net nic,model=e1000              # E1000 网卡
-redir tcp:PORT::7                          # TCP端口转发（echo服务）
-redir tcp:PORT::80                         # TCP端口转发（HTTP服务）
```

---

## 3. 系统启动流程

### 3.1 启动顺序概览

```
BIOS → Boot Loader (boot.S + main.c) → Kernel Entry (entry.S) → i386_init()
     → mem_init() → env_init() → trap_init()
     → mp_init() → lapic_init() → pic_init()
     → ENV_CREATE(fs_fs) → ENV_CREATE(net_ns)
     → ENV_CREATE(user_*) → sched_yield()
```

### 3.2 详细阶段

#### 阶段1：BIOS
- 上电自检 (POST)
- 加载第一个可引导设备的 512 字节引导扇区到 `0x7C00`
- 跳转到 `0x7C00` 执行

#### 阶段2：Boot Loader (`boot/boot.S` + `boot/main.c`)
- 从实模式切换到 32 位保护模式
- 启用 A20 地址线
- 设置临时 GDT
- 从磁盘加载内核 ELF 镜像到物理内存 `0x100000` (1MB)
- 跳转到内核入口 `entry.S`

#### 阶段3：内核入口 (`kern/entry.S`)
- 设置内核页目录 `entry_pgdir`，映射虚拟地址 `0xF0000000` → 物理地址 `0x00000000`
- 启用分页
- 设置内核栈
- 跳转到 C 代码 `i386_init()`

#### 阶段4：内核初始化 (`kern/init.c`)

```c
void i386_init(void)
{
    cons_init();       // 初始化控制台（键盘 + 显示器）
    mem_init();        // 初始化内存管理（物理页 + 虚拟内存）
    env_init();        // 初始化环境（进程）数组
    trap_init();       // 初始化中断描述符表 (IDT) 和 TSS
    mp_init();         // 检测多处理器配置
    lapic_init();      // 初始化 APIC 中断控制器
    pic_init();        // 初始化 8259A PIC
    time_init();       // 初始化时钟
    pci_init();        // 初始化 PCI 总线
    lock_kernel();     // 获取大内核锁
    boot_aps();        // 启动其他 CPU 核心
    ENV_CREATE(fs_fs, ENV_TYPE_FS);    // 创建文件系统服务进程
    ENV_CREATE(net_ns, ENV_TYPE_NS);   // 创建网络服务进程
    ENV_CREATE(user_yield, ENV_TYPE_USER);  // 创建初始用户进程
    sched_yield();     // 调度运行第一个进程
}
```

### 3.3 多处理器启动

- `boot_aps()` 将 AP 启动代码 (`mpentry.S`) 复制到 `MPENTRY_PADDR`
- 通过 LAPIC 发送 IPI 逐个启动 AP
- 每个 AP 在 `mp_main()` 中初始化自身的 LAPIC、TSS、GDT
- 获取大内核锁后调用 `sched_yield()` 开始调度

---

## 4. 内存管理

### 4.1 虚拟内存布局

```
      4GB ───────> +------------------------------+
                   |         Kernel Space         | RW/--
                   |   (Remapped Physical Mem)    |
                   |                              |
KERNBASE(0xF0000000)+------------------------------+
 KSTACKTOP          |   CPU0 Kernel Stack (64KB)  |
                    |   CPU0 Guard     (64KB)     |
                    |   CPU1 Kernel Stack (64KB)  |
                    |   CPU1 Guard     (64KB)     |
                    |          ...                |
 MMIOLIM  (0xEFC00000)+------------------------------+
                    |   Memory-Mapped I/O (4MB)   |
 MMIOBASE (0xEF800000)+------------------------------+
                    |   Cur. Page Table (4MB)     | R-/R-
 UVPT     (0xEF400000)+------------------------------+
                    |   RO PAGES (4MB)            | R-/R-
 UPAGES   (0xEF000000)+------------------------------+
                    |   RO ENVS (4MB)             | R-/R-
 UENVS    (0xEEC00000)+------------------------------+
 UXSTACKTOP         |   User Exception Stack (4KB)| RW/RW
 USTACKTOP(0xEEBFE000)+------------------------------+
                    |   Normal User Stack (4KB)   | RW/RW
                    |                              |
                    |   Program Data & Heap       |
 UTEXT    (0x00800000)+------------------------------+
                    |   Empty Memory              |
      0 ───────>    +------------------------------+
```

关键地址常量 (定义于 `inc/memlayout.h`)：

| 符号 | 值 | 说明 |
|------|------|------|
| `KERNBASE` | `0xF0000000` | 内核空间起始 |
| `ULIM` / `MMIOBASE` | `0xEF800000` | 用户空间上限 |
| `UTEXT` | `0x00800000` | 用户代码段起始 |
| `USTACKTOP` | `0xEEBFE000` | 用户栈顶 |
| `KSTACKTOP` | `0xF0000000` | 内核栈顶 |
| `PGSIZE` | `0x1000` (4KB) | 页面大小 |

### 4.2 物理页管理 (`kern/pmap.c`)

```c
// 页面信息结构
struct PageInfo {
    struct PageInfo *pp_link;  // 空闲链表下一项
    uint16_t pp_ref;           // 引用计数
};

// 关键函数
page_alloc(ALLOC_ZERO);  // 分配一页（可选清零）
page_free(pp);            // 释放一页
page_insert(pgdir, pp, va, perm);  // 建立映射
page_lookup(pgdir, va, pte_store); // 查找映射
page_remove(pgdir, va);   // 移除映射
```

JOS 使用双向链表管理空闲物理页面。`page_init()` 识别系统可用的物理内存（记录在 `npages` 和 `npages_basemem` 中）。

### 4.3 虚拟内存管理

- **内核页表** (`kern_pgdir`)：在内核启动时创建，映射所有物理内存到 `KERNBASE` 之上，对内核代码是可读写的
- **用户页表** (`env_pgdir`)：每个用户环境有自己的页目录，上方 (≥UTOP) 的内容直接复制自内核页表
- **UVPT 映射**：用户只读访问当前环境的页表，实现 page-fault 处理

### 4.4 缺页异常与 COW

JOS 在 Lab 4 实现了 Copy-on-Write Fork：

1. 父进程 fork 时，不复制物理页，而是将父子进程的页都标记为只读 + COW
2. 任一方写操作触发 Page Fault
3. Fault handler 识别 COW 页，分配新物理页并复制数据

每个环境可设置 `env_pgfault_upcall` 处理用户态缺页异常，用于实现用户级内存管理。

---

## 5. 进程与环境管理

### 5.1 核心概念

JOS 使用 **环境 (Environment)** 的概念来表示进程。一个环境包含：

- 地址空间 (页目录)
- 寄存器状态 (Trapframe)
- 进程状态 (FREE, DYING, RUNNABLE, RUNNING, NOT_RUNNABLE)
- 父子关系 (env_parent_id)

### 5.2 环境结构 (`inc/env.h`)

```c
struct Env {
    struct Trapframe env_tf;    // 保存的寄存器
    struct Env *env_link;       // 空闲链表指针
    envid_t env_id;             // 唯一环境ID
    envid_t env_parent_id;      // 父环境ID
    enum EnvType env_type;      // 类型: USER / FS / NS
    unsigned env_status;        // 状态: FREE/DYING/RUNNABLE/RUNNING/NOT_RUNNABLE
    uint32_t env_runs;          // 运行次数
    int env_cpunum;             // 所在CPU编号
    pde_t *env_pgdir;           // 页目录虚拟地址
    void *env_pgfault_upcall;   // 缺页异常回调入口
    bool env_ipc_recving;       // 是否阻塞等待IPC
    void *env_ipc_dstva;        // IPC页面映射目标地址
    uint32_t env_ipc_value;     // IPC传递的值
    envid_t env_ipc_from;       // IPC发送者ID
    int env_ipc_perm;           // IPC页面权限
};
```

环境ID编码：
```
+1+---------------21-----------------+--------10--------+
|0|          Uniqueifier             |   Environment    |
| |                                  |      Index       |
+------------------------------------+------------------+
                                     \--- ENVX(eid) --/
```

通过 `ENVX(eid)` 提取环境索引，`uniqueifier` 防止重用旧 ID。

### 5.3 环境生命周期

```
                    ┌─────────┐
                    │  FREE   │
                    └────┬────┘
                         │ env_alloc()
                    ┌────▼────────┐
                    │ NOT_RUNNABLE│◄───────────── sys_env_set_status()
                    └────┬───────┘
                         │ sys_env_set_status(ENV_RUNNABLE)
                    ┌────▼────┐
              ┌────▶│ RUNNABLE│
              │     └────┬───┘
              │          │ sched_yield() → env_run()
              │     ┌────▼────┐
              │     │ RUNNING │
              │     └────┬───┘
              │          │ sys_yield()
              │          │ sys_env_destroy()
              └──────────┘
```

### 5.4 关键环境管理函数 (`kern/env.c`)

| 函数 | 功能 |
|------|------|
| `env_init()` | 初始化 envs 数组和空闲链表 |
| `env_alloc(e, parent_id)` | 分配新环境 |
| `env_create(binary, type)` | 从 ELF 二进制创建环境 |
| `env_destroy(e)` | 销毁环境，释放资源 |
| `env_run(e)` | 切换到环境 e 执行（不返回） |
| `envid2env(envid, &env_store, checkperm)` | 通过ID查找环境 |
| `env_setup_vm(e)` | 初始化环境的虚拟内存 |
| `ENV_CREATE(x, type)` | 宏，从 ELF 二进制创建环境的便捷方式 |

---

## 6. 中断、异常与系统调用

### 6.1 中断描述符表 (IDT)

JOS 在 `trap_init()` 中配置完整的 256 条目 IDT：

| 向量号 | 类型 | 处理函数 | DPL |
|--------|------|---------|-----|
| 0-19 | x86 异常 | `divide_handler` 等 | 0 |
| T_SYSCALL (0x30) | 系统调用 | `syscall_handler` | 3 |
| T_BRKPT (0x03) | 断点 | `brkpt_handler` | 3 |
| IRQ_OFFSET+0 | 时钟中断 | `timer_handler` | 0 |
| IRQ_OFFSET+1 | 键盘中断 | `kbd_handler` | 0 |
| IRQ_OFFSET+4 | 串口中断 | `serial_handler` | 0 |
| IRQ_OFFSET+14 | IDE磁盘 | `ide_handler` | 0 |

使用 `SETGATE` 宏配置每种异常/中断的 DPL 和类型（trap/interrupt gate）。

### 6.2 陷阱帧 (Trapframe)

当发生中断/异常/系统调用时，CPU 自动保存以下状态到内核栈：

```c
struct Trapframe {
    struct PushRegs tf_regs;  // edi, esi, ebp, oesp, ebx, edx, ecx, eax
    uint16_t tf_es;
    uint16_t tf_padding1;
    uint16_t tf_ds;
    uint16_t tf_padding2;
    uint32_t tf_trapno;      // 陷阱号
    uint32_t tf_err;         // 错误码
    uintptr_t tf_eip;
    uint16_t tf_cs;
    uint16_t tf_padding3;
    uint32_t tf_eflags;
    uintptr_t tf_esp;
    uint16_t tf_ss;
    uint16_t tf_padding4;
};
```

### 6.3 系统调用机制

#### 系统调用表 (`inc/syscall.h`)

```c
enum {
    SYS_cputs = 0,              // 输出字符串到控制台
    SYS_cgetc,                  // 读取一个字符
    SYS_getenvid,               // 获取当前环境ID
    SYS_env_destroy,            // 销毁环境
    SYS_page_alloc,             // 分配页面映射
    SYS_page_map,               // 映射页面
    SYS_page_unmap,             // 取消映射
    SYS_exofork,                // 创建新环境（fork）
    SYS_env_set_status,         // 设置环境状态
    SYS_env_set_trapframe,      // 设置陷阱帧
    SYS_env_set_pgfault_upcall, // 设置缺页回调
    SYS_yield,                  // 主动让出CPU
    SYS_ipc_try_send,           // IPC发送
    SYS_ipc_recv,               // IPC接收
    SYS_time_msec,              // 获取毫秒时间
    SYS_pkt_try_send,           // 网络发送
    SYS_pkt_try_recv,           // 网络接收
    NSYSCALLS,
};
```

#### 系统调用流程

1. 用户程序调用库函数（如 `sys_cputs()` in `lib/syscall.c`）
2. 库函数将参数放入寄存器（eax=系统调用号），执行 `int $T_SYSCALL`
3. CPU 通过 IDT 跳转到 `trapentry.S` 中的 `syscall_handler`
4. `syscall_handler` 保存寄存器后调用 `trap.c` 中的 `trap_dispatch()`
5. `trap_dispatch()` 识别 `T_SYSCALL`，调用 `syscall()` in `kern/syscall.c`
6. `syscall()` 根据系统调用号分派到具体的内核函数
7. 返回值存入 `tf->tf_regs.reg_eax`

#### 用户空间内存检查

```c
// 系统调用在处理用户提供的指针前，必须验证其合法性
user_mem_assert(env, s, len, PTE_U);
// 错误时会销毁环境
```

---

## 7. 多任务调度

### 7.1 调度器 (`kern/sched.c`)

JOS 采用 **轮转调度 (Round-Robin)** 策略：

```c
void sched_yield(void)
{
    struct Env *idle = curenv;
    int start = idle ? ENVX(idle->env_id) + 1 : 0;

    for (int i = 0; i < NENV; i++) {
        int j = (start + i) % NENV;
        if (envs[j].env_status == ENV_RUNNABLE)
            env_run(&envs[j]);   // 切换到可运行环境
    }

    if (idle && idle->env_status == ENV_RUNNING)
        env_run(idle);           // 没有其他环境，继续运行当前

    sched_halt();                // 陷入空闲状态
}
```

- 最多支持 **1024 (NENV)** 个环境
- 每个环境可从 `env_status` 跟踪其状态
- 没有可运行环境时进入 `sched_halt()`：释放大内核锁，执行 `sti; hlt` 等待中断唤醒

### 7.2 大内核锁 (Big Kernel Lock)

JOS 使用一个全局自旋锁保护内核临界区：

```c
struct Spinlock kernel_lock;

lock_kernel();    // 进入内核时获取
unlock_kernel();  // 离开内核时释放
```

AP 启动后必须先获取大内核锁才能调用 `sched_yield()`。

### 7.3 上下文切换

`env_run()` 调用 `env_pop_tf()`，后者：

1. 将 `env_tf` 的寄存器弹出到真实 CPU 寄存器
2. 执行 `iret` 指令返回到用户空间
3. 完成从内核到用户的特权级切换

---

## 8. 进程间通信 (IPC)

JOS 实现了**页面级别的 IPC** 机制：

### 8.1 IPC 系统调用

| 系统调用 | 功能 |
|---------|------|
| `sys_ipc_try_send(envid, value, srcva, perm)` | 尝试向目标发送页面和值 |
| `sys_ipc_recv(dstva)` | 阻塞等待接收 IPC |

### 8.2 IPC 工作流程

```
发送方:                           接收方:
  设置 value, srcva, perm            sys_ipc_recv(dstva)
  sys_ipc_try_send(to, ...)    →     阻塞在 env_ipc_recving=true
    检查目标是否在接收
    如果目标 env_ipc_recving=true:
      复制页面映射到目标的 dstva
      设置目标 env_ipc_value, env_ipc_from, env_ipc_perm
      唤醒目标 (设为 RUNNABLE)
      返回 0
    否则：
      返回 -E_IPC_NOT_RECV
```

### 8.3 FS 和 NS 服务进程的 IPC 使用

- **FS Server** (`fs/serv.c`)：通过 IPC 接收文件操作请求（OPEN, READ, WRITE, STAT 等）
- **NS Server** (`net/`)：通过 IPC 接收网络数据包 (NSREQ_INPUT) 和发送请求 (NSREQ_OUTPUT)

lib/nsipc.c 中封装了 IPC 通信的通用模式：
```c
// 请求-响应模式
ipc_send(fs_env, type, &fsipcbuf, PTE_P|PTE_W|PTE_U);
ipc_recv(NULL, NULL, NULL);
```

---

## 9. 文件系统

### 9.1 架构

JOS 的文件系统采用**微内核设计**——文件系统作为独立的用户态服务进程运行：

```
用户程序 ←→ FS Server (用户态) ←→ IDE 磁盘驱动 (内核态)
                ↑
                └── IPC 通信
```

### 9.2 磁盘布局

```
┌──────────┬──────────┬──────────┬─────────────────────────────────┐
│ Boot     │ Super    │ Bitmap   │      Data Blocks                │
│ Sector   │ Block    │ Blocks   │    (Files + Directories)        │
│  (块0)    │  (块1)   │  (块2+)  │      (从 bitmap 后开始)          │
└──────────┴──────────┴──────────┴─────────────────────────────────┘
```

- **Super Block**：包含魔法数 `FS_MAGIC`、磁盘总块数、根目录文件块号
- **Bitmap**：记录每个块的分配状态（1=空闲, 0=已用）
- **Data Blocks**：存储文件和目录数据

### 9.3 文件结构 (`fs/fs.h`)

```c
struct File {
    char f_name[MAXNAMELEN];          // 文件名 (最大128字节)
    off_t f_size;                      // 文件大小
    uint32_t f_type;                   // 类型: FTYPE_REG / FTYPE_DIR
    uint32_t f_direct[NDIRECT];        // 直接块指针 (10个)
    uint32_t f_indirect;               // 间接块指针
};

struct Super {
    uint32_t s_magic;                  // 魔法数: FS_MAGIC
    uint32_t s_nblocks;                // 磁盘总块数
    struct File s_root;                // 根目录文件
};
```

- 每个文件 10 个直接块，1 个间接块（含 1024 个块指针）
- 最大文件大小 = (10 + 1024) × 4096 ≈ 4MB

### 9.4 关键 FS 操作

| 操作 | 函数 | 文件 |
|------|------|------|
| 初始化 | `fs_init()` | `fs/fs.c` |
| 分配块 | `alloc_block()` | `fs/fs.c` |
| 释放块 | `free_block(blockno)` | `fs/fs.c` |
| 查找文件 | `file_get_block()` | `fs/fs.c` |
| 遍历目录 | `dir_lookup()` | `fs/fs.c` |
| IPC 服务 | `serve_*()` | `fs/serv.c` |

### 9.5 块缓存 (`fs/bc.c`)

```c
// 读取磁盘块到缓存
bc_pgfault(diskaddr(blockno));

// 标记块为脏，回写到磁盘
flush_block(diskaddr(blockno));
```

块缓存使用页故障机制：当访问未映射的磁盘地址时，触发 `bc_pgfault()` 从 IDE 读取数据。

---

## 10. Shell 操作

### 10.1 启动过程

JOS 的 Shell (`user/sh.c`) 由 `init` 进程 (`user/init.c`) 自动启动：

```c
// init.c
while (1) {
    r = spawnl("/sh", "sh", (char*)0);
    wait(r);
}
```

- init 打开控制台作为 fd 0, 1（stdin/stdout）
- 当 shell 退出时，init 重新启动一个新的 shell

### 10.2 支持的命令

JOS 文件系统中内置的用户程序：

| 程序 | 功能 |
|------|------|
| `sh` | Shell 解释器 |
| `ls` | 列出目录内容 |
| `cat` | 显示文件内容 |
| `echo` | 输出文本 |
| `mkdir` | 创建目录 |
| `rm` | 删除文件 |
| `wc` | 字数统计 |
| `grep` | 文本搜索 |
| `kill` | 终止进程 |
| `ln` | 链接文件 |
| `httpd` | HTTP Web 服务器 |

### 10.3 Shell 语法

支持的特殊字符和操作：

```sh
# 输入重定向
cat < filename

# 输出重定向
echo hello > filename

# 管道
echo hello | cat

# 所有命令需要从 / 开始（PATH=/）
ls /
cat /motd
```

### 10.4 Shell 内部实现

Shell 通过以下系统调用实现功能：
- `fork()` + `spawn()`：创建子进程运行命令
- `open()`, `read()`, `write()`, `close()`：文件描述符操作
- `dup()`：复制文件描述符（用于重定向）
- `pipe()`：创建管道
- `wait()`：等待子进程

---

## 11. 网络子系统

### 11.1 架构

```
用户程序 (httpd, echo server)
        │ syscall IPC
        ▼
NS Server (net/serv.c)     ←→   Input Helper (net/input.c)
        │                              │
        │ IPC                          │ sys_pkt_try_recv
        ▼                              ▼
 Output Helper (net/output.c)     E1000 Driver (kern/e1000.c)
        │                              │
        │ sys_pkt_try_send             │ 硬件操作
        └──────────┬───────────────────┘
                   ▼
             E1000 网卡硬件
```

### 11.2 E1000 驱动 (`kern/e1000.c`)

基于 Intel 82540EM 网卡：
- **发送环 (TX Ring)**：驱动→硬件，描述符队列
- **接收环 (RX Ring)**：硬件→驱动，描述符队列 + 数据缓冲区
- **E1000 寄存器**：通过内存映射 I/O (MMIO) 访问，地址 `MMIOBASE + 偏移`

### 11.3 网络协议栈

JOS 集成了 lwIP 协议栈 (`net/lwip/`)：
- IP 层 (IPv4)
- TCP 协议
- UDP 协议
- DHCP 客户端
- DNS 解析
- ICMP 协议
- ARP 协议

### 11.4 网络相关系统调用

```c
SYS_pkt_try_send(buf, len)  // 发送网络包 (非阻塞)
SYS_pkt_try_recv(buf, len)  // 接收网络包 (非阻塞，返回 -E_RX_NO_PACKET)
```

### 11.5 测试网络功能

```bash
# QEMU 会将端口转发到宿主机
# 测试 echo 服务
echo "hello" | nc localhost PORT7

# 测试 HTTP 服务
curl http://localhost:PORT80/

# 使用 JOS 内置 httpd 启动 Web 服务器
httpd
```

---

## 12. 内核监视器

### 12.1 概述

内核监视器 (`kern/monitor.c`) 是内建的调试命令行工具，当内核发生 panic 或系统空闲时进入。

```c
void monitor(struct Trapframe *tf) {
    cprintf("Welcome to the JOS kernel monitor!\n");
    cprintf("Type 'help' for a list of commands.\n");
    // 进入 K> 提示符循环
}
```

### 12.2 内置命令

| 命令 | 功能 |
|------|------|
| `help` | 显示所有可用命令列表 |
| `kerninfo` | 显示内核关键符号地址和内存占用 |
| `backtrace` | 打印栈回溯信息 |

### 12.3 kerninfo 输出示例

```
Special kernel symbols:
  _start                  0010000c (phys)
  entry  f010000c (virt)  0010000c (phys)
  etext  f0101a75 (virt)  00101a75 (phys)
  edata  f0112300 (virt)  00112300 (phys)
  end    f0113060 (virt)  00113060 (phys)
Kernel executable memory footprint: 76KB
```

### 12.4 backtrace 输出示例

```
Stack backtrace:
  ebp f0109e58  eip f0100a62  args 00000001 f0109e80 f0109e98 f0100ed2 00000031
  ebp f0109ed8  eip f01000fc  args 00000000 00000000 f0100058 00000000 00000000
```

---

## 13. 调试指南

### 13.1 GDB 调试

```bash
# 终端1：启动 QEMU 等待 GDB
make qemu-gdb

# 终端2：启动 GDB
make gdb
```

GDB 连接到 QEMU 后可以：

```gdb
# 设置断点
b i386_init
b trap_init
b syscall

# 查看寄存器
info registers

# 查看内存
x/10x 0xf0100000

# 查看栈帧
info stack
backtrace

# 单步执行
si     # 汇编级单步
ni     # 汇编级单步（跳过函数调用）
```

### 13.2 GDB 端口配置

GDB 端口通过用户 UID 自动生成：
```
GDBPORT = (uid % 5000) + 25000
```

`.gdbinit` 文件从 `.gdbinit.tmpl` 自动生成，配置正确的端口号。

### 13.3 常见调试技巧

#### 追踪 trick1：使用 cprintf

在内核代码中加入 `cprintf` 输出调试信息（小心不要在中断上下文中过度使用）：

```c
cprintf("DEBUG: env_id=%08x, status=%d\n", curenv->env_id, curenv->env_status);
```

#### 追踪 trick2：panic 与 backtrace

`_panic()` 会输出文件名、行号和调用栈后进入 monitor：

```c
void _panic(const char *file, int line, const char *fmt, ...) {
    panicstr = fmt;
    asm volatile("cli; cld");
    cprintf("kernel panic on CPU %d at %s:%d: ", cpunum(), file, line);
    // ...
    while (1) monitor(NULL);   // 进入交互式调试
}
```

#### 追踪 trick3：打印寄存器

```c
print_trapframe(tf);    // 打印 Trapframe 完整内容
print_regs(&tf->tf_regs); // 仅打印通用寄存器
```

### 13.4 常见崩溃诊断

| 现象 | 可能原因 |
|------|---------|
| Triple Fault | 双重故障中发生第三个异常，通常是 GDT/IDT 配置错误 |
| Page Fault in Kernel | 访问了未映射的内核地址（检查指针和 KADDR/PADDR 宏） |
| General Protection Fault | 特权级违规（如在内核中使用用户指针） |
| Double Fault | 栈溢出或内核栈问题 |

---

## 14. Lab 实验体系

### 14.1 Lab 1: Booting a PC

**目标**：理解 x86 启动过程，实现内核监视器

**核心文件**：
- `boot/boot.S`：引导汇编代码
- `boot/main.c`：Boot loader C 代码
- `kern/monitor.c`：内核监视器实现

**主要任务**：
- 理解 PC 物理地址空间布局
- 实现 `mon_backtrace()` 栈回溯功能
- 扩展 monitor 命令

### 14.2 Lab 2: Memory Management

**目标**：实现物理内存和虚拟内存管理

**核心文件**：`kern/pmap.c`

**主要任务**：
- Part 1：实现物理页管理 (`page_init`, `page_alloc`, `page_free`)
- Part 2：实现虚拟内存 (`pgdir_walk`, `page_insert`, `page_lookup`)
- Part 3：设置内核地址空间 (`mem_init`)

### 14.3 Lab 3: User-Level Environments

**目标**：实现用户进程、异常处理和系统调用

**核心文件**：
- `kern/env.c`：环境管理
- `kern/trap.c`：中断/异常处理
- `kern/syscall.c`：系统调用

**主要任务**：
- Part A：环境数据结构、`env_create`、`env_run`
- Part B：IDT 初始化、`trap_dispatch`、系统调用实现、页面错误处理

### 14.4 Lab 4: Preemptive Multitasking

**目标**：多处理器支持、COW Fork、IPC

**核心文件**：
- `kern/sched.c`：调度器
- `kern/syscall.c`：fork/IPC 系统调用
- `lib/fork.c`：用户态 fork 实现

**主要任务**：
- Part A：多处理器启动、round-robin 调度
- Part B：Copy-on-Write Fork
- Part C：抢占式调度（时钟中断）、进程间通信

### 14.5 Lab 5: File System

**目标**：实现磁盘文件系统、spawn 机制和 Shell

**核心文件**：
- `fs/fs.c`：文件系统核心
- `fs/serv.c`：FS 服务进程
- `user/sh.c`：Shell 实现

**主要任务**：
- 文件系统：磁盘布局、Bitmap、文件创建/读写
- Spawn：从文件系统加载并执行程序
- Shell：I/O 重定向、管道、命令执行

### 14.6 Lab 6: Network Driver

**目标**：实现 E1000 网卡驱动和网络协议栈集成

**核心文件**：
- `kern/e1000.c` + `kern/e1000.h`：E1000 驱动
- `net/input.c`：网络接收
- `net/output.c`：网络发送
- `net/lwip/`：lwIP 协议栈

**主要任务**：
- 初始化 E1000 网卡（MMIO）
- 实现发送环和接收环管理
- 网络数据包收发系统调用
- 集成 lwIP 协议栈，实现 Web 服务器

---

## 15. 常见问题与技巧

### 15.1 构建相关

```bash
# xv6 构建
cd xv6-public/
make

# xv6 运行
make qemu

# 如果 GDB 端口冲突，可在 conf/env.mk 中覆盖
GDBPORT=26000
```

### 15.2 内核与用户态的区别

| 特性 | 内核态 | 用户态 |
|------|--------|--------|
| 代码地址 | ≥ `KERNBASE` (0xF0000000) | < `ULIM` (0xEF800000) |
| CPL | 0 (最高特权) | 3 (最低特权) |
| 段选择子 | GD_KT / GD_KD | GD_UT / GD_UD |
| 编译宏 | `-DJOS_KERNEL` | `-DJOS_USER` |
| 函数入口 | `i386_init()` | `umain(argc, argv)` |

### 15.3 地址转换宏

```c
// 内核虚拟地址 → 物理地址
#define PADDR(kva)  ((uint32_t)(kva) - KERNBASE)

// 物理地址 → 内核虚拟地址
#define KADDR(pa)   ((void *)((uint32_t)(pa) + KERNBASE))

// 物理页号 → PageInfo 指针
struct PageInfo *page2kva(struct PageInfo *pp);
struct PageInfo *pa2page(physaddr_t pa);
```

### 15.4 常见陷阱

1. **用户指针检查**：系统调用中所有用户提供的指针都必须检查 `user_mem_assert`
2. **页表引用计数**：`page_insert` 和 `page_remove` 必须正确维护 `pp_ref`
3. **IDT 设置**：用户可调用的入口（断点、系统调用）DPL 必须设为 3
4. **多核竞态**：操作全局数据结构前获取大内核锁
5. **环境ID重用**：使用 `envid2env(envid, &e, 1)` 验证环境有效性

### 15.5 xv6 对比 JOS

| 特性 | xv6 | JOS |
|------|-----|-----|
| 设计理念 | 单体内核 | 微内核/混合 |
| 文件系统 | 内核态 | 用户态服务进程 |
| 进程数 | NPROC (64) | NENV (1024) |
| 页表 | 进程独立 | 环境独立 |
| 系统调用 | 内核函数直接调用 | INT + IDT 分发 |
| 网络 | 无 | E1000 + lwIP |

### 15.6 代码规范

- **注释**：JOS 代码风格不鼓励冗余注释，关键逻辑通过代码本身表达
- **错误处理**：使用 `panic()` 处理不可恢复错误，`warn()` 处理可恢复警告
- **断言**：大量使用 `assert()` 检查不变量
- **命名**：内核函数通常带前缀表示所属模块（如 `env_*`, `page_*`, `sys_*`）

---

## 16. 附录：关键数据结构速查

### 16.1 Trapframe 寄存器布局

```
Offset  Field
0x00    reg_edi
0x04    reg_esi
0x08    reg_ebp
0x0C    reg_oesp (original ESP before pusha)
0x10    reg_ebx
0x14    reg_edx
0x18    reg_ecx
0x1C    reg_eax
0x20    tf_es
0x24    tf_ds
0x28    tf_trapno
0x2C    tf_err
0x30    tf_eip
0x34    tf_cs
0x38    tf_eflags
0x3C    tf_esp (user)
0x40    tf_ss
```

### 16.2 环境状态枚举

| 状态 | 值 | 含义 |
|------|-----|------|
| `ENV_FREE` | 0 | 空闲，可被分配 |
| `ENV_DYING` | 1 | 正在销毁中（僵尸状态） |
| `ENV_RUNNABLE` | 2 | 可运行，等待调度 |
| `ENV_RUNNING` | 3 | 正在某个 CPU 上运行 |
| `ENV_NOT_RUNNABLE` | 4 | 不可运行（如等待 IPC） |

### 16.3 环境类型

| 类型 | 值 | 说明 |
|------|-----|------|
| `ENV_TYPE_USER` | 0 | 普通用户进程 |
| `ENV_TYPE_FS` | 1 | 文件系统服务进程 |
| `ENV_TYPE_NS` | 2 | 网络服务进程 |

### 16.4 文件类型

| 类型 | 值 | 说明 |
|------|-----|------|
| `FTYPE_REG` | 0 | 普通文件 |
| `FTYPE_DIR` | 1 | 目录 |

### 16.5 段选择子 (GDT)

| 选择子 | 用途 | DPL |
|--------|------|-----|
| `GD_KT` (0x08) | 内核代码段 | 0 |
| `GD_KD` (0x10) | 内核数据段 | 0 |
| `GD_UT` (0x18) | 用户代码段 | 3 |
| `GD_UD` (0x20) | 用户数据段 | 3 |
| `GD_TSS0` (0x28) | CPU0 TSS | 0 |

### 16.6 页面权限位

| 位 | 宏 | 含义 |
|-----|-----|------|
| 0 | `PTE_P` | Present（页面存在） |
| 1 | `PTE_W` | Writable（可写） |
| 2 | `PTE_U` | User accessible（用户可访问） |
| 3 | `PTE_PWT` | Write-through caching |
| 4 | `PTE_PCD` | Cache disable |
| 5 | `PTE_A` | Accessed（已访问） |
| 6 | `PTE_D` | Dirty（已修改） |
| 7 | `PTE_PS` | Page Size（大页标记） |
| 8 | `PTE_G` | Global（全局页） |
| 9-11 | `PTE_AVAIL` | 软件可用位（用于 COW 等） |

### 16.7 make 目标速查

```bash
make              # 构建所有
make qemu         # 在 QEMU 中运行
make qemu-nox     # 在 QEMU 中运行（无图形）
make qemu-gdb     # QEMU + GDB 调试模式
make gdb          # 连接 GDB
make grade        # 运行评分脚本
make clean        # 清理构建文件
```

---

*本文档基于 MIT 6.828 Fall 2012 课程资料、JOS 源码（Lab 1-6 完整实现）、xv6 源码及课程讲义整理而成。*
