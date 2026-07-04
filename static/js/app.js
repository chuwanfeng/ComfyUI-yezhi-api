/**
 * ComfyUI-Yezhi-API — Vue 3 SPA
 * 视觉风格复刻 Dreamifly
 */
const { createApp, ref, computed, reactive, onMounted, watch, nextTick } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;
const { createPinia, defineStore } = Pinia;

// ═══════════════════════════════════════════════
// 全局 Toast
// ═══════════════════════════════════════════════
const toasts = ref([]);
let toastId = 0;
function showToast(message, type = 'info', duration = 3000) {
 const id = ++toastId;
 toasts.value.push({ id, message, type });
 setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, duration);
}
window.toast = {
 success: (m) => showToast(m, 'success'),
 error: (m) => showToast(m, 'error'),
 info: (m) => showToast(m, 'info'),
};

// ═══════════════════════════════════════════════
// 全局 图片灯箱（全站共享）
// ═══════════════════════════════════════════════
const lightboxSrc = ref(null);
const openLightbox = (url) => { lightboxSrc.value = url; };
const closeLightbox = () => { lightboxSrc.value = null; };
// 挂到 window 上供子组件调用
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;

// ═══════════════════════════════════════════════
// API 工具
// ═══════════════════════════════════════════════
async function api(path, opts = {}) {
 const headers = opts.headers || {};
 if (useAuthStore().token) headers.Authorization = `Bearer ${useAuthStore().token}`;
 if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
 headers['Content-Type'] = 'application/json';
 opts.body = JSON.stringify(opts.body);
 }
 const r = await fetch(path, { ...opts, headers });
 if (!r.ok) {
 let err;
 try { err = await r.json(); } catch { err = { error: '请求失败' }; }
 throw new Error(err.error || `HTTP ${r.status}`);
 }
 return r.json();
}

// ═══════════════════════════════════════════════
// Pinia Store
// ═══════════════════════════════════════════════
const useAuthStore = defineStore('auth', {
 state: () => ({
 token: localStorage.getItem('yezhi_token') || '',
 user: null,
 selfHosted: false,
 ready: false,
 }),
 getters: {
 isLoggedIn: (s) => !!s.token && !!s.user,
 },
 actions: {
 async init() {
 try {
 const d = await api('/api/health');
 this.selfHosted = d.self_hosted;
 } catch {}
 if (this.token) await this.fetchMe();
 this.ready = true;
 },
 async fetchMe() {
 try {
 const d = await api('/api/auth/me');
 this.user = d.user;
 } catch {
 this.logout();
 }
 },
 login(token, user) {
 this.token = token;
 this.user = user;
 localStorage.setItem('yezhi_token', token);
 },
 logout() {
 this.token = '';
 this.user = null;
 localStorage.removeItem('yezhi_token');
 },
 },
});

// ═══════════════════════════════════════════════
// 共享: 模型数据 — 仅保留厂商 API 模型
// ═══════════════════════════════════════════════
const FALLBACK_MODELS = [
 { id: 'Qwen-Image', name: 'Qwen-Image', description: '通义千问图像', cover: '/static/models/Qwen-Image.jpg', recommended: true, isText2Image: true, isImageEdit: true, isVideo: false, normalSteps: 30, maxSteps: 50 },
 { id: 'nano-banana', name: 'Nano Banana 2', description: 'Google Gemini Flash', cover: '/static/models/nano-banana-2.jpg', recommended: true, isText2Image: true, isImageEdit: true, isVideo: false, normalSteps: 20, maxSteps: 40 },
];

const STYLES = [
 { id: 'realistic', name: '真实', cover: '/static/styles/realistic.png' },
 { id: 'anime', name: '动漫', cover: '/static/styles/anima.png' },
 { id: 'cartoon', name: '卡通', cover: '/static/styles/cartoon.png' },
 { id: 'oil-painting', name: '油画', cover: '/static/styles/oil-painting.png' },
 { id: 'line-Art', name: '线稿', cover: '/static/styles/line-Art.png' },
 { id: 'pixel', name: '像素', cover: '/static/styles/pixel.png' },
 { id: 'lego', name: '乐高', cover: '/static/styles/lego.png' },
 { id: 'vector-line', name: '矢量', cover: '/static/styles/vector line.png' },
 { id: 'puppet', name: '木偶', cover: '/static/styles/puppet.png' },
 { id: 'risograph', name: '丝印', cover: '/static/styles/risograph.png' },
];

// ═══════════════════════════════════════════════
// 页面: 首页 (Hero 复刻 Dreamifly 风格)
// ═══════════════════════════════════════════════
const HomePage = {
 template: `
 <div>
 <div class="hero">
 <div class="hero-content fade-in">
 <div class="greet">
 <img src="/static/images/default-logo.svg" alt="">
 <div>
 <div class="name">Yezhi</div>
 <div class="sub">墨韵 Yezhi · 免费AI绘画在线生成工具 | 一键生成动漫、插画、艺术图</div>
 </div>
 </div>
 <h1 class="hero-title">
 以墨为魂，<br>
 <span class="accent">一念万象</span>
 </h1>
 <div class="hero-tags">
 <span class="tag">快速生成</span>
 <span class="tag">十多种模型</span>
 <span class="tag">完全免费</span>
 <span class="tag">自由定制</span>
 <span class="tag">中文支持</span>
 </div>
 <p class="hero-desc">
支持nsfw图片、视频生成，<b>免费无限制</b>。
 </p>
 <div class="hero-actions">
 <button class="btn btn-primary" @click="$router.push('/generate')">开始创作</button>
 </div>
 <div class="hero-stats">
 <div><span class="num">{{ stats.total || 0 }}</span> 次生成</div>
 <div>今日 <span class="num">{{ stats.daily || 0 }}</span></div>
 <div v-if="authStore.selfHosted" style="color:var(--cinnabar)">自用模式</div>
 </div>
 </div>
 <div class="hero-visual fade-in">
 <img :src="demos[currentDemo].img" :alt="demos[currentDemo].title">
 <div class="dots">
 <span v-for="(d, i) in demos" :key="i" class="dot" :class="{ active: i === currentDemo }" @click="currentDemo = i"></span>
 </div>
 </div>
 </div>

 <!-- 模型展示 -->
 <div class="section">
 <h2 class="section-title">顶尖 AI 模型</h2>
 <p class="section-sub">支持 12+ 主流模型，覆盖动漫、写实、油画等 10+ 风格</p>
 <div class="model-grid">
 <div v-for="m in models" :key="m.id" class="model-card" @click="goGenerate(m)">
 <img :src="m.cover || '/static/models/' + m.id + '.jpg'" :alt="m.name" @error="e => e.target.src='/static/images/default-logo.svg'">
 <div class="name">{{ m.name }}</div>
 </div>
 </div>
 </div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const models = ref(FALLBACK_MODELS);
 const stats = ref({});
 const currentDemo = ref(0);
 const demos = [
 { img: '/static/images/demo-1.png', title: '动漫' },
 { img: '/static/images/demo-2.png', title: '插画' },
 { img: '/static/images/demo-3.png', title: '艺术' },
 ];

 onMounted(async () => {
 try {
 const d = await api('/api/models');
 if (d.models && d.models.length) {
 models.value = d.models.length > FALLBACK_MODELS.length ? d.models : FALLBACK_MODELS;
 }
 const s = await api('/api/stats');
 stats.value = s;
 } catch {}

 setInterval(() => { currentDemo.value = (currentDemo.value + 1) % demos.length; }, 4000);
 });

 const goGenerate = (m) => {
 sessionStorage.setItem('yezhi_preferred_model', m.id);
 window.location.hash = '/generate';
 };

 return { authStore, models, stats, currentDemo, demos, goGenerate };
 },
};

// ═══════════════════════════════════════════════
// 页面: 生成页 (复刻原项目双栏 + 风格网格)
// ═══════════════════════════════════════════════
const GeneratePage = {
 template: `
 <div class="page fade-in">
 <!-- 提示词区 -->
 <div class="card mb-4">
 <div class="form-label">
 <img src="/static/form/prompt.svg" alt="">提示词
 </div>
 <textarea v-model="prompt" class="textarea" placeholder="请输入英文提示词以获得最佳效果..." rows="3"></textarea>

 <div v-if="showNegative" class="mt-3">
 <div class="form-label">
 <img src="/static/form/negative.svg" alt="">负面提示词
 <span class="text-xs text-muted">(用逗号分隔)</span>
 </div>
 <input v-model="negativePrompt" class="input" placeholder="不希望出现的元素">
 </div>

 <div class="toolbar">
 <button class="tool-btn" @click="randomPrompt">
 <img src="/static/form/prompt.svg" alt="">随机提示词
 </button>
 <button class="tool-btn" @click="showStylePicker = !showStylePicker">
 <img src="/static/form/image.svg" alt="">风格
 </button>
 <button class="tool-btn" @click="cycleRatio">
 <img src="/static/form/aspect-ratio.svg" alt="">{{ ratio }}
 </button>
 <button class="tool-btn" @click="optimizePrompt" :disabled="optimizing || !prompt">
 <img src="/static/form/prompt.svg" alt="">{{ optimizing ? '优化中...' : '优化提示词' }}
 </button>
 <div style="margin-left: auto">
 <button class="btn btn-generate" @click="generate" :disabled="generating || !prompt">
 
 {{ generating ? '生成中...' : '生成图片' }}
 </button>
 </div>
 </div>
 </div>

 <!-- 配置 + 预览 -->
 <div class="f gap-4" style="align-items: flex-start">
 <!-- 左: 配置 -->
 <div class="card" style="width: 480px; flex-shrink: 0">
 <!-- 上传参考图（多图） -->
 <div class="form-label">
 <img src="/static/form/upload.svg" alt="">上传参考图片
 <span class="text-xs text-muted">(可选, 用于图生图/图像编辑)</span>
 </div>
 <div class="f gap-2" style="flex-wrap:wrap;align-items:flex-start"
 @dragenter.prevent="dragRef = true"
 @dragover.prevent="dragRef = true"
 @dragleave.prevent="dragRef = false"
 @drop.prevent="onRefDrop"
 :class="{ 'drop-highlight': dragRef }">
 <div v-for="(img, i) in referenceImages" :key="i" style="position:relative;width:80px;height:80px;border-radius:4px;overflow:hidden;border:1px solid var(--ink-border)">
 <img :src="img" style="width:100%;height:100%;object-fit:cover">
 <button @click="referenceImages.splice(i,1)" class="btn btn-ghost" style="position:absolute;top:2px;right:2px;background:rgba(0,0,0,.6);color:#fff;width:20px;height:20px;line-height:1;font-size:12px;padding:0;border-radius:50%">×</button>
 </div>
 <div class="upload-zone" @click="triggerUpload" :class="{ 'drag-over': dragRef }" style="width:80px;height:80px;min-height:auto;border:dashed 2px var(--ink-border);display:flex;align-items:center;justify-content:center;cursor:pointer;border-radius:4px;flex-shrink:0">
 <span style="font-size:24px;color:var(--ink-fade)">{{ dragRef ? '+' : '+' }}</span>
 </div>
 <input ref="fileInput" type="file" accept="image/*" multiple @change="onFileSelected" style="display:none">
 </div>
 <div style="margin-top:4px">
 <button class="btn btn-ghost text-xs" @click="openWorksPicker">从我的作品选择</button>
 </div>

 <!-- 音频拖放 -->
 <div class="form-label mt-3">
 <img src="/static/form/prompt.svg" alt="">音频参考
 </div>
 <div class="f gap-2" style="flex-wrap:wrap;align-items:flex-start"
 @dragenter.prevent="dragAudio = true"
 @dragover.prevent="dragAudio = true"
 @dragleave.prevent="dragAudio = false"
 @drop.prevent="onAudioDrop"
 :class="{ 'drop-highlight': dragAudio }">
 <div v-for="(a, i) in audioFiles" :key="i" style="position:relative;height:36px;display:flex;align-items:center;padding:0 8px;border-radius:4px;background:var(--card-bg);border:1px solid var(--ink-border);font-size:12px;gap:6px">
 
 <span style="max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ a.name || '音频 '+(i+1) }}</span>
 <button @click="audioFiles.splice(i,1)" class="btn btn-ghost" style="margin-left:4px;width:18px;height:18px;line-height:1;font-size:11px;padding:0;border-radius:50%;background:rgba(0,0,0,.5);color:#fff">×</button>
 </div>
 <div class="upload-zone" @click="triggerAudio" :class="{ 'drag-over': dragAudio }" style="height:36px;min-height:auto;border:dashed 2px var(--ink-border);display:flex;align-items:center;justify-content:center;cursor:pointer;border-radius:4px;flex-shrink:0;padding:0 12px">
 <span style="font-size:14px;color:var(--ink-fade)">{{ dragAudio ? '松开放入' : '+ 添加音频' }}</span>
 </div>
 <input ref="audioInput" type="file" accept="audio/*" @change="onAudioSelected" style="display:none">
 </div>

 <!-- 模型选择 -->
 <div class="form-label mt-4">
 <img src="/static/form/models.svg" alt="">模型
 </div>
 <div class="model-selector" @click="modelDropdownOpen = !modelDropdownOpen">
 <img :src="selectedModel.cover || '/static/models/' + selectedModel.id + '.jpg'" class="thumb" @error="e => e.target.style.display='none'">
 <div class="name">{{ selectedModel.name }}</div>
 <div class="tags">
 <span v-if="selectedModel.isText2Image" class="tag" style="font-size:10px;padding:2px 6px">文生图</span>
 <span v-if="selectedModel.isImageEdit" class="tag" style="font-size:10px;padding:2px 6px;background:#d1fae5;color:#047857">图像编辑</span>
 </div>
 <span style="color: var(--ink-fade)">▾</span>
 </div>
 <div v-if="modelDropdownOpen" class="card mt-2" style="padding: 8px; max-height: 240px; overflow-y: auto">
 <div v-for="m in models" :key="m.id" class="model-selector mb-1" style="padding:6px" @click.stop="selectModel(m)">
 <img :src="m.cover || '/static/models/' + m.id + '.jpg'" class="thumb" @error="e => e.target.style.display='none'">
 <div class="name">{{ m.name }}</div>
 <span class="text-xs text-muted">{{ m.description }}</span>
 </div>
 <div v-if="workflows.length" style="padding:6px 0; border-top:1px solid var(--ink-border); margin:4px 0; font-size:11px; color:var(--ink-fade)">自定义工作流</div>
 <div v-for="w in workflows" :key="'wf_'+w.id" class="model-selector mb-1" style="padding:6px" @click.stop="selectModel(w)">
 <img :src="w.cover_url || '/static/common/workflow.svg'" class="thumb" @error="e => e.target.style.display='none'">
 <div class="name">{{ w.name }}</div>
 <span class="text-xs text-muted">{{ w.description || '自定义工作流' }}</span>
 </div>
 </div>

 <!-- 风格选择器 -->
 <div v-if="showStylePicker" class="mt-3">
 <div class="form-label">选择风格</div>
 <div class="style-grid">
 <div v-for="s in styles" :key="s.id" class="style-card" :class="{ selected: selectedStyle === s.id }" @click="selectStyle(s)">
 <img :src="s.cover" :alt="s.name" @error="e => e.target.src='/static/images/default-logo.svg'">
 <div class="name">{{ s.name }}</div>
 </div>
 </div>
 </div>

 <!-- 高级选项 -->
 <div class="advanced-trigger mt-3" :class="{ open: showAdvanced }" @click="showAdvanced = !showAdvanced">
 展开高级选项
 </div>
 <div class="advanced-content" :class="{ open: showAdvanced }">
 <div class="param-row" style="margin-bottom:8px">
 <div style="flex:1">
 <div class="text-xs text-muted mb-1">宽度</div>
 <input v-model.number="customW" type="number" min="64" max="2048" class="input" placeholder="自动">
 </div>
 <div style="flex:1; margin-left:8px">
 <div class="text-xs text-muted mb-1">高度</div>
 <input v-model.number="customH" type="number" min="64" max="2048" class="input" placeholder="自动">
 </div>
 </div>
 <div class="param-grid">
 <div>
 <div class="text-xs text-muted mb-1">步数</div>
 <input v-model.number="steps" type="number" min="1" :max="selectedModel.maxSteps || 50" class="input">
 </div>
 <div>
 <div class="text-xs text-muted mb-1">生成数量</div>
 <input v-model.number="batchSize" type="number" min="1" max="4" class="input">
 </div>
 <div>
 <div class="text-xs text-muted mb-1">时长(秒)</div>
 <input v-model.number="duration" type="number" min="1" max="60" class="input" placeholder="自动">
 </div>
 <div>
 <div class="text-xs text-muted mb-1">帧率</div>
 <input v-model.number="fps" type="number" min="8" max="60" class="input" placeholder="自动">
 </div>
 <div v-if="selectedModel && selectedModel.type === 'workflow'">
 <div class="text-xs text-muted mb-1">音频开始帧</div>
 <input v-model.number="audioStartTime" type="number" min="0" class="input" placeholder="0">
 </div>
 <div v-if="selectedModel && selectedModel.type === 'workflow'">
 <div class="text-xs text-muted mb-1">音频长度(秒)</div>
 <input v-model.number="audioDuration" type="number" min="1" class="input" placeholder="全段">
 </div>
 </div>
 </div>
 </div>

 <!-- 右: 预览大图 -->
 <div class="preview-card flex-1">
 <div class="preview-header">
 <h3>
 <img src="/static/common/preview.svg" alt="" style="width:18px;height:18px;vertical-align:middle;margin-right:6px">
 预览
 </h3>
 <button v-if="results.length" class="btn btn-secondary" @click="downloadAll">下载图片</button>
 </div>

 <div class="preview-image">
 <div v-if="generating" class="text-center">
 <div class="spin" style="margin: 0 auto 12px"></div>
 <div class="text-sm text-muted">生成中... 请耐心等待</div>
 <div class="progress mt-3" style="width: 200px; margin: 12px auto 0">
 <div class="progress-bar" :style="{ width: progress + '%' }"></div>
 </div>
 <div class="text-xs text-muted mt-2">{{ statusText }}</div>
 </div>
 <div v-else-if="results.length" class="fc ac gap-3" style="width:100%">
 <template v-for="(r, i) in results" :key="i">
 <video v-if="r.mediaType === 'video'" :src="r.url" controls preload="metadata" style="max-width:100%;border-radius:4px"></video>
 <img v-else :src="r.url" :alt="'Result ' + (i+1)" style="max-width:100%;border-radius:4px;cursor:pointer" @click="zoomImage(r.url)">
 </template>
 </div>
 <div v-else class="empty">
 <img src="/static/common/preview.svg" alt="">
 <div class="mt-2 text-sm">点击「生成图片」开始创作</div>
 <div class="text-xs text-muted mt-1">图片生成可能耗时较长，请耐心等待</div>
 </div>
 </div>

 <div v-if="results.length" class="status-line success">生成完成 ({{ elapsed }}s) · {{ results.length }} 个{{ lastMediaType === 'video' ? '视频' : '图片' }}</div>
 <div v-if="error" class="status-line error">{{ error }}</div>
 </div>
 </div>

 <!-- 作品选择弹窗 -->
 <div v-if="showWorksPicker" class="modal-overlay" @click.self="showWorksPicker=false">
 <div class="modal" style="max-width:640px">
 <div class="modal-header">
 <h3>选择参考图</h3>
 <button class="btn btn-ghost" @click="showWorksPicker=false">×</button>
 </div>
 <div class="modal-body">
 <div v-if="worksPickerLoading" class="text-center p-4"><div class="spin"></div></div>
 <div v-else-if="myWorks.length === 0" class="text-center p-4 text-muted">还没有作品</div>
 <div v-else class="works-picker-grid">
 <div v-for="img in myWorks" :key="img.id" class="works-picker-item" @click="pickReference(img)">
 <img :src="img.imageUrl" :alt="img.prompt" @error="e => e.target.style.display='none'">
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const models = ref(FALLBACK_MODELS);
 const workflows = ref([]);
 const styles = ref(STYLES);
 const selectedModel = ref(FALLBACK_MODELS[0]);
 const selectedStyle = ref(null);
 const modelDropdownOpen = ref(false);
 const showStylePicker = ref(false);
 const showAdvanced = ref(false);
 const showNegative = ref(false);

 const prompt = ref('');
 const negativePrompt = ref('');
 const ratio = ref('1:1');
 const customW = ref(null);
 const customH = ref(null);
 const steps = ref(28);
 const batchSize = ref(1);
 const duration = ref(null); // 视频时长（秒）
 const fps = ref(null); // 视频帧率
 const lastMediaType = ref('image');
 const audioStartTime = ref(0);
 const audioDuration = ref(null); // 最近一次生成类型
 const dragRef = ref(false);
 const referenceImages = ref([]);
 const fileInput = ref(null);

 const dragAudio = ref(false);
 const audioFiles = ref([]);
 const audioInput = ref(null);

 const generating = ref(false);
 const optimizing = ref(false);
 const results = ref([]);
 const error = ref('');
 const progress = ref(0);
 const statusText = ref('');
 const elapsed = ref(0);

 // works picker
 const showWorksPicker = ref(false);
 const worksPickerLoading = ref(false);
 const myWorks = ref([]);

 const RATIOS = ['1:1', '16:9', '9:16', '4:3', '3:4'];

 onMounted(async () => {
 try {
 const d = await api('/api/models');
 if (d.models && d.models.length) {
 models.value = d.models;
 selectedModel.value = d.models[0];
 }
 } catch {}
 // 加载用户工作流
 try {
 const wd = await api('/api/workflows/my');
 workflows.value = (wd.workflows || []).map(w => ({ ...w, type: 'workflow' }));
 } catch {}
 const preferred = sessionStorage.getItem('yezhi_preferred_model');
 if (preferred) {
 const m = models.value.find(x => x.id === preferred) || workflows.value.find(x => x.id === preferred);
 if (m) selectedModel.value = m;
 sessionStorage.removeItem('yezhi_preferred_model');
 }
 // 「生成同款」参数恢复
 const remakeData = sessionStorage.getItem('yezhi_remake');
 if (remakeData) {
 try {
 const rm = JSON.parse(remakeData);
 prompt.value = rm.prompt || '';
 negativePrompt.value = rm.negativePrompt || '';
 steps.value = rm.steps || 28;
 ratio.value = rm.ratio || '1:1';
 // 恢复宽高
 if (rm.width) customW.value = rm.width;
 if (rm.height) customH.value = rm.height;
 // 恢复视频参数
 if (rm.duration) duration.value = rm.duration;
 if (rm.fps != null) fps.value = rm.fps;
 if (rm.audioStartTime != null) audioStartTime.value = rm.audioStartTime;
 if (rm.audioDuration != null) audioDuration.value = rm.audioDuration;
 if (rm.mediaType) lastMediaType.value = rm.mediaType;
 // 恢复参考图
 if (rm.referenceImages && rm.referenceImages.length) {
 referenceImages.value = rm.referenceImages;
 }
 // 恢复音频文件
 if (rm.audioFiles && rm.audioFiles.length) {
 audioFiles.value = rm.audioFiles;
 }
 // 展开高级选项（有自定义参数时）
 if (rm.width || rm.height || rm.duration || rm.fps || rm.audioStartTime || rm.audioDuration) showAdvanced.value = true;
 // 尝试匹配模型或工作流
 if (rm.workflowId) {
 const wf = workflows.value.find(x => x.id === rm.workflowId);
 if (wf) selectedModel.value = wf;
 }
 if (!rm.workflowId || !selectedModel.value.type) {
 const m = models.value.find(x => x.id === rm.modelId || x.name === rm.modelName);
 if (m) selectedModel.value = m;
 }
 } catch {}
 sessionStorage.removeItem('yezhi_remake');
 }
 });

 const triggerUpload = () => fileInput.value.click();
 const onFileSelected = (e) => {
 const files = Array.from(e.target.files || []);
 addRefFiles(files);
 e.target.value = ''; // 允许重复选同一文件
 };
 const onRefDrop = (e) => {
 dragRef.value = false;
 const files = Array.from(e.dataTransfer.files || []).filter(f => f.type.startsWith('image/'));
 if (files.length) addRefFiles(files);
 };
 const addRefFiles = (files) => {
 files.forEach(f => {
 const r = new FileReader();
 r.onload = () => { referenceImages.value.push(r.result); };
 r.readAsDataURL(f);
 });
 };

 const triggerAudio = () => audioInput.value?.click();
 const onAudioSelected = (e) => {
 const files = Array.from(e.target.files || []);
 addAudioFiles(files);
 e.target.value = '';
 };
 const onAudioDrop = (e) => {
 dragAudio.value = false;
 const files = Array.from(e.dataTransfer.files || []).filter(f => f.type.startsWith('audio/'));
 if (files.length) addAudioFiles(files);
 };
 const addAudioFiles = (files) => {
 files.forEach(f => {
 const r = new FileReader();
 r.onload = () => { audioFiles.value.push({ name: f.name, data: r.result }); };
 r.readAsDataURL(f);
 });
 };

 const selectModel = (m) => { selectedModel.value = m; modelDropdownOpen.value = false; };
 const modelList = computed(() => [...models.value, ...workflows.value]);
 const selectStyle = (s) => {
 selectedStyle.value = selectedStyle.value === s.id ? null : s.id;
 if (selectedStyle.value) {
 prompt.value = prompt.value ? prompt.value + ', ' + s.name + ' style' : s.name + ' style';
 }
 };
 const cycleRatio = () => {
 const i = RATIOS.indexOf(ratio.value);
 ratio.value = RATIOS[(i + 1) % RATIOS.length];
 };
 const randomPrompt = () => {
 const samples = [
 'a beautiful girl with long hair, soft lighting, intricate details',
 'epic landscape, mountains, sunset, cinematic, ultra detailed',
 'futuristic city, neon lights, cyberpunk, night scene',
 'cute cat, kawaii style, big eyes, pastel colors',
 'magical forest, glowing mushrooms, fantasy art, ethereal light',
 'ancient chinese palace, traditional architecture, misty mountains',
 ];
 prompt.value = samples[Math.floor(Math.random() * samples.length)];
 };

 const optimizePrompt = async () => {
 if (!prompt.value) return;
 optimizing.value = true;
 try {
 const d = await api('/api/optimize-prompt', {
 method: 'POST', body: { prompt: prompt.value, model_id: selectedModel.value.id }
 });
 if (d.optimized) prompt.value = d.optimized;
 if (d.negative) negativePrompt.value = d.negative;
 window.toast.success('提示词已优化');
 } catch (e) {
 window.toast.error('优化失败: ' + e.message);
 } finally {
 optimizing.value = false;
 }
 };

 const generate = async () => {
 if (!prompt.value || generating.value) return;
 generating.value = true; results.value = []; error.value = ''; progress.value = 0; statusText.value = '提交任务...';
 const t0 = Date.now();

 const [w, h] = ratio.value.split(':').map(Number);
 const width = customW.value || (w >= h ? 1024 : Math.round(1024 * w / h));
 const height = customH.value || (w >= h ? Math.round(1024 * h / w) : 1024);

 try {
 const r = await fetch('/api/generate', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json', ...(authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {}) },
 body: JSON.stringify({
 mode: 'quick',
 prompt: prompt.value,
 negative_prompt: negativePrompt.value,
 model_id: selectedModel.value.type === 'workflow' ? '' : selectedModel.value.id,
 workflow_id: selectedModel.value.type === 'workflow' ? selectedModel.value.id : '',
 width, height,
 steps: steps.value,
 batch_size: batchSize.value,
 seed: -1,
 duration: duration.value,
 fps: fps.value,
 audio_start_time: audioStartTime.value,
 audio_duration: audioDuration.value,
 reference_images: referenceImages.value,
 audio: audioFiles.value.map(a => a.data),
 }),
 });

 if (!r.ok) {
 const d = await r.json();
 throw new Error(d.error || '生成失败');
 }

 statusText.value = '排队中...';
 const reader = r.body.getReader();
 const decoder = new TextDecoder();
 let buffer = '';
 progress.value = 10;

 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 buffer += decoder.decode(value, { stream: true });
 const lines = buffer.split('\n');
 buffer = lines.pop() || '';

 for (const line of lines) {
 if (!line.startsWith('data: ')) continue;
 try {
 const evt = JSON.parse(line.slice(6));
 if (evt.type === 'queued') {
 statusText.value = '队列中...';
 progress.value = 20;
 } else if (evt.type === 'progress') {
 statusText.value = evt.message || '生成中...';
 progress.value = Math.min(80, 20 + (evt.percent || 0) * 0.6);
 } else if (evt.type === 'image' || evt.type === 'video') {
 results.value.push({ url: evt.url, id: evt.id, mediaType: evt.media_type || 'image' });
 progress.value = 90;
 lastMediaType.value = evt.media_type || 'image';
 } else if (evt.type === 'error') {
 error.value = evt.message;
 } else if (evt.type === 'done') {
 progress.value = 100;
 statusText.value = '完成';
 }
 } catch {}
 }
 }
 elapsed.value = ((Date.now() - t0) / 1000).toFixed(1);
 } catch (e) {
 error.value = e.message;
 window.toast.error(e.message);
 } finally {
 generating.value = false;
 }
 };

 const downloadAll = () => {
 results.value.forEach((r, i) => {
 const isVideo = r.mediaType === 'video';
 const ext = isVideo ? 'mp4' : 'png';
 const a = document.createElement('a');
 a.href = r.url;
 a.download = `yezhi-${Date.now()}-${i+1}.${ext}`;
 a.click();
 });
 };

 const zoomImage = (url) => $openLightbox(url);

 const openWorksPicker = async () => {
 showWorksPicker.value = true;
 if (myWorks.value.length === 0) {
 worksPickerLoading.value = true;
 try {
 const d = await api('/api/user/images?limit=50');
 myWorks.value = d.images || [];
 } catch {}
 worksPickerLoading.value = false;
 }
 };

 const pickReference = async (img) => {
 try {
 const resp = await fetch(img.imageUrl);
 const blob = await resp.blob();
 const r = new FileReader();
 r.onload = () => { referenceImages.value.push(r.result); };
 r.readAsDataURL(blob);
 } catch { referenceImages.value.push(img.imageUrl); }
 showWorksPicker.value = false;
 };

 return {
 authStore, models, workflows, styles, selectedModel, selectedStyle, modelDropdownOpen,
 showStylePicker, showAdvanced, showNegative,
 prompt, negativePrompt, ratio, customW, customH, steps, batchSize, duration, fps, lastMediaType,
 dragRef, referenceImages, fileInput,
 audioStartTime, audioDuration,
 dragAudio, audioFiles, audioInput,
 generating, optimizing, results, error, progress, statusText, elapsed,
 triggerUpload, onFileSelected, onRefDrop, selectModel, modelList, selectStyle, cycleRatio,
 triggerAudio, onAudioSelected, onAudioDrop,
 randomPrompt, optimizePrompt, generate, downloadAll, zoomImage,
 showWorksPicker, worksPickerLoading, myWorks, openWorksPicker, pickReference,
 };
 },
};

// ═══════════════════════════════════════════════
// 页面: 社区
// ═══════════════════════════════════════════════
const CommunityPage = {
 template: `
 <div class="page fade-in">
 <h2 class="section-title">创意社区</h2>
 <p class="section-sub mb-4">发现 AI 创作灵感，分享你的作品</p>

 <!-- 标签筛选 -->
 <div class="filter-bar">
 <span class="filter-tag" :class="{ active: activeFilter === '' }" @click="setFilter('')">全部</span>
 <span v-for="m in modelTags" :key="m" class="filter-tag" :class="{ active: activeFilter === m }" @click="setFilter(m)">{{ m }}</span>
 </div>

 <div v-if="loading" class="text-center p-6"><div class="spin" style="margin: 0 auto"></div></div>
 <div v-else-if="images.length === 0" class="text-center p-6 text-muted">社区还没有作品，快去生成一些分享吧</div>
 <div v-else>
 <div class="community-grid">
 <div v-for="img in images" :key="img.id" class="community-item">
 <video v-if="img.mediaType === 'video'" :src="img.imageUrl" style="cursor:pointer;width:100%;aspect-ratio:1;object-fit:cover;border-radius:4px 4px 0 0" controls muted preload="metadata" playsinline></video>
 <img v-else :src="img.thumbnailUrl" :alt="img.prompt" @error="e => e.target.src='/static/images/default-logo.svg'" @click="$openLightbox(img.imageUrl || img.thumbnailUrl)" style="cursor:pointer">
 <div class="community-meta">
 <div class="user">
 <img :src="img.userAvatar || '/static/images/default-avatar.svg'" alt="" @error="e => e.target.src='/static/images/default-avatar.svg'">
 <span class="name">{{ img.userName || '匿名' }}</span>
 </div>
 <div class="prompt" :title="img.prompt">{{ img.prompt || '无提示词' }}</div>
 <div class="actions">
 <span @click="toggleLike(img)" class="like-btn" :class="{ liked: img.liked }">
 <svg class="icon-heart" viewBox="0 0 24 24" width="16" height="16"><path d="M12 21s-7-4.5-9.5-9C1 9 2.5 5 6 5c2 0 3.5 1 4.5 2.5C11.5 6 13 5 15 5c3.5 0 5 4 3.5 7-2.5 4.5-9.5 9-9.5 9z" fill="currentColor"/></svg>
 {{ img.likeCount || 0 }}
 </span>
 <span class="fav-btn">
 <svg class="icon-star" viewBox="0 0 24 24" width="16" height="16"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
 </span>
 <span style="margin-left: auto" class="model-tag">{{ img.modelName }}</span>
 </div>
 </div>
 </div>
 </div>
 <div v-if="hasMore" class="text-center p-4">
 <button class="btn btn-secondary" @click="loadMore" :disabled="loadingMore">
 {{ loadingMore ? '加载中...' : '加载更多' }}
 </button>
 </div>
 </div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const images = ref([]);
 const loading = ref(true);
 const loadingMore = ref(false);
 const activeFilter = ref('');
 const modelTags = ref([]);
 const total = ref(0);
 const pageSize = 24;

 const load = async () => {
 loading.value = true;
 try {
 const params = new URLSearchParams({ limit: pageSize, offset: 0 });
 const d = await api('/api/community/feed?' + params);
 images.value = d.images || [];
 total.value = d.total || 0;
 // 提取模型标签
 const tags = new Set();
 images.value.forEach(img => { if (img.modelName) tags.add(img.modelName); });
 modelTags.value = [...tags].sort();
 } catch {
 images.value = [];
 } finally {
 loading.value = false;
 }
 };

 const setFilter = (m) => {
 activeFilter.value = m;
 // 前端过滤
 };

 const filteredImages = computed(() => {
 if (!activeFilter.value) return images.value;
 return images.value.filter(img => img.modelName === activeFilter.value);
 });

 const hasMore = computed(() => images.value.length < total.value);

 const loadMore = async () => {
 if (loadingMore.value) return;
 loadingMore.value = true;
 try {
 const params = new URLSearchParams({ limit: pageSize, offset: images.value.length });
 const d = await api('/api/community/feed?' + params);
 const newImages = d.images || [];
 images.value = [...images.value, ...newImages];
 // 更新标签
 newImages.forEach(img => { if (img.modelName && !modelTags.value.includes(img.modelName)) modelTags.value.push(img.modelName); });
 modelTags.value.sort();
 } catch {} finally {
 loadingMore.value = false;
 }
 };

 const toggleLike = async (img) => {
 if (!authStore.isLoggedIn) { window.toast.info('请先登录'); return; }
 try {
 const d = await api(`/api/community/likes/${img.id}`, { method: 'POST' });
 img.liked = d.liked;
 img.likeCount += d.liked ? 1 : -1;
 } catch {}
 };

 onMounted(load);
 return { authStore, images: filteredImages, loading, loadingMore, activeFilter, modelTags, hasMore, setFilter, loadMore, toggleLike };
 },
};

// ═══════════════════════════════════════════════
// 页面: 我的作品
// ═══════════════════════════════════════════════
const MyWorksPage = {
 template: `
 <div class="page fade-in">
 <h2 class="section-title">我的作品</h2>
 <p class="section-sub mb-4">管理你生成的所有图片</p>

 <div v-if="!authStore.isLoggedIn" class="card text-center p-6">
 <div class="text-muted mb-3">请先登录</div>
 <button class="btn btn-primary" @click="$router.push('/login')">去登录</button>
 </div>
 <template v-else>
 <!-- 标签筛选 -->
 <div v-if="modelTags.length > 0" class="filter-bar">
 <span class="filter-tag" :class="{ active: activeFilter === '' }" @click="activeFilter = ''">全部</span>
 <span v-for="m in modelTags" :key="m" class="filter-tag" :class="{ active: activeFilter === m }" @click="activeFilter = m">{{ m }}</span>
 </div>

 <div v-if="images.length === 0" class="text-center p-6 text-muted">还没有作品，去生成一些吧</div>
 <div v-else>
 <div class="community-grid">
 <div v-for="img in filteredImages" :key="img.id" class="community-item">
 <video v-if="img.mediaType === 'video'" :src="img.thumbnailUrl || img.imageUrl" style="cursor:pointer;width:100%;aspect-ratio:1;object-fit:cover;border-radius:4px 4px 0 0" controls muted preload="metadata" playsinline></video>
 <img v-else :src="img.thumbnailUrl || img.imageUrl" :alt="img.prompt" @click="$openLightbox(img.imageUrl)" style="cursor:pointer">
 <div class="works-meta">
 <div class="works-prompt" :title="img.prompt">{{ img.prompt || '无提示词' }}</div>
 <div class="works-info">
 <span class="model-tag">{{ img.modelName }}</span>
 <span v-if="img.workflowId" class="model-tag" style="color:var(--ink-fade)">工作流</span>
 <span v-if="img.isPublic" class="status-pill published">已发布</span>
 </div>
 <div class="works-btns">
 <button class="btn btn-ghost btn-sm" @click="remake(img)" style="color:var(--cinnabar)">生成同款</button>
 <button v-if="!img.isPublic" class="btn btn-ghost btn-sm" @click="publish(img)">发布</button>
 <button class="btn btn-ghost btn-sm" @click="remove(img)">删除</button>
 </div>
 </div>
 </div>
 </div>
 <div v-if="hasMore" class="text-center p-4">
 <button class="btn btn-secondary" @click="loadMore" :disabled="loadingMore">
 {{ loadingMore ? '加载中...' : '加载更多' }}
 </button>
 </div>
 </div>
 </template>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const allImages = ref([]);
 const activeFilter = ref('');
 const loadingMore = ref(false);
 const total = ref(0);
 const pageSize = 50;

 const images = computed(() => allImages.value);

 const modelTags = computed(() => {
 const tags = new Set();
 allImages.value.forEach(img => { if (img.modelName) tags.add(img.modelName); });
 return [...tags].sort();
 });

 const filteredImages = computed(() => {
 if (!activeFilter.value) return allImages.value;
 return allImages.value.filter(img => img.modelName === activeFilter.value);
 });

 const hasMore = computed(() => allImages.value.length < total.value);

 const load = async () => {
 if (!authStore.isLoggedIn) return;
 try {
 const d = await api('/api/user/images?limit=' + pageSize);
 allImages.value = d.images || [];
 total.value = d.total || 0;
 } catch {}
 };

 const loadMore = async () => {
 if (loadingMore.value) return;
 loadingMore.value = true;
 try {
 const d = await api('/api/user/images?limit=' + pageSize + '&offset=' + allImages.value.length);
 allImages.value = [...allImages.value, ...(d.images || [])];
 } catch {} finally {
 loadingMore.value = false;
 }
 };

 const publish = async (img) => {
 try {
 await api(`/api/user/images/${img.id}/publish`, { method: 'POST' });
 img.isPublic = true;
 window.toast.success('已发布到社区');
 } catch (e) { window.toast.error(e.message); }
 };

 const remove = async (img) => {
 if (!confirm('确定删除？')) return;
 try {
 await api(`/api/user/images/${img.id}`, { method: 'DELETE' });
 allImages.value = allImages.value.filter(i => i.id !== img.id);
 window.toast.success('已删除');
 } catch (e) { window.toast.error(e.message); }
 };

 const remake = (img) => {
 sessionStorage.setItem('yezhi_remake', JSON.stringify({
 modelName: img.modelName,
 modelId: img.workflowId ? '' : img.modelName,
 workflowId: img.workflowId || '',
 prompt: img.prompt || '',
 negativePrompt: img.negativePrompt || '',
 steps: img.steps || 28,
 ratio: img.ratio || '1:1',
 width: img.width || null,
 height: img.height || null,
 duration: img.durationSeconds || img.duration_seconds || null,
 fps: img.fps || null,
 audioStartTime: img.audioStartTime || img.audio_start_time || null,
 audioDuration: img.audioDuration || img.audio_duration || null,
 mediaType: img.mediaType || img.media_type || 'image',
 referenceImages: img.referenceImages || [],
 audioFiles: img.audioFiles || [],
 }));
 router.push('/generate');
 };

 onMounted(load);
 return { authStore, images, filteredImages, modelTags, activeFilter, hasMore, loadingMore, publish, remove, remake, loadMore };
 },
};

/**
 * 新增页面: 设置页 + 工作流管理页
 */

// ═════════════════════════════════════════════
// 页面: 设置
// ═════════════════════════════════════════════
const SettingsPage = {
 template: `
 <div class="page fade-in">
 <h2 class="section-title">设置</h2>
 <p class="section-sub mb-4">个性化配置与偏好设置</p>

 <!-- 用户信息 -->
 <div class="card mb-4">
 <h3 class="form-label mb-3">个人信息</h3>
 <div v-if="!authStore.isLoggedIn" class="text-center p-4 text-muted">
 <div class="mb-3">请先登录</div>
 <button class="btn btn-primary" @click="$router.push('/login')">去登录</button>
 </div>
 <div v-else class="settings-section">
 <div class="setting-row">
 <div class="setting-label">昵称</div>
 <input v-model="profile.nickname" class="input" placeholder="设置昵称" @blur="saveProfile">
 </div>
 <div class="setting-row">
 <div class="setting-label">签名</div>
 <input v-model="profile.signature" class="input" placeholder="个性签名" @blur="saveProfile">
 </div>
 <div class="setting-row">
 <div class="setting-label">头像</div>
 <div class="f gap-2 ac">
 <img :src="profile.avatar || '/static/images/default-avatar.svg'" style="width:48px;height:48px;border-radius:50%;object-fit:cover">
 <label class="btn btn-secondary text-sm" style="cursor:pointer">
 上传头像
 <input type="file" accept="image/*" @change="uploadAvatar" style="display:none">
 </label>
 </div>
 </div>
 </div>
 </div>

 <!-- 偏好设置 -->
 <div class="card mb-4">
 <h3 class="form-label mb-3">生成偏好</h3>
 <div class="settings-section">
 <div class="setting-row">
 <div class="setting-label">默认模型</div>
 <select v-model="prefs.defaultModel" class="input" @change="savePrefs">
 <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
 </select>
 </div>
 <div class="setting-row">
 <div class="setting-label">默认步数</div>
 <input v-model.number="prefs.defaultSteps" type="number" min="1" max="50" class="input" style="width:120px" @blur="savePrefs">
 </div>
 <div class="setting-row">
 <div class="setting-label">默认尺寸</div>
 <select v-model="prefs.defaultRatio" class="input" style="width:150px" @change="savePrefs">
 <option value="1:1">1:1 (1024×1024)</option>
 <option value="16:9">16:9 (1344×768)</option>
 <option value="9:16">9:16 (768×1344)</option>
 <option value="4:3">4:3 (1152×896)</option>
 <option value="3:4">3:4 (896×1152)</option>
 </select>
 </div>
 <div class="setting-row">
 <div class="setting-label">自动优化提示词</div>
 <label class="toggle">
 <input type="checkbox" v-model="prefs.autoOptimize">
 <span class="toggle-slider"></span>
 </label>
 </div>
 </div>
 </div>

 <!-- 积分信息 -->
 <div class="card mb-4">
 <h3 class="form-label mb-3">💰 积分信息</h3>
 <div v-if="!authStore.isLoggedIn" class="text-sm text-muted text-center p-3">登录后查看积分信息</div>
 <div v-else-if="points !== null" class="f gap-4 ac">
 <div class="stat-box">
 <div class="stat-num">{{ points.balance || 0 }}</div>
 <div class="stat-label">当前积分</div>
 </div>
 <div class="stat-box">
 <div class="stat-num">{{ points.totalSpent || 0 }}</div>
 <div class="stat-label">已消耗</div>
 </div>
 <div class="stat-box">
 <div class="stat-num">{{ points.packageCount || 0 }}</div>
 <div class="stat-label">积分包</div>
 </div>
 </div>
 <div v-else class="text-sm text-muted text-center p-3">加载中...</div>
 </div>

 <!-- 保存提示 -->
 <div v-if="saved" class="status-line success" style="margin-top:16px"> 设置已自动保存</div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const models = ref(FALLBACK_MODELS);
 const profile = ref({ nickname: '', signature: '', avatar: '' });
 const prefs = ref({ defaultModel: '', defaultSteps: 28, defaultRatio: '1:1', autoOptimize: false });
 const points = ref(null);
 const saved = ref(false);
 let saveTimer = null;

 const autoSave = () => {
 clearTimeout(saveTimer);
 saved.value = true;
 saveTimer = setTimeout(() => { saved.value = false; }, 2000);
 };

 const saveProfile = async () => {
 if (!authStore.isLoggedIn) return;
 autoSave();
 try {
 await api('/api/user/profile', { method: 'PUT', body: profile.value });
 } catch {}
 };

 const uploadAvatar = async (e) => {
 const f = e.target.files[0];
 if (!f) return;
 const fd = new FormData();
 fd.append('file', f);
 try {
 const d = await api('/api/upload/avatar', { method: 'POST', body: fd, headers: {} });
 profile.value.avatar = d.url;
 window.toast.success('头像已更新');
 } catch (e) { window.toast.error(e.message); }
 };

 const savePrefs = () => {
 autoSave();
 localStorage.setItem('yezhi_prefs', JSON.stringify(prefs.value));
 };

 const loadPrefs = () => {
 try {
 const stored = localStorage.getItem('yezhi_prefs');
 if (stored) prefs.value = JSON.parse(stored);
 } catch {}
 };

 onMounted(async () => {
 if (authStore.user) {
 profile.value = { ...authStore.user };
 }
 loadPrefs();
 if (authStore.isLoggedIn) {
 try {
 const d = await api('/api/points/balance');
 points.value = d;
 } catch {}
 }
 });

 return { authStore, models, profile, prefs, points, saved, saveProfile, uploadAvatar, savePrefs };
 },
};

// ═════════════════════════════════════════════
// 页面: 工作流管理
// ═════════════════════════════════════════════

const WorkflowsPage = {
 template: `
 <div class="page fade-in">
 <div class="jb ac mb-4">
 <div>
 <h2 class="section-title" style="margin-bottom:0">我的工作流</h2>
 <p class="section-sub" style="margin-top:4px">自定义 ComfyUI 工作流，支持从 ComfyUI 导入</p>
 </div>
 <button class="btn btn-primary" @click="showCreate = true">新建工作流</button>
 </div>

 <!-- 登录提示 -->
 <div v-if="!authStore.isLoggedIn" class="card text-center p-6 mb-4">
 <div class="text-muted mb-3">登录后可创建和管理自定义工作流</div>
 <button class="btn btn-primary" @click="$router.push('/login')">去登录</button>
 </div>

 <!-- 拖拽上传区域 -->
 <div v-if="authStore.isLoggedIn" 
 class="drop-zone mb-4" 
 :class="{ 'drop-active': dragOver }"
 @dragenter.prevent="dragOver = true"
 @dragover.prevent="dragOver = true"
 @dragleave.prevent="dragOver = false"
 @drop.prevent="onDrop">
 <div class="drop-icon"><img src="/static/common/upload.svg" alt="" style="width:40px;height:40px;opacity:0.3"></div>
 <div class="drop-text">{{ dragOver ? '松手导入工作流' : '拖拽 ComfyUI JSON 文件到此处' }}</div>
 <div class="text-xs text-muted mt-2">或</div>
 <label class="btn btn-secondary mt-2" style="cursor:pointer">
 选择文件
 <input type="file" accept=".json" @change="onFileSelect" style="display:none" ref="fileInput">
 </label>
 </div>

 <!-- 工作流列表 -->
 <div v-if="workflows.length === 0 && authStore.isLoggedIn" class="card text-center p-6 mb-4">
 <img src="/static/common/workflow.svg" alt="" style="width:64px;height:64px;opacity:0.25;margin-bottom:12px">
 <div class="text-muted mb-3">还没有自定义工作流</div>
 <div class="text-sm text-muted mb-4">拖拽 ComfyUI API JSON 文件到上方区域即可快速导入</div>
 <button class="btn btn-secondary" @click="showImport = true"> 手动粘贴导入</button>
 </div>

 <div v-if="workflows.length > 0" class="workflow-grid">
 <div v-for="wf in workflows" :key="wf.id" class="workflow-card">
 <img :src="wf.cover_url || '/static/images/default-logo.svg'" class="wf-cover" @error="e => e.target.src='/static/images/default-logo.svg'">
 <div class="wf-body">
 <div class="wf-name">{{ wf.name }}</div>
 <div class="wf-desc text-sm text-muted">{{ wf.description || '无描述' }}</div>
 <div class="wf-meta text-xs text-muted mt-2">
 <span>{{ wf.is_builtin ? '内置' : '自定义' }}</span>
 <span>使用 {{ wf.use_count || 0 }} 次</span>
 <span v-if="wf.is_public">公开</span>
 </div>
 </div>
 <div class="wf-actions">
 <button class="btn btn-primary text-sm" @click="useWorkflow(wf)">使用</button>
 <button v-if="!wf.is_builtin" class="btn btn-ghost text-sm" @click="editWorkflow(wf)">编辑</button>
 <button v-if="!wf.is_builtin" class="btn btn-ghost text-sm" @click="deleteWorkflow(wf)">删除</button>
 </div>
 </div>
 </div>

 <!-- 导入弹窗 -->
 <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
 <div class="modal-card">
 <div class="modal-header">
 <h3>导入工作流</h3>
 <button class="btn btn-ghost" @click="showImport = false">×</button>
 </div>
 <div class="modal-body">
 <div class="form-label">工作流名称</div>
 <input v-model="importData.name" class="input mb-3" placeholder="给你的工作流起个名字">
 <div class="form-label">ComfyUI 地址 (可选)</div>
 <input v-model="importData.comfyui_url" class="input mb-3" placeholder="http://localhost:8188">
 <div class="form-label">工作流 JSON <span class="text-xs text-muted">(从 ComfyUI 导出)</span></div>
 <textarea v-model="importData.workflow_json" class="textarea" rows="8" placeholder='{"3": {"class_type": "KSampler", "inputs": {...}}}'></textarea>
 </div>
 <div class="modal-footer">
 <button class="btn btn-ghost" @click="showImport = false">取消</button>
 <button class="btn btn-primary" @click="importWorkflow" :disabled="!importData.workflow_json">导入</button>
 </div>
 </div>
 </div>

 <!-- 创建/编辑弹窗 -->
 <div v-if="showCreate || editingWorkflow" class="modal-overlay" @click.self="closeModal">
 <div class="modal-card">
 <div class="modal-header">
 <h3>{{ editingWorkflow ? '编辑工作流' : '新建工作流' }}</h3>
 <button class="btn btn-ghost" @click="closeModal">×</button>
 </div>
 <div class="modal-body">
 <div class="form-label">工作流名称 *</div>
 <input v-model="editData.name" class="input mb-3" placeholder="工作流名称">
 <div class="form-label">描述</div>
 <input v-model="editData.description" class="input mb-3" placeholder="简短描述">
 <div class="form-label">ComfyUI 地址</div>
 <input v-model="editData.comfyui_url" class="input mb-3" placeholder="留空使用全局配置">
 <div class="form-label">封面图 URL</div>
 <input v-model="editData.cover_url" class="input mb-3" placeholder="封面图片地址">
 <div class="form-label">工作流 JSON *</div>
 <textarea v-model="editData.workflow_json" class="textarea" rows="8" placeholder='{"3": {"class_type": "KSampler", ...}}'></textarea>
 <div class="text-xs text-muted mt-2"> 可从 ComfyUI 的"导出 API"按钮获取 JSON</div>
 </div>
 <div class="modal-footer">
 <button class="btn btn-ghost" @click="closeModal">取消</button>
 <button class="btn btn-primary" @click="saveWorkflow" :disabled="!editData.name || !editData.workflow_json">
 {{ editingWorkflow ? '保存' : '创建' }}
 </button>
 </div>
 </div>
 </div>

 <!-- 工作流详情/测试 -->
 <div v-if="testingWorkflow" class="modal-overlay" @click.self="testingWorkflow = null">
 <div class="modal-card" style="max-width:700px">
 <div class="modal-header">
 <h3>测试工作流: {{ testingWorkflow.name }}</h3>
 <button class="btn btn-ghost" @click="testingWorkflow = null">×</button>
 </div>
 <div class="modal-body">
 <div class="form-label">提示词</div>
 <textarea v-model="testPrompt" class="textarea" rows="3" placeholder="输入测试提示词"></textarea>
 <button class="btn btn-primary mt-3" @click="runTest" :disabled="testing || !testPrompt">
 {{ testing ? '测试中...' : '▶ 测试运行' }}
 </button>
 <div v-if="testResults.length > 0" class="mt-4">
 <div class="form-label">结果</div>
 <div class="f gap-3" style="flex-wrap:wrap">
 <img v-for="(r, i) in testResults" :key="i" :src="r" style="max-width:200px;border-radius:4px">
 </div>
 </div>
 <div v-if="testError" class="mt-3 text-sm" style="color:#b91c1c">{{ testError }}</div>
 </div>
 </div>
 </div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const workflows = ref([]);
 const showCreate = ref(false);
 const showImport = ref(false);
 const editingWorkflow = ref(null);
 const testingWorkflow = ref(null);
 const testPrompt = ref('');
 const testing = ref(false);
 const testResults = ref([]);
 const testError = ref('');
 const dragOver = ref(false);
 const fileInput = ref(null);

 const importData = ref({ name: '', workflow_json: '', comfyui_url: '' });
 const editData = ref({ name: '', description: '', comfyui_url: '', cover_url: '', workflow_json: '' });

 // 读取文件并导入
 const readAndImportFile = (file) => {
 if (!file || !file.name.endsWith('.json')) {
 window.toast.error('请选择 .json 文件');
 return;
 }
 const reader = new FileReader();
 reader.onload = async (e) => {
 const jsonStr = e.target.result;
 try {
 JSON.parse(jsonStr); // validate
 const baseName = file.name.replace('.json', '');
 const d = await api('/api/workflows/import', {
 method: 'POST', body: {
 name: baseName,
 workflow_json: jsonStr,
 comfyui_url: '',
 }
 });
 workflows.value.unshift(d.workflow);
 window.toast.success('工作流 ' + baseName + ' 导入成功');
 } catch (e) {
 window.toast.error('导入失败: ' + e.message);
 }
 };
 reader.readAsText(file);
 };

 // 拖拽处理
 const onDrop = (e) => {
 dragOver.value = false;
 const files = e.dataTransfer.files;
 if (files.length > 0) {
 readAndImportFile(files[0]);
 }
 };

 // 文件选择处理
 const onFileSelect = (e) => {
 const files = e.target.files;
 if (files.length > 0) {
 readAndImportFile(files[0]);
 }
 // Reset input
 if (fileInput.value) fileInput.value.value = '';
 };

 const load = async () => {
 if (!authStore.isLoggedIn) return;
 try {
 const d = await api('/api/workflows');
 workflows.value = d.workflows || [];
 } catch (e) {
 window.toast.error('加载失败: ' + e.message);
 }
 };

 const importWorkflow = async () => {
 if (!importData.value.workflow_json) return;
 try {
 const wf = JSON.parse(importData.value.workflow_json);
 const d = await api('/api/workflows/import', {
 method: 'POST', body: {
 name: importData.value.name || '导入的工作流',
 workflow_json: importData.value.workflow_json,
 comfyui_url: importData.value.comfyui_url,
 }
 });
 workflows.value.unshift(d.workflow);
 showImport.value = false;
 importData.value = { name: '', workflow_json: '', comfyui_url: '' };
 window.toast.success('工作流导入成功');
 } catch (e) {
 window.toast.error('导入失败: ' + e.message);
 }
 };

 const editWorkflow = async (wf) => {
 editingWorkflow.value = wf;
 editData.value = {
 name: wf.name,
 description: wf.description || '',
 comfyui_url: wf.comfyui_url || '',
 cover_url: wf.cover_url || '',
 workflow_json: '',
 };
 // 从服务端加载完整 JSON
 try {
 const d = await api('/api/workflows/' + wf.id + '/json');
 editData.value.workflow_json = JSON.stringify(d.workflow_json, null, 2);
 } catch (e) {
 window.toast.error('加载工作流内容失败');
 }
 };

 const saveWorkflow = async () => {
 try {
 // 发送前确保 workflow_json 是字符串
 const body = { ...editData.value };
 if (typeof body.workflow_json === 'object') {
 body.workflow_json = JSON.stringify(body.workflow_json);
 }

 if (editingWorkflow.value) {
 const d = await api('/api/workflows/' + editingWorkflow.value.id, {
 method: 'PUT', body: body
 });
 const idx = workflows.value.findIndex(w => w.id === editingWorkflow.value.id);
 if (idx >= 0) workflows.value[idx] = { ...workflows.value[idx], ...d.workflow };
 } else {
 const d = await api('/api/workflows', {
 method: 'POST', body: body
 });
 workflows.value.unshift(d.workflow);
 }
 closeModal();
 window.toast.success(editingWorkflow.value ? '保存成功' : '创建成功');
 } catch (e) {
 window.toast.error(e.message);
 }
 };

 const closeModal = () => {
 showCreate.value = false;
 editingWorkflow.value = null;
 editData.value = { name: '', description: '', comfyui_url: '', cover_url: '', workflow_json: '' };
 };

 const deleteWorkflow = async (wf) => {
 if (!confirm('确定删除工作流 "' + wf.name + '"？')) return;
 try {
 await api('/api/workflows/' + wf.id, { method: 'DELETE' });
 workflows.value = workflows.value.filter(w => w.id !== wf.id);
 window.toast.success('已删除');
 } catch (e) { window.toast.error(e.message); }
 };

 const useWorkflow = (wf) => {
 sessionStorage.setItem('yezhi_workflow_id', wf.id);
 sessionStorage.setItem('yezhi_workflow_name', wf.name);
 window.location.hash = '/generate';
 };

 const runTest = async () => {
 if (!testPrompt.value || testing.value) return;
 testing.value = true;
 testResults.value = [];
 testError.value = '';
 try {
 const wfJson = testingWorkflow.value?.workflow_json;
 const r = await fetch('/api/generate', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json', ...(authStore.token ? { Authorization: 'Bearer ' + authStore.token } : {}) },
 body: JSON.stringify({
 mode: 'direct',
 workflow: JSON.parse(wfJson),
 comfy_url: testingWorkflow.value?.comfyui_url || '',
 prompt: testPrompt.value,
 }),
 });
 const reader = r.body.getReader();
 const decoder = new TextDecoder();
 let buffer = '';
 while (true) {
 const { done, value } = await reader.read();
 if (done) break;
 buffer += decoder.decode(value, { stream: true });
 const lines = buffer.split('\n');
 buffer = lines.pop() || '';
 for (const line of lines) {
 if (!line.startsWith('data: ')) continue;
 try {
 const evt = JSON.parse(line.slice(6));
 if (evt.type === 'image') testResults.value.push(evt.url);
 if (evt.type === 'error') testError.value = evt.message;
 } catch {}
 }
 }
 } catch (e) {
 testError.value = e.message;
 } finally {
 testing.value = false;
 }
 };

 onMounted(load);

 return {
 authStore, workflows, showCreate, showImport, editingWorkflow, testingWorkflow,
 testPrompt, testing, testResults, testError, dragOver, fileInput,
 importData, editData,
 importWorkflow, editWorkflow, saveWorkflow, closeModal, deleteWorkflow, useWorkflow, runTest,
 onDrop, onFileSelect,
 };
 },
};



// ═══════════════════════════════════════════════
// 页面: 登录
// ═══════════════════════════════════════════════
const AuthPage = {
 template: `
 <div class="auth-card">
 <div class="fc ac gap-2 mb-4">
 <img src="/static/images/default-logo.svg" style="width:64px;height:64px;border-radius:50%;box-shadow:0 4px 12px rgba(249,115,22,.25)">
 <div>
 <div class="auth-title">{{ mode === 'login' ? '登录' : '注册' }}</div>
 <div class="auth-sub">ComfyUI-Yezhi-API</div>
 </div>
 </div>

 <div class="form-label">邮箱</div>
 <input v-model="email" type="email" class="input mb-3" placeholder="your@email.com">

 <div class="form-label">密码</div>
 <input v-model="password" type="password" class="input mb-4" placeholder="至少 6 位">

 <div v-if="mode === 'register'" class="mb-3">
 <div class="form-label">昵称 (可选)</div>
 <input v-model="nickname" class="input" placeholder="你的昵称">
 </div>

 <button class="btn btn-primary w-full mb-3" @click="submit" :disabled="loading" style="padding: 12px">
 {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '创建账号') }}
 </button>

 <div v-if="error" class="text-sm" style="color:#b91c1c;text-align:center;margin-bottom:12px">{{ error }}</div>

 <div class="text-sm text-center text-muted">
 {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
 <a href="#" @click.prevent="mode = mode === 'login' ? 'register' : 'login'" style="color:var(--cinnabar);text-decoration:none;font-weight:600">
 {{ mode === 'login' ? '马上注册' : '去登录' }}
 </a>
 </div>

 <div v-if="authStore.selfHosted" class="mt-4 text-center text-xs text-muted" style="background:var(--cinnabar-pale);padding:8px;border-radius:4px">
 提示: 自用模式下无需登录即可使用
 </div>
 </div>`,
 setup() {
 const authStore = useAuthStore();
 const mode = ref('login');
 const email = ref('');
 const password = ref('');
 const nickname = ref('');
 const loading = ref(false);
 const error = ref('');

 const submit = async () => {
 error.value = '';
 const url = mode.value === 'login' ? '/api/auth/login' : '/api/auth/register';
 const body = { email: email.value, password: password.value };
 if (mode.value === 'register' && nickname.value) body.nickname = nickname.value;
 loading.value = true;
 try {
 const d = await api(url, { method: 'POST', body });
 authStore.login(d.token, d.user);
 window.toast.success('登录成功');
 window.location.hash = '/';
 } catch (e) {
 error.value = e.message;
 } finally {
 loading.value = false;
 }
 };

 return { authStore, mode, email, password, nickname, loading, error, submit };
 },
};

// ═══════════════════════════════════════════════
// Router & App
// ═══════════════════════════════════════════════
const routes = [
 { path: '/', component: HomePage },
 { path: '/generate', component: GeneratePage },
 { path: '/community', component: CommunityPage },
 { path: '/works', component: MyWorksPage },
 { path: '/workflows', component: WorkflowsPage },
 { path: '/settings', component: SettingsPage },

 { path: '/login', component: AuthPage },
];

const router = createRouter({ history: createWebHashHistory(), routes });

const app = createApp({
 setup() {
 const authStore = useAuthStore();
 const isActive = (path) => {
 if (path === '/generate') return router.currentRoute.value.path === '/' || router.currentRoute.value.path === '/generate';
 return router.currentRoute.value.path === path;
 };
 const logout = () => {
 authStore.logout();
 window.toast.success('已退出登录');
 };
 onMounted(() => authStore.init());
 return { authStore, isActive, logout, lightboxSrc, openLightbox, closeLightbox };
 },
});

app.use(createPinia());
app.use(router);
app.config.globalProperties.$openLightbox = openLightbox;
app.mount('#app');
