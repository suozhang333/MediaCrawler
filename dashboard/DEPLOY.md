# Streamlit Cloud 部署指南

## 1. 推送代码到 GitHub

```bash
# 确保 dashboard 目录已提交到 git
git add dashboard/
git commit -m "Add Streamlit dashboard"
git push origin main
```

## 2. 创建 Streamlit Cloud 应用

1. 访问 https://streamlit.io/cloud
2. 点击 **"New app"**
3. 选择你的 GitHub 仓库
4. 配置：
   - **Main file path**: `dashboard/app.py`
   - **Branch**: `main`

## 3. 配置 Secrets

在 Streamlit Cloud 管理界面：

1. 点击 **"⋮"** → **"Settings"**
2. 选择 **"Secrets"** 标签
3. 添加以下内容：

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

## 4. 启动应用

点击 **"Deploy"**，等待部署完成。

访问地址：`https://your-app-name.streamlit.app`

## 5. 验证

打开应用后应看到：
- ✅ 数据正常加载
- ✅ 图表正常显示
- ✅ 无配置错误

---

## 常见问题

### Q: 显示 "缺少 Supabase 配置"
A: 检查 Secrets 是否正确配置，变量名是否匹配

### Q: 数据加载失败
A: 检查 Supabase URL 和 Key 是否正确，表名是否为 `xhs_notes`

### Q: 图表不显示
A: 检查是否有数据，情感分析是否已运行

---

## 本地测试

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

访问 http://localhost:8501
