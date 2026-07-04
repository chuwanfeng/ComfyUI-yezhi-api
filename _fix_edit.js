const fs = require('fs');
let s = fs.readFileSync('static/js/app.js', 'utf8');

const old = `const editWorkflow = (wf) => {
 editingWorkflow.value = wf;
 editData.value = {
 name: wf.name,
 description: wf.description || '',
 comfyui_url: wf.comfyui_url || '',
 cover_url: wf.cover_url || '',
 workflow_json: wf.workflow_json || '',
 };
 };`;

const newFn = `const editWorkflow = async (wf) => {
 editingWorkflow.value = wf;
 editData.value = {
 name: wf.name,
 description: wf.description || '',
 comfyui_url: wf.comfyui_url || '',
 cover_url: wf.cover_url || '',
 workflow_json: '',
 };
 try {
 const d = await api('/api/workflows/' + wf.id + '/json');
 editData.value.workflow_json = JSON.stringify(d.workflow_json || d, null, 2);
 } catch (e) { window.toast.error('加载工作流内容失败'); }
 };`;

if (s.indexOf(old) === -1) { console.log('NOT FOUND'); process.exit(1); }
s = s.replace(old, newFn);
fs.writeFileSync('static/js/app.js', s, 'utf8');
try { new Function(s); console.log('OK, len:', s.length); } catch (e) { console.log('ERR:', e.message.substring(0, 200)); }
