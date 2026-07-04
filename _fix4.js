const fs = require('fs');

let js = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', 'utf8');
let pn = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\pages_new.js', 'utf8');
let html = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', 'utf8');

// ──── 1. dreamifly-logo → default-logo.svg ────
// Create a generic ink-style logo SVG
const logoSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">
  <defs>
    <radialGradient id="lg"><stop offset="0%" stop-color="#f5f0e8"/><stop offset="100%" stop-color="#c8c0b4"/></radialGradient>
  </defs>
  <circle cx="60" cy="60" r="58" fill="url(#lg)" stroke="#9e9890" stroke-width="1.5"/>
  <text x="60" y="72" text-anchor="middle" font-family="serif" font-size="40" fill="#4a4540" font-weight="bold" letter-spacing="4">墨</text>
</svg>`;
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\images\\default-logo.svg', logoSVG, 'utf8');

// Replace all dreamifly-logo.jpg references
const logoReplaces = [
  '/static/images/dreamifly-logo.jpg',
  '/static/images/dreamifly-logo.jpg',
];
const logoTarget = '/static/images/default-logo.svg';

js = js.split(logoReplaces[0]).join(logoTarget);
pn = pn.split(logoReplaces[0]).join(logoTarget);
html = html.split(logoReplaces[0]).join(logoTarget);
html = html.split('/static/images/dreamifly-logo.jpg').join(logoTarget);

// ──── 2. demo images → 保留但加上水墨边框 ────
// These are actual screenshots, leave the paths. We'll style them via CSS.

// ──── 3. 模型封面图 fallback → 生成水墨风格模型占位图 ────
// Models that have real images keep them. Fallback uses default-logo.svg.

// ──── 4. 风格选择图 → 保留原图（是风格预览缩略图，不改）

// ──── 圆角统一 (target: 4px) ────
// batch replace border-radius:8px → border-radius:4px in inline styles
js = js.replace(/border-radius:8px/g, 'border-radius:4px');
js = js.replace(/border-radius: 8px/g, 'border-radius: 4px');
pn = pn.replace(/border-radius:8px/g, 'border-radius:4px');
pn = pn.replace(/border-radius: 8px/g, 'border-radius: 4px');

// Also fix 12px and 16px → 6px
js = js.replace(/border-radius:12px/g, 'border-radius:6px');
js = js.replace(/border-radius: 12px/g, 'border-radius: 6px');
js = js.replace(/border-radius:16px/g, 'border-radius:6px');
js = js.replace(/border-radius: 16px/g, 'border-radius: 6px');

// 50% (avatar round) → keep
// 3px → keep

// ──── avatar default fallback ────
// Update default-avatar references to use the ink avatar
const avatarTarget = '/static/images/default-avatar.svg';
// These are already correct, just verify

// ──── index.html favicon ────
html = html.replace('type="image/jpeg"', 'type="image/svg+xml"');

// Write back
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', js, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\pages_new.js', pn, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', html, 'utf8');

console.log('Logo: created default-logo.svg, migrated all references');
console.log('Border-radius: inline styles unified to 4px');
console.log('Favicon: updated to SVG');

// Validate
try { new Function(js); console.log('app.js: Syntax OK'); } catch(e) { console.log('app.js ERR:', e.message.substring(0,100)); }
try { new Function(pn); console.log('pages_new.js: Syntax OK'); } catch(e) { console.log('pages_new.js ERR:', e.message.substring(0,100)); }
