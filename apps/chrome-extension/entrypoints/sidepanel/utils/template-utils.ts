export interface TemplateField {
  id: string;
  name: string;
  description: string;
  regex: string;
  note: string;
}

export interface CrawlerTemplate {
  fields: TemplateField[];
  updatedAt: string;
  version: string;
}

/**
 * 生成唯一ID
 */
export const generateFieldId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
};

/**
 * 创建新的模板字段
 */
export const createNewField = (overrides: Partial<TemplateField> = {}): TemplateField => {
  return {
    id: generateFieldId(),
    name: '',
    description: '',
    regex: '',
    note: '',
    ...overrides,
  };
};

/**
 * 创建预设的正则字段
 */
export const createRegexField = (
  type: 'match' | 'team' | 'time' | 'odds' | 'custom' = 'custom',
): TemplateField => {
  const presets = {
    match: {
      name: '比赛编号',
      description: '比赛的唯一标识编号',
      regex: 'data-mid="(\\d+)"',
      note: '用于标识每场比赛',
    },
    team: {
      name: '球队名称',
      description: '主队或客队名称',
      regex: 'class="[^"]*team[^"]*"[^>]*>([^<]+)',
      note: '提取球队信息',
    },
    time: {
      name: '比赛时间',
      description: '比赛开始时间',
      regex: 'class="[^"]*time[^"]*"[^>]*>([^<]+)',
      note: '格式：MM-DD HH:mm',
    },
    odds: {
      name: '赔率信息',
      description: '胜平负赔率',
      regex: 'class="[^"]*odds[^"]*"[^>]*>([\\d\\.]+)',
      note: '提取赔率数据',
    },
    custom: {
      name: '自定义字段',
      description: '请输入字段说明',
      regex: '',
      note: '请添加备注',
    },
  };

  return createNewField(presets[type]);
};

/**
 * 获取默认模板字段 - 基于test-rules.json
 */
export const getDefaultTemplateFields = (): TemplateField[] => {
  return [
    {
      id: generateFieldId(),
      name: '比赛编号',
      description: '比赛编号',
      regex: '<p[^>]*class="xuhao"[^>]*>\\s*([^<\\s]+)\\s*</p>',
      note: '比赛编号',
    },
    {
      id: generateFieldId(),
      name: '比赛ID',
      description: '提取比赛ID',
      regex: 'MatchID=([0-9]+)',
      note: '比赛的唯一标识ID',
    },
    {
      id: generateFieldId(),
      name: '联赛名称',
      description: '联赛名称',
      regex: '<a[^>]*class="liansai"[^>]*>[\\s]*([^<]+?)[\\s]*</a>',
      note: '比赛所属联赛',
    },
    {
      id: generateFieldId(),
      name: '比赛时间',
      description: '比赛时间',
      regex: '<time[^>]*class="timetxt"[^>]*>(\\d{2}:\\d{2})</time>',
      note: '比赛开始时间',
    },
    {
      id: generateFieldId(),
      name: '主队名称',
      description: '主队名称',
      regex: '<em[^>]*class="ctrl_homename"[^>]*>([^<]+)</em>',
      note: '主场球队名称',
    },
    {
      id: generateFieldId(),
      name: '主队排名',
      description: '主队排名',
      regex: '<cite class="pm">\\[([^\\]]+)\\]([^<]*)</cite><em class="ctrl_homename">',
      note: '主队当前排名',
    },
    {
      id: generateFieldId(),
      name: '客队名称',
      description: '客队名称',
      regex: '<em[^>]*class="ctrl_awayname"[^>]*>([^<]+)</em>',
      note: '客场球队名称',
    },
    {
      id: generateFieldId(),
      name: '客队排名',
      description: '客队排名',
      regex: '<em class="ctrl_awayname">[^<]+</em>\\s*<cite class="pm">\\[([^\\]]+)\\]([^<]*)</cite>',
      note: '客队当前排名',
    },
    {
      id: generateFieldId(),
      name: '胜赔率',
      description: '胜赔率',
      regex: 'betway="0"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">胜</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '主队获胜赔率',
    },
    {
      id: generateFieldId(),
      name: '平赔率',
      description: '平赔率',
      regex: 'betway="0"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">平</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '平局赔率',
    },
    {
      id: generateFieldId(),
      name: '负赔率',
      description: '负赔率',
      regex: 'betway="0"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">负</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '客队获胜赔率',
    },
    {
      id: generateFieldId(),
      name: '让球数',
      description: '让球数',
      regex: '<em[^>]*class="rangqiu[^>]*ctrl_special"[^>]*>([+-]?[0-9]+)</em>',
      note: '让球盘口数值',
    },
    {
      id: generateFieldId(),
      name: '让球胜赔率',
      description: '让球胜赔率',
      regex: 'betway="1"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">胜</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '让球盘主队获胜赔率',
    },
    {
      id: generateFieldId(),
      name: '让球平赔率',
      description: '让球平赔率',
      regex: 'betway="1"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">平</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '让球盘平局赔率',
    },
    {
      id: generateFieldId(),
      name: '让球负赔率',
      description: '让球负赔率',
      regex: 'betway="1"[\\s\\S]*?<div[^>]*class="listbetbtn ctrl_betopt"[^>]*>[\\s]*<p[^>]*class="fl font3 ctrl_txt">负</p>[\\s]*<p[^>]*class="fr gray9 ctrl_odds">([0-9.]+)</p>',
      note: '让球盘客队获胜赔率',
    },
  ];
};

/**
 * 验证模板字段
 */
export const validateTemplateField = (
  field: TemplateField,
): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (!field.name.trim()) {
    errors.push('字段名称不能为空');
  }

  if (!field.description.trim()) {
    errors.push('字段说明不能为空');
  }

  if (!field.regex.trim()) {
    errors.push('正则表达式不能为空');
  } else {
    try {
      new RegExp(field.regex);
    } catch (e) {
      errors.push('正则表达式格式无效');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};

/**
 * 验证整个模板
 */
export const validateTemplate = (fields: TemplateField[]): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (fields.length === 0) {
    errors.push('模板至少需要一个字段');
    return { valid: false, errors };
  }

  // 检查字段名称重复
  const names = fields.map((f) => f.name.trim()).filter((n) => n);
  const duplicateNames = names.filter((name, index) => names.indexOf(name) !== index);
  if (duplicateNames.length > 0) {
    errors.push(`字段名称重复: ${[...new Set(duplicateNames)].join(', ')}`);
  }

  // 验证每个字段
  fields.forEach((field, index) => {
    const validation = validateTemplateField(field);
    if (!validation.valid) {
      errors.push(`字段 ${index + 1}: ${validation.errors.join(', ')}`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
};

/**
 * 保存模板到存储
 */
export const saveTemplateToStorage = async (
  fields: TemplateField[],
): Promise<{ success: boolean; error?: string }> => {
  try {
    const validation = validateTemplate(fields);
    if (!validation.valid) {
      return {
        success: false,
        error: validation.errors.join('; '),
      };
    }

    const template: CrawlerTemplate = {
      fields,
      updatedAt: new Date().toISOString(),
      version: '1.0.0',
    };

    await chrome.storage.local.set({ crawlerTemplate: template });
    return { success: true };
  } catch (error: any) {
    return {
      success: false,
      error: error.message || '保存失败',
    };
  }
};

/**
 * 从存储加载模板
 */
export const loadTemplateFromStorage = async (): Promise<{
  success: boolean;
  template?: CrawlerTemplate;
  error?: string;
}> => {
  try {
    const result = await chrome.storage.local.get('crawlerTemplate');
    if (result.crawlerTemplate) {
      return {
        success: true,
        template: result.crawlerTemplate,
      };
    } else {
      // 返回默认模板
      const defaultTemplate: CrawlerTemplate = {
        fields: getDefaultTemplateFields(),
        updatedAt: new Date().toISOString(),
        version: '1.0.0',
      };
      return {
        success: true,
        template: defaultTemplate,
      };
    }
  } catch (error: any) {
    return {
      success: false,
      error: error.message || '加载失败',
    };
  }
};

/**
 * 导出模板为JSON
 */
export const exportTemplate = (fields: TemplateField[]): string => {
  const template: CrawlerTemplate = {
    fields,
    updatedAt: new Date().toISOString(),
    version: '1.0.0',
  };
  return JSON.stringify(template, null, 2);
};

/**
 * 从JSON导入模板
 */
export const importTemplate = (
  jsonString: string,
): { success: boolean; fields?: TemplateField[]; error?: string } => {
  try {
    const template = JSON.parse(jsonString) as CrawlerTemplate;

    if (!template.fields || !Array.isArray(template.fields)) {
      return {
        success: false,
        error: '无效的模板格式：缺少fields字段',
      };
    }

    const validation = validateTemplate(template.fields);
    if (!validation.valid) {
      return {
        success: false,
        error: `模板验证失败: ${validation.errors.join('; ')}`,
      };
    }

    return {
      success: true,
      fields: template.fields,
    };
  } catch (error: any) {
    return {
      success: false,
      error: `解析失败: ${error.message}`,
    };
  }
};
