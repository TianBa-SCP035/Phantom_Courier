# Phantom Courier

Phantom_Courier 是一个文件监控和自动传输系统，用于部署到实验仪器电脑中，监控硬盘文件，找到指定类型文件，通过 SMB 协议传递给其他 Windows 电脑的共享文件夹，或通过 SSH 协议传递给其他 Linux 服务器。支持黑白名单模式的正则匹配，以及多协议多目标地址文件同步功能，同时提供图形化界面配置和监控。

注：Gating为附加自动门控程序，用于根据实验需求，在文件上传完成后，自动调用其他程序进行图片生成。

## 项目概述

Phantom_Courier 由三个独立的可执行程序组成：

1. **Control** - 主控程序（图形界面）- 通过配置文件调整 Service 参数，监控服务状态
2. **Service** - 核心服务（Windows 服务）- 文件扫描和同结构上传，支持多规则和目标地址
3. **Gating**  - 门控程序（由同事负责）- 接受 Service 的调用，自动圈门并生成结果图和csv文件

## 目录结构

```
Phantom_Courier/
├── build/                        # PyInstaller 打包临时文件
├── dist/                         # 部署目录（用户安装后的目录结构）
│   ├── bin/                     # 可执行文件
│   │   ├── Control.exe           # 主控程序
│   │   ├── Service.exe           # 核心服务
│   │   └── Gating.exe           # 门控程序
│   ├── config/                  # 配置文件
│   │   └── service_config.json  # Service 配置文件
│   ├── data/                    # 数据记录文件
│   │   ├── uploaded.json         # 上传记录
│   │   ├── failed.json           # 失败记录
│   │   ├── dirs.json            # 文件夹记录
│   │   └── gating_records.json   # Gating 调用记录
│   └── logs/                    # 日志文件
│       └── service.log          # Service 运行日志
├── installer/                    # 安装包打包脚本
│   ├── output/                  # 最终安装包输出目录
│   │   └── Phantom_Courier_Setup.exe
│   ├── scripts/                 # 打包脚本
│   │   ├── build_exe.bat        # 从 src 打包 EXE 到 dist
│   │   ├── build_gating.bat     # 打包 Gating.exe
│   │   └── package.bat          # 从 dist 打包安装包
│   └── Phantom_Courier.iss          # Inno Setup 安装脚本
├── src/                          # 源代码目录
│   ├── Control/                   # Control 源代码
│   ├── Gating/                    # Gating 源代码
│   ├── Service/                   # Service 源代码
│   │   ├── config_loader.py      # 配置文件加载器
│   │   ├── logger.py             # 日志记录器
│   │   ├── service_instance.py   # 主服务逻辑
│   │   ├── service_wrapper.py    # Windows 服务包装器
│   │   ├── main.py               # 主入口文件
│   │   ├── test_service.py       # 测试脚本
│   │   ├── scanner/              # 扫描模块
│   │   │   ├── file_filter.py    # 文件过滤器
│   │   │   ├── file_scanner.py   # 文件扫描器
│   │   │   └── stability_checker.py # 稳定性检查器
│   │   ├── uploader/             # 上传模块
│   │   │   ├── sftp_uploader.py  # SFTP 上传器
│   │   │   └── smb_uploader.py   # SMB 上传器
│   │   └── gating/               # Gating 模块
│   │       └── gating_manager.py # Gating 管理器
│   └── workspace_env/             # 开发环境运行目录（结构与 dist 一致）
│       ├── config/               # 开发环境配置文件
│       ├── data/                 # 开发环境数据记录
│       └── logs/                 # 开发环境日志文件
├── tests/                        # 测试文件区
├── .gitignore                    # Git 忽略文件
├── LICENSE                       # 项目许可证
├── README.md                     # 项目说明
└── requirements.txt              # Python 依赖
```

## 1. Service 业务逻辑

Service 是 Phantom Courier 的核心功能，作为 Windows 服务安装，可独立运行。
整体构架的业务逻辑分为三个阶段：

1. **目录遍历阶段** - 扫描根目录，找出符合条件的文件夹
2. **文件判别阶段** - 对每个文件夹，过滤出需要上传的文件
3. **文件上传阶段** - 对需要上传的文件进行稳定性检查和上传（可选功能Gating调用）

### 目录遍历阶段
```
遍历所有根目录（支持多目录，深度优先，逐层遍历）
  ↓
对每个文件夹：
  - 判断是否应该扫描（应用文件夹过滤规则 + 比较修改时间 / always_scan_files 参数）
  ↓
  如果应该扫描：
    - 添加到待处理文件夹列表
  ↓
  如果不应该扫描：
    - 不处理该文件夹
  ↓
  继续遍历子文件夹（os.walk 自动处理）
  ↓
遍历完成后，返回符合条件的文件夹路径列表，并将这些文件夹信息更新到 dirs.json 文件中
```
**关键点**：
- 目录修改时间只有当该文件夹内的文件发生新增、删除、重命名时才会变化
- 如果是子文件夹内发生修改，父文件夹的修改时间不会变化
- 无论是否需要扫描，都继续遍历其子文件夹（可以考虑砍分支加快扫描速度）
- 只有通过了筛选条件的文件夹才会被更新到 dirs 记录文件中
- 如果 `always_scan_files` 为 true，则只要是通过文件夹筛选条件的文件夹（注意黑白名单），无论修改时间是否变化，都会进入文件判别阶段（当文件内部发生修改时，目录时间也不会变化）

### 文件判别阶段
```
1. 获取文件夹内所有条目名（文件名、子文件夹名），循环拼接完整路径（子文件夹过滤）
   ↓
2. 应用文件过滤规则（黑白名单正则），剔除不需要的文件，并获取大小和修改时间信息
   ↓
3. 检查失败记录（failed.json）
   - 如果文件在失败记录中：
     - 检查文件大小或修改时间是否变化
     - 如果变化：添加到待上传列表
     - 如果未变化：检查重试次数
       - 如果重试次数 < retry_count：添加到待上传列表
       - 如果重试次数 >= retry_count：不添加到待上传列表
   - 如果文件不在失败记录中：检查uploaded记录
   ↓
4. 检查上传记录（uploaded.json）
   - 如果文件在上传记录中：
     - 检查文件大小或修改时间是否变化
     - 如果变化：添加到待上传列表
     - 如果未变化：检查所有目标的上传状态
       - 计算期望的目标路径（expected_target_path = target_path + relative_path）
       - 遍历所有目标：
         - 如果某个目标的 status != 'success'：添加到待上传列表
         - 如果某个目标不存在：添加到待上传列表
       - 如果所有目标都上传成功：不添加到待上传列表
   - 如果文件不在上传记录中：
     - 添加到待上传列表
   ↓
5. 每判别完一个目录，立即将文件信息字典传递给上传阶段
```
**关键点**：
- 文件判别阶段返回需要上传的文件字典（包含文件大小时间信息）
- listdir/stat 异常时会跳过对应目录/文件（不中断整轮）。
- 文件过滤规则针对文件名（不包含路径带后缀），第3、4步为互斥分支。
- 外层是目录循环判别，内层是文件循环判别，均为依次执行。

### 文件上传阶段
```
1. 入参：当前目录的“待上传文件字典”
   ↓
2.首次运行特殊分支（upload_on_first_run=false）
   - 找出所有待上传的文件，获取大小、时间信息，不执行文件上传
   - 为每个文件生成各目标的：协议，路径，ip，status，并保存到内存中
   - 保存到记录文件并结束本目录上传流程
   ↓
3. 常规上传分支：初始化 remaining_files（待处理文件列表），为空直接返回0
   - 循环检查文件稳定性（最多 file_check_round 轮，默认 2 轮）：
     - 先按配置做稳定性采样（N次，间隔M秒）
     - 批量判断哪些文件的大小和时间在N次采样中保持一致
     - 遍历稳定文件列表（完整路径）
     - 每个稳定文件开始处理前先取一次最新 os.stat 信息
       - 遍历每个目标地址（本次运行配置参数拼接），执行上传
         - 每个目标如果失败会等待2秒并立即重试1次
         - 立即记录每个目标的上传结果到内存中（协议、ip、路径、status）
         - 若该文件所有目标都成功：从 failed 中移除该文件（如果存在）
         - 若任一目标失败：写入/更新 failed
           - 文件内容变化：retry_count重置为0
           - 文件内容未变化：retry_count + 1
     - 将本轮上传结果落盘到 uploaded、failed、dirs文件中
     - 将“本轮稳定文件”从 remaining_files 移除（不论其上传是否成功）
   - 若 remaining_files 为空：提前结束循环
   ↓
4. 循环结束，再次保存记录返回本目录成功上传数量
```
**上传协议**：
- 支持 SFTP（Linux 服务器）
- 支持 SMB（Windows 共享文件夹）
- 两者可以同时启用，支持多个目标地址
- 保持原文件的目录结构（如 A/123/44/ss.txt → B/123/44/ss.txt）

### Gating 附加功能
```
文件上传阶段结束后，对每个文件夹：
  ↓
1. 如果 Gating 功能已启用且有待上传文件：
   - 获取文件夹内的所有文件信息（重新扫描）
   - 判断文件夹是否为 Gating 文件夹（所有文件都是 .fcs）
   ↓
2. 如果是 Gating 文件夹：
   - 检查文件夹稳定性（使用 check_folder_stability 函数）
   - 如果通过：
     - 执行 Gating 流程
     - 启动独立的 Gating.exe 进程（子进程）
     - 记录为已调用（gating_records.json 中记录）
     - 继续处理下一个文件夹（不等待 Gating 完成）
   - 如果不通过：
     - 跳过，继续下一个文件夹
  ↓
3. 如果不是 Gating 文件夹：
   - 跳过，继续下一个文件夹
```
**关键点**：
- Gating 的调用信息记录在文件中（文件锁防并发冲突）
- 以文件夹路径为主键，记录调用时间、结果等信息
- 由 Control 的前台页面供用户查看


### 服务生命周期

**启动流程**：
1. 加载配置与日志
2. 加载运行记录（uploaded / failed / dirs）
3. 初始化扫描、上传、Gating组件
4. 立即执行一轮扫描
5. 进入定时循环（每 interval 秒）

**停止流程**：
1. 设置停止标志（不再开启新一轮扫描）
2. 唤醒等待中的定时器（可立即响应停止）
3. 等待当前流程在超时时间内结束（最多约60秒）
4. 落盘保存运行记录
5. 断开上传连接并退出

### 记录文件

**data 目录**：
- **uploaded.json** - 上传状态记录
  - 每个文件记录包含：
    - size：文件大小
    - mod_time：文件修改时间
    - destinations：目标地址字典
      - 每个目标包含：
        - protocol：协议类型（sftp 或 smb）
        - ip：服务器 IP 地址
        - target_path：目标路径（包含文件名）
        - upload_time：上传时间
        - status：上传状态（success 或 failed）
- **failed.json** - 上传失败的文件记录
  - 每个文件记录包含：
    - size：文件大小
    - mod_time：文件修改时间
    - error：错误信息
    - retry_count：重试次数
    - last_fail_time：最后失败时间
- **dirs.json** - 文件夹扫描记录
  - 文件夹完整路径：
    - last_dir_mod_time：文件夹最后修改时间
    - last_scan_time：最后扫描时间
- **gating_records.json** - Gating 记录文件
  - 每个文件夹记录包含：
    - call_time：调用时间
    - status：调用状态（ called 或 success ）
    - result_paths：结果文件路径（如果成功，由Gating写入，列表）

**logs 目录**（运行日志）：
- **service.log** - Service 运行日志（DEBUG/INFO/WARNING/ERROR 级别）


### 配置参数

**扫描配置**：
- `root_paths` - 扫描根目录（支持多个路径）
- `interval` - 扫描间隔（秒），开发环境 30 秒，实际环境 30 分钟 = 1800 秒
- `recursive` - 是否递归扫描子文件夹（关闭相当于指定模式）
- `always_scan_files` - 是否总是进行文件扫描（默认 false）

**过滤配置**：
- `folder_mode` - 文件夹过滤模式，whitelist（白名单）或 blacklist（黑名单）
- `file_mode` - 文件过滤模式，whitelist（白名单）或 blacklist（黑名单）
- `include_folders` - 包含的文件夹名称（白名单模式，支持正则表达式，支持多个）
- `exclude_folders` - 排除的文件夹名称（黑名单模式，支持正则表达式，支持多个）
- `include_patterns` - 包含的文件名模式（白名单模式，支持正则表达式，支持多个）
- `exclude_patterns` - 排除的文件名模式（黑名单模式，支持正则表达式，支持多个）
- `exclude_hidden` - 是否排除隐藏文件（以 . 开头的文件）

**稳定性配置**：
- `file_check_count` - 文件稳定性检查次数（连续 N 次大小和修改时间不变才算稳定）
- `file_check_interval` - 文件稳定性检查间隔（秒）
- `file_check_round` - 文件稳定性判别轮次（默认 2 轮）

**上传配置**：
- `enabled` - 是否启用上传功能
- `retry_count` - 上传失败后的重试次数（0 表示不重试）
- `upload_on_first_run` - 首次扫描时是否上传已有文件（默认 true）
- `sftp` - SFTP 默认配置（用于填充 destinations 中的空参数）
  - `host` - SFTP 服务器地址
  - `port` - SFTP 服务器端口（默认 22）
  - `username` - SFTP 登录用户名
  - `password` - SFTP 登录密码
  - `target_path` - SFTP 目标路径
- `smb` - SMB 默认配置（用于填充 destinations 中的空参数）
  - `server_ip` - SMB 服务器 IP 地址
  - `server_port` - SMB 服务器端口（默认 139）
  - `username` - SMB 登录用户名
  - `password` - SMB 登录密码
  - `share_name` - SMB 共享名称
  - `target_path` - SMB 目标路径
- `destinations` - 上传目标数组（支持多个目标）
  - `protocol` - 协议类型（sftp 或 smb）
  - SFTP 协议参数：
    - `host` - SFTP 服务器地址（如果为空，使用 sftp 默认配置）
    - `port` - SFTP 服务器端口（如果为空，使用 sftp 默认配置）
    - `username` - SFTP 登录用户名（如果为空，使用 sftp 默认配置）
    - `password` - SFTP 登录密码（如果为空，使用 sftp 默认配置）
    - `target_path` - SFTP 目标路径（如果为空，使用 sftp 默认配置）
  - SMB 协议参数：
    - `server_ip` - SMB 服务器 IP 地址（如果为空，使用 smb 默认配置）
    - `server_port` - SMB 服务器端口（如果为空，使用 smb 默认配置）
    - `username` - SMB 登录用户名（如果为空，使用 smb 默认配置）
    - `password` - SMB 登录密码（如果为空，使用 smb 默认配置）
    - `share_name` - SMB 共享名称（如果为空，使用 smb 默认配置）
    - `target_path` - SMB 目标路径（如果为空，使用 smb 默认配置）

**Gating 配置**：
- `enabled` - 是否启用 Gating 调用功能
- `exe_path` - Gating 程序路径（相对于 bin 目录）
- `file_extension` - 文件扩展名（文件夹内所有文件必须都是此扩展名才会触发 Gating 调用）

**存储配置**：
- `upload_record_file` - 上传记录文件名（默认 uploaded.json）
- `failed_record_file` - 失败记录文件名（默认 failed.json）
- `dir_record_file` - 文件夹记录文件名（默认 dirs.json）
- `gating_record_file` - Gating 记录文件名（默认 gating_records.json）

**日志配置**：
- `level` - 日志级别（DEBUG、INFO、WARNING、ERROR）
- `log_file` - 日志文件名（存储在 logs 目录）

## 2. Control（主控程序）

Control 是图形界面程序，用于管理和监控 Service。

#### 2.1 功能
**参数配置**
- 读取和修改 Service 配置文件
- 实时保存配置
**服务管理**
- 安装/卸载 Windows 服务
- 启动/停止 Service
- 查看服务运行状态
**日志查看**
- 实时查看 Service 运行日志
- 查看上传记录（data 层面）
- 查看 Gating 记录（data 层面）

## 3. Gating（门控程序）

Gating 是独立的可执行程序，由同事负责。

### 3.1 功能

- 接受文件夹路径作为参数
- 处理文件夹内的文件并生成图片csv等文件
- 将处理结果更新到记录文件（是否成功、结果文件路径）

### 3.2 调用方式

- 由 Service 通过子进程调用
- 传入参数：文件夹路径
- 输出：将结果记录到 data 目录的文件中

## 开发和部署

### 开发环境

- 源代码位于 `src/` 目录
- 配置文件和日志位于 `src/workspace_env/` 目录
- 开发环境扫描间隔：30 秒
- 直接运行 `python src/Service/main.py` 即可测试

### 部署环境

- 可执行文件位于 `dist/bin/` 目录
- 配置文件和日志位于 `dist/` 目录
- 部署环境扫描间隔：30 分钟
- 通过安装包安装后，Service 作为 Windows 服务运行

## 打包和安装

### 打包 EXE

运行 `installer/scripts/build_exe.bat`：
1. 从 `src/` 打包 Control、Service、Gating 到 `dist/bin/`
2. 复制配置文件到 `dist/config/`
3. PyInstaller 临时文件存储在 `build/` 目录

### 打包安装包

运行 `installer/scripts/package.bat`：
1. 调用 `build_exe.bat` 打包 EXE
2. 使用 Inno Setup 将 `dist/` 打包成安装包
3. 安装包输出到 `installer/output/Phantom_Courier_Setup.exe`

### 安装

运行 `installer/output/Phantom_Courier_Setup.exe`：
1. 安装到 `C:\Program Files\Phantom_Courier\`
2. 自动安装 Windows 服务
3. 自动启动 Service

## 技术栈

- **语言**：Python 3.x
- **GUI 框架**：PySimpleGUI（Control）
- **Windows 服务**：pywin32（Service）
- **打包工具**：PyInstaller
- **安装包工具**：Inno Setup
- **上传协议**：
  - SFTP：paramiko
  - SMB：pysmb


## 注意事项

1. **Service 独立运行**：Service 不依赖 Control，可独立作为 Windows 服务运行
2. **配置文件通信**：Control 和 Service 通过配置文件通信，不直接调用
3. **Gating 子进程**：Service 通过子进程调用 Gating，避免 Gating 崩溃影响 Service
4. **日志和记录分离**：log 是运行日志，data 是业务记录
