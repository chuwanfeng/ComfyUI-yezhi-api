const fs = require('fs');
let js = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', 'utf8');
let css = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', 'utf8');

// ═══════════════════════════════════════════════
// FIX 1: Hero 区下移 — 用 padding-top 推下去，模型区滚动后才可见
// ═══════════════════════════════════════════════
css = css.replace(
  '.hero {\n  display: grid; grid-template-columns: 1fr 480px; gap: 64px;\n  align-items: center; padding: 40px 56px 32px; max-width: 1600px; margin: 0 auto;\n}',
  '.hero {\n  display: grid; grid-template-columns: 1fr 480px; gap: 64px;\n  align-items: center; padding: 120px 56px 64px; max-width: 1600px; margin: 0 auto;\n  min-height: calc(100vh - 60px);\n}'
);

console.log('FIX 1: hero padding-top 40→120, min-height 100vh-60px (模型区需滚动)');

// ═══════════════════════════════════════════════
// FIX 2: 4K 下文字和图片间距太大 — gap 从固定 64px 改为响应式
// ═══════════════════════════════════════════════
css = css.replace(
  'gap: 64px;\n  align-items: center; padding: 120px 56px 64px; max-width: 1600px;',
  'gap: 64px;\n  align-items: center; padding: 120px 56px 64px; max-width: 1400px;'
);

// 4K 下缩小 gap，限制整体宽度不让两边撑开
css = css.replace(
  '@media (min-width: 1920px) {\n  .page { max-width: 1600px; }\n  .hero { max-width: 1600px; }\n}',
  '@media (min-width: 1920px) {\n  .page { max-width: 1600px; }\n  .hero { max-width: 1400px; gap: 48px; }\n}'
);
css = css.replace(
  '@media (min-width: 2560px) {\n  .page { max-width: 1800px; padding: 48px 64px; }\n  .hero { max-width: 1800px; }\n}',
  '@media (min-width: 2560px) {\n  .page { max-width: 1800px; padding: 48px 64px; }\n  .hero { max-width: 1400px; gap: 48px; }\n}'
);

console.log('FIX 2: hero max-width 1600→1400, 4K gap 64→48');

// ═══════════════════════════════════════════════
// FIX 3: 作品页按钮不要与工作流名同行 — 改为图片下方独立行
// ═══════════════════════════════════════════════
// 当前结构: prompt + actions(同行) → 改为 prompt + actions(独立行)
// 把 actions 从 community-meta 里移出来，放到卡片底部

// 替换作品页的 meta 区域
const oldWorksMeta = `<div class="community-meta">
 <div class="prompt" :title="img.prompt">{{ img.prompt || '无提示词' }}</div>
 <div class="actions">
 <span>{{ img.modelName }}</span>
 <span v-if="img.isPublic" style="color:var(--cinnabar)">已发布</span>
 <span style="margin-left: auto">
 <button class="btn btn-ghost text-xs" @click="remake(img)" style="color:var(--cinnabar)">生成同款</button>
 <button v-if="!img.isPublic" class="btn btn-ghost text-xs" @click="publish(img)">发布</button>
 <button class="btn btn-ghost text-xs" @click="remove(img)">删除</button>
 </span>
 </div>
 </div>`;

const newWorksMeta = `<div class="works-meta">
 <div class="works-prompt" :title="img.prompt">{{ img.prompt || '无提示词' }}</div>
 <div class="works-info">
 <span>{{ img.modelName }}</span>
 <span v-if="img.isPublic" class="status-pill published">已发布</span>
 </div>
 <div class="works-btns">
 <button class="btn btn-ghost btn-sm" @click="remake(img)" style="color:var(--cinnabar)">生成同款</button>
 <button v-if="!img.isPublic" class="btn btn-ghost btn-sm" @click="publish(img)">发布</button>
 <button class="btn btn-ghost btn-sm" @click="remove(img)">删除</button>
 </div>
 </div>`;

js = js.replace(oldWorksMeta, newWorksMeta);
console.log('FIX 3: works page buttons moved to separate row');

// 添加 works-meta CSS
const worksCSS = `
/* ── 作品页卡片: 三段式布局 ─────────────────── */
.works-meta {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.works-prompt {
  font-size: 12px; color: var(--ink-mid);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.works-info {
  display: flex; gap: 8px; align-items: center;
  font-size: 11px; color: var(--ink-fade);
}
.works-btns {
  display: flex; gap: 4px;
  padding-top: 8px;
  border-top: 1px solid var(--ink-border-light);
}
.works-btns .btn { flex: 1; text-align: center; }

/* 状态标签 */
.status-pill {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
}
.status-pill.published {
  background: rgba(74,124,89,0.12);
  color: var(--verdant);
}

/* 小号按钮 */
.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}
`;

css = css.trimEnd() + '\n' + worksCSS + '\n';

// 写回
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', js, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\app.css', css, 'utf8');

try { new Function(js); console.log('app.js: Syntax OK'); } catch(e) { console.log('app.js ERR:', e.message.substring(0,120)); }
console.log('CSS size:', css.length);
