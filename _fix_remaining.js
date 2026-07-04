const fs = require('fs');

// ── Fix pages_new.js: strip emojis + migrate CSS vars ──
const pnPath = 'D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\pages_new.js';
let pn = fs.readFileSync(pnPath, 'utf8');

// Strip emojis
const emojiRE = /[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}\u{2702}-\u{27B0}\u{FE00}-\u{FEFF}\u{200D}]/gu;
pn = pn.replace(emojiRE, '');

// Clean double-spaces and unnecessary whitespace from emoji removal
// But be careful not to break template strings
pn = pn.replace(/  +/g, ' ');

// Migrate old CSS vars
pn = pn.replace(/var\(--primary\)/g, 'var(--cinnabar)');
pn = pn.replace(/var\(--border\)/g, 'var(--ink-border)');
pn = pn.replace(/var\(--muted-fg\)/g, 'var(--ink-fade)');
pn = pn.replace(/var\(--text-muted\)/g, 'var(--ink-fade)');
pn = pn.replace(/var\(--card-bg\)/g, 'var(--card-bg)'); // unchanged but safe

fs.writeFileSync(pnPath, pn, 'utf8');
console.log('pages_new.js: emojis stripped, vars migrated. Size:', pn.length);

// ── Fix new_pages.css: remove duplicate rules, update border vars ──
const npPath = 'D:\\vps\\python\\ComfyUI-yezhi-api\\static\\css\\new_pages.css';
let np = fs.readFileSync(npPath, 'utf8');

// Replace any old border/muted vars
np = np.replace(/var\(--border\)/g, 'var(--ink-border)');
np = np.replace(/var\(--border-light\)/g, 'var(--ink-border-light)');
np = np.replace(/var\(--muted-fg\)/g, 'var(--ink-fade)');
np = np.replace(/var\(--primary\)/g, 'var(--cinnabar)');
np = np.replace(/var\(--primary-dark\)/g, 'var(--cinnabar-dark)');

fs.writeFileSync(npPath, np, 'utf8');
console.log('new_pages.css: vars migrated. Size:', np.length);

// Validate both files
try {
  for (const [name, path] of [['app.js', jsPath], ['pages_new.js', pnPath]]) {
    new Function(fs.readFileSync(path, 'utf8'));
    console.log(name + ': Syntax OK');
  }
} catch(e) {
  console.log('Syntax ERROR:', e.message.substring(0, 120));
}
