# ComfyUI-yezhi-api 项目初始化

## 目标
将 `D:\vps\python\Dreamifly` (Next.js/Node.js) 改造为 Python 项目 `ComfyUI-yezhi-api`，
前端风格参考 `toonflow-python` 的 TDesign 设计体系 + Vue 3 SPA。

## 技术选型
- **后端**: Python 3 + Flask (蓝图模式)
- **ORM**: SQLAlchemy 2.0 + PostgreSQL
- **认证**: JWT + bcrypt
- **前端**: Vue 3 + Vue Router 4 + Pinia (CDN, 无 Node.js 构建)
- **设计体系**: TDesign CSS 变量系统 (从 toonflow-python 复用)

## 已完成

### 1. 项目骨架 (35 个文件)
- `app.py`: Flask 入口，注册 10 个蓝图
- `config.py`: 环境变量统一管理，`SELF_HOSTED_MODE` 开关
- `.env.example`: 完整环境变量模板
- `requirements.txt`: 13 个核心依赖

### 2. 数据模型 (5 个 model 文件，20+ 表)
- `models/user.py`: user, session, account, verification
- `models/points.py`: user_points, points_record, cdk, subscription, order
- `models/generation.py`: site_stats, model_usage, ip_daily_usage, user_generated_image
- `models/community.py`: community_tag, community_like, image_report
- `models/admin.py`: ip_blacklist, account_blacklist, profanity_words, user_limit_config, avatar_frame, allowed_email_domain

### 3. 工具模块 (6 个 utils)
- `comfy_client.py`: ComfyUI API 封装 (queue_prompt → poll → get_images)
- `model_config.py`: 15 个 AI 模型配置定义（完整复刻 Dreamifly）
- `moderation.py`: 图片/文本审核 (SELF_HOSTED_MODE 直接放行)
- `profanity_filter.py`: 敏感词过滤 (SELF_HOSTED_MODE 直接放行)
- `prompt_optimizer.py`: LLM 提示词优化 (SELF_HOSTED_MODE 且未配置 LLM 时返回原文)
- `storage.py`: 本地/OSS 文件存储
- `auth.py`: JWT 签发/验证

### 4. API 蓝图 (10 个 services, 40+ 端点)
- **auth_api**: 注册/登录/获取用户/修改密码/更新资料
- **generation_api**: 图像生成 (SSE 流式), 快捷模式 (prompt+model) 和直接模式 (workflow JSON)
- **model_api**: 模型列表/详情
- **upload_api**: 文件上传
- **prompt_api**: LLM 提示词优化
- **stats_api**: 站点统计
- **user_api**: 用户配额/作品 CRUD/发布社区
- **points_api**: 积分余额/签到/CDK兑换/套餐列表
- **community_api**: 社区动态/点赞/举报
- **admin_api**: 用户管理/封禁/敏感词/IP黑名单/内容审核

### 5. 前端 (Vue 3 SPA)
- `templates/index.html`: Vue 3 + Vue Router + Pinia CDN 入口
- `static/js/app.js`: 完整 SPA 应用 (~650 行)
  - Pinia store: auth (token/user/selfHosted)
  - 路由: /, /my-works, /community, /profile, /login
  - 组件: Toast, HomePage (生成), MyWorksPage, CommunityPage, AuthPage, ProfilePage
  - 生成页功能: 模型选择→参数配置→SSE 流式接收结果
- `static/css/app.css`: TDesign CSS 变量系统 (38KB, 从 toonflow-python 复用)

### 6. SELF_HOSTED_MODE 开关
设置 `SELF_HOSTED_MODE=true` 后:
- moderation.py: `check_image_safety()` / `check_text_safety()` 直接返回 True
- profanity_filter.py: `contains_profanity()` 直接返回 False
- generation_api.py: `_check_quota()` 跳过限额检查
- user_api.py: 配额返回 `dailyRemaining: -1` (无限制)

## 状态
项目骨架已完成，可直接 `pip install -r requirements.txt` → 配置 `.env` → `python app.py` 启动。
需要补充: 模型封面图片 (static/models/), ComfyUI workflow JSON 模板, 支付宝/邮件具体实现。
