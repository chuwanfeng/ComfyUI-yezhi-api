# ComfyUI-Yezhi-API

> 🎨 企业级 ComfyUI 前端中台 — 多模型调度 / 工作流管理 / 社区 / 积分 / 管理后台，开箱即用的 AI 图像生成平台。

## ✨ 特性

- **15+ 模型统一调度** — 内置 HiDream/Flux/Kontext/SD3.5/Qwen-Image/Z-Image/Wan/LTX 系列模型配置，一键切换
- **工作流即模型** — 支持导入 ComfyUI 原生 JSON 工作流，自动解析参数映射，工作流即插即用
- **参数智能显隐** — 根据工作流类型自动显示/隐藏：提示词、参考图、音频、分辨率、步数、CFG、去噪、帧率、时长
- **多模态生成** — 支持文生图、图生图、图生视频、音频驱动视频、Qwen 图像编辑
- **社区生态** — 作品发布/浏览/点赞/举报/标签筛选/搜索
- **积分系统** — 每日签到 / CDK 兑换 / 积分消费 / 套餐管理
- **管理后台** — 用户管理 / 封禁 / 系统设置 / 站点统计
- **自用模式** — `SELF_HOSTED_MODE=true` 跳过审核/敏感词/限额，零门槛私有部署
- **提示词优化** — 可接 LLM 自动优化提示词（支持 Qwen3-VL 等）
- **多存储后端** — 本地文件系统 / 阿里云 OSS

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 实例（本地或远程）
- （可选）PostgreSQL — 默认使用 SQLite，开箱即用

### 安装

```bash
# 1. 克隆
git clone https://github.com/chuwanfeng/ComfyUI-yezhi-api.git
cd ComfyUI-yezhi-api

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env：
#   - 设置 SECRET_KEY 为随机字符串
#   - 配置至少一个 ComfyUI 模型端点
#   - (可选) 配置 LLM 提示词优化、OSS、支付宝

# 4. 启动
python app.py
# 访问 http://localhost:5090
```

首次运行自动创建 SQLite 数据库和表结构。

### Windows 一键启动

```batch
start.bat
```

---

## 📁 项目结构

```
ComfyUI-yezhi-api/
├── app.py                  # Flask 入口，注册所有 Blueprint
├── config.py               # 配置管理 (读取 .env + 环境变量)
├── .env.example            # 环境变量模板
├── requirements.txt        # Python 依赖
├── start.bat               # Windows 一键启动脚本
│
├── models/                 # SQLAlchemy ORM 数据模型
│   ├── _base.py            # 基类 (UUID / 时间戳)
│   ├── user.py             # 用户模型
│   ├── generation.py       # 生成记录
│   ├── workflow.py         # 工作流 / 模板
│   ├── community.py        # 点赞 / 标签 / 举报
│   ├── points.py           # 积分 / CDK / 套餐
│   ├── admin.py            # 管理操作日志
│   └── setting.py          # 系统设置
│
├── services/               # Flask Blueprint API 层
│   ├── db.py               # 数据库会话工厂
│   ├── auth_api.py         # 注册 / 登录 / JWT 鉴权
│   ├── generation_api.py   # SSE 图像/视频生成核心
│   ├── model_api.py        # 模型列表 / 工作流列表
│   ├── workflow_api.py     # 工作流 CRUD / 导入 / 参数映射
│   ├── community_api.py    # 社区动态 / 点赞 / 举报
│   ├── upload_api.py       # 文件上传
│   ├── user_api.py         # 用户作品 / 个人资料
│   ├── points_api.py       # 积分余额 / 签到 / CDK
│   ├── prompt_api.py       # LLM 提示词优化
│   ├── stats_api.py        # 站点统计
│   ├── settings_api.py     # 系统设置管理
│   └── admin_api.py        # 管理员 API
│
├── utils/                  # 工具模块
│   ├── comfy_client.py     # ComfyUI WebSocket/HTTP 客户端
│   ├── model_config.py     # 15+ 模型配置（宽高比/步数/元数据）
│   ├── auth.py             # JWT 签发 / 验证 / 鉴权装饰器
│   ├── storage.py          # 本地 / OSS 双后端存储
│   ├── prompt_optimizer.py # LLM 提示词优化
│   ├── moderation.py       # 内容审核（自用模式跳过）
│   └── profanity_filter.py # 敏感词过滤（自用模式跳过）
│
├── static/
│   ├── css/app.css         # TDesign 设计体系样式
│   ├── css/new_pages.css   # 新增页面样式
│   ├── js/app.js           # Vue 3 SPA 单文件应用 (~1900行)
│   ├── models/             # 模型/工作流 SVG 封面
│   ├── form/               # 表单图标
│   └── fonts/              # 思源黑体
│
├── templates/
│   └── index.html          # Vue 3 SPA 入口
│
├── workflows/              # 用户工作流 JSON 存储
└── migrations/             # Alembic 数据库迁移
```

---

## 🔧 配置参考

### 自用模式

```env
SELF_HOSTED_MODE=true
```
启用后：跳过审核、敏感词过滤、每日配额限制，无需登录即可使用。

### 模型端点

至少配置一个 ComfyUI 端点，页面才会展示对应模型：

```env
Flux_Dev_URL=http://127.0.0.1:8188
Z_Image_Turbo_URL=http://127.0.0.1:8188
Qwen_Image_URL=http://127.0.0.1:8188
...
```

不配置的模型自动从页面隐藏。

### 工作流导入

支持导入 ComfyUI 原生 JSON 工作流。系统自动：
1. 分析节点类型 → 确定文生图/图生视频/音频驱动/图像编辑
2. 提取参数映射 → prompt / negative_prompt / width / height / steps / cfg / denoise / fps / duration
3. 上传参考图 → 映射到 LoadImage 节点
4. 上传音频 → 映射到 VHS_LoadAudioUpload 节点
5. seed 自动注入 → 无需手动配置

---

## 📡 API 端点

### 认证
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 注册 |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/me` | GET | 当前用户信息 |
| `/api/auth/profile` | PUT | 更新个人资料 |

### 生成
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/generate` | POST | SSE 流式图像/视频生成 |
| `/api/models` | GET | 模型 + 工作流列表 |
| `/api/optimize-prompt` | POST | LLM 提示词优化 |
| `/api/upload` | POST | 文件上传 |
| `/api/stats` | GET | 站点统计 |

### 工作流
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/workflows` | GET | 列表（公开 + 内置 + 我的） |
| `/api/workflows` | POST | 创建 |
| `/api/workflows/import` | POST | 从 ComfyUI JSON 导入 |
| `/api/workflows/:id` | GET/PUT/DELETE | 查看/更新/删除 |

### 用户
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/user/images` | GET | 我的作品列表 |
| `/api/user/images/:id` | DELETE | 删除作品 |

### 社区
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/community/feed` | GET | 社区动态（支持 ?tag= & ?q= 搜索） |
| `/api/community/likes/:id` | POST | 点赞/取消点赞 |
| `/api/community/report` | POST | 举报 |

### 积分
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/points/balance` | GET | 积分余额 |
| `/api/points/award-daily` | POST | 每日签到 |
| `/api/points/cdk/redeem` | POST | CDK 兑换 |
| `/api/points/packages` | GET | 积分套餐 |

### 管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/users/:id/ban` | POST | 封禁/解封 |

---

## 🛠 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | Flask 3.1 + Blueprint |
| 数据库 | SQLAlchemy 2.0 + SQLite / PostgreSQL |
| 认证 | JWT (PyJWT) |
| 前端 | Vue 3 (CDN) + 组件化 SPA |
| UI | TDesign 设计体系 + Tailwind 工具类混合 |
| 实时通信 | Server-Sent Events (SSE) |
| 图像处理 | Pillow |
| 部署 | 单文件 Python SPA (index.html 直接渲染) |

---

## 📄 License

MIT
