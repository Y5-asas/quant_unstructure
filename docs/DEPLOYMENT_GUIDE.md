# Streamlit 应用部署指南

## 方法一：使用 ngrok（最简单，适合临时测试）

### 步骤：

1. **安装 ngrok**
   ```bash
   # macOS
   brew install ngrok
   
   # 或从官网下载：https://ngrok.com/download
   ```

2. **启动 Streamlit 应用**
   ```bash
   cd /Users/y5/Downloads/alpha_arena/quant_unstructure
   conda activate alpha_arena_env
   streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
   ```

3. **在另一个终端启动 ngrok**
   ```bash
   ngrok http 8501
   ```

4. **获取公网 URL**
   - ngrok 会显示一个公网 URL，例如：`https://xxxx-xx-xx-xx-xx.ngrok-free.app`
   - 将这个 URL 分享给朋友即可访问

**优点**：快速、简单，适合临时测试  
**缺点**：免费版有连接数限制，URL 每次启动会变化

---

## 方法二：修改 Streamlit 配置允许局域网访问

### 步骤：

1. **创建/修改 Streamlit 配置文件**
   ```bash
   mkdir -p ~/.streamlit
   ```

2. **编辑配置文件** `~/.streamlit/config.toml`：
   ```toml
   [server]
   address = "0.0.0.0"  # 监听所有网络接口
   port = 8501
   enableCORS = false
   enableXsrfProtection = false
   
   [browser]
   gatherUsageStats = false
   ```

3. **启动应用**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **获取你的局域网 IP**
   ```bash
   # macOS
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

5. **分享访问地址**
   - 格式：`http://你的IP地址:8501`
   - 例如：`http://192.168.1.100:8501`

**优点**：简单，不需要额外工具  
**缺点**：只能在同一个局域网内访问（比如同一个 WiFi）

---

## 方法三：部署到 Streamlit Cloud（免费，永久）

### 步骤：

1. **将代码推送到 GitHub**
   ```bash
   cd /Users/y5/Downloads/alpha_arena/quant_unstructure
   git add .
   git commit -m "Add Streamlit frontend"
   git push origin main  # 或你的分支名
   ```

2. **创建 requirements.txt**
   确保包含所有依赖：
   ```txt
   streamlit>=1.29.0
   plotly>=5.0.0
   pandas>=2.0.0
   numpy>=1.24.0
   openai>=1.0.0
   zhipuai>=2.0.0
   python-dotenv>=1.0.0
   tqdm>=4.65.0
   yfinance>=0.2.0
   ```

3. **访问 Streamlit Cloud**
   - 打开 https://share.streamlit.io/
   - 使用 GitHub 账号登录
   - 点击 "New app"
   - 选择你的仓库和分支
   - Main file path: `streamlit_app.py`
   - 点击 "Deploy"

4. **配置环境变量**
   - 在 Streamlit Cloud 的设置中添加 `.env` 文件中的 API keys
   - 或者使用 Secrets 功能添加环境变量

5. **获取公网 URL**
   - 部署完成后会获得一个 URL，例如：`https://your-app-name.streamlit.app`
   - 这个 URL 是永久的，可以分享给任何人

**优点**：免费、永久、公网可访问  
**缺点**：需要 GitHub 账号，需要配置环境变量

---

## 方法四：部署到云服务器（适合生产环境）

### 步骤：

1. **准备云服务器**（阿里云、腾讯云、AWS 等）
   - 安装 Python 3.11
   - 安装 conda 或 venv

2. **上传代码到服务器**
   ```bash
   scp -r quant_unstructure user@your-server-ip:/path/to/
   ```

3. **在服务器上安装依赖并运行**
   ```bash
   conda create -n alpha_arena_env python=3.11
   conda activate alpha_arena_env
   pip install -r requirements.txt
   streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
   ```

4. **配置防火墙**
   - 开放 8501 端口
   - 或使用 Nginx 反向代理 + HTTPS

**优点**：完全控制，适合生产环境  
**缺点**：需要服务器，需要配置和维护

---

## 推荐方案

- **临时测试**：使用方法一（ngrok）
- **局域网分享**：使用方法二（修改配置）
- **公网分享**：使用方法三（Streamlit Cloud）

