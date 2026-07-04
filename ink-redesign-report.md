# ComfyUI-Yezhi-API 水墨风 UI 改造 — 执行报告

**时间**: 2026-07-04 15:46–16:05  
**Git 标签**: `backup-20260704-ink-redesign`  
**基准**: `backup-20260704-before-ink-redesign`（改造前快照）

---

## 已完成的 Phase

### Phase 1: 设计令牌替换 ✅
**文件**: `static/css/app.css` — 完全重写（29KB）

| 维度 | 原值 | 新值 |
|------|------|------|
| 背景色 | 暖橙渐变 | 宣纸 #f5f0e8 + 纤维纹理 |
| 主色调 | 橙 #f97316 | 朱砂红 #c43a31 |
| 文字色 | #111827 | 浓墨 #1a1a1a |
| 辅助文字 | #6b7280 | 淡墨 #6b6660 |
| 边框 | #e5e7eb | 极淡墨 #c8c0b4 |
| 字体 | 思源黑体(单层) | 马善政(标题)+思源宋体(正文) |
| 卡片圆角 | 16px | 6px |
| 按钮交互 | 上浮阴影 | 印章按压 scale(0.97) |
| 加载动画 | 橙色 spinner | 墨色渐变旋转 |
| 页面动画 | fadeIn 平移 | inkFadeIn 墨晕扩散 |

**颜色变量** — 12 色体系:
- `--paper` / `--card-bg` / `--card-bg-hover`
- `--ink` / `--ink-light` / `--ink-mid` / `--ink-fade` / `--ink-border`
- `--cinnabar` / `--cinnabar-dark` / `--cinnabar-pale`
- `--gold` / `--verdant` / `--indigo`

### Phase 2: 图标系统生成 ✅
**文件**: `static/ink-icons/` 目录 22 组 SVG

| 图标 | 文件 | 设计语言 |
|------|------|---------|
| 快速生成 | generate.svg | 墨滴核心+星芒笔触发散 |
| 社区 | comunity.svg | 远山轮廓+飞鸟+水面 |
| 作品(编辑) | edit.svg | 毛笔斜放 |
| 设置 | faq.svg | 朱砂印章"印"字(残破) |
| 预览 | preview.svg | 展开的画卷 |
| VIP | crown.svg | 金色印章"贵"字(残破) |
| 提示词 | prompt.svg | 墨点+笔锋弧线(灵感迸发) |
| 模型 | models.svg | 层叠水墨方块(山石意象) |
| 上传 | upload.svg | 枯笔飞白云朵+箭头 |
| 负面词 | negative.svg | 朱砂斜杠否定+墨圈 |
| 宽度 | width.svg | 浓墨横笔+箭头+飞白 |
| 高度 | height.svg | 浓墨竖笔+箭头+飞白 |
| 比例 | aspect-ratio.svg | 重叠墨框+虚线暗示 |
| 步数 | steps.svg | 三阶墨色台阶 |
| 积分 | points.svg | 水墨古铜钱(外圆内方) |
| 图片 | image.svg | 墨色山水简笔+朱砂日 |
| 降噪 | denoise.svg | 墨滴涟漪(三层扩散) |
| 分辨率 | resolution.svg | 墨框四角标尺 |
| 数量 | generation-number.svg | 墨笔"三"字+余韵 |
| 默认头像 | default-avatar.svg | 水墨剪影人像 |
| GitHub | github.svg | 墨竹简笔 |
| QQ/微信 | qq.svg / wechat.svg | 水墨简笔画+消息气泡 |

### Phase 3: 模板与 JS 路径迁移 ✅
- `templates/index.html`: 标题改"墨韵"，导航图标全切到 ink-icons
- `static/js/app.js`: 12 处图标路径替换（form→ink-icons, common→ink-icons）
- `static/js/pages_new.js`: 2 处头像路径替换
- `static/css/new_pages.css`: 重写，与水墨系统兼容

### 背景装饰 ✅
- 宣纸纤维纹理（双方向 CSS repeating-linear-gradient）
- 水墨远山剪影（SVG base64，底部固定）
- 散落墨点（7 个 radial-gradient 随机分布）
- 侧边栏淡墨竖线分隔

---

## 回退方式

```bash
# 回退到改造前
git reset --hard backup-20260704-before-ink-redesign

# 回到当前水墨风
git checkout main
```

## 后续待实施（Phase 4-5）

- 字体自托管: 下载 MaShanZheng-Regular.ttf / NotoSerifSC-*.ttf 到 static/fonts/
- 动画系统: 墨迹扩散入场、墨滴加载替换 spinner
- 梅花/墨竹装饰 SVG（角落装饰）
- 登录页 auth-card 微调
