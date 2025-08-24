# WeChat Article Downloader Chrome/Edge 插件

## 项目介绍

本项目基于 [fengxxc/wechatmp2markdown](https://github.com/fengxxc/wechatmp2markdown) 开发，在日常阅览的场景下简化微信公众号文章的下载过程，后续计划叠加RAG或其他高层组织方式，实现更便捷的收藏功能。通过添加本地 Python 服务和浏览器插件，实现了一键下载功能。

新的用户体验：  
➜ 微信公众号设置在默认浏览器（Chrome或Edge）打开  
➜ 发现公众号文章值得收藏  
➜ 点击浏览器插件一键下载当前正在看（聚焦页面）的文章  

原项目提供了**通过命令行**将微信公众号文章转换为 Markdown 格式的功能，本项目在此基础上：
1. 用Python封装了命令行调用过程
2. 提供了本地 HTTP 服务
3. 开发了从本地加载的浏览器插件实现一键下载
4. 支持Windows和macOS系统
5. 支持Chrome和Edge浏览器
6. 提供一键式启动和配置工具

### 功能特点
- 支持一键下载当前浏览的微信公众号文章
- 自动转换为 Markdown 格式
- 保留原文图片
- 简单易用的浏览器插件界面
- 跨平台支持（Windows/macOS，自动检测32/64位）
- 多浏览器支持（自动适配Chrome/Edge）
- 一键式启动配置
- 增强型浏览器信息检测

## 使用方法

### 一键式安装配置（推荐）

1. 确保你的系统已安装 Python 3.7 或更高版本。
2. 运行一键式配置工具：

```bash
python setup.py
```

3. 按照提示完成以下步骤：
   - 安装依赖
   - 启动服务器
   - 安装浏览器插件
   - 配置开机自启动（可选）

### 命令行选项

查看可用选项：

```bash
python setup.py -h
```

仅启动服务器：

```bash
python setup.py --server-only
```

仅安装依赖：

```bash
python setup.py --install-deps
```

仅配置自启动：

```bash
python setup.py --setup-autostart
```

### 手动安装

#### 1. 需要 Python 环境
确保你的系统已安装 Python 3.7 或更高版本。
（确保你使用的是Chrome或Edge浏览器）

#### 2. 手动运行py文件
可以用VS Code等编辑器打开`run_exe_in_cli.py`，右上角点击运行（F5）
或通过命令行执行：

```bash
python run_exe_in_cli.py --url "https://mp.weixin.qq.com/s/xxxxx"
```

#### 3. 手动安装浏览器插件

##### 3.1 安装依赖
```bash
pip install flask flask-cors
```

##### 3.2 启动本地服务 （需要先cd到项目文件夹）
```bash
python server.py
```

##### 3.3 安装 Chrome/Edge 插件
1. 打开 Chrome/Edge 浏览器，访问 `chrome://extensions/` 或 `edge://extensions/`
2. 开启右上角的"开发者模式"
3. 点击左上角的"加载已解压的扩展程序"
4. 选择项目目录下的 `chrome_extension` 文件夹
5. 完成安装，插件图标将出现在浏览器工具栏

##### 3.4 插件使用方法
1. 确保本地服务 (`server.py`) 正在运行
2. 打开任意微信公众号文章
3. 点击浏览器工具栏上的插件图标
4. 点击"📥 下载当前页面"按钮
5. 文章将被下载并转换为 Markdown 格式，保存在 `downloads` 目录中

## Project Overview

This project extends [fengxxc/wechatmp2markdown](https://github.com/fengxxc/wechatmp2markdown) by adding a local Python service and a browser extension to enable one-click downloads of WeChat public account articles. The original project provides functionality to convert WeChat articles to Markdown format, while this extension simplifies the process by:
1. Encapsulating command-line operations
2. Providing a local HTTP service
3. Implementing a browser extension for one-click downloads
4. Supporting both Windows and macOS platforms
5. Supporting Chrome and Edge browsers
6. Providing one-click setup and configuration

### Features
- One-click download of WeChat articles
- Automatic conversion to Markdown format
- Image preservation
- User-friendly browser extension interface
- Cross-platform support (Windows/macOS, auto-detect 32/64-bit)
- Multi-browser support (auto-adapting to Chrome/Edge)
- One-click setup and configuration
- Enhanced browser detection
