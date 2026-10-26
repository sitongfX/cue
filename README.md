# Cue · 实时回答提示

一个纯网页应用：听对方说话，实时给出可以直接说出口的回答，并引用你自己的资料。
所有内容都在浏览器里运行，没有服务器；API Key 只保存在页面内存里，资料和记录保存在你自己的浏览器里。

## 部署到 GitHub Pages
1. 新建一个仓库，把这个文件夹里的所有文件（`index.html`、`manifest.webmanifest`、`sw.js`、`icon.svg`、`.nojekyll`）放到仓库根目录。
2. 仓库 Settings → Pages → Source 选 `Deploy from a branch`，分支选 `main`、目录选 `/ (root)`，保存。
3. 一两分钟后打开 `https://<你的用户名>.github.io/<仓库名>/`。

## 使用
- 设置 → 模型：粘贴 Gemini API Key（https://aistudio.google.com/apikey）。
- 电脑上的 Chrome 可以同时收你的麦克风和会议里对方的声音；手机只能用麦克风。
- 地址栏或页面右上角可以「安装」，之后像普通 App 一样从桌面 / 主屏幕打开。
