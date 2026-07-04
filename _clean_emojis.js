const fs = require('fs');

// ── 1. Fix index.html sidebar icons ──
let html = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', 'utf8');
html = html.replace('⏻', '⏻');      // power symbol: leave as-is or replace
html = html.replace('🔑', '🔑');    // leave or replace

// Actually replace them with text
html = html.replace("title=\"退出\" @click=\"logout\">\n          <span style=\"font-size: 16px\">⏻</span>", "title=\"退出\" @click=\"logout\">\n          <img src=\"/static/common/logout.svg\" alt=\"退出\" style=\"width:18px;height:18px\">");
html = html.replace("title=\"登录\" @click=\"$router.push('/login')\">\n          <span style=\"font-size: 16px\">🔑</span>", "title=\"登录\" @click=\"$router.push('/login')\">\n          <img src=\"/static/common/login.svg\" alt=\"登录\" style=\"width:18px;height:18px\">");

fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\templates\\index.html', html, 'utf8');
console.log('index.html: sidebar icons replaced');

// ── 2. Fix app.js remaining emojis ──
let js = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', 'utf8');

// Community page emojis
js = js.replace('<h2 class="section-title">🌐 创意社区</h2>', '<h2 class="section-title">创意社区</h2>');
js = js.replace('<p class="section-sub mb-4">发现 AI 创作灵感，分享你的作品</p>', '<p class="section-sub mb-4">发现 AI 创作灵感，分享你的作品</p>');
js = js.replace('<span @click="toggleLike(img)">❤️ {{ img.likeCount || 0 }}</span>', '<span @click="toggleLike(img)" class="like-btn"> {{ img.likeCount || 0 }}</span>');
js = js.replace('<span>📊 {{ img.reportCount || 0 }}</span>', '<span>{{ img.reportCount || 0 }} 次</span>');

// MyWorks page emojis
js = js.replace('<h2 class="section-title">📂 我的作品</h2>', '<h2 class="section-title">我的作品</h2>');
js = js.replace('<span v-if="img.isPublic" style="color:var(--cinnabar)">🌐 已发布</span>', '<span v-if="img.isPublic" style="color:var(--cinnabar)">已发布</span>');
js = js.replace('去生成一些吧 ', '去生成一些吧');

// Settings page (in app.js) - already mostly clean but check
js = js.replace('<h2 class="section-title"> 设置</h2>', '<h2 class="section-title">设置</h2>');
js = js.replace('<h3 class="form-label mb-3"> 个人信息</h3>', '<h3 class="form-label mb-3">个人信息</h3>');
js = js.replace('<h3 class="form-label mb-3"> 生成偏好</h3>', '<h3 class="form-label mb-3">生成偏好</h3>');

// Workflows page emojis
js = js.replace('<h2 class="section-title" style="margin-bottom:0">🔧 我的工作流</h2>', '<h2 class="section-title" style="margin-bottom:0">我的工作流</h2>');
js = js.replace('<button class="btn btn-primary" @click="showCreate = true">+ 新建工作流</button>', '<button class="btn btn-primary" @click="showCreate = true">新建工作流</button>');

// Drop zone emojis in workflows page
js = js.replace('<div class="drop-icon">📂</div>', '<div class="drop-icon"><img src="/static/common/upload.svg" alt="" style="width:40px;height:40px;opacity:0.3"></div>');

// Empty state emojis
js = js.replace('<div style="font-size:48px;margin-bottom:12px">🔧</div>', '<img src="/static/common/workflow.svg" alt="" style="width:64px;height:64px;opacity:0.25;margin-bottom:12px">');

// Workflow card builtin icons
js = js.replace('<span>{{ wf.is_builtin ? \'🏠 内置\' : \' 自定义\' }}</span>', '<span>{{ wf.is_builtin ? \'内置\' : \'自定义\' }}</span>');
js = js.replace('<span v-if="wf.is_public">🌐 公开</span>', '<span v-if="wf.is_public">公开</span>');

// Workflow import modal
js = js.replace('<h3> 导入工作流</h3>', '<h3>导入工作流</h3>');

// Clean up community empty state emoji
js = js.replace('还没有作品，快去生成一些分享吧 ✨', '还没有作品，快去生成一些分享吧');

// Works page remake icon
js = js.replace('<button class="btn btn-ghost text-xs" @click="remake(img)" style="color:var(--cinnabar)"> 生成同款</button>', '<button class="btn btn-ghost text-xs" @click="remake(img)" style="color:var(--cinnabar)">生成同款</button>');

// Fix double spaces from emoji cleanup
js = js.replace(/  +/g, ' ');

fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\app.js', js, 'utf8');
console.log('app.js: emojis cleaned. Size:', js.length);

// ── 3. Fix pages_new.js settings emojis ──
let pn = fs.readFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\pages_new.js', 'utf8');

pn = pn.replace('<h2 class="section-title"> 设置</h2>', '<h2 class="section-title">设置</h2>');
pn = pn.replace('<h3 class="form-label mb-3"> 个人信息</h3>', '<h3 class="form-label mb-3">个人信息</h3>');
pn = pn.replace('<h3 class="form-label mb-3"> 生成偏好</h3>', '<h3 class="form-label mb-3">生成偏好</h3>');
pn = pn.replace('个性化配置与偏好设置</p>', '个性化配置与偏好设置</p>'); // already clean

// Fix double spaces  
pn = pn.replace(/  +/g, ' ');

fs.writeFileSync('D:\\vps\\python\\ComfyUI-yezhi-api\\static\\js\\pages_new.js', pn, 'utf8');
console.log('pages_new.js: cleaned. Size:', pn.length);

// ── Validate ──
try {
  new Function(js);
  console.log('app.js: Syntax OK');
} catch(e) {
  console.log('app.js ERROR:', e.message.substring(0, 100));
}
try {
  new Function(pn);
  console.log('pages_new.js: Syntax OK');
} catch(e) {
  console.log('pages_new.js ERROR:', e.message.substring(0, 100));
}
