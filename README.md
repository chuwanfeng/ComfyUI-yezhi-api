# ComfyUI-Yezhi-API
# Python 私有化 AI 图像生成平台

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 SELF_HOSTED_MODE=true 和 SECRET_KEY

# 3. 初始化数据库 (需先创建 PostgreSQL 数据库 "yezhi")
python app.py    # 首次运行自动建表

# 或者使用 Alembic 迁移
alembic upgrade head

# 4. 启动
python app.py
# 访问 http://localhost:5000
```

## 目录结构

```
ComfyUI-yezhi-api/
├── app.py              # Flask 入口
├── config.py           # 配置 (读取 .env)
├── .env.example        # 环境变量模板
├── requirements.txt    # Python 依赖
├── models/             # SQLAlchemy ORM 模型
├── services/           # Flask Blueprint API
├── utils/              # 工具模块
│   ├── comfy_client.py    # ComfyUI API 客户端
│   ├── model_config.py    # 15+ 模型配置
│   ├── moderation.py       # 图片/文本审核
│   ├── profanity_filter.py # 敏感词 (自用模式跳过)
│   └── prompt_optimizer.py # LLM 提示词优化
├── templates/
│   └── index.html      # Vue 3 SPA 入口
├── static/
│   ├── css/app.css     # TDesign 设计体系
│   └── js/app.js       # Vue 3 应用
└── migrations/         # Alembic 迁移
```

## 自用模式 (SELF_HOSTED_MODE)

设置 `SELF_HOSTED_MODE=true` 后：
* 🚫 跳过所有内容审核
* 🚫 跳过敏感词过滤
* 🚫 无每日配额限制
* 🚫 无需登录即可使用

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/health | GET | 健康检查 |
| /api/auth/register | POST | 注册 |
| /api/auth/login | POST | 登录 |
| /api/auth/me | GET | 当前用户 |
| /api/generate | POST | 图像生成 (SSE) |
| /api/models | GET | 模型列表 |
| /api/optimize-prompt | POST | LLM 优化提示词 |
| /api/upload | POST | 文件上传 |
| /api/stats | GET | 站点统计 |
| /api/user/quota | GET | 用户配额 |
| /api/user/images | GET/DELETE | 用户作品 |
| /api/community/feed | GET | 社区动态 |
| /api/community/likes/:id | POST | 点赞/取消 |
| /api/community/report | POST | 举报 |
| /api/points/balance | GET | 积分余额 |
| /api/points/award-daily | POST | 每日签到 |
| /api/points/cdk/redeem | POST | CDK 兑换 |
| /api/points/packages | GET | 积分套餐 |
| /api/admin/users | GET | 管理-用户列表 |
| /api/admin/users/:id/ban | POST | 管理-封禁用户 |
