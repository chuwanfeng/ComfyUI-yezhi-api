const fs = require('fs');

// Read app.js
const js = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', 'utf8');
const html = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', 'utf8');

// ── app.js changes ──────────────────────────────────

let jsNew = js;

// Home page: title + copy optimization
jsNew = jsNew.replace(
  '通过AI释放你的',
  '以墨为魂，'
);
jsNew = jsNew.replace(
  '无限想象力',
  '一念万象'
);
jsNew = jsNew.replace(
  '只需一键！',
  ''
);
jsNew = jsNew.replace(
  '          <span class="tag">快速生成</span>\n          <span class="tag">多种模型</span>\n          <span class="tag">无需登录</span>\n          <span class="tag">高度定制</span>\n          <span class="tag">支持中文</span>',
  '          <span class="tag">快速生成</span>\n          <span class="tag">十多种模型</span>\n          <span class="tag">完全免费</span>\n          <span class="tag">自由定制</span>\n          <span class="tag">中文支持</span>'
);
jsNew = jsNew.replace(
  'Yezhi · 免费AI绘画在线生成工具',
  '墨韵 Yezhi · 免费AI绘画在线生成工具'
);
// Remove emoji from section title
jsNew = jsNew.replace(
  /<h2 class="section-title">.*?顶尖 AI 模型<\/h2>/s,
  '<h2 class="section-title">顶尖 AI 模型</h2>'
);
jsNew = jsNew.replace(
  '支持 12+ 主流模型，覆盖动漫、真实、油画等 10+ 风格',
  '支持 12+ 主流模型，覆盖动漫、写实、油画等 10+ 风格'
);
// Remove emoji from hero-stats
jsNew = jsNew.replace(
  '          <div>🖼️ <span class="num">{{ stats.total || 0 }}</span> 次生成</div>',
  '          <div><span class="num">{{ stats.total || 0 }}</span> 次生成</div>'
);
jsNew = jsNew.replace(
  '          <div>📅 今日 <span class="num">{{ stats.daily || 0 }}</span></div>',
  '          <div>今日 <span class="num">{{ stats.daily || 0 }}</span></div>'
);
jsNew = jsNew.replace(
  '🔓 自用模式',
  '自用模式'
);

// Generate page: remove emoji from generate button
jsNew = jsNew.replace(
  '<span style="font-size: 18px">✦</span>',
  ''
);

// Remove emoji from "从我的作品选择" and "添加音频" etc
jsNew = jsNew.replace(
  '📁 从我的作品选择',
  '从我的作品选择'
);
jsNew = jsNew.replace(
  /<span>🎵<\/span>/g,
  ''
);
jsNew = jsNew.replace(
  '📥 松开放入',
  '松开放入'
);
jsNew = jsNew.replace(
  `style="font-size:14px;color:var(--muted-fg)">{{ dragAudio ? '📥 松开放入' : '+ 添加音频' }}`,
  `style="font-size:14px;color:var(--muted-fg)">{{ dragAudio ? '松开放入' : '+ 添加音频' }}`
);
jsNew = jsNew.replace(
  /<span style="font-size:24px;color:var\(--muted-fg\)">{{ dragRef \? '📥' : '\+' }}<\/span>/g,
  '<span style="font-size:24px;color:var(--muted-fg)">{{ dragRef ? \'+\' : \'+\' }}</span>'
);
jsNew = jsNew.replace(
  '📐 自定义工作流',
  '自定义工作流'
);

// Status line emojis
jsNew = jsNew.replace(
  '✅ 生成完成',
  '生成完成'
);
jsNew = jsNew.replace(
  '❌ {{ error }}',
  '{{ error }}'
);

// Works picker modal
jsNew = jsNew.replace(
  '📁 选择参考图',
  '选择参考图'
);

// Community page: "我的作品" image error
jsNew = jsNew.replace(
  /<img v-else :src="img\.thumbnailUrl" :alt="img\.prompt" @error="e => e\.target\.src='\/static\/images\/dreamifly-logo\.jpg'"/g,
  '<img v-else :src="img.thumbnailUrl" :alt="img.prompt" @error="e => e.target.src=\'/static/images/dreamifly-logo.jpg\'"'
);

// model dropdown text: remove emoji
jsNew = jsNew.replace(
  '添加音频',
  '添加音频'
);

// ── index.html changes ──────────────────────────────

let htmlNew = html;

htmlNew = htmlNew.replace(
  'AI 创作平台',
  '墨韵 AI 创作平台'
);

// ── Write back ──────────────────────────────────────

fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', jsNew, 'utf8');
fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', htmlNew, 'utf8');

console.log('Patch done.');
console.log('app.js:', jsNew.length, 'bytes');
console.log('index.html:', htmlNew.length, 'bytes');
