<template>
  <div class="template-editor">
    <div class="header">
      <h3>爬虫模板配置</h3>
      <div class="header-actions">
        <button @click="saveTemplate" class="save-btn">保存模板</button>
        <button @click="resetTemplate" class="reset-btn">重置</button>
      </div>
    </div>

    <div class="template-fields">
      <div v-for="(field, index) in templateFields" :key="field.id" class="field-row">
        <div class="field-header">
          <span class="field-number">{{ index + 1 }}</span>
          <input v-model="field.name" placeholder="字段名称" class="field-name" />
          <button
            @click="removeField(index)"
            class="remove-btn"
            :disabled="templateFields.length <= 1"
          >
            ×
          </button>
        </div>

        <div class="field-content">
          <div class="input-group">
            <label>说明:</label>
            <input v-model="field.description" placeholder="字段说明" class="field-input" />
          </div>

          <div class="input-group">
            <label>正则:</label>
            <textarea
              v-model="field.regex"
              placeholder="正则表达式"
              class="field-textarea"
              rows="2"
            ></textarea>
          </div>

          <div class="input-group">
            <label>备注:</label>
            <input v-model="field.note" placeholder="备注信息" class="field-input" />
          </div>
        </div>
      </div>
    </div>

    <div class="actions">
      <button @click="addField" class="add-btn"> + 增加字段 </button>
      <button @click="addRegexField" class="add-regex-btn"> + 新增正则 </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';

interface TemplateField {
  id: string;
  name: string;
  description: string;
  regex: string;
  note: string;
}

const templateFields = ref<TemplateField[]>([]);

// 初始化默认字段
const initializeDefaultFields = async () => {
  try {
    const response = await fetch(chrome.runtime.getURL('test-scripts/test-rules.json'));
    const testRulesData = await response.json();
    
    // 将test-rules.json的数据转换为模板字段格式
    templateFields.value = testRulesData.parsingRules.map((rule: any) => ({
      id: generateId(),
      name: rule.description, // 使用description作为显示名称
      description: rule.description,
      regex: rule.regex,
      note: rule.fieldName,
    }));
    
    console.log('从test-rules.json初始化模板字段:', templateFields.value.length, '个字段');
  } catch (error) {
    console.error('初始化模板字段失败:', error);
    // 如果加载失败，使用空数组
    templateFields.value = [];
  }
};

// 生成唯一ID
const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

// 添加新字段
const addField = () => {
  templateFields.value.push({
    id: generateId(),
    name: '',
    description: '',
    regex: '',
    note: '',
  });
};

// 添加正则字段
const addRegexField = () => {
  templateFields.value.push({
    id: generateId(),
    name: '新正则字段',
    description: '请输入字段说明',
    regex: '',
    note: '请添加备注',
  });
};

// 删除字段
const removeField = (index: number) => {
  if (templateFields.value.length > 1) {
    templateFields.value.splice(index, 1);
  }
};

// 保存模板
const saveTemplate = () => {
  const template = {
    fields: templateFields.value,
    updatedAt: new Date().toISOString(),
  };

  // 保存到本地存储
  chrome.storage.local
    .set({ crawlerTemplate: template })
    .then(() => {
      console.log('模板保存成功');
      // 可以添加成功提示
    })
    .catch((error) => {
      console.error('模板保存失败:', error);
    });
};

// 重置模板
const resetTemplate = async () => {
  await initializeDefaultFields();
};

// 加载保存的模板
const loadTemplate = async () => {
  try {
    const result = await chrome.storage.local.get('crawlerTemplate');
    if (result.crawlerTemplate && result.crawlerTemplate.fields) {
      templateFields.value = result.crawlerTemplate.fields;
    } else {
      await initializeDefaultFields();
    }
  } catch (error) {
    console.error('加载模板失败:', error);
    await initializeDefaultFields();
  }
};

// 定义事件
const emit = defineEmits<{
  'template-updated': [fields: TemplateField[]];
}>();

// 组件挂载时加载模板
onMounted(() => {
  loadTemplate();
});

// 监听模板字段变化
watch(
  templateFields,
  (newFields) => {
    emit('template-updated', newFields);
  },
  { deep: true },
);

// 导出模板数据供父组件使用
defineExpose({
  templateFields,
  saveTemplate,
  resetTemplate,
});
</script>

<style scoped>
.template-editor {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #333;
}

.header h3 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.save-btn,
.reset-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.save-btn {
  background: #4caf50;
  color: white;
}

.save-btn:hover {
  background: #45a049;
}

.reset-btn {
  background: #f44336;
  color: white;
}

.reset-btn:hover {
  background: #da190b;
}

.template-fields {
  max-height: 400px;
  overflow-y: auto;
}

.field-row {
  background: #2a2a2a;
  border-radius: 6px;
  margin-bottom: 15px;
  padding: 15px;
  border: 1px solid #333;
}

.field-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.field-number {
  background: #4caf50;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.field-name {
  flex: 1;
  padding: 8px 12px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 14px;
}

.field-name:focus {
  outline: none;
  border-color: #4caf50;
}

.remove-btn {
  background: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:disabled {
  background: #666;
  cursor: not-allowed;
}

.remove-btn:hover:not(:disabled) {
  background: #da190b;
}

.field-content {
  display: grid;
  gap: 12px;
}

.input-group {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.input-group label {
  color: #ccc;
  font-size: 12px;
  min-width: 40px;
  padding-top: 8px;
}

.field-input,
.field-textarea {
  flex: 1;
  padding: 8px 12px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.field-textarea {
  resize: vertical;
  min-height: 50px;
}

.field-input:focus,
.field-textarea:focus {
  outline: none;
  border-color: #4caf50;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #333;
}

.add-btn,
.add-regex-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.add-btn {
  background: #2196f3;
  color: white;
}

.add-btn:hover {
  background: #1976d2;
}

.add-regex-btn {
  background: #ff9800;
  color: white;
}

.add-regex-btn:hover {
  background: #f57c00;
}
</style>
