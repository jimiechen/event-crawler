/**
 * 足球比赛数据解析器 - Chrome扩展版本
 * 适用于Chrome扩展环境，移除了Node.js特定依赖
 */

/**
 * 调用chrome_get_web_content工具获取HTML内容
 * @param {string} url - 目标URL
 * @param {string} sessionId - MCP会话ID
 * @returns {Promise<Object|null>} 工具调用结果
 */
export async function getChromeWebContent(url, sessionId) {
  console.log(`\n🌐 调用chrome_get_web_content工具...`);
  console.log(`📍 目标URL: ${url}`);
  console.log(`🔑 会话ID: ${sessionId}`);
  console.log(`📋 请求参数:`, {
    url: url,
    htmlContent: true,
    textContent: false,
    wait_time: 5000,
    timeout: 30000,
  });

  const toolCallRequest = {
    jsonrpc: '2.0',
    id: 2,
    method: 'tools/call',
    params: {
      name: 'chrome_get_web_content',
      arguments: {
        url: url,
        htmlContent: true, // 获取HTML内容而不是文本
        textContent: false,
        wait_time: 5000, // 增加等待时间
        timeout: 30000, // 添加超时设置
      },
    },
  };

  try {
    const response = await fetch('http://localhost:56889/mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        'User-Agent': 'Football-Parser/1.0',
        'MCP-Session-ID': sessionId,
      },
      body: JSON.stringify(toolCallRequest),
    });

    console.log(`📊 响应状态: ${response.status}`);
    console.log(`📋 响应头:`, Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ HTTP错误 ${response.status}: ${errorText}`);
      throw new Error(`HTTP错误 ${response.status}: ${errorText}`);
    }

    const data = await response.text();
    console.log(`📄 原始响应数据长度: ${data.length}`);
    console.log(`📄 原始响应数据前500字符:`, data.substring(0, 500));

    let toolResult = null;

    if (data.includes('event: message')) {
      // 解析SSE格式
      console.log('🔍 检测到SSE格式响应，开始解析...');
      const lines = data.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(line.substring(6));
            console.log('📋 SSE数据行:', jsonData);
            if (jsonData.result && !jsonData.result.isError) {
              toolResult = jsonData.result;
              console.log('✅ 找到有效的SSE结果');

              // 检查并解析content字段
              if (toolResult.content && Array.isArray(toolResult.content)) {
                // 如果content是数组，查找text类型的内容
                for (const contentItem of toolResult.content) {
                  if (contentItem.type === 'text' && contentItem.text) {
                    try {
                      // 尝试解析text字段中的JSON
                      const textData = JSON.parse(contentItem.text);
                      if (textData.htmlContent) {
                        toolResult.content = textData.htmlContent;
                        console.log('✅ 成功提取htmlContent字符串');
                        break;
                      }
                    } catch (e) {
                      // 如果不是JSON，直接使用text内容
                      toolResult.content = contentItem.text;
                      console.log('✅ 使用text内容作为htmlContent');
                      break;
                    }
                  }
                }
              }
              break;
            }
          } catch (e) {
            console.log('⚠️  SSE行解析失败，继续尝试下一行:', e.message);
          }
        }
      }

      if (!toolResult) {
        console.error('❌ SSE格式响应中未找到有效结果');
        throw new Error('SSE格式响应中未找到有效结果');
      }
    } else {
      // 尝试直接解析JSON
      console.log('🔍 尝试直接解析JSON格式响应...');
      try {
        const response = JSON.parse(data);
        console.log('📋 JSON响应:', response);
        if (response.result && !response.result.isError) {
          toolResult = response.result;
          console.log('✅ 找到有效的JSON结果');
        } else {
          console.error('❌ JSON响应中未找到有效结果或存在错误');
          throw new Error('JSON响应中未找到有效结果或存在错误');
        }
      } catch (e) {
        console.error(`❌ JSON解析失败: ${e.message}`);
        throw new Error(`JSON解析失败: ${e.message}`);
      }
    }

    if (toolResult) {
      console.log('✅ 成功获取页面HTML内容');
      console.log(`📄 HTML内容长度: ${toolResult.content ? toolResult.content.length : 0}`);
      return toolResult;
    } else {
      console.error(`❌ 工具执行错误或响应格式异常`);
      throw new Error('工具执行错误或响应格式异常');
    }
  } catch (error) {
    console.error(`❌ 获取页面内容失败: ${error.message}`);
    throw error;
  }
}

/**
 * 解析足球比赛数据
 * @param {string} htmlContent - HTML内容
 * @returns {Array} 解析后的比赛数据数组
 */
export function parseFootballMatches(htmlContent) {
  console.log('\n⚽ 开始解析足球比赛数据...');

  // 类型检查和转换
  if (typeof htmlContent !== 'string') {
    console.log('⚠️  htmlContent不是字符串类型，尝试转换...');
    console.log('📋 htmlContent类型:', typeof htmlContent);
    console.log('📋 htmlContent值:', htmlContent);

    if (htmlContent && typeof htmlContent === 'object') {
      // 如果是对象，尝试提取字符串内容
      if (htmlContent.content) {
        htmlContent = htmlContent.content;
      } else if (htmlContent.htmlContent) {
        htmlContent = htmlContent.htmlContent;
      } else {
        htmlContent = JSON.stringify(htmlContent);
      }
    } else {
      htmlContent = String(htmlContent || '');
    }

    console.log('✅ 转换后的htmlContent类型:', typeof htmlContent);
  }

  console.log(`📄 HTML内容长度: ${htmlContent.length} 字符`);

  // 提取比赛日期
  let matchDate = '';
  const datePattern =
    /<p class="listtoptxt fl font12"[^>]*>[^<]*?([0-9]{4}-[0-9]{2}-[0-9]{2})[^<]*?<\/p>/i;
  const dateMatch = htmlContent.match(datePattern);
  if (dateMatch) {
    matchDate = dateMatch[1];
    console.log(`📅 提取到比赛日期: ${matchDate}`);
  } else {
    console.log('⚠️  未找到比赛日期，尝试其他模式...');
    // 尝试更宽松的日期匹配
    const looseDatePattern = /([0-9]{4}-[0-9]{2}-[0-9]{2})/;
    const looseDateMatch = htmlContent.match(looseDatePattern);
    if (looseDateMatch) {
      matchDate = looseDateMatch[1];
      console.log(`📅 使用宽松模式提取到日期: ${matchDate}`);
    }
  }

  const footballMatches = [];

  try {
    // 添加调试：检查HTML中是否包含关键元素
    console.log('🔍 检查HTML结构...');
    const hasCtrlEachmatch = htmlContent.includes('ctrl_eachmatch');
    const hasDataMid = htmlContent.includes('data-mid=');
    const hasXuhao = htmlContent.includes('class="xuhao"');
    console.log(`  - ctrl_eachmatch: ${hasCtrlEachmatch}`);
    console.log(`  - data-mid: ${hasDataMid}`);
    console.log(`  - xuhao: ${hasXuhao}`);

    // 如果没有找到关键元素，输出HTML片段用于调试
    if (!hasCtrlEachmatch) {
      console.log('⚠️  未找到ctrl_eachmatch，输出HTML片段用于调试:');
      const htmlPreview = htmlContent.substring(0, 2000);
      console.log('HTML前2000字符:', htmlPreview);
    }

    // 使用正则表达式分割每个比赛项目 - 匹配完整的比赛项目结构
    const matchPattern =
      /<div[^>]*class="[^"]*ctrl_eachmatch[^"]*"[^>]*data-mid="(\d+)"[^>]*>([\s\S]*?)(?=<div[^>]*class="[^"]*ctrl_eachmatch[^"]*"|<\/section>)/g;
    const matches = [];
    let match;

    console.log('🔍 开始正则匹配...');
    while ((match = matchPattern.exec(htmlContent)) !== null) {
      console.log(`  ✅ 找到比赛: matchId=${match[1]}`);
      matches.push({
        matchId: match[1],
        html: match[2],
      });
    }

    console.log(`🎯 正则匹配结果: 找到 ${matches.length} 个比赛容器`);

    if (matches.length === 0) {
      console.log('🔍 未找到比赛数据，尝试查找其他可能的容器...');
      const possibleContainers = [
        /<div[^>]*class="[^"]*match[^"]*"/gi,
        /<div[^>]*class="[^"]*game[^"]*"/gi,
        /<div[^>]*class="[^"]*item[^"]*"/gi,
        /<div[^>]*data-[^>]*>/gi,
      ];

      possibleContainers.forEach((pattern, index) => {
        const found = htmlContent.match(pattern);
        if (found && found.length > 0) {
          console.log(`🔍 可能的容器模式 ${index + 1}:`, found.slice(0, 3));
        }
      });

      return [];
    }

    // 处理每个比赛项目
    matches.forEach((matchData, index) => {
      const matchId = matchData.matchId;
      const matchHtml = matchData.html;

      console.log(`🔍 开始解析比赛 ${matchId}...`);

      const match = {
        matchId: matchId,
        matchNumber: null,
        basicInfo: {},
        teams: {
          home: {},
          away: {},
        },
        odds: {
          win: null,
          draw: null,
          lose: null,
        },
        handicapOdds: {
          win: null,
          draw: null,
          lose: null,
          handicap: null,
        },
        links: {},
        moreGames: 0,
        rawHtml: matchHtml, // 添加原始HTML数据用于调试
      };

      // 1. 提取基本信息
      console.log(`  📋 解析基本信息...`);

      // 比赛序号（如"一005"）
      const matchNumberMatch = matchHtml.match(/<p class="xuhao">\s*([^<]+?)\s*<\/p>/i);
      if (matchNumberMatch) {
        match.matchNumber = matchNumberMatch[1].trim();
        console.log(`    ✅ 比赛序号: ${match.matchNumber}`);
      } else {
        console.log(`    ❌ 未找到比赛序号`);
      }

      // 提取MatchID（从链接中提取）
      const matchIdPattern = /href="[^"]*MatchID=([^&"]+)/i;
      const matchIdMatch = matchHtml.match(matchIdPattern);
      if (matchIdMatch) {
        match.matchId = matchIdMatch[1].trim();
        console.log(`    ✅ MatchID: ${match.matchId}`);
      } else {
        console.log(`    ❌ 未找到MatchID`);
      }

      // 联赛名称
      const leagueMatch = matchHtml.match(/<a[^>]*class="liansai"[^>]*>([^<]+)<\/a>/i);
      if (leagueMatch) {
        match.basicInfo.league = leagueMatch[1].trim();
        console.log(`    ✅ 联赛: ${match.basicInfo.league}`);
      } else {
        console.log(`    ❌ 未找到联赛名称`);
      }

      // 比赛时间
      const timeMatch = matchHtml.match(/<time[^>]*class="timetxt"[^>]*>([^<]+)<\/time>/i);
      if (timeMatch) {
        const originalTime = timeMatch[1].trim();
        // 如果有日期，则组合日期和时间
        if (matchDate) {
          match.basicInfo.time = `${matchDate} ${originalTime}`;
        } else {
          match.basicInfo.time = originalTime;
        }
        console.log(`    ✅ 比赛时间: ${match.basicInfo.time}`);
      } else {
        console.log(`    ❌ 未找到比赛时间`);
        // 如果没有找到时间但有日期，至少显示日期
        if (matchDate) {
          match.basicInfo.time = matchDate;
        }
      }

      // 2. 提取球队信息
      console.log(`  🏈 解析球队信息...`);

      // 主队名称和排名 - 支持多种HTML结构
      let homeTeamMatch = matchHtml.match(
        /<cite[^>]*class="pm"[^>]*>\[([^\]]+)\]<\/cite><em[^>]*class="ctrl_homename"[^>]*>([^<]+)<\/em>/i,
      );
      if (homeTeamMatch) {
        match.teams.home = {
          name: homeTeamMatch[2].trim(),
          rank: homeTeamMatch[1].trim(),
        };
        console.log(`    ✅ 主队(带排名): ${match.teams.home.name} [${match.teams.home.rank}]`);
      } else {
        // 尝试匹配没有排名的主队名称
        homeTeamMatch = matchHtml.match(/<em[^>]*class="ctrl_homename"[^>]*>([^<]+)<\/em>/i);
        if (homeTeamMatch) {
          match.teams.home = {
            name: homeTeamMatch[1].trim(),
            rank: '',
          };
          console.log(`    ✅ 主队(无排名): ${match.teams.home.name}`);
        } else {
          console.log(`    ❌ 未找到主队信息，输出HTML片段用于调试:`);
          console.log(matchHtml.substring(0, 500));
          match.teams.home = {
            name: '',
            rank: '',
          };
        }
      }

      // 客队名称和排名 - 支持多种HTML结构
      let awayTeamMatch = matchHtml.match(
        /<em[^>]*class="ctrl_awayname"[^>]*>([^<]+)<\/em>\s*<cite[^>]*class="pm"[^>]*>\[([^\]]+)\]<\/cite>/i,
      );
      if (awayTeamMatch) {
        match.teams.away = {
          name: awayTeamMatch[1].trim(),
          rank: awayTeamMatch[2].trim(),
        };
        console.log(`    ✅ 客队(带排名): ${match.teams.away.name} [${match.teams.away.rank}]`);
      } else {
        // 尝试匹配没有排名的客队名称
        awayTeamMatch = matchHtml.match(/<em[^>]*class="ctrl_awayname"[^>]*>([^<]+)<\/em>/i);
        if (awayTeamMatch) {
          match.teams.away = {
            name: awayTeamMatch[1].trim(),
            rank: '',
          };
          console.log(`    ✅ 客队(无排名): ${match.teams.away.name}`);
        } else {
          console.log(`    ❌ 未找到客队信息，输出HTML片段用于调试:`);
          console.log(matchHtml.substring(0, 500));
          match.teams.away = {
            name: '',
            rank: '',
          };
        }
      }

      // 3. 提取赔率数据
      // 检查是否为未开售状态 - 查找包含"未"、"开"、"售"的按钮
      const notAvailablePattern =
        /<div class="listbetbtn listbetbtnnot ctrl_not_sale ctrl_betopt"[^>]*>\s*<p class="fl font3 ctrl_txt">(未|开|售)<\/p>/;
      const isNotAvailable = notAvailablePattern.test(matchHtml);

      // 提取胜平负赔率 (betway="0")
      const betway0Pattern =
        /<div[^>]*class="[^"]*ctrl_betway_wrap[^"]*"[^>]*betway="0"[^>]*>([\s\S]*?)<\/div>\s*<\/div>/;
      const betway0Match = betway0Pattern.exec(matchHtml);

      if (isNotAvailable) {
        // 未开售状态，胜平负赔率设为0
        match.odds = { win: 0, draw: 0, lose: 0 };
        console.log(`    ⚠️  比赛未开售`);
      } else {
        // 正常状态，提取实际赔率
        const odds = { win: null, draw: null, lose: null };

        if (betway0Match) {
          const betway0Content = betway0Match[1];

          // 分别提取胜、平、负的赔率
          const winMatch = betway0Content.match(
            /data-v="16"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
          );
          const drawMatch = betway0Content.match(
            /data-v="15"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
          );
          const loseMatch = betway0Content.match(
            /data-v="14"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
          );

          if (winMatch) odds.win = parseFloat(winMatch[1]) || 0;
          if (drawMatch) odds.draw = parseFloat(drawMatch[1]) || 0;
          if (loseMatch) odds.lose = parseFloat(loseMatch[1]) || 0;

          console.log(`    ✅ 胜平负赔率: ${odds.win} / ${odds.draw} / ${odds.lose}`);
        }

        match.odds = odds;
      }

      // 提取让球胜平负赔率 (betway="1") - 无论是否未开售都要解析
      const betway1Pattern =
        /<div[^>]*class="[^"]*ctrl_betway_wrap[^"]*"[^>]*betway="1"[^>]*>([\s\S]*?)<\/div>\s*<\/div>/;
      const betway1Match = betway1Pattern.exec(matchHtml);

      if (betway1Match) {
        const betway1Content = betway1Match[1];

        // 提取让球数 - 从em标签的data-v属性中提取
        const handicapPattern = /<em[^>]*data-v="([^"]+)"[^>]*>([^<]+)<\/em>/;
        const handicapMatch = handicapPattern.exec(betway1Content);
        if (handicapMatch) {
          match.handicapOdds.handicap = handicapMatch[1]; // data-v的值
        }

        // 分别提取胜、平、负的赔率
        const winMatch = betway1Content.match(
          /data-v="13"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
        );
        const drawMatch = betway1Content.match(
          /data-v="11"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
        );
        const loseMatch = betway1Content.match(
          /data-v="10"[^>]*>[\s\S]*?<p class="fr gray9 ctrl_odds">([\d.]+)<\/p>/,
        );

        if (winMatch) match.handicapOdds.win = parseFloat(winMatch[1]) || null;
        if (drawMatch) match.handicapOdds.draw = parseFloat(drawMatch[1]) || null;
        if (loseMatch) match.handicapOdds.lose = parseFloat(loseMatch[1]) || null;

        console.log(
          `    ✅ 让球${match.handicapOdds.handicap}赔率: ${match.handicapOdds.win} / ${match.handicapOdds.draw} / ${match.handicapOdds.lose}`,
        );
      }

      // 4. 提取链接信息
      // 构建6个完整的链接字段
      const baseUrl = 'https://m.okooo.com';
      const fromParam = '&from=%2Fweixin%2Fjing%2F';

      // 设置6个必需的链接字段
      match.links = {
        handicap: `${baseUrl}/match/handicap.php?MatchID=${match.matchId}${fromParam}`,
        exchanges: `${baseUrl}/match/exchanges.php?MatchID=${match.matchId}${fromParam}`,
        game: `${baseUrl}/match/game.php?MatchID=${match.matchId}${fromParam}`,
        form: `${baseUrl}/match/form.php?MatchID=${match.matchId}${fromParam}`,
        odds: `${baseUrl}/match/odds.php?MatchID=${match.matchId}${fromParam}`,
        history: `${baseUrl}/match/history.php?MatchID=${match.matchId}${fromParam}`,
      };

      // 5. 提取更多玩法数量
      const moreGamesPattern = /<cite[^>]*class="[^"]*morenum[^"]*"[^>]*>(\d+)<\/cite>/i;
      const moreGamesMatch = matchHtml.match(moreGamesPattern);
      const moreGamesCount = moreGamesMatch ? parseInt(moreGamesMatch[1]) : 0;

      // 设置更多玩法数量
      match.moreGames = moreGamesCount;

      footballMatches.push(match);

      console.log(
        `✅ 解析比赛: ${match.matchNumber} ${match.teams.home.name || 'undefined'} vs ${match.teams.away.name || 'undefined'}`,
      );
    });

    console.log(`\n🎯 总共解析到 ${footballMatches.length} 场比赛`);
    return footballMatches;
  } catch (error) {
    console.error('❌ 足球比赛数据解析失败:', error.message);
    throw error;
  }
}

/**
 * 初始化MCP会话
 * @returns {Promise<string|null>} 会话ID或null
 */
export async function initializeMCPSession() {
  console.log('🔌 初始化MCP会话...');

  const initRequest = {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {
        tools: {},
      },
      clientInfo: {
        name: 'Football-Parser',
        version: '1.0.0',
      },
    },
  };

  try {
    const response = await fetch('http://localhost:56889/mcp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
        'User-Agent': 'Football-Parser/1.0',
      },
      body: JSON.stringify(initRequest),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ MCP初始化失败: HTTP ${response.status}: ${errorText}`);
      return null;
    }

    const data = await response.text();
    let result = null;

    // 处理SSE格式响应
    if (data.includes('event: message')) {
      const lines = data.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonData = JSON.parse(line.substring(6));
            if (jsonData.result) {
              result = jsonData;
              break;
            }
          } catch (e) {
            // 继续尝试下一行
          }
        }
      }
    } else {
      // 尝试直接解析JSON
      result = JSON.parse(data);
    }

    if (result && result.result) {
      const sessionId = response.headers.get('mcp-session-id') || 'default-session';
      console.log('✅ MCP会话初始化成功');
      console.log(`📋 会话ID: ${sessionId}`);
      return sessionId;
    } else {
      console.error('❌ MCP初始化失败: 无效响应');
      return null;
    }
  } catch (error) {
    console.error(`❌ MCP连接错误: ${error.message}`);
    return null;
  }
}

/**
 * 生成足球比赛报告
 * @param {Array} matches - 比赛数据数组
 */
export function generateFootballReport(matches) {
  console.log('\n📊 === 足球比赛数据报告 ===');
  console.log(`总比赛场次: ${matches.length}`);

  // 按联赛统计
  const leagueStats = {};
  matches.forEach((match) => {
    const league = match.basicInfo.league || '未知联赛';
    leagueStats[league] = (leagueStats[league] || 0) + 1;
  });

  console.log('\n📈 联赛分布:');
  Object.entries(leagueStats).forEach(([league, count]) => {
    console.log(`  ${league}: ${count} 场`);
  });

  // 显示前几场比赛的详细信息
  console.log('\n🏆 比赛详情 (前5场):');
  matches.slice(0, 5).forEach((match, index) => {
    console.log(`\n${index + 1}. ${match.matchNumber} - ${match.basicInfo.league}`);
    console.log(`   MatchID: ${match.matchId}`);
    console.log(`   时间: ${match.basicInfo.time}`);
    console.log(
      `   对阵: ${match.teams.home?.name}[${match.teams.home?.rank || '?'}] vs ${match.teams.away?.name}[${match.teams.away?.rank || '?'}]`,
    );

    if (match.odds.win !== 0 || match.odds.draw !== 0 || match.odds.lose !== 0) {
      console.log(
        `   胜平负: ${match.odds.win || '?'} / ${match.odds.draw || '?'} / ${match.odds.lose || '?'}`,
      );

      if (match.handicapOdds.handicap) {
        console.log(
          `   让球${match.handicapOdds.handicap}: ${match.handicapOdds.win || '?'} / ${match.handicapOdds.draw || '?'} / ${match.handicapOdds.lose || '?'}`,
        );
      }
    } else {
      console.log(`   赔率: 未开售`);
    }
  });
}
