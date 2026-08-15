# Coruna - iOS 漏洞利用工具包

> [!CAUTION]
> 本仓库包含捕获的恶意 payload，仅用于教育和研究目的。虽然所有 C2 URL 已被关闭，但 payload 可能仍包含潜在有害代码。

从 `https://sadjd.mijieqi[.]cn/group.html` 提取的针对多个 iOS 版本的漏洞利用工具包。

和人工进行了部分反混淆、符号化处理，并修改为加载解密后的 payload。

这些脚本已修改为支持本地部署，仅包含经过测试的设备漏洞链。

---

## 获取完整 PRO 项目



---

## 项目架构

### 漏洞利用链（三阶段）

本项目实现了完整的 iOS 漏洞利用链，分为三个阶段：

| 阶段 | 功能 | 涉及文件 |
| :--- | :--- | :--- |
| **Stage 1** | WebKit 内存损坏漏洞，获取代码执行权 | `Stage1_*.js` |
| **Stage 2** | PAC（Pointer Authentication Code）绕过，获取内核读写权限 | `Stage2_*.js` |
| **Stage 3** | 沙箱逃逸，获取系统级权限并执行 payload | `Stage3_VariantA.js`, `Stage3_VariantB.js` |

### 支持的 iOS 版本

| 设备 | iOS 版本 | WebKit 漏洞链 |
| :--- | :--- | :--- |
| iPhone 6s+ | 15.4.1 | jacurutu -> VariantB |
| iPhone Xs Max | 16.5 | terrorbird -> seedbell -> VariantB |
| iPhone 15 Pro Max | 17.0 | cassowary -> seedbell_pre -> seedbell_17 -> VariantB |

---

## 新增功能

### Flask 后端管理系统

项目新增了完整的后端管理系统，用于管理和查看从 iOS 设备获取的数据：

**接口说明：**

| 接口 | 方法 | 功能 |
| :--- | :--- | :--- |
| `/api/report` | POST | 接收漏洞利用状态报告 |
| `/api/device-data` | POST | 接收设备数据回传（通讯录、短信、照片等） |
| `/api/results` | GET | 获取漏洞报告列表 |
| `/api/manifest` | GET | 获取 payload 清单 |
| `/api/analysis` | GET | 获取技术分析文档 |

**数据存储：**

- `data/reports.json` - 漏洞利用状态报告
- `data/device_data.json` - 设备数据（通讯录、短信、照片等）

### 管理面板（Dashboard）

访问地址：`http://<本地IP>:5000/`

**四个功能 Tab：**

1. **漏洞报告** - 查看漏洞利用结果统计和详细报告
2. **设备数据** - 查看从设备获取的完整数据（点击展开查看详情）
3. **Payload 管理** - 查看所有可用的 payload 列表
4. **技术分析** - 查看加密方案和漏洞链分析文档

---

## 项目结构

```
coruna/
├── app.py                    # Flask 后端服务（新增）
├── group.html                # 漏洞利用链主入口
├── platform_module.js        # 平台检测模块
├── utility_module.js         # 工具函数模块
├── ANALYSIS.md               # 技术分析文档
├── data/                     # 数据存储目录（新增）
│   ├── reports.json          # 漏洞报告数据
│   └── device_data.json      # 设备数据
├── payloads/                 # 解密后的 payload 文件
│   ├── manifest.json         # payload 清单
│   ├── bootstrap.dylib       # 引导库
│   └── <hash>/               # 按 hash 分组的 payload
│       ├── entry0_type0x08.dylib  # 类型 0x08: 主 payload
│       ├── entry1_type0x09.dylib  # 类型 0x09: 数据采集
│       ├── entry2_type0x0f.dylib  # 类型 0x0f: 权限提升
│       └── entry3_type0x07.bin    # 类型 0x07: 配置数据
├── downloaded/               # 原始下载的加密脚本
├── extracted/                # 提取的二进制文件
├── other/                    # 其他版本的漏洞脚本
├── SpringBoardTweak/         # SpringBoard 插件
└── 展示/                     # 系统截图
    ├── ScreenShot_2026-07-20_100801_636.png  # 漏洞报告
    ├── ScreenShot_2026-07-20_100823_690.png  # 设备数据
    └── ScreenShot_2026-07-20_100830_648.png  # Payload 管理
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors
```

### 2. 启动后端服务

```bash
python app.py
```

后端服务运行在：`http://localhost:5000/`

### 3. 启动前端文件服务

```bash
python -m http.server 8080
```

前端服务运行在：`http://localhost:8080/`

### 4. iOS 设备访问

在 iOS 设备的 Safari 浏览器中访问：

```
http://<你的电脑IP>:8080/group.html
```

设备会自动检测 iOS 版本并执行对应的漏洞链。

---

## 系统展示

### 漏洞报告页面

![漏洞报告](展示/ScreenShot_2026-07-20_100801_636.png)

显示漏洞利用结果统计（总记录数、成功数、失败数、不支持数），以及详细的报告列表。

### 设备数据页面

![设备数据](展示/ScreenShot_2026-07-20_100823_690.png)

按设备分组展示采集到的数据，点击设备卡片可展开查看完整详情：
- 设备信息：UDID、iOS 版本、设备型号、手机号、系统信息、位置
- 用户数据：通讯录、短信、照片
- 原始数据：data_payload、metadata

### Payload 管理页面

![Payload 管理](展示/ScreenShot_2026-07-20_100830_648.png)

展示所有可用的 payload 列表，支持按 hash 或 iOS 版本搜索。

---

## 技术分析

详细的技术分析请参考 [ANALYSIS.md](ANALYSIS.md)，包含：
- ChaCha20 加密方案解析
- F00DBEEF 容器格式
- iOS 版本适配表
- Payload 类型说明

---

## 免责声明

本项目仅用于教育和研究目的。未经授权使用漏洞利用工具攻击他人设备是违法的。使用者需遵守当地法律法规，仅在获得明确授权的设备上进行测试。