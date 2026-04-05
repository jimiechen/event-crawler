var ChanLunReportGen = (function() {
    'use strict';

    function generateMarkdown(results) {
        if (!results || results.length === 0) return '# 无测试结果\n';
        var passed = results.filter(function(r) { return r.status === 'passed'; }).length;
        var failed = results.length - passed;

        var md = '# 缠论自动画图 - 自动化测试报告\n\n';
        md += '## 测试概览\n\n| 项目 | 数值 |\n|------|------|\n';
        md += '| 总用例数 | ' + results.length + ' |\n';
        md += '| ✅ 通过 | ' + passed + ' |\n';
        md += '| ❌ 失败 | ' + failed + ' |\n';
        md += '| 通过率 | ' + (results.length > 0 ? ((passed / results.length) * 100).toFixed(1) : 0) + '% |\n';
        md += '| 测试时间 | ' + new Date().toLocaleString('zh-CN') + ' |\n\n';

        md += '## 详细结果\n\n';
        results.forEach(function(r) {
            md += (r.status === 'passed' ? '### ✅ ' : '### ❌ ') + r.name + '\n\n';
            md += '**状态**: ' + (r.status === 'passed' ? '通过' : '失败') + '\n\n';
            if (r.expected) md += '**预期结果**: ' + r.expected + '\n\n';
            if (!r.pass && r.actual) md += '**实际结果**: ' + r.actual + '\n\n';

            if (r.step && r.step.length) {
                md += '#### 操作步骤\n';
                r.step.forEach(function(s, i) { md += (i + 1) + '. ' + s + '\n'; });
                md += '\n';
            }
            if (r.screenshot) md += '![截图](' + r.screenshot + ')\n\n';
            if (r.video) md += '📹 [录屏视频](' + r.video + ')\n\n';
            md += '---\n\n';
        });

        md += '## 环境信息\n- **浏览器**: Chromium (Playwright)\n';
        if (typeof process !== 'undefined' && process.platform) md += '- **操作系统**: ' + process.platform + '\n';
        md += '- **生成时间**: ' + new Date().toISOString() + '\n';

        return md;
    }

    function generateHTML(results) {
        var passed = results.filter(function(r) { return r.status === 'passed'; }).length;
        var failed = results.length - passed;
        var pct = results.length > 0 ? ((passed / results.length) * 100).toFixed(1) : 0;

        var html = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">';
        html += '<title>缠论测试报告</title>';
        html += '<style>body{font-family:"Microsoft YaHei",sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#f8fafc;}';
        html += '.card{background:white;border-radius:8px;padding:16px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,0.08);}';
        html += '.pass{color:#16a34a}.fail{color:#dc2626}.badge{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:bold}';
        html += '.badge-pass{background:#dcfce7;color:#16a34a}.badge-fail{background:#fee2e2;color:#dc2626}';
        html += '.step{font-size:13px;color:#64748b;padding:4px 0 4px 16px;} .screenshot{max-width:100%;border-radius:6px;margin-top:8px;border:1px solid #e2e8f0;}</style>';
        html += '</head><body>';

        html += '<div class="card"><h1 style="margin:0">📐 缠论自动画图 - 测试报告</h1>';
        html += '<p style="color:#64748b">' + new Date().toLocaleString('zh-CN') + '</p></div>';

        html += '<div class="card" style="display:flex;gap:15px;flex-wrap:wrap;">';
        html += '<div class="badge badge-pass">✅ 通过 ' + passed + '</div>';
        html += '<div class="badge badge-fail">❌ 失败 ' + failed + '</div>';
        html += '<div class="badge" style="background:#f1f5f9;color:#475569">总计 ' + results.length + '</div>';
        html += '<div class="badge" style="background:#ede9fe;color:#6d28d9">通过率 ' + pct + '%</div></div>';

        results.forEach(function(r) {
            html += '<div class="card">';
            html += '<h3 style="margin:0 0 8px">' + (r.status === 'passed' ? '✅' : '❌') + ' ' + r.name + '</h3>';
            if (r.expected) html += '<p style="margin:4px 0;font-size:13px;"><b>预期:</b> ' + r.expected + '</p>';
            if (!r.pass && r.actual) html += '<p style="margin:4px 0;font-size:13px;color:#dc2626;"><b>实际:</b> ' + r.actual + '</p>';
            if (r.step && r.step.length) {
                html += '<div style="margin-top:8px;font-size:13px;color:#64748b;font-weight:bold;">操作步骤:</div>';
                r.step.forEach(function(s, i) { html += '<div class="step">' + (i+1) + '. ' + s + '</div>'; });
            }
            if (r.screenshot) html += '<img class="screenshot" src="' + r.screenshot + '" alt="截图"/>';
            html += '</div>';
        });

        html += '</body></html>';
        return html;
    }

    return {
        generateMarkdown: generateMarkdown,
        generateHTML: generateHTML
    };
})();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChanLunReportGen;
}
