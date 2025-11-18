# GitHub SSH 密钥配置指南

## 当前状态
- ✅ SSH 密钥已生成：`~/.ssh/id_rsa.pub`
- ✅ SSH 密钥已添加到 ssh-agent
- ❌ SSH 公钥尚未添加到 GitHub 账户

## 解决步骤

### 方法 1：添加 SSH 公钥到 GitHub（推荐）

1. **复制你的 SSH 公钥**
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```
   复制输出的完整内容（以 `ssh-rsa` 开头）

2. **添加到 GitHub**
   - 访问：https://github.com/settings/keys
   - 点击 "New SSH key"
   - Title: 填写一个描述（如 "MacBook Pro"）
   - Key: 粘贴刚才复制的公钥内容
   - 点击 "Add SSH key"

3. **测试连接**
   ```bash
   ssh -T git@github.com
   ```
   应该看到：`Hi Y5-asas! You've successfully authenticated...`

4. **推送代码**
   ```bash
   cd /Users/y5/Downloads/alpha_arena/quant_unstructure
   git push -u origin streamlit-app
   ```

### 方法 2：使用 GitHub CLI（如果已安装）

```bash
gh auth login
git push -u origin streamlit-app
```

### 方法 3：使用 HTTPS + Personal Access Token

1. 生成 Personal Access Token：
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 选择权限：`repo`
   - 复制生成的 token

2. 使用 token 推送：
   ```bash
   git remote set-url origin https://YOUR_TOKEN@github.com/Y5-asas/quant_unstructure.git
   git push -u origin streamlit-app
   ```

## 当前分支状态

- ✅ 分支已创建：`streamlit-app`
- ✅ 代码已提交：26 个文件，3308 行代码
- ⏳ 等待推送到 GitHub

## 提交内容

- `streamlit_app.py` - Streamlit 主应用
- `main_nlp.py` - NLP 回测模式
- `backend/` - 后端 API 结构
- `utils/` - 工具函数
- `llm/` - LLM API 客户端
- `docs/` - 文档
- `requirements.txt` - 依赖列表
- `scripts/` - 脚本文件

所有代码已安全保存在本地，配置好 SSH 后即可推送。

