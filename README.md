# WeChat Article Downloader Chrome 插件

⚠️ **注意**：
- Chrome 插件目前仅在 macOS 环境下测试通过

## 项目介绍

本项目基于 [fengxxc/wechatmp2markdown](https://github.com/fengxxc/wechatmp2markdown) 开发，在日常阅览的场景下简化微信公众号文章的下载过程，后续计划叠加RAG或其他高层组织方式，实现更便捷的收藏功能。通过添加本地 Python 服务和 Chrome 插件，实现了一键下载功能。

新的用户体验：
-> 微信公众号设置在默认浏览器（Chrome）打开
-> 发现公众号文章值得收藏
-> 点击浏览器拓展一键下载当前正在看（聚焦页面）的文章

原项目提供了**通过命令行**将微信公众号文章转换为 Markdown 格式的功能，本项目在此基础上：
1. 用Python封装了命令行调用过程
2. 提供了本地 HTTP 服务
3. 开发了从本地加载的 Chrome 插件实现一键下载

### 功能特点
- 支持一键下载当前浏览的微信公众号文章
- 自动转换为 Markdown 格式
- 保留原文图片
- 简单易用的浏览器插件界面

## 使用方法

### 1. 需要 Python 环境
确保你的系统已安装 Python 3.7 或更高版本。
（确保你使用的是Chrome浏览器）

### 2. 不想安装Chrome插件，需要运行py文件
可以用VS Code等编辑器打开`run_exe_in_cli.py`，右上角点击运行（F5）

### 3. 安装Chrome插件，在浏览器页面即可点击下载
即通过插件自动唤起`run_exe_in_cli.py`

### 3.1 安装依赖
```bash
pip install flask flask-cors
```

### 3.2 启动本地服务 （需要先cd到项目文件夹）
```bash
python server.py
```
或
```bash
python3 server.py
```

### 3.3 安装 Chrome 插件
1. 打开 Chrome 浏览器，访问 `chrome://extensions/`
2. 开启右上角的"开发者模式"
3. 点击左上角的"加载已解压的扩展程序"
4. 选择项目目录下的 `chrome_extension` 文件夹
5. 完成安装，插件图标将出现在浏览器工具栏

### 3.4 插件使用方法
1. 确保本地服务 (`server.py`) 正在运行
2. 打开任意微信公众号文章
3. 点击 Chrome 工具栏上的插件图标
4. 点击"📥 下载当前页面"按钮
5. 文章将被下载并转换为 Markdown 格式，保存在 `downloads` 目录中

## Project Overview

This project extends [fengxxc/wechatmp2markdown](https://github.com/fengxxc/wechatmp2markdown) by adding a local Python service and a Chrome extension to enable one-click downloads of WeChat public account articles. The original project provides functionality to convert WeChat articles to Markdown format, while this extension simplifies the process by:
1. Encapsulating command-line operations
2. Providing a local HTTP service
3. Implementing a Chrome extension for one-click downloads

### Features
- One-click download of WeChat articles
- Automatic conversion to Markdown format
- Image preservation
- User-friendly browser extension interface
