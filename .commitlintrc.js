module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat',     // 新功能
      'fix',      // 修复Bug
      'docs',     // 文档更新
      'style',    // 代码格式（不影响功能）
      'refactor', // 重构（不是新功能也不是修复）
      'perf',     // 性能优化
      'test',     // 测试相关
      'chore'     // 构建/工具相关
      'revert',   // 回滚提交
      'build'     // 构建系统或外部依赖变更
      'ci'        // CI配置文件和脚本变更
      'chore'     // 其他不修改src或test文件的变更
    ]],
    'type-case': [2, 'always', 'lower-case'],
    'scope-case': [2, 'always', 'kebab-case'],
    'subject-case': [0, 'never'],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 100],
    'body-leading-blank': [1, 'always'],
    'body-max-line-length': [2, 'always', 100],
    'footer-max-line-length': [2, 'always', 100],
  },
  plugins: [
    'commitlint-plugin-function-rules',
  ],
  ignores: [
    '(?:^|\\s*)(?:Merge pull request|Merge branch|Squash|Rebase|Fixup)',
    '(?:^|\\s*)(?:Initial commit|Update README|Update documentation)',
    '(?:^|\\s*)(?:Bump version|Release v\\d+\\.\\d+\\.\\d+)',
    '(?:^|\\s*)(?:Update dependencies|Update submodules)',
  ],
};
