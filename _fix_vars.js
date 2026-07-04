const fs = require('fs');

const jsPath = 'D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js';
let js = fs.readFileSync(jsPath, 'utf8');

// Map old CSS vars to new ink-system vars
const varReplacements = [
  // Primary → cinnabar (朱砂红)
  ['var(--primary)', 'var(--cinnabar)'],
  ['var(--primary-lighter)', 'var(--cinnabar-pale)'],
  // Border → ink-border (淡墨边框)
  ['var(--border)', 'var(--ink-border)'],
  ['var(--border-light)', 'var(--ink-border-light)'],
  ['var(--border-lighter)', 'var(--ink-border-light)'],
  // Muted foreground → ink-fade (次墨色)
  ['var(--muted-fg)', 'var(--ink-fade)'],
  ['var(--text-muted)', 'var(--ink-fade)'],
  // Card background
  ['var(--card-bg)', 'var(--card-bg)'],  // already exists, no change
];

for (const [old, replacement] of varReplacements) {
  // Only replace if old is different from new
  if (old !== replacement) {
    js = js.split(old).join(replacement);
  }
}

// Standardize border styles: look for "solid var(--ink-border)" and similar
// Replace legacy border utilities in inline styles
const borderFixes = [
  ['1px solid var(--border)', '1px solid var(--ink-border)'],
  ['2px solid var(--border)', '2px solid var(--ink-border)'],
  ['solid var(--border)', 'solid var(--ink-border)'],
  ['dashed var(--border)', 'dashed var(--ink-border)'],
  ['1px solid var(--border-light)', '1px solid var(--ink-border-light)'],
  ['border: var(--border)', 'border: var(--ink-border)'],
  ['var(--border) !important', 'var(--ink-border) !important'],
  ['var(--color-border)', 'var(--ink-border)'],
  ['color: var(--muted)', 'color: var(--ink-fade)'],
  ['color: var(--text-secondary)', 'color: var(--ink-fade)'],
];

// Only apply if not already using ink- vars
for (const [old, rep] of borderFixes) {
  if (js.includes(old)) {
    js = js.split(old).join(rep);
  }
}

// Fix known inline styles referencing old color values
const inlineStyleFixes = [
  // Text-muted → ink-fade
  ['color:var(--text-muted)', 'color:var(--ink-fade)'],
  ['color: var(--text-muted)', 'color: var(--ink-fade)'],
  // Primary → cinnabar
  ['color:var(--primary)', 'color:var(--cinnabar)'],
  ['color: var(--primary)', 'color: var(--cinnabar)'],
  ['style="color:var(--primary)"', 'style="color:var(--cinnabar)"'],
  ['style="background:var(--primary)"', 'style="background:var(--cinnabar)"'],
  ['style="border-color:var(--primary)"', 'style="border-color:var(--cinnabar)"'],
  // Primary darker variants
  ['style="color:var(--primary-dark)"', 'style="color:var(--cinnabar-dark)"'],
];

for (const [old, rep] of inlineStyleFixes) {
  if (js.includes(old)) {
    js = js.split(old).join(rep);
  }
}

// Write back
fs.writeFileSync(jsPath, js, 'utf8');
console.log('CSS var migration done. New size:', js.length);

// Validate syntax
try {
  new Function(js);
  console.log('Syntax: OK');
} catch (e) {
  console.log('Syntax ERROR:', e.message.substring(0, 120));
}
