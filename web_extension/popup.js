// 防止重复点击的标志
let isDownloading = false;

document.getElementById('downloadBtn').onclick = async () => {
    const downloadBtn = document.getElementById('downloadBtn');
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
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
            const checkResponse = await fetch('http://localhost:5001/status', {
                method: 'GET'
            });
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

        // 服务器在线，发送下载请求
        const response = await fetch('http://localhost:5001/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({url: tab.url})
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            statusDiv.textContent = '⏳正在下载中...⏳';
            statusDiv.className = 'success';
            // 2秒后更新为下载成功
            setTimeout(() => {
                statusDiv.textContent = '✅已推送下载';
            }, 2000);
        } else {
            statusDiv.textContent = `下载失败: ${data.message || '未知错误'}`;
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