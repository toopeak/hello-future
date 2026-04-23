const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const CONFIG_PATH = path.join(__dirname, 'config.json');

// 读取配置
function readConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    return {
      stocks: [],
      schedule: { enabled: true, time: '09:00', days: [1, 2, 3, 4, 5] },
      feishuWebhook: ''
    };
  }
  return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
}

// 保存配置
function saveConfig(config) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
}

// 查询单只股票
async function queryStock(code) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(code)}?interval=1d&range=5d`;
  const res = await axios.get(url, {
    headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' },
    timeout: 15000
  });
  const chart = res.data.chart?.result?.[0];
  if (!chart) return null;

  const meta = chart.meta;
  const quote = chart.indicators?.quote?.[0];
  const len = chart.timestamp?.length || 0;

  return {
    code,
    name: meta.shortName || meta.longName || code,
    price: quote?.close?.[len - 1] ?? meta.regularMarketPrice,
    prevClose: meta.chartPreviousClose ?? meta.previousClose ?? (quote?.close?.[len - 1] ?? meta.regularMarketPrice),
    open: quote?.open?.[len - 1] ?? meta.regularMarketPrice,
    high: quote?.high?.[len - 1] ?? meta.regularMarketDayHigh,
    low: quote?.low?.[len - 1] ?? meta.regularMarketDayLow,
    volume: quote?.volume?.[len - 1] ?? meta.regularMarketVolume,
    fiftyTwoWeekHigh: meta.fiftyTwoWeekHigh,
    fiftyTwoWeekLow: meta.fiftyTwoWeekLow
  };
}

// 多 Agent 分析
function analyzeStock(stock) {
  const change = stock.price - stock.prevClose;
  const changePct = stock.prevClose ? (change / stock.prevClose * 100) : 0;
  const dayRange = stock.high - stock.low;

  // Agent 1: 价值投资者
  const valueInvestor = [];
  if (stock.fiftyTwoWeekHigh && stock.fiftyTwoWeekLow) {
    const position = (stock.price - stock.fiftyTwoWeekLow) / (stock.fiftyTwoWeekHigh - stock.fiftyTwoWeekLow);
    if (position <= 0.2) valueInvestor.push('💡 接近52周低点，安全边际较厚，适合长线布局');
    else if (position >= 0.8) valueInvestor.push('⚠️ 接近52周高点，估值偏贵，建议等待回调');
    else valueInvestor.push('➖ 处于合理区间，持续观察');
  }
  if (changePct <= -5) valueInvestor.push('🎩 大跌市场恐慌，但也是长期买家的零售价');
  if (stock.volume > 8000000) valueInvestor.push('🌬️ 成交量放大但价格波动不大，或有机构在偷偷吸筹');

  // Agent 2: 技术分析师
  const technical = [];
  if (dayRange > 0) {
    const distToHigh = stock.high - stock.price;
    const distToLow = stock.price - stock.low;
    if (distToHigh / dayRange < 0.05) technical.push('🎯 接近最高点收盘，多头占优，短线强势');
    else if (distToLow / dayRange < 0.05) technical.push('🛡️ 接近最低点收盘，空头占优，支撑位可能失效');
    else technical.push('➖ 收盘中庸，方向不明，等待方向选择');
  }
  if (changePct >= 3 && stock.volume > 5000000) technical.push('🚀 放量突破，趋势可能反转');
  if (changePct <= -3 && stock.volume > 5000000) technical.push('💥 放量跌破，趋势走坏');

  // Agent 3: 风控官
  const riskOfficer = [];
  const amplitude = dayRange > 0 ? (dayRange / stock.prevClose * 100) : 0;
  if (amplitude > 5) riskOfficer.push('🚨 当日振幅超5%，波动率较高，建议控制仓位');
  else riskOfficer.push('✅ 振幅在合理范围，风险可控');
  const stopLoss = stock.prevClose * 0.95;
  riskOfficer.push(`⛔ 建议止损位置 ${stopLoss.toFixed(2)} 元`);
  if (changePct <= -3) riskOfficer.push('📊 单日大跌，不建议追涨杀跌');

  return { change, changePct, valueInvestor, technical, riskOfficer };
}

// 推送到飞书
async function pushToFeishu(stocksData, config) {
  if (!config.feishuWebhook) {
    console.error('飞书 Webhook 未配置');
    return;
  }

  const stockElements = stocksData.map(s => {
    const sign = s.analysis.change >= 0 ? '📈' : '📉';
    return {
      tag: 'div',
      text: {
        tag: 'lark_md',
        content: `**${sign} ${s.name} (${s.code})**\n当前价格: ${s.price.toFixed(2)} 元 | 涨跌额: ${s.analysis.change >= 0 ? '+' : ''}${s.analysis.change.toFixed(2)} 元 | 涨跌幅: ${s.analysis.change >= 0 ? '+' : ''}${s.analysis.changePct.toFixed(2)}%\n成交量: ${(s.volume / 10000).toFixed(2)} 万股 | 昨收: ${s.prevClose.toFixed(2)} 元`
      }
    };
  });

  const analysisElements = stocksData.map(s => {
    return {
      tag: 'div',
      text: {
        tag: 'lark_md',
        content: `**${s.name}** 分析结论:\n💰 价值投资者: ${s.analysis.valueInvestor.join(' | ')}\n📉 技术分析师: ${s.analysis.technical.join(' | ')}\n🛡️ 风控官: ${s.analysis.riskOfficer.join(' | ')}`
      }
    };
  });

  const card = {
    msg_type: 'interactive',
    card: {
      header: {
        title: { tag: 'plain_text', content: '📊 每日持仓监控汇总' },
        template: 'blue'
      },
      elements: [
        ...stockElements,
        { tag: 'hr' },
        ...analysisElements,
        { tag: 'note', elements: [{ tag: 'plain_text', content: `⏰ 数据更新时间: ${new Date().toLocaleString('zh-CN', { hour12: false })}` }] }
      ]
    }
  };

  await axios.post(config.feishuWebhook, card, { timeout: 10000 });
}

// 执行监控任务
async function runMonitoring() {
  console.log(`[${new Date().toLocaleString('zh-CN')}] 开始执行监控任务...`);
  const config = readConfig();
  const enabledStocks = config.stocks.filter(s => s.enabled);

  if (enabledStocks.length === 0) {
    console.log('没有启用的股票，跳过本次执行');
    return { success: true, message: '没有启用的股票', count: 0 };
  }

  const results = [];
  for (const stock of enabledStocks) {
    try {
      const data = await queryStock(stock.code);
      if (data) {
        data.analysis = analyzeStock(data);
        results.push(data);
      }
    } catch (e) {
      console.error(`查询 ${stock.code} 失败:`, e.message);
    }
  }

  if (results.length > 0) {
    try {
      await pushToFeishu(results, config);
      console.log(`✅ 已推送 ${results.length} 只股票到飞书`);
      return { success: true, count: results.length };
    } catch (e) {
      console.error('飞书推送失败:', e.message);
      return { success: false, error: e.message };
    }
  }

  return { success: true, count: 0 };
}

// 定时任务实例
let cronJob = null;

function setupCron() {
  // 停止旧任务
  if (cronJob) {
    cronJob.stop();
    cronJob = null;
  }

  const config = readConfig();
  if (!config.schedule.enabled) {
    console.log('定时任务已禁用');
    return;
  }

  const [hour, minute] = config.schedule.time.split(':');
  const days = config.schedule.days.join(',');
  const cronExpr = `${minute} ${hour} * * ${days}`;

  console.log(`定时任务已设置: ${cronExpr} (北京时间)`);

  cronJob = cron.schedule(cronExpr, async () => {
    await runMonitoring();
  }, {
    timezone: 'Asia/Shanghai',
    scheduled: true
  });
}

// API 路由
app.get('/api/config', (req, res) => {
  res.json(readConfig());
});

app.post('/api/config', (req, res) => {
  try {
    saveConfig(req.body);
    setupCron();
    res.json({ success: true });
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

app.post('/api/trigger', async (req, res) => {
  res.json({ success: true, message: '任务已触发，请查看飞书' });
  await runMonitoring();
});

app.get('/api/stock/validate', async (req, res) => {
  const { code } = req.query;
  if (!code) return res.status(400).json({ success: false, error: '缺少股票代码' });

  try {
    const data = await queryStock(code);
    if (data) {
      res.json({ success: true, name: data.name, code: data.code });
    } else {
      res.json({ success: false, error: '未找到该股票' });
    }
  } catch (e) {
    res.status(500).json({ success: false, error: e.message });
  }
});

// 启动服务
const PORT = 3000;
app.listen(PORT, () => {
  console.log('=================================');
  console.log(`🚀 投资助手已启动`);
  console.log(`🔗 配置界面: http://localhost:${PORT}`);
  console.log('=================================');
  setupCron();
});
