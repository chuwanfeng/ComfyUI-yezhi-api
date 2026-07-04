const fs = require('fs');
const path = require('path');

const file = 'D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js';
let content = fs.readFileSync(file, 'utf8');

const replacements = [
  ['/static/form/prompt.svg', '/static/ink-icons/prompt.svg'],
  ['/static/form/negative.svg', '/static/ink-icons/negative.svg'],
  ['/static/form/upload.svg', '/static/ink-icons/upload.svg'],
  ['/static/form/models.svg', '/static/ink-icons/models.svg'],
  ['/static/form/image.svg', '/static/ink-icons/image.svg'],
  ['/static/form/aspect-ratio.svg', '/static/ink-icons/aspect-ratio.svg'],
  ['/static/form/width.svg', '/static/ink-icons/width.svg'],
  ['/static/form/height.svg', '/static/ink-icons/height.svg'],
  ['/static/form/steps.svg', '/static/ink-icons/steps.svg'],
  ['/static/form/points.svg', '/static/ink-icons/points.svg'],
  ['/static/form/denoise.svg', '/static/ink-icons/denoise.svg'],
  ['/static/form/resolution.svg', '/static/ink-icons/resolution.svg'],
  ['/static/form/generation-number.svg', '/static/ink-icons/generation-number.svg'],
  ['/static/common/generate.svg', '/static/ink-icons/generate.svg'],
  ['/static/common/comunity.svg', '/static/ink-icons/comunity.svg'],
  ['/static/common/edit.svg', '/static/ink-icons/edit.svg'],
  ['/static/common/faq.svg', '/static/ink-icons/faq.svg'],
  ['/static/common/preview.svg', '/static/ink-icons/preview.svg'],
  ['/static/common/crown.svg', '/static/ink-icons/crown.svg'],
  ['/static/common/github.svg', '/static/ink-icons/github.svg'],
  ['/static/common/qq.svg', '/static/ink-icons/qq.svg'],
  ['/static/common/wechat.svg', '/static/ink-icons/wechat.svg'],
  ['/static/images/default-avatar.svg', '/static/ink-icons/default-avatar.svg'],
];

let count = 0;
for (const [old, nu] of replacements) {
  const before = content.length;
  content = content.split(old).join(nu);
  if (content.length !== before) count++;
}

fs.writeFileSync(file, content, 'utf8');
console.log(`Done. ${count} replacements applied. Size: ${content.length}`);

// Verify no old paths remain
const oldPatterns = content.match(/\/static\/(common|form)\//g);
if (oldPatterns) {
  console.log('WARNING: remaining old paths:', oldPatterns);
} else {
  console.log('OK: zero old paths remaining');
}
