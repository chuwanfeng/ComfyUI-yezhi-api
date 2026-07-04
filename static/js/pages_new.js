/**
 * 新增页面: 设置页 + 工作流管理页
 */

// ═════════════════════════════════════════════
// 页面: 设置
// ═════════════════════════════════════════════
const SettingsPage = {
  template: `
  <div class="page fade-in">
    <h2 class="section-title">⚙️ 设置</h2>
    <p class="section-sub mb-4">个性化配置与偏好设置</p>

    <!-- 用户信息 -->
    <div class="card mb-4">
      <h3 class="form-label mb-3">👤 个人信息</h3>
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
      <h3 class="form-label mb-3">🎨 生成偏好</h3>
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
    <div v-if="saved" class="status-line success" style="margin-top:16px">✅ 设置已自动保存</div>
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
        <h2 class="section-title" style="margin-bottom:0">🔧 我的工作流</h2>
        <p class="section-sub" style="margin-top:4px">自定义 ComfyUI 工作流，支持从 ComfyUI 导入</p>
      </div>
      <button class="btn btn-primary" @click="showCreate = true">+ 新建工作流</button>
    </div>

    <!-- 登录提示 -->
    <div v-if="!authStore.isLoggedIn" class="card text-center p-6 mb-4">
      <div class="text-muted mb-3">登录后可创建和管理自定义工作流</div>
      <button class="btn btn-primary" @click="$router.push('/login')">去登录</button>
    </div>

    <!-- 工作流列表 -->
    <div v-if="workflows.length === 0 && authStore.isLoggedIn" class="card text-center p-6 mb-4">
      <div style="font-size:48px;margin-bottom:12px">🔧</div>
      <div class="text-muted mb-3">还没有自定义工作流</div>
      <div class="text-sm text-muted mb-4">从 ComfyUI 导出的 API JSON 可以在这里管理</div>
      <button class="btn btn-secondary" @click="showImport = true">📥 导入工作流</button>
    </div>

    <div v-if="workflows.length > 0" class="workflow-grid">
      <div v-for="wf in workflows" :key="wf.id" class="workflow-card">
        <img :src="wf.cover_url || '/static/images/dreamifly-logo.jpg'" class="wf-cover" @error="e => e.target.src='/static/images/dreamifly-logo.jpg'">
        <div class="wf-body">
          <div class="wf-name">{{ wf.name }}</div>
          <div class="wf-desc text-sm text-muted">{{ wf.description || '无描述' }}</div>
          <div class="wf-meta text-xs text-muted mt-2">
            <span>{{ wf.is_builtin ? '🏠 内置' : '👤 自定义' }}</span>
            <span>使用 {{ wf.use_count || 0 }} 次</span>
            <span v-if="wf.is_public">🌐 公开</span>
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
          <h3>📥 导入工作流</h3>
          <button class="btn btn-ghost" @click="showImport = false">✕</button>
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
          <button class="btn btn-ghost" @click="closeModal">✕</button>
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
          <div class="text-xs text-muted mt-2">💡 可从 ComfyUI 的"导出 API"按钮获取 JSON</div>
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
          <button class="btn btn-ghost" @click="testingWorkflow = null">✕</button>
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
              <img v-for="(r, i) in testResults" :key="i" :src="r" style="max-width:200px;border-radius:8px">
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

    const importData = ref({ name: '', workflow_json: '', comfyui_url: '' });
    const editData = ref({ name: '', description: '', comfyui_url: '', cover_url: '', workflow_json: '' });

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

    const editWorkflow = (wf) => {
      editingWorkflow.value = wf;
      editData.value = {
        name: wf.name,
        description: wf.description || '',
        comfyui_url: wf.comfyui_url || '',
        cover_url: wf.cover_url || '',
        workflow_json: wf.workflow_json || '',
      };
    };

    const saveWorkflow = async () => {
      try {
        if (editingWorkflow.value) {
          const d = await api('/api/workflows/' + editingWorkflow.value.id, {
            method: 'PUT', body: editData.value
          });
          const idx = workflows.value.findIndex(w => w.id === editingWorkflow.value.id);
          if (idx >= 0) workflows.value[idx] = { ...workflows.value[idx], ...d.workflow };
        } else {
          const d = await api('/api/workflows', {
            method: 'POST', body: editData.value
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
      testPrompt, testing, testResults, testError, importData, editData,
      importWorkflow, editWorkflow, saveWorkflow, closeModal, deleteWorkflow, useWorkflow, runTest,
    };
  },
};
