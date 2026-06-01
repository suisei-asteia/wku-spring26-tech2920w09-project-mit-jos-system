# JOS 系统演示教程

> 本文档为 `c:\jos-pku\jos-lab\` 中完整实现的 JOS 操作系统提供分步演示指南，覆盖 Lab 1 至 Lab 6 的全部功能。

---

## 目录

1. [环境要求](#1-环境要求)
2. [快速开始：构建与运行](#2-快速开始构建与运行)
3. [Lab 1 演示：启动、内核监视器与 Backtrace](#3-lab-1-演示启动内核监视器与-backtrace)
4. [Lab 2 演示：内存管理](#4-lab-2-演示内存管理)
5. [Lab 3 演示：用户环境、中断与系统调用](#5-lab-3-演示用户环境中断与系统调用)
6. [Lab 4 演示：多处理器、COW Fork 与 IPC](#6-lab-4-演示多处理器-cow-fork-与-ipc)
7. [Lab 5 演示：文件系统、Spawn 与 Shell](#7-lab-5-演示文件系统spawn-与-shell)
8. [Lab 6 演示：网络驱动与 HTTP 服务](#8-lab-6-演示网络驱动与-http-服务)
9. [自动评分脚本](#9-自动评分脚本)
10. [GDB 调试指南](#10-gdb-调试指南)
11. [常见问题排查](#11-常见问题排查)

---

## 1. 环境要求

| 组件 | 说明 |
|------|------|
| 操作系统 | Linux (Ubuntu 16.04+ 推荐)，或 WSL |
| 交叉编译工具链 | `i386-jos-elf-gcc` 等 (GCCPREFIX) |
| 模拟器 | QEMU (支持 i386) |
| Python | 2.7 或 3.x (运行评分脚本) |
| Perl | 构建辅助 (`sign.pl`, `mergedep.pl`) |

**工具链安装（Ubuntu）：**
```bash
sudo apt-get update
sudo apt-get install -y build-essential gdb git qemu python perl
```

> 详细工具链安装参考: https://pdos.csail.mit.edu/6.828/2018/tools.html

**配置工具链前缀（按需）：**

编辑 `conf/env.mk`，取消注释并设置正确的 `GCCPREFIX`：
```makefile
# 如果系统工具链就是 i386-elf 兼容的：
GCCPREFIX=''

# 如果安装了 i386-jos-elf 前缀的工具链：
# GCCPREFIX='i386-jos-elf-'
```

---

## 2. 快速开始：构建与运行

```bash
cd c:/jos-pku/jos-lab/     # Windows 路径
# 或
cd /mnt/c/jos-pku/jos-lab/ # WSL 路径
```

### 2.1 编译系统

```bash
make
```

首次编译会生成 `obj/` 目录，包含内核镜像 `obj/kern/kernel.img` 和文件系统镜像 `obj/fs/fs.img`。

### 2.2 运行 JOS

```bash
make qemu              # 图形模式
make qemu-nox          # 无图形模式（串口输出到终端）
make qemu-nox CPUS=4   # 模拟 4 核 SMP
```

**退出 QEMU：** 按 `Ctrl-a` 然后按 `x`（无图形模式），或直接关闭 QEMU 窗口。

---

## 3. Lab 1 演示：启动、内核监视器与 Backtrace

### 3.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `boot/boot.S` + `boot/main.c` | Boot loader：从实模式切换到32位保护模式，加载内核 ELF |
| `kern/kdebug.c` | STABS 调试符号解析、行号搜索 |
| `kern/monitor.c` | 内核监视器命令 (`help`, `kerninfo`, `backtrace`) |

### 3.2 演示步骤

**步骤1：运行 JOS 进入内核监视器**

```bash
make qemu-nox
```

你将看到内核监视器提示符：
```
Welcome to the JOS kernel monitor!
Type 'help' for a list of commands.
K>
```

**步骤2：查看可用命令**

```
K> help
help - Display this list of commands
kerninfo - Display information about the kernel
backtrace - Display the stack backtrace
```

**步骤3：查看内核信息**

```
K> kerninfo
Special kernel symbols:
  _start                  0010000c (phys)
  entry  f010000c (virt)  0010000c (phys)
  etext  f0101a75 (virt)  00101a75 (phys)
  edata  f020e000 (virt)  0010e000 (phys)
  end    f020f000 (virt)  0010f000 (phys)
Kernel executable memory footprint: 64KB
```

**步骤4：查看函数调用栈**

```
K> backtrace
Stack backtrace:
  ebp f010ef58  eip f0100a6f  args 00000001 f010ef80 00000000 f0100f9f f0100f84 00000000
  ebp f010ef78  eip f0100a8b  args 00000000 00000000 00000000 f0100f9f f0100f84 00000000
  ebp f010efb8  eip f0100f9f  args 00000000 00000000 00000000 00000000 00000000 00000000
  ebp f010efd8  eip f010003e  args 00000000 00001aac 00000644 00000000 00000000 00000000
  ebp f010eff8  eip f0100045  args 00000000 00000000 00000000 00000000 00000000 00000000
```

---

## 4. Lab 2 演示：内存管理

### 4.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `kern/pmap.c` | `boot_alloc`, `page_init`, `page_alloc`, `page_free`, `page_decref` |
| `kern/pmap.c` | `pgdir_walk`, `boot_map_region`, `page_insert`, `page_lookup`, `page_remove` |
| `kern/pmap.c` | `mem_init`：建立内核虚拟地址空间映射 |

### 4.2 演示步骤

**步骤1：观察内存检测**

启动后观察内核输出：
```
Physical memory: 131072K available, base = 640K, extended = 130432K
```

**步骤2：自动内存检查**

系统在 `mem_init()` 中自动运行多项检查：
```
check_page_free_list() succeeded!
check_page_alloc() succeeded!
check_page() succeeded!
check_kern_pgdir() succeeded!
check_page_installed_pgdir() succeeded!
```

### 4.3 关键数据结构

```
物理内存布局（启动后）：
  0x00000000 - 0x00000FFF  : 保留 (页0, IDT/BIOS)
  0x00001000 - 0x0009EFFF  : 空闲 (base memory)
  0x0009F000 - 0x0009FFFF  : MPENTRY_PADDR (AP 启动代码)
  0x000A0000 - 0x000FFFFF  : I/O Hole
  0x00100000 - ...         : 扩展内存 (内核/空闲)

虚拟地址空间：
  KERNBASE (0xF0000000) 以上 : 内核空间
  UTOP (0xEEC00000) 以上     : 用户只读
  ULIM (0xEF800000) 以上     : 内核空间，用户不可访问
```

---

## 5. Lab 3 演示：用户环境、中断与系统调用

### 5.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `kern/env.c` | `env_init`, `env_setup_vm`, `env_alloc`, `load_icode`, `env_create`, `env_run` |
| `kern/trapentry.S` | 所有异常/中断入口点 (0-19 号 + IRQ) |
| `kern/trap.c` | `trap_init`, `trap_dispatch`, `page_fault_handler` |
| `kern/syscall.c` | `sys_cputs`, `sys_cgetc`, `sys_getenvid`, `sys_env_destroy` |
| `kern/kdebug.c` | `user_mem_check` 用户内存访问验证 |
| `lib/libmain.c` | `thisenv` 指针初始化 |

### 5.2 演示步骤

**步骤1：运行用户程序并触发异常**

```bash
make qemu-nox
```

启动后自动运行 `user_hello`：
```
hello, world
i am environment 00001000
```

**步骤2：演示除零异常保护**

在 Shell 中运行：
```
K> divzero
```

预期输出：
```
Incoming TRAP frame at 0xefffffbc
TRAP frame at 0xf.......
  trap 0x00000000 Divide error
  eip  0x008.....
  ss   0x----0023
.00001001. free env 00001001
```

**步骤3：演示内存越界保护**

```
K> faultread
```

预期显示页面错误并被内核捕获。

**步骤4：演示系统调用 (cputs)**

用户程序通过 `cprintf` 输出字符的过程：
```
用户程序 → sys_cputs() → trap(T_SYSCALL) → trap_dispatch() 
→ syscall(SYS_cputs) → cprintf()
```

---

## 6. Lab 4 演示：多处理器、COW Fork 与 IPC

### 6.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `kern/pmap.c` | `mem_init_mp`：多 CPU 内核栈映射 |
| `kern/trap.c` | `trap_init_percpu`：每 CPU 的 TSS/栈设置 |
| `kern/sched.c` | `sched_yield`：轮转调度 |
| `kern/env.c` | `env_alloc` 中 `FL_IF` 用户态开中断 |
| `kern/syscall.c` | `sys_exofork`, `sys_env_set_status`, `sys_page_alloc`, `sys_page_map`, `sys_page_unmap` |
| `kern/syscall.c` | `sys_env_set_pgfault_upcall`, `sys_ipc_try_send`, `sys_ipc_recv` |
| `lib/pgfault.c` | `set_pgfault_handler`：注册页错误处理 |
| `lib/pfentry.S` | `_pgfault_upcall`：从页错误返回的汇编入口 |
| `lib/fork.c` | `fork`：COW 用户级 fork |
| `lib/ipc.c` | `ipc_send`, `ipc_recv`：进程间通信 |

### 6.2 多处理器演示

```bash
make qemu-nox CPUS=4
```

观察 SMP 启动输出：
```
SMP: CPU 1 starting
SMP: CPU 2 starting
SMP: CPU 3 starting
```

### 6.3 COW Fork 演示

```bash
make qemu-nox
```

在 Shell 中运行 `forktree`：
```
K> forktree
```

预期能看到进程树：
```
1000: I am ''
1001: I am '0'
2002: I am '00'
2003: I am '01'
...
```

**COW 工作原理：**
```
父进程 fork()
  → sys_exofork() 创建子进程
  → duppage() 将父进程页面标记为 PTE_COW（父子都是只读）
  → 子进程写入 COW 页面时触发 pgfault
  → pgfault() 分配新页面、复制数据、重新映射为可写
```

### 6.4 IPC 演示

**Ping-pong 测试：**
```
K> pingpong
```

提示两个进程通过 IPC 互相发送消息。

**素数管道筛选：**
```
K> primes
```

使用 IPC + 管道实现素数筛选。

---

## 7. Lab 5 演示：文件系统、Spawn 与 Shell

### 7.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `fs/fs.c` | `alloc_block`, `file_block_walk`, `file_get_block`, `dir_lookup`, `file_read`, `file_write` |
| `fs/bc.c` | `flush_block`：块缓存回写 |
| `fs/serv.c` | `serve_read`, `serve_write`, `serve_open` |
| `lib/file.c` | `devfile_write`：用户态文件写入 |
| `lib/spawn.c` | `spawn`, `init_stack`, `map_segment`, `copy_shared_pages` |
| `user/sh.c` | Shell：`<` 输入重定向、`>` 输出重定向、`|` 管道 |
| `kern/syscall.c` | `sys_env_set_trapframe` |

### 7.2 演示步骤

**步骤1：进入 Shell**

JOS 启动后自动进入 Shell：
```
$
```

**步骤2：列举文件**

```
$ ls
```

预期输出文件系统根目录下的文件列表。

**步骤3：查看文件内容**

```
$ cat lorem
```

**步骤4：输出重定向**

```
$ cat lorem > newfile
$ cat newfile
```

**步骤5：输入重定向**

```
$ cat < lorem
```

**步骤6：管道**

```
$ cat lorem | cat
```

**步骤7：运行文件系统测试程序**

```
$ testfile
```

**Spawn 创建进程流程：**
```
Shell → spawn(prog, argv)
  → sys_exofork()             创建子进程
  → init_stack()              设置栈（传递 argc/argv）
  → map_segment()             加载 ELF 段
  → sys_env_set_trapframe()    设置入口 eip
  → sys_env_set_status(ENV_RUNNABLE)
  → 子进程开始执行
```

---

## 8. Lab 6 演示：网络驱动与 HTTP 服务

### 8.1 涵盖内容

| 文件 | 实现内容 |
|------|----------|
| `kern/e1000.c` | `e1000_transmit_init`, `e1000_receive_init`, `e1000_transmit`, `e1000_receive` |
| `kern/pci.c` | PCI 设备扫描，E1000 网卡识别与使能 |
| `kern/syscall.c` | `sys_time_msec`, `sys_pkt_try_send`, `sys_pkt_try_receive` |
| `net/input.c` | 网络输入进程：从驱动收包，IPC 发给 NS 服务 |
| `net/output.c` | 网络输出进程：从 NS 服务收包，发给驱动 |
| `net/serv.c` | NS 服务：lwIP TCP/IP 协议栈集成 |
| `user/httpd.c` | HTTP Web 服务器 |

### 8.2 演示步骤

**步骤1：启动 JOS 并观察网络初始化**

```bash
make qemu-nox
```

观察输出：
```
ns: 52:54:00:12:34:56 bound to static IP 10.0.2.15
NS: TCP/IP initialized.
```

**步骤2：查看 E1000 设备状态**

内核输出中包含：
```
device status:[00000183]
```

**步骤3：打开 Web 浏览器，访问 HTTP 服务**

QEMU 默认将 TCP 端口 26080 转发到 JOS 内部的端口 80。

在浏览器中访问：
```
http://localhost:26080/
```

可以看到 JOS HTTP 服务器返回的网页内容。

**步骤4：网络数据流**

```
外部网络
  ↕  QEMU 端口转发 (tcp:26080::80)
E1000 网卡驱动 (kern/e1000.c)
  ↕  sys_pkt_try_send / sys_pkt_try_receive
input 进程 (net/input.c) / output 进程 (net/output.c)
  ↕  IPC
NS 网络服务 (net/serv.c) — lwIP TCP/IP 协议栈
  ↕  socket API
HTTP 服务 (user/httpd.c)
```

---

## 9. 自动评分脚本

JOS 提供 Python 评分脚本来验证各 Lab 实现：

### 9.1 运行评分

```bash
make grade   # 需要先安装 i386-jos-elf-gcc 工具链并编译
```

或单独运行某个 Lab 的评分：
```bash
# Linux 环境下
python grade-lab1
python grade-lab2
python grade-lab3
python grade-lab4
python grade-lab5
python grade-lab6

# 如果 Python 版本问题，试试:
python3 grade-lab1
```

### 9.2 各 Lab 评分项

| Lab | 评分文件 | 主要测试内容 |
|-----|----------|-------------|
| Lab 1 | `grade-lab1` | `printf` 输出、`backtrace` 栈帧数、`backtrace` 参数、符号名、行号 |
| Lab 2 | `grade-lab2` | `check_page_alloc`, `check_page`, `check_kern_pgdir`, `check_page_installed_pgdir` |
| Lab 3 | `grade-lab3` | 除零异常、软中断、段异常、页面错误处理、断点异常、系统调用 |
| Lab 4 | `grade-lab4` | `dumbfork`, `forktree`, `spin`、压力测试、`pingpong`、`primes` |
| Lab 5 | `grade-lab5` | `testfile`、Spawn、Shell `ls`/`cat`/`echo`、重定向 |
| Lab 6 | `grade-lab6` | `testtime`、网络输出/输入、HTTP 请求/响应 |

### 9.3 评分脚本工作原理

1. 启动 QEMU 并运行 JOS
2. 使用 GDB 连接到 QEMU，设置断点
3. 逐项运行测试程序
4. 用正则表达式匹配输出，验证结果
5. 汇总分数

---

## 10. GDB 调试指南

### 10.1 启动调试会话

```bash
# 终端 1：启动带 GDB 支持的 QEMU
make qemu-nox-gdb

# 终端 2：启动 GDB
make gdb
```

### 10.2 常用调试命令

```gdb
# 设置断点
(gdb) b i386_init           # 内核入口
(gdb) b mem_init            # 内存初始化
(gdb) b trap                # 陷阱处理
(gdb) b page_fault_handler  # 页面错误
(gdb) b syscall             # 系统调用分发

# 在用户代码设断点
(gdb) b umain               # 用户程序入口

# 执行控制
(gdb) c                     # 继续执行
(gdb) si                    # 单步执行（机器指令）
(gdb) ni                    # 单步执行（跳过调用）
(gdb) finish                # 执行到函数返回

# 检查状态
(gdb) info registers        # 查看寄存器
(gdb) bt                    # 查看调用栈
(gdb) p/x *pages            # 打印变量
(gdb) x/16x 0xf0100000      # 查看内存

# 切换地址空间
(gdb) symbol-file obj/user/hello     # 加载用户程序符号
(gdb) symbol-file obj/kern/kernel    # 切换回内核符号
```

### 10.3 调试多 CPU

```gdb
(gdb) info threads          # 查看所有 CPU 线程
(gdb) thread 2              # 切换到 CPU 1
```

---

## 11. 常见问题排查

### 11.1 编译错误

**Q: `i386-jos-elf-gcc: command not found`**

A: 配置 `conf/env.mk`，设置 `GCCPREFIX=''` 使用系统 gcc（如果系统 gcc 支持 ELF32-i386），或安装专用工具链。

### 11.2 运行时错误

**Q: `qemu: could not open disk image`**

A: 确保先运行 `make` 编译整个系统。

**Q: `triple fault`**

A: 这通常是 IDT/GDT 或 TSS 设置错误。检查：
- `trap_init()` 中 `SETGATE` 的门类型、DPL 是否正确
- `trap_init_percpu()` 中 TSS 初始化
- GDT 表中的段描述符

**Q: `page_fault in kernel mode`**

A: 内核访问了未映射的虚拟地址。常见原因：
- `mem_init()` 中 KERNBASE 以上映射不完整
- `pgdir_walk()` 返回的指针未通过 `KADDR` 转换

### 11.3 评分脚本错误

**Q: `QEMU启动后无输出`**

A: 确保 `grade-lab*` 脚本中的 Python 路径和 QEMU 路径正确。检查 `conf/env.mk` 中的 `QEMU` 变量。

**Q: `Grade script cannot find jos.out`**

A: QEMU 输出未被重定向。检查 `GNUmakefile` 中 `QEMUOPTS` 的 `-serial mon:stdio` 选项。

---

## 附录A：JOS 启动流程图

```
BIOS
  ↓ 加载引导扇区(512B)到 0x7C00
boot.S (实模式 → 32位保护模式)
  ↓ 设置 GDT、A20、分段
boot/main.c (bootmain)
  ↓ 从磁盘读取内核 ELF → 物理 0x100000
kern/entry.S
  ↓ 设置 entry_pgdir、启用分页
i386_init() (kern/init.c)
  ├─ mem_init()       Lab 2: 内存管理
  ├─ env_init()       Lab 3: 进程管理
  ├─ trap_init()      Lab 3: IDT/中断
  ├─ mp_init()        Lab 4: SMP
  ├─ lapic_init()     Lab 4: 本地 APIC
  ├─ pic_init()       Lab 4: 8259A PIC
  ├─ time_init()      Lab 6: 时钟
  ├─ pci_init()       Lab 6: PCI 扫描
  ├─ lock_kernel()    Lab 4: 大内核锁
  ├─ boot_aps()       Lab 4: 启动 AP
  ├─ ENV_CREATE(fs_fs)   Lab 5: 文件系统服务
  ├─ ENV_CREATE(net_ns)  Lab 6: 网络服务
  ├─ ENV_CREATE(user_*)  Lab 5: 用户进程
  └─ sched_yield()    Lab 4: 调度到用户态
```

## 附录B：关键文件修改清单

| Lab | 文件 | 修改摘要 |
|-----|------|---------|
| Lab 1 | `kern/kdebug.c` | 补全 N_SLINE 行号搜索 |
| Lab 1 | `kern/monitor.c` | 注册 `backtrace` 命令到 commands[] |
| Lab 3 | `kern/trap.c` | 修复 CPL 判断：`(tf->tf_cs & 3) == 0` |
| Lab 5 | `user/sh.c` | 移除管道 `|` 后的死代码 `panic` |
