const fs = require('fs');
let s = fs.readFileSync('static/js/app.js', 'utf8');

const oldFn = `const publish = async (img) => {
 try {
 await api(\`/api/user/images/\${img.id}/publish\`, { method: 'POST' });
 img.isPublic = true;
 window.toast.success('已发布到社区');
 } catch (e) { window.toast.error(e.message); }
 };`;

const newFn = `const publish = async (img) => {
 try {
 const d = await api(\`/api/user/images/\${img.id}/publish\`, { method: 'POST' });
 img.isPublic = d.isPublic;
 window.toast.success(d.message);
 } catch (e) { window.toast.error(e.message); }
 };`;

if (s.indexOf(oldFn) === -1) { console.log('FN NOT FOUND'); process.exit(1); }
s = s.replace(oldFn, newFn);
fs.writeFileSync('static/js/app.js', s, 'utf8');
try { new Function(s); console.log('OK, len:', s.length); } catch (e) { console.log('ERR:', e.message.substring(0, 200)); }
