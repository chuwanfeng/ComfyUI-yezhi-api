const fs = require('fs');
let s = fs.readFileSync('static/js/app.js', 'utf8');
const oldBtn = '<button class="btn btn-primary" @click="showCreate = true">+ 新建工作流</button>';
const newBtn = '<div style="display:flex;gap:8px"><button class="btn btn-secondary" @click="showImport = true">导入工作流</button><button class="btn btn-primary" @click="showCreate = true">+ 新建工作流</button></div>';
if (s.indexOf(oldBtn) === -1) { console.log('NOT FOUND'); process.exit(1); }
s = s.replace(oldBtn, newBtn);
fs.writeFileSync('static/js/app.js', s, 'utf8');
try { new Function(s); console.log('OK, len:', s.length); } catch (e) { console.log('ERR:', e.message.substring(0, 200)); }
