const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

const CONFIG_PATH = path.join(__dirname, 'config.json');

// 读取配置
function readConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    return { stocks: [], schedule: { enabled: true, time: '09:00', days: [1,2,3,4,5] }, feishuWebhook: '' };
  }
  return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
}

// 调用 Python 脚本获取股票数据
function getStockData(code) {
  return new Promise((resolve, reject) => {
    const cmd = `python3 "${path.join(__dirname, 'get_stock_data.py')}" "${code}"`;
    exec(cmd, { timeout: 30000, env: { ...process.env, PYTHONPATH: '/Users/alextu/Library/Python/3.9/lib/python/site-packages' } }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(`Python 执行失败: ${error.message}`));
        return;
      }
      try {
        const data = JSON.parse(stdout);
        resolve(data);
      } catch (e) {
        reject(new Error('解析 Python 输出失败'));
      }
    });
  });
}

// ====== 多 Agent 分析引擎 ======

function analyzeValuation(price, fundamentals) {
  const analysis = [];
  const score = { value: 0, max: 0 };

  // PE 分析
  if (fundamentals.pe) {
    score.max += 25;
    if (fundamentals.pe < 15) { analysis.push('✅ PE 低于 15，估值偏低，安全边际较厚'); score.value += 25; }
    else if (fundamentals.pe < 25) { analysis.push('➖ PE 在 15-25 之间，估值合理'); score.value += 15; }
    else { analysis.push('⚠️ PE 高于 25，估值偏贵'); score.value += 5; }
  }

  // PB 分析
  if (fundamentals.pb) {
    score.max += 25;
    if (fundamentals.pb < 1.5) { analysis.push('✅ PB 低于 1.5，资产便宜'); score.value += 25; }
    else if (fundamentals.pb < 3) { analysis.push('➖ PB 在 1.5-3 之间，资产估值合理'); score.value += 15; }
    else { analysis.push('⚠️ PB 高于 3，资产估值较高'); score.value += 5; }
  }

  // 股息率分析
  if (fundamentals.dividend_yield) {
    score.max += 20;
    if (fundamentals.dividend_yield > 3) { analysis.push('✅ 股息率超3%，现金回报丰厚'); score.value += 20; }
    else if (fundamentals.dividend_yield > 1.5) { analysis.push('➖ 股息率在1.5%-3%，回报一般'); score.value += 12; }
    else { analysis.push('⚠️ 股息率低于1.5%，现金回报较弱'); score.value += 5; }
  }

  // 52周位置分析
  if (price.fifty_two_week_high && price.fifty_two_week_low && price.price) {
    score.max += 30;
    const position = (price.price - price.fifty_two_week_low) / (price.fifty_two_week_high - price.fifty_two_week_low);
    if (position <= 0.2) { analysis.push('💡 接近52周低点，安全边际极厚'); score.value += 30; }
    else if (position <= 0.4) { analysis.push('➖ 处于52周中低区间，价格合理'); score.value += 20; }
    else if (position <= 0.6) { analysis.push('➖ 处于52周中位，价格合理'); score.value += 15; }
    else if (position <= 0.8) { analysis.push('⚠️ 处于52周中高区间，估值偏贵'); score.value += 10; }
    else { analysis.push('⚠️ 接近52周高点，估值较高'); score.value += 5; }
  }

  const rating = score.max > 0 ? Math.round((score.value / score.max) * 100) : 50;
  let verdict = '';
  if (rating >= 80) verdict = '🟢 低估值 - 关注买入机会';
  else if (rating >= 60) verdict = '🟡 合理估值 - 可持续观察';
  else verdict = '🔴 高估值 - 建议等待';

  return { agent: '估值分析师', rating, verdict, points: analysis };
}

function analyzeQuality(price, fundamentals) {
  const analysis = [];
  const score = { value: 0, max: 0 };

  // ROE 分析（巴菲特最重视的指标）
  if (fundamentals.roe) {
    score.max += 30;
    const roePct = fundamentals.roe * 100;
    if (roePct >= 20) { analysis.push('🌟 ROE 超过20%，顶级盈利能力，护城河极深'); score.value += 30; }
    else if (roePct >= 15) { analysis.push('✅ ROE 在15-20%，优秀的盈利能力'); score.value += 25; }
    else if (roePct >= 10) { analysis.push('➖ ROE 在10-15%，盈利能力良好'); score.value += 15; }
    else { analysis.push('⚠️ ROE 低于10%，盈利能力一般'); score.value += 5; }
  }

  // 毛利率分析
  if (fundamentals.gross_margin) {
    score.max += 25;
    const gm = fundamentals.gross_margin * 100;
    if (gm >= 50) { analysis.push('🌟 毛利率超50%，强大的定价权和护城河'); score.value += 25; }
    else if (gm >= 30) { analysis.push('✅ 毛利率在30-50%，良好的竞争力'); score.value += 18; }
    else if (gm >= 15) { analysis.push('➖ 毛利率在15-30%，行业平均水平'); score.value += 10; }
    else { analysis.push('⚠️ 毛利率低于15%，行业竞争激烈'); score.value += 5; }
  }

  // 净利率分析
  if (fundamentals.profit_margin) {
    score.max += 20;
    const pm = fundamentals.profit_margin * 100;
    if (pm >= 20) { analysis.push('✅ 净利率超20%，转化效率极高'); score.value += 20; }
    else if (pm >= 10) { analysis.push('➖ 净利率在10-20%，转化效率良好'); score.value += 12; }
    else { analysis.push('⚠️ 净利率低于10%，成本控制需改善'); score.value += 5; }
  }

  // 营收增长分析
  if (fundamentals.revenue_growth !== undefined && fundamentals.revenue_growth !== null) {
    score.max += 25;
    const rg = fundamentals.revenue_growth * 100;
    if (rg >= 20) { analysis.push('🚀 营收增长超20%，高成长阶段'); score.value += 25; }
    else if (rg >= 10) { analysis.push('✅ 营收增长在10-20%，稳定成长'); score.value += 20; }
    else if (rg >= 0) { analysis.push('➖ 营收增长在0-10%，成长趋缓'); score.value += 10; }
    else { analysis.push('⚠️ 营收负增长，业务面临挑战'); score.value += 0; }
  }

  const rating = score.max > 0 ? Math.round((score.value / score.max) * 100) : 50;
  let verdict = '';
  if (rating >= 80) verdict = '🟢 优质 - 伟大的公司';
  else if (rating >= 60) verdict = '🟡 良好 - 质量过关';
  else verdict = '🔴 一般 - 质量需改善';

  return { agent: '质量分析师', rating, verdict, points: analysis };
}

function analyzeSafety(price, fundamentals) {
  const analysis = [];
  const score = { value: 0, max: 0 };

  // 负债权益比
  if (fundamentals.debt_to_equity !== undefined && fundamentals.debt_to_equity !== null) {
    score.max += 30;
    const de = fundamentals.debt_to_equity;
    if (de < 0.2) { analysis.push('✅ 几乎无负债，财务极其健康'); score.value += 30; }
    else if (de < 0.5) { analysis.push('✅ 负债率低，财务健康'); score.value += 25; }
    else if (de < 1.0) { analysis.push('➖ 负债率适中，财务较稳健'); score.value += 15; }
    else { analysis.push('⚠️ 负债率较高，财务风险需关注'); score.value += 5; }
  }

  // 流动比率
  if (fundamentals.current_ratio) {
    score.max += 25;
    const cr = fundamentals.current_ratio;
    if (cr >= 2) { analysis.push('✅ 流动比率大于2，短期偿债能力强'); score.value += 25; }
    else if (cr >= 1.5) { analysis.push('➖ 流动比率适中，短期偿债能力较好'); score.value += 18; }
    else if (cr >= 1) { analysis.push('⚠️ 流动比率偏低，注意流动性'); score.value += 10; }
    else { analysis.push('🚨 流动比率小于1，存在短期偿债风险'); score.value += 0; }
  }

  // 自由现金流
  if (fundamentals.free_cashflow !== undefined && fundamentals.free_cashflow !== null) {
    score.max += 25;
    if (fundamentals.free_cashflow > 0) { analysis.push('✅ 自由现金流正向，企业造血能力强'); score.value += 25; }
    else { analysis.push('⚠️ 自由现金流为负，营运压力较大'); score.value += 5; }
  }

  // 当日振幅风险
  if (price.high && price.low && price.prev_close) {
    score.max += 20;
    const amplitude = ((price.high - price.low) / price.prev_close) * 100;
    if (amplitude < 3) { analysis.push('✅ 当日振幅较小，市场情绪稳定'); score.value += 20; }
    else if (amplitude < 5) { analysis.push('➖ 当日振幅适中，波动正常'); score.value += 12; }
    else if (amplitude < 8) { analysis.push('⚠️ 当日振幅较大，注意风险'); score.value += 8; }
    else { analysis.push('🚨 当日振幅超过8%，市场情绪极端'); score.value += 2; }
  }

  const rating = score.max > 0 ? Math.round((score.value / score.max) * 100) : 50;
  let verdict = '';
  if (rating >= 80) verdict = '🟢 安全 - 财务极健康';
  else if (rating >= 60) verdict = '🟡 稳健 - 财务较安全';
  else verdict = '🔴 警戒 - 财务风险较高';

  return { agent: '财务安全官', rating, verdict, points: analysis };
}

function analyzeDecision(valuation, quality, safety) {
  const avgRating = Math.round((valuation.rating + quality.rating + safety.rating) / 3);
  
  let verdict = '';
  let position = '';
  
  if (avgRating >= 75) {
    verdict = '🟢 强烈看好 - 估值低 + 质量优 + 财务健康';
    position = '建议仓位: 60-80% 仓位';
  } else if (avgRating >= 60) {
    verdict = '🟡 适度看好 - 合理估值，质量过关';
    position = '建议仓位: 40-60% 仓位';
  } else if (avgRating >= 45) {
    verdict = '🟠 中性 - 某些方面存在隱忧';
    position = '建议仓位: 20-40% 仓位';
  } else {
    verdict = '🔴 警惕 - 估值高或质量/财务有隐患';
    position = '建议仓位: 0-20% 仓位，或等待';
  }

  return { agent: '投资决策官', rating: avgRating, verdict, position };
}

// 分析单只股票
async function analyzeStock(code) {
  const data = await getStockData(code);
  if (!data.success) {
    return { success: false, error: data.error, code };
  }

  const valuation = analyzeValuation(data.price, data.fundamentals);
  const quality = analyzeQuality(data.price, data.fundamentals);
  const safety = analyzeSafety(data.price, data.fundamentals);
  const decision = analyzeDecision(valuation, quality, safety);

  return {
    success: true,
    code: data.price.code,
    name: data.price.name,
    price: data.price,
    fundamentals: data.fundamentals,
    agents: [valuation, quality, safety, decision]
  };
}

// ====== API 路由 ======

// 分析单只股票
app.get('/api/analyze', async (req, res) => {
  const { code } = req.query;
  if (!code) return res.status(400).json({ success: false, error: '缺少股票代码' });
  
  try {
    const result = await analyzeStock(code);
    res.json(result);
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// 分析全部持仓
app.get('/api/analyze-all', async (req, res) => {
  const config = readConfig();
  const enabledStocks = config.stocks.filter(s => s.enabled);
  
  if (enabledStocks.length === 0) {
    return res.json({ success: false, error: '没有启用的股票' });
  }

  const results = [];
  const errors = [];
  
  for (const stock of enabledStocks) {
    try {
      const result = await analyzeStock(stock.code);
      if (result.success) results.push(result);
      else errors.push({ code: stock.code, error: result.error });
    } catch (e) {
      errors.push({ code: stock.code, error: e.message });
    }
  }

  res.json({ success: true, count: results.length, stocks: results, errors });
});

// 生成飞书卡片
app.get('/api/feishu-card', async (req, res) => {
  const config = readConfig();
  const enabledStocks = config.stocks.filter(s => s.enabled);
  
  if (enabledStocks.length === 0) {
    return res.json({ success: false, error: '没有启用的股票' });
  }

  const results = [];
  for (const stock of enabledStocks) {
    try {
      const result = await analyzeStock(stock.code);
      if (result.success) results.push(result);
    } catch (e) {
      console.error(`分析 ${stock.code} 失败:`, e.message);
    }
  }

  if (results.length === 0) {
    return res.json({ success: false, error: '所有股票分析失败' });
  }

  // 构建飞书卡片
  const elements = [];
  
  results.forEach(r => {
    const price = r.price;
    const decision = r.agents[3];
    const sign = price.change >= 0 ? '📈' : '📉';
    
    elements.push({
      tag: 'div',
      text: {
        tag: 'lark_md',
        content: `**${sign} ${r.name} (${r.code})**\n当前价: ${price.price?.toFixed(2)} | 涨跌: ${price.change >= 0 ? '+' : ''}${price.change?.toFixed(2)} (${price.change_pct?.toFixed(2)}%)\n**综合评级**: ${decision.verdict}`
      }
    });
    
    elements.push({
      tag: 'div',
      text: {
        tag: 'lark_md',
        content: r.agents.map(a => `**${a.agent}**: ${a.rating}分 - ${a.verdict}${a.points ? '\\n• ' + a.points.join('\\n• ') : ''}`).join('\\n\\n')
      }
    });
    
    elements.push({ tag: 'hr' });
  });

  // 移除最后一个分隔线
  elements.pop();

  const card = {
    msg_type: 'interactive',
    card: {
      header: {
        title: { tag: 'plain_text', content: '📊 投资助手 - 每日持仓监控分析' },
        template: 'blue'
      },
      elements: [
        ...elements,
        { tag: 'note', elements: [{ tag: 'plain_text', content: `⏰ 分析时间: ${new Date().toLocaleString('zh-CN', { hour12: false })}` }] }
      ]
    }
  };

  res.json({ success: true, card });
});

// 推送到飞书
app.post('/api/push', async (req, res) => {
  const config = readConfig();
  if (!config.feishuWebhook) {
    return res.status(400).json({ success: false, error: '飞书 Webhook 未配置' });
  }

  try {
    const cardRes = await axios.get('http://localhost:3001/api/feishu-card');
    if (!cardRes.data.success) {
      return res.status(500).json(cardRes.data);
    }
    
    await axios.post(config.feishuWebhook, cardRes.data.card, { timeout: 10000 });
    res.json({ success: true, message: '已推送到飞书' });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// 启动服务
const PORT = 3001;
app.listen(PORT, () => {
  console.log('=================================');
  console.log(`🧠 投资分析服务已启动`);
  console.log(`🔗 API 地址: http://localhost:${PORT}`);
  console.log('=================================');
  console.log(`接口列表:`);
  console.log(`  GET  /api/analyze?code=600519.SS  - 分析单只股票`);
  console.log(`  GET  /api/analyze-all             - 分析所有持仓`);
  console.log(`  GET  /api/feishu-card             - 生成飞书卡片`);
  console.log(`  POST /api/push                    - 推送到飞书`);
  console.log('=================================');
});

// 处理异常，防止进程崩溃
process.on('uncaughtException', (err) => {
  console.error('未捕获的异常:', err);
});
