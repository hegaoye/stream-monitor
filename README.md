# 使用说明

### 框架使用说明

### 安装依赖包

```shell
#安装依赖包, 加入：--break-system-packages 突破限制管理
pip install   --break-system-packages -r  requirements.txt
```

### 启动

```shell
#执行，启动后默认端口为 8080
python main.py
```

### 守护进程

#### 安装 `supervisor`

```shell
apt-get install supervisor
```

#### 配置 `supervisor`

```
文件位置：/etc/supervisor/conf.d/
命名规则：<appname>.conf

[program:monitor]
autorestart=true               ; 程序异常退出后自动重启              
autostart=true                 ; 在 supervisord 启动的时候也自动启动
numprocs=1                     ; 默认为1
redirect_stderr=true           ; 重定向输出的日志
command=python main.py          ; 启动命令 最好绝对路径
user=root                      ; 使用 root 用户来启动该进程
directory=/home/monitor         ; 程序的启动目录
stdout_logfile_maxbytes = 20MB ; 日志最大大小
stdout_logfile_backups = 20    ; 文件保存数量
loglevel=info                  ; 日志级别
stdout_logfile = /var/log/supervisor/flask_server.log ;日志保存文件名
```

#### `supervisor` 操作指令

```
supervisorctl 操作
supervisorctl 是 supervisord 的命令行客户端工具，使用的配置和 supervisord 一样，这里就不再说了。下面，主要介绍 supervisorctl 操作的常用命令：
输入命令 supervisorctl 进入 supervisorctl 的 shell 交互界面：

help # 查看帮助
status # 查看程序状态
stop program_name # 关闭 指定的程序
start program_name # 启动 指定的程序
restart program_name # 重启 指定的程序
tail -f program_name # 查看 该程序的日志
update # 重启配置文件修改过的程序（修改了配置，通过这个命令加载新的配置)

也可以直接通过 shell 命令操作：
supervisorctl status
supervisorctl update
```