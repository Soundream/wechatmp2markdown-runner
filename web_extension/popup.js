// 防止重复点击的标志
let isDownloading = false;
// 自动检测当前浏览器环境
const browserAPI = typeof chrome !== 'undefined' ? chrome : browser;

// 默认设置
const DEFAULT_SETTINGS = {
    serverTimeout: 15 // 分钟
};

// 当前设置
let currentSettings = {...DEFAULT_SETTINGS};

// 保存设置到存储
function saveSettings() {
    browserAPI.storage.sync.set({ settings: currentSettings });
}

// 加载设置
async function loadSettings() {
    return new Promise((resolve) => {
        browserAPI.storage.sync.get('settings', (data) => {
            if (data.settings) {
                currentSettings = {...DEFAULT_SETTINGS, ...data.settings};
            }
            resolve(currentSettings);
        });
    });
}

// 显示浏览器和版本信息，设置页面初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 检测浏览器类型
    const userAgent = navigator.userAgent;
    const browserInfo = document.getElementById('browser-info');
    if (userAgent.includes('Edg')) {
        browserInfo.textContent = '当前运行于: Microsoft Edge';
    } else if (userAgent.includes('Chrome')) {
        browserInfo.textContent = '当前运行于: Google Chrome';
    } else {
        browserInfo.textContent = '当前运行于: 其他浏览器';
    }
    
    // 加载设置
    await loadSettings();
    
    // 初始化设置界面
    document.getElementById('serverTimeout').value = currentSettings.serverTimeout;
    
    // 设置切换
    document.getElementById('settingsToggle').addEventListener('click', () => {
        const panel = document.getElementById('settingsPanel');
        panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
    });
    
    // 保存设置
    document.getElementById('saveSettingsBtn').addEventListener('click', () => {
        currentSettings.serverTimeout = parseInt(document.getElementById('serverTimeout').value) || DEFAULT_SETTINGS.serverTimeout;
        saveSettings();
        
        const panel = document.getElementById('settingsPanel');
        panel.style.display = 'none';
        
        // 显示保存成功消息
        const status = document.getElementById('status');
        status.textContent = '✅ 设置已保存';
        status.className = 'success';
        status.style.display = 'block';
        
        // 3秒后隐藏消息
        setTimeout(() => {
            status.style.display = 'none';
        }, 3000);
    });
    
    // 重置设置
    document.getElementById('resetSettingsBtn').addEventListener('click', () => {
        currentSettings = {...DEFAULT_SETTINGS};
        document.getElementById('serverTimeout').value = currentSettings.serverTimeout;
        saveSettings();
        
        const panel = document.getElementById('settingsPanel');
        panel.style.display = 'none';
        
        // 显示重置成功消息
        const status = document.getElementById('status');
        status.textContent = '✅ 设置已重置为默认';
        status.className = 'success';
        status.style.display = 'block';
        
        // 3秒后隐藏消息
        setTimeout(() => {
            status.style.display = 'none';
        }, 3000);
    });
});

document.getElementById('downloadBtn').onclick = async () => {
    const downloadBtn = document.getElementById('downloadBtn');
    // 使用检测到的浏览器API
    const [tab] = await browserAPI.tabs.query({active: true, currentWindow: true});
    const statusDiv = document.getElementById('status');
    
    // 如果正在下载中，则不处理点击
    if (isDownloading) {
        console.log('已有下载任务正在进行中，请稍候');
        return;
    }
    
    // 设置正在下载标志，并禁用按钮
    isDownloading = true;
    downloadBtn.disabled = true;
    downloadBtn.textContent = '处理中...';
    
    try {
        // 先检查服务器是否在线
        let serverStatus = false;
        try {
            // 使用更可靠的检查方法，增加超时处理
            const checkResponse = await Promise.race([
                fetch('http://localhost:5001/status', {
                    method: 'GET'
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('连接超时')), 3000)
                )
            ]);
            serverStatus = (await checkResponse.json()).status === 'running';
        } catch (e) {
            console.error("服务器连接检查失败", e);
        }

        if (!serverStatus) {
            statusDiv.textContent = '🌐⚠️服务器未运行，请先启动服务';
            statusDiv.className = 'error';
            statusDiv.style.display = 'block';
            return;
        }

        try {
            // 立即显示处理中状态
            statusDiv.textContent = '⏳推送下载请求...';
            statusDiv.className = 'success';
            statusDiv.style.display = 'block';
            
            // 服务器在线，发送下载请求，包含超时设置
            fetch('http://localhost:5001/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: tab.url,
                    timeout: currentSettings.serverTimeout
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('服务器响应:', data);
                // 无论服务器如何响应，都显示下载已推送
                // 因为我们现在使用的是异步处理，实际下载在后台进行
            })
            .catch(error => {
                console.error('下载请求错误:', error);
                // 即使请求出错，也不影响用户体验
                // 因为我们已经立即给出反馈
            });
            
            // 立即显示成功状态，不等待服务器响应
            setTimeout(() => {
                statusDiv.textContent = '✅已推送下载';
                statusDiv.className = 'success';
            }, 1000);
        } catch (err) {
            console.error("请求准备错误", err);
            statusDiv.textContent = `请求错误: ${err.message}`;
            statusDiv.className = 'error';
        }
        statusDiv.style.display = 'block';
    } catch (err) {
        console.error("请求错误", err);
        statusDiv.textContent = '🌐⚠️服务器连接失败，请确保服务已启动';
        statusDiv.className = 'error';
        statusDiv.style.display = 'block';
    } finally {
        // 无论成功或失败，3秒后重置按钮状态
        setTimeout(() => {
            isDownloading = false;
            downloadBtn.disabled = false;
            downloadBtn.textContent = '📥 下载当前页面';
        }, 3000);
    }
};