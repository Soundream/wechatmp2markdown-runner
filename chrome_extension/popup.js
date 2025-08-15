document.getElementById('downloadBtn').onclick = async () => {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const statusDiv = document.getElementById('status');
    
    try {
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
                statusDiv.textContent = '✅下载成功';
            }, 2000);
        } else {
            statusDiv.textContent = '下载失败';
            statusDiv.className = 'error';
        }
        statusDiv.style.display = 'block';
    } catch (err) {
        statusDiv.textContent = '🌐⚠️服务器连接失败';
        statusDiv.className = 'error';
        statusDiv.style.display = 'block';
    }
};