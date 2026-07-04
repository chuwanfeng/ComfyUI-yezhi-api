const fs = require('fs');
let js = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', 'utf8');
let css = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', 'utf8');
let html = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', 'utf8');

// ═══════════════════════════════════════════════
// FIX 1: 4K 分辨率下两侧空白过大 — 放宽 max-width
// ═══════════════════════════════════════════════
css = css.replace(
  '.page { padding: 40px 48px; max-width: 1200px; margin: 0 auto; }',
  '.page { padding: 40px 48px; max-width: 1600px; margin: 0 auto; }'
);

// Hero 也要放宽
css = css.replace(
  '.hero {\n  display: grid; grid-template-columns: 1fr 480px; gap: 64px;\n  align-items: center; padding: 72px 56px; min-height: 70vh;\n}',
  '.hero {\n  display: grid; grid-template-columns: 1fr 480px; gap: 64px;\n  align-items: center; padding: 56px 56px; min-height: 60vh; max-width: 1600px; margin: 0 auto;\n}'
);

console.log('FIX 1: max-width 1200→1600, hero padding adjusted');

// ═══════════════════════════════════════════════
// FIX 2: 首页整体下移，模型需滚动才显示 — 缩减 hero 高度
// ═══════════════════════════════════════════════
// 把 min-height: 70vh → 0, 减小 padding, 让模型区域自然跟上
css = css.replace(
  'padding: 56px 56px; min-height: 60vh; max-width: 1600px;',
  'padding: 40px 56px 32px; max-width: 1600px;'
);

// hero-visual 也缩小
css = css.replace(
  '.hero-visual {\n  position: relative; aspect-ratio: 1;',
  '.hero-visual {\n  position: relative; aspect-ratio: 16/10;'
);

// section 间距缩小
css = css.replace(
  '.section { margin-top: 56px; }',
  '.section { margin-top: 32px; }'
);
// 如果没有上面的模式，直接添加
if (!css.includes('.section { margin-top: 32px; }')) {
  css = css.replace('.section {', '.section { margin-top: 32px;');
}

console.log('FIX 2: hero height reduced, section margin tightened');

// ═══════════════════════════════════════════════
// FIX 3: 作品页按钮文字竖排 — actions 布局修复
// ═══════════════════════════════════════════════
// 问题是按钮在窄列中被 flex-wrap 挤成竖排
// 修复: 给 actions 加 white-space:nowrap + flex-wrap:nowrap
js = js.replace(
  `<span style="margin-left: auto">
 <button class="btn btn-ghost text-xs" @click="remake(img)" style="color:var(--cinnabar)">生成同款</button>
 <button v-if="!img.isPublic" class="btn btn-ghost text-xs" @click="publish(img)">发布</button>
 <button class="btn btn-ghost text-xs" @click="remove(img)">删除</button>
 </span>`,
  `<div class="works-actions">
 <button class="btn btn-ghost text-xs" @click="remake(img)" style="color:var(--cinnabar);white-space:nowrap">生成同款</button>
 <button v-if="!img.isPublic" class="btn btn-ghost text-xs" @click="publish(img)" style="white-space:nowrap">发布</button>
 <button class="btn btn-ghost text-xs" @click="remove(img)" style="white-space:nowrap">删除</button>
 </div>`
);

// 也修复 video border-radius 引用
js = js.replace(
  'border-radius:4px 8px 0 0',
  'border-radius:4px 4px 0 0'
);

// 添加 works-actions CSS
const worksActionsCSS = `
/* ── 作品页操作按钮 ─────────────────────────── */
.works-actions {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
  margin-left: auto;
  flex-shrink: 0;
}
.works-actions .btn { white-space: nowrap; }

/* ── 社区/作品网格: 4K 适配 ─────────────────── */
.community-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)) !important;
}

/* ── 4K 超宽屏内容居中 ──────────────────────── */
@media (min-width: 1920px) {
  .page { max-width: 1600px; }
  .hero { max-width: 1600px; }
}
@media (min-width: 2560px) {
  .page { max-width: 1800px; padding: 48px 64px; }
  .hero { max-width: 1800px; }
}
`;

css = css.trimEnd() + '\n' + worksActionsCSS + '\n';

console.log('FIX 3: works-actions nowrap + 4K media queries');

// ═══════════════════════════════════════════════
// FIX 4: 字体 404 — 删除 @font-face 引用，改用 CDN
// ═══════════════════════════════════════════════
// 移除本地 @font-face，用 Google Fonts CDN 替代
css = css.replace(
  /@font-face \{[^}]*\}[^@]*@font-face \{[^}]*\}[^@]*@font-face \{[^}]*\}/s,
  '/* 字体改为 CDN 加载，见 index.html */'
);

// 更彻底：替换所有 @font-face 块
css = css.replace(/@font-face\s*\{[^}]*\}/g, '');
// 清理空行
css = css.replace(/\n{3,}/g, '\n\n');

// 在 index.html 添加 Google Fonts 链接
const fontLinks = `  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=ZCOOL+XiaoWei&display=swap" rel="stylesheet">`;

// 在 </head> 前插入
if (!html.includes('fonts.googleapis.com')) {
  html = html.replace('</head>', fontLinks + '\n</head>');
}

console.log('FIX 4: @font-face removed, Google Fonts CDN added');

// 写回
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', js, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', css, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', html, 'utf8');

// 验证
try { new Function(js); console.log('app.js: Syntax OK'); } catch(e) { console.log('app.js ERR:', e.message.substring(0,120)); }
console.log('CSS size:', css.length);
console.log('HTML size:', html.length);
