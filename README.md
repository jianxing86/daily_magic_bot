# 每日报告机器人 (Daily Report Bot)

每日自动生成包含天气预报和新闻摘要的邮件报告，使用Gemini AI进行内容处理和生成。

## 功能特点

- 📊 **天气播报**：
  - 实时解析北京和济南的天气数据（weather.com.cn）
  - **新功能**：天气状况与温度同行显示，信息密度更高
  - 提供日出日落时间、风力等级及天气预警信息
- 🔬 **科学新闻（5 个顶级新闻源）**：
  - **Nature 最新新闻** + **Nature 研究文章**
  - **ScienceDaily 主页** + **科学板块** + **大脑认知板块**
  - 覆盖范围：每次获取约 **136 条**最新新闻（最近 2 天内）
  - AI智能筛选：白矮星、脉冲星、恒星物理、望远镜、心理学、认知神经科学、元认知等领域
  - 提供中英双语标题和AI生成的中文摘要
  - **新设计**：新闻链接采用简洁的 `🔗` 按钮 + 日期标注（yyyy-mm-dd）
- 🤖 **AI处理（Gemini 2.5 Flash）**：
  - **极速架构**：采用 Unified Request 模式，每次运行仅需 **2次** AI调用
  - **智能融合**：哈利波特角色开场白智能融合当日天气与科学大新闻
  - **批量处理**：一次性完成多条新闻的翻译与总结
  - 筛选结果：10-25 条精选新闻
- ✉️ **精美邮件**：
  - 响应式HTML设计，完美适配移动端（优化页边距与字体）
  - 清新素雅的配色方案，重点信息一目了然

## 项目结构

```
1_DailyReportBot/
├── config.py              # 配置管理
├── weather_parser.py      # 天气数据解析
├── news_fetcher.py        # 新闻获取
├── gemini_processor.py    # Gemini AI处理
├── email_sender.py        # 邮件发送
├── main.py                # 主程序
├── requirements.txt       # Python依赖
├── .env.template          # 环境变量模板
├── .gitignore            # Git忽略文件
└── README.md             # 本文件
```

## 安装步骤

### 1. 克隆或下载项目

```bash
cd /Users/jianxing/Documents/Antigravity_Projects/1_DailyReportBot
```

### 2. 创建Conda环境（推荐）

```bash
conda create -n daily_report python=3.10
conda activate daily_report
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制模板文件并填写配置：

```bash
cp .env.template .env
```

编辑`.env`文件，填写以下信息：

```bash
# Gemini API配置
GEMINI_API_KEY=your_actual_api_key_here

# 邮箱配置（以Gmail为例）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
# 如果使用国内邮箱（如QQ、163、高校邮箱），通常使用SSL端口 465
# SMTP_PORT=465
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password

# 接收邮箱（用逗号分隔）
RECEIVER_EMAILS=email1@example.com,email2@example.com
```

**重要提示**：
- **Gemini API密钥**：从[Google AI Studio](https://aistudio.google.com/)获取
- **Gmail应用密码**：需要在Google账户中生成[应用专用密码](https://myaccount.google.com/apppasswords)

## 使用方法

### 邮件发送测试（新功能）

快速测试SMTP配置是否正确，发送一封简单的测试邮件（不消耗AI Token）：

```bash
python main.py --email-test
```

### 测试运行（不发送邮件）

生成完整报告的HTML预览，保存在`/tmp`目录，不发送邮件：

```bash
python main.py --test --no-send
```

### 测试发送完整报告

生成并发送包含天气和新闻的完整报告：

```bash
python main.py --test
```

### 正式运行

```bash
python main.py
```

## GitHub Actions 部署

本项目设计为在GitHub Actions中运行。创建`.github/workflows/daily_report.yml`：

```yaml
name: Daily Report

on:
  schedule:
    # 每天北京时间早上8点运行 (UTC 0:00)
    - cron: '0 0 * * *'
  workflow_dispatch:  # 允许手动触发

jobs:
  send-report:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run daily report
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
          SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
          RECEIVER_EMAILS: ${{ secrets.RECEIVER_EMAILS }}
        run: |
          python main.py
```

**在GitHub仓库中设置Secrets**：
- Settings → Secrets and variables → Actions → New repository secret
- 添加所有环境变量（`GEMINI_API_KEY`、`SENDER_EMAIL`等）

需要添加的 Secrets 列表（建议直接复制 Name）：

| Name (变量名) | Secret (值/占位符) |
| :--- | :--- |
| `GEMINI_API_KEY` | `your_api_key_here` |
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SENDER_EMAIL` | `your_email@gmail.com` |
| `SENDER_PASSWORD` | `your_app_password` |
| `RECEIVER_EMAILS` | `email1@example.com,email2@example.com` |

## 天气数据来源

程序会自动从以下URL实时获取最新天气数据：
- 北京：https://www.weather.com.cn/weather1d/101010100.shtml
- 济南：https://www.weather.com.cn/weather1d/101120101.shtml

**注意**：项目文件夹中的HTML文件仅用于本地调试，程序运行时会直接从URL获取最新数据。

## 故障排查

### 1. 邮件发送失败

- 检查SMTP配置是否正确
- Gmail需要开启"允许不够安全的应用访问"或使用应用专用密码
- 检查网络连接

### 2. Gemini API调用失败

- 确认API密钥正确
- 检查API配额是否用尽
- 确认网络能访问Google服务

### 3. 天气数据解析失败
- 确认HTML文件存在且路径正确
- 检查HTML文件是否为最新版本
- 查看日志确认具体错误

## 更新日志

### v2.0 (2025-12-04)
- 🚀 **架构重构**：实现 Unified AI Request，将多次 AI 调用合并为 2 次，大幅提升速度并降低成本。
- � **新闻源升级**：
  - 从单一 ScienceDaily 扩展至 **5 个顶级新闻源**（Nature News、Nature Research、ScienceDaily × 3）
  - 新闻获取量：136 条（最近 2 天内）
  - 智能日期过滤，确保新闻时效性
  - AI 筛选优化：支持白矮星、脉冲星、恒星物理、望远镜、心理学、认知神经科学、元认知等多领域
- �📱 **UI 升级**：
  - 全面优化移动端显示效果，减少页边距，提升阅读体验
  - 天气卡片布局调整（天气状况与温度同行显示），信息密度更高
  - 新闻链接改为简洁的图标按钮 `🔗`
  - 新增日期显示（小字灰色，格式：yyyy-mm-dd）
- 🔍 **能力增强**：
  - 新闻筛选结果：10-25 条精选新闻（可根据重要性动态调整）
  - 哈利波特问候语升级，能够感知并评论当天的科学大新闻
- 🛠 **技术栈**：升级至 `gemini-2.5-flash` 模型，响应更快
