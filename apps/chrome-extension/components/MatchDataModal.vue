<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="close">
        <div class="modal-container">
          <!-- 头部 -->
          <div class="modal-header">
            <h3 class="modal-title">
              <span class="icon">📊</span>
              比赛数据 - {{ matchId }}
            </h3>
            <button class="close-btn" @click="close" title="关闭">
              <span>×</span>
            </button>
          </div>

          <!-- 内容区 -->
          <div class="modal-body">
            <div v-if="loading" class="loading-state">
              <div class="spinner"></div>
              <p>加载中...</p>
            </div>

            <div v-else-if="error" class="error-state">
              <span class="icon">⚠️</span>
              <p>{{ error }}</p>
            </div>

            <div v-else-if="data" class="data-content">
              <div class="json-container">
                <pre class="json-code"><code v-html="formattedJson"></code></pre>
              </div>
            </div>
          </div>

          <!-- 底部 -->
          <div class="modal-footer">
            <button
              class="copy-btn"
              :class="{ 'copied': copied }"
              @click="copyData"
              :disabled="!data || loading"
            >
              <span class="icon">{{ copied ? '✅' : '📋' }}</span>
              {{ copied ? '已复制' : '一键复制' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

const props = defineProps<{
  visible: boolean;
  matchId: string;
  date: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const loading = ref(false);
const error = ref('');
const data = ref<any>(null);
const copied = ref(false);

// 格式化JSON显示
const formattedJson = computed(() => {
  if (!data.value) return '';
  const jsonStr = JSON.stringify(data.value, null, 2);
  // 简单的语法高亮
  return jsonStr
    .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
    .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
    .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
    .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
    .replace(/: (null)/g, ': <span class="json-null">$1</span>');
});

// 监听visible变化，打开时加载数据
watch(() => props.visible, async (newVal) => {
  if (newVal) {
    await loadData();
  } else {
    // 关闭时重置状态
    data.value = null;
    error.value = '';
    copied.value = false;
  }
});

// 加载数据
async function loadData() {
  loading.value = true;
  error.value = '';
  data.value = null;

  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/okooo/parse/result/${props.date}/${props.matchId}`
    );

    if (response.status === 404) {
      // 数据不存在
      error.value = `比赛 ${props.matchId} 的解析数据不存在\n\n可能原因：\n1. 该比赛尚未完成爬虫\n2. 该比赛尚未完成解析\n3. 日期不匹配（当前查询：${props.date}）\n\n请先完成爬虫和解析流程`;
      loading.value = false;
      return;
    }

    const result = await response.json();

    if (result.success) {
      data.value = result.data;
    } else {
      error.value = result.message || '获取数据失败';
    }
  } catch (e) {
    error.value = '网络请求失败: ' + (e as Error).message;
  } finally {
    loading.value = false;
  }
}

// 复制数据
async function copyData() {
  if (!data.value) return;

  try {
    const jsonStr = JSON.stringify(data.value, null, 2);
    await navigator.clipboard.writeText(jsonStr);
    copied.value = true;

    // 2秒后恢复按钮状态
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch (e) {
    console.error('复制失败:', e);
    alert('复制失败，请手动复制');
  }
}

// 关闭弹窗
function close() {
  emit('close');
}

// ESC键关闭
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.visible) {
    close();
  }
}

// 监听键盘事件
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleKeydown);
}
</script>

<style scoped>
/* 遮罩层 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* 弹窗容器 */
.modal-container {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

/* 头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-title .icon {
  font-size: 20px;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

/* 内容区 */
.modal-body {
  flex: 1;
  overflow: hidden;
  padding: 0;
  min-height: 300px;
}

.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  gap: 16px;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-state .icon {
  font-size: 48px;
}

.error-state p {
  color: #ef4444;
  font-size: 14px;
  white-space: pre-line;
  text-align: center;
  line-height: 1.6;
  max-width: 90%;
}

/* JSON显示区 */
.data-content {
  height: 100%;
  max-height: 60vh;
  overflow: auto;
}

.json-container {
  background: #1e1e1e;
  padding: 16px;
  min-height: 100%;
}

.json-code {
  margin: 0;
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}

/* JSON语法高亮 */
:deep(.json-key) {
  color: #9cdcfe;
}

:deep(.json-string) {
  color: #ce9178;
}

:deep(.json-number) {
  color: #b5cea8;
}

:deep(.json-boolean) {
  color: #569cd6;
}

:deep(.json-null) {
  color: #569cd6;
}

/* 底部 */
.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  background: #f9fafb;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.copy-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.copy-btn.copied {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9) translateY(20px);
}
</style>
