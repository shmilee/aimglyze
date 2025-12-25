// 全局状态管理
const AppState = {
    config: {},
    currentData: null,
    currentImageData: null, // 新增：存储当前图片的Base64数据
    currentImageName: null, // 新增：存储当前图片的文件名
    isDarkTheme: false,
    isConnected: false,
    isSampleData: false,
    connectionCheckInterval: null, // 连接检查定时器
    lastConnectionCheck: 0,        // 上次连接检查时间
    connectionCheckIntervalMs: 30*1000 // 每30秒检查一次
};
// DOM 元素引用
const elements = {
    uploadArea: null,
    fileInput: null,
    uploadProgress: null,
    progressFill: null,
    progressText: null,
    actionButtons: null,
    loadingElement: null,
    connectionStatus: null,
    mobileConnectionStatus: null,
    pageTitle: null,
    pageSubtitle: null,
    loadSampleBtn: null,
    resultsContainer: null,
    emptyState: null,
    resultsContent: null,
    imageName: null,
    imageDesc: null,
    tagsContainer: null,
    fileInfoSection: null,
    fileInfo: null,
    sampleIndicator: null,
    sampleNote: null,
    // 新增元素引用
    thumbnailContainer: null,
    thumbnailImage: null,
    imagePreviewModal: null,
    previewImage: null,
    previewFilename: null,
    modalOverlay: null,
    modalCloseBtn: null
};
// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
    loadConfig();
    startConnectionMonitoring(); // 启动连接监控
});
// 初始化DOM元素引用
function initializeElements() {
    elements.uploadArea = document.getElementById('uploadArea');
    elements.fileInput = document.getElementById('fileInput');
    elements.uploadProgress = document.getElementById('uploadProgress');
    elements.progressFill = document.getElementById('progressFill');
    elements.progressText = document.getElementById('progressText');
    elements.actionButtons = document.getElementById('actionButtons');
    elements.loadingElement = document.getElementById('loading');
    elements.connectionStatus = document.getElementById('connectionStatus');
    elements.mobileConnectionStatus = document.getElementById('mobileConnectionStatus');
    elements.pageTitle = document.getElementById('pageTitle');
    elements.pageSubtitle = document.getElementById('pageSubtitle');
    elements.loadSampleBtn = document.getElementById('loadSampleBtn');
    // 结果相关元素
    elements.resultsContainer = document.getElementById('resultsContainer');
    elements.emptyState = document.getElementById('emptyState');
    elements.resultsContent = document.getElementById('resultsContent');
    elements.imageName = document.getElementById('imageName');
    elements.imageDesc = document.getElementById('imageDesc');
    elements.tagsContainer = document.getElementById('tagsContainer');
    elements.fileInfoSection = document.getElementById('fileInfoSection');
    elements.fileInfo = document.getElementById('fileInfo');
    elements.sampleIndicator = document.getElementById('sampleIndicator');
    elements.sampleNote = document.getElementById('sampleNote');
    // 新增元素
    elements.thumbnailContainer = document.getElementById('thumbnailContainer');
    elements.thumbnailImage = document.getElementById('thumbnailImage');
    elements.imagePreviewModal = document.getElementById('imagePreviewModal');
    elements.previewImage = document.getElementById('previewImage');
    elements.previewFilename = document.getElementById('previewFilename');
    elements.modalOverlay = elements.imagePreviewModal.querySelector('.modal-overlay');
    elements.modalCloseBtn = elements.imagePreviewModal.querySelector('.close-btn');
}
// 初始化事件监听器
function initializeEventListeners() {
    // 文件输入变化
    elements.fileInput.addEventListener('change', handleFileSelect);
    // 拖放事件
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);
    // 点击上传区域
    elements.uploadArea.addEventListener('click', () => {
        elements.fileInput.click();
    });
    // 示例数据按钮事件
    if (elements.loadSampleBtn) {
        elements.loadSampleBtn.addEventListener('click', loadSampleData);
    }
    // 缩略图点击事件
    if (elements.thumbnailImage) {
        elements.thumbnailImage.addEventListener('click', showImagePreview);
    }
    // 模态框关闭事件
    if (elements.modalOverlay) {
        elements.modalOverlay.addEventListener('click', closeImagePreview);
    }
    if (elements.modalCloseBtn) {
        elements.modalCloseBtn.addEventListener('click', closeImagePreview);
    }
    // ESC键关闭模态框
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.imagePreviewModal.style.display === 'flex') {
            closeImagePreview();
        }
    });
    // 初始主题检查
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        AppState.isDarkTheme = true;
        document.body.classList.add('dark-theme');
        updateThemeButton();
    }
}
// 启动连接监控
function startConnectionMonitoring() {
    // 立即执行第一次检查
    checkConnection();
    // 设置定时检查
    AppState.connectionCheckInterval = setInterval(() => {
        checkConnection();
    }, AppState.connectionCheckIntervalMs);
    // 记录开始时间
    AppState.lastConnectionCheck = Date.now();
}
// 停止连接监控
function stopConnectionMonitoring() {
    if (AppState.connectionCheckInterval) {
        clearInterval(AppState.connectionCheckInterval);
        AppState.connectionCheckInterval = null;
    }
}
// 检查服务器连接
async function checkConnection() {
    try {
        // 使用更快的请求方式，设置超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3秒超时
        const response = await fetch('/api/health', {
            method: 'GET',
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        clearTimeout(timeoutId);
        if (response.ok) {
            if (!AppState.isConnected) {
                // 从断开到连接
                AppState.isConnected = true;
                updateConnectionStatus(true);
                console.log(`✅ 服务器连接恢复 - ${new Date().toLocaleTimeString()}`);
            }
        } else {
            if (AppState.isConnected) {
                // 从连接到断开
                AppState.isConnected = false;
                updateConnectionStatus(false);
                console.log(`❌ 服务器连接失败 - ${new Date().toLocaleTimeString()}`);
            }
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.log(`⏰ 服务器连接超时 - ${new Date().toLocaleTimeString()}`);
        } else {
            console.log(`❌ 服务器连接错误 - ${new Date().toLocaleTimeString()}:`, error.message);
        }
        if (AppState.isConnected) {
            // 从连接到断开
            AppState.isConnected = false;
            updateConnectionStatus(false);
        }
    }
    // 更新最后检查时间
    AppState.lastConnectionCheck = Date.now();
}
// 更新连接状态显示
function updateConnectionStatus(connected) {
    const updateStatusElement = (element) => {
        if (!element) return;
        const statusIcon = element.querySelector('.status-icon');
        if (connected) {
            element.innerHTML = '<i class="fas fa-check-circle status-icon connected"></i> 服务器连接正常';
        } else {
            element.innerHTML = '<i class="fas fa-exclamation-circle status-icon disconnected"></i> 服务器连接失败';
        }
    };
    // 更新两个状态元素（PC端和移动端）
    updateStatusElement(elements.connectionStatus);
    updateStatusElement(elements.mobileConnectionStatus);
}
// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            AppState.config = await response.json();
            // 更新页面标题和副标题
            updatePageTitle();
            // 根据配置显示/隐藏示例数据按钮
            updateSampleDataButton();
            // 应用主题
            if (AppState.config.frontend.theme === 'dark' && !AppState.isDarkTheme) {
                toggleTheme();
            }
            console.log('配置加载成功:', AppState.config);
        }
    } catch (error) {
        console.error('加载配置失败:', error);
    }
}
// 更新页面标题
function updatePageTitle() {
    if (elements.pageTitle && AppState.config.frontend?.title) {
        elements.pageTitle.innerHTML = `<i class="fas fa-image"></i> ${AppState.config.frontend.title}`;
        document.title = AppState.config.frontend.title;
    }
    if (elements.pageSubtitle && AppState.config.frontend?.subtitle) {
        elements.pageSubtitle.textContent = AppState.config.frontend.subtitle;
    }
}
// 更新示例数据按钮显示
function updateSampleDataButton() {
    if (!elements.loadSampleBtn) return;
    // 根据配置显示/隐藏示例按钮
    if (AppState.config.frontend?.show_sample_data) {
        elements.loadSampleBtn.style.display = 'inline-flex';
    } else {
        elements.loadSampleBtn.style.display = 'none';
    }
}
// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        validateAndUploadFile(file);
    }
}
// 处理拖放
function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.style.borderColor = 'var(--primary-color)';
    elements.uploadArea.style.backgroundColor = 'rgba(74, 107, 255, 0.1)';
}
function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.style.borderColor = '';
    elements.uploadArea.style.backgroundColor = '';
}
function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    elements.uploadArea.style.borderColor = '';
    elements.uploadArea.style.backgroundColor = '';
    const file = event.dataTransfer.files[0];
    if (file) {
        validateAndUploadFile(file);
    }
}
// 验证并上传文件
function validateAndUploadFile(file) {
    // 检查服务器连接
    if (!AppState.isConnected) {
        alert('服务器连接失败，请检查网络连接后再试。');
        return;
    }
    // 验证文件类型
    const allowedExtensions = AppState.config.allowed_extensions || ['.jpg', '.jpeg', '.png', '.webp'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(fileExt)) {
        alert(`不支持的文件格式: ${fileExt}\n支持格式: ${allowedExtensions.join(', ')}`);
        return;
    }
    // 验证文件大小
    const maxSize = (AppState.config.max_upload_size || 10) * 1024 * 1024;
    if (file.size > maxSize) {
        alert(`文件太大: ${(file.size / 1024 / 1024).toFixed(2)}MB\n最大支持: ${maxSize / 1024 / 1024}MB`);
        return;
    }
    // 保存图片数据用于缩略图
    readFileAsDataURL(file).then(dataURL => {
        AppState.currentImageData = dataURL;
        AppState.currentImageName = file.name;
        uploadFile(file);
    }).catch(error => {
        console.error('读取文件失败:', error);
        uploadFile(file); // 即使读取失败也继续上传
    });
}
// 读取文件为DataURL
function readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}
// 上传文件并分析
async function uploadFile(file) {
    showLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
        // 模拟进度
        simulateProgress();
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || '上传失败');
        }
        const result = await response.json();
        // 如果有错误
        if (result.error) {
            throw new Error(result.error);
        }
        // 保存结果
        AppState.currentData = result.result;
        AppState.currentData.cache_key = result.cache_key;
        if (result.file_info) {
            AppState.currentData.file_info = result.file_info;
        }
        // 标记为不是示例数据
        AppState.isSampleData = false;
        // 渲染结果
        renderResults();
    } catch (error) {
        console.error('上传失败:', error);
        alert(`分析失败: ${error.message}`);
    } finally {
        showLoading(false);
        resetProgress();
    }
}
// 模拟进度条
function simulateProgress() {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 90) {
            clearInterval(interval);
        }
        updateProgress(progress);
    }, 200);
}
function updateProgress(percent) {
    if (elements.progressFill) {
        elements.progressFill.style.width = `${percent}%`;
    }
}
function resetProgress() {
    if (elements.progressFill) {
        elements.progressFill.style.width = '0%';
    }
}
// 显示/隐藏加载状态
function showLoading(show) {
    if (show) {
        elements.uploadProgress.style.display = 'block';
        elements.loadingElement.style.display = 'block';
    } else {
        elements.uploadProgress.style.display = 'none';
        elements.loadingElement.style.display = 'none';
    }
}
// 加载示例数据
async function loadSampleData() {
    showLoading(true);
    try {
        const response = await fetch('/api/sample');
        if (!response.ok) {
            throw new Error('加载示例数据失败');
        }
        const data = await response.json();
        AppState.currentData = data;
        // 标记为示例数据
        AppState.isSampleData = true;
        // 清除图片数据
        AppState.currentImageData = null;
        AppState.currentImageName = null;
        // 渲染结果
        renderResults();
    } catch (error) {
        console.error('加载示例数据失败:', error);
        alert(`加载示例数据失败: ${error.message}`);
    } finally {
        showLoading(false);
    }
}
// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    // 对于小于1MB的文件，保留1位小数；对于大于等于1MB的文件，保留2位小数
    const decimals = i < 2 ? 1 : 2;
    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}
// 渲染结果
function renderResults() {
    if (!AppState.currentData) return;
    // 隐藏空状态
    elements.emptyState.style.display = 'none';
    elements.resultsContent.style.display = 'block';
    // 更新图片名称
    if (elements.imageName && AppState.currentData.name) {
        elements.imageName.textContent = AppState.currentData.name;
    }
    // 更新详细描述
    if (elements.imageDesc && AppState.currentData.desc) {
        elements.imageDesc.textContent = AppState.currentData.desc;
    }
    // 更新标签
    if (elements.tagsContainer && AppState.currentData.tags && Array.isArray(AppState.currentData.tags)) {
        elements.tagsContainer.innerHTML = '';
        AppState.currentData.tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';
            tagElement.textContent = tag;
            elements.tagsContainer.appendChild(tagElement);
        });
    }
    // 更新文件信息（如果有）
    if (AppState.currentData.file_info) {
        elements.fileInfoSection.style.display = 'block';
        const fileInfo = AppState.currentData.file_info;
        let fileInfoHTML = '';
        if (fileInfo.hash) {
            fileInfoHTML += `
                <div class="file-info-item">
                    <span class="file-info-label">文件哈希：</span>
                    <span class="file-info-value">${fileInfo.hash}</span>
                </div>
            `;
        }
        if (fileInfo.size) {
            const formattedSize = formatFileSize(fileInfo.size);
            fileInfoHTML += `
                <div class="file-info-item">
                    <span class="file-info-label">文件大小：</span>
                    <span class="file-info-value">${formattedSize}</span>
                </div>
            `;
        }
        if (fileInfo.mime_type) {
            fileInfoHTML += `
                <div class="file-info-item">
                    <span class="file-info-label">文件类型：</span>
                    <span class="file-info-value">${fileInfo.mime_type}</span>
                </div>
            `;
        }
        if (fileInfo.saved !== undefined) {
            fileInfoHTML += `
                <div class="file-info-item">
                    <span class="file-info-label">文件保存：</span>
                    <span class="file-info-value">${fileInfo.saved ? '已保存' : '未保存'}</span>
                </div>
            `;
        }
        elements.fileInfo.innerHTML = fileInfoHTML;
    } else {
        elements.fileInfoSection.style.display = 'none';
    }
    // 更新缩略图
    updateThumbnail();
    // 更新示例数据标识
    if (AppState.isSampleData) {
        elements.sampleIndicator.style.display = 'flex';
        elements.sampleNote.style.display = 'block';
    } else {
        elements.sampleIndicator.style.display = 'none';
        elements.sampleNote.style.display = 'none';
    }
}
// 更新缩略图
function updateThumbnail() {
    if (AppState.currentImageData && !AppState.isSampleData) {
        // 显示缩略图容器
        elements.thumbnailContainer.style.display = 'flex';
        // 设置缩略图
        elements.thumbnailImage.src = AppState.currentImageData;
        // 重新绑定点击事件
        elements.thumbnailImage.onclick = showImagePreview;
        console.log('缩略图已更新，点击事件已绑定');
    } else {
        // 隐藏缩略图容器（示例数据或无图片时）
        elements.thumbnailContainer.style.display = 'none';
    }
}
// 显示图片预览
function showImagePreview() {
    console.log('showImagePreview被调用');
    if (!AppState.currentImageData) {
        console.warn('没有图片数据可预览');
        return;
    }
    // 设置预览图片
    elements.previewImage.src = AppState.currentImageData;
    // 设置文件名
    if (AppState.currentImageName) {
        elements.previewFilename.textContent = AppState.currentImageName;
    } else if (AppState.currentData && AppState.currentData.name) {
        elements.previewFilename.textContent = AppState.currentData.name;
    } else {
        elements.previewFilename.textContent = '预览图片';
    }
    // 直接设置display为flex（覆盖CSS的默认值）
    elements.imagePreviewModal.style.display = 'flex';
    console.log('模态框已显示，display设置为flex');
}
// 关闭图片预览
function closeImagePreview() {
    elements.imagePreviewModal.style.display = 'none';
}
// 清空分析结果
function clearResults() {
    if (confirm('确定要清空所有分析结果吗？')) {
        AppState.currentData = null;
        AppState.currentImageData = null;
        AppState.currentImageName = null;
        AppState.isSampleData = false;
        // 显示空状态
        elements.emptyState.style.display = 'block';
        elements.resultsContent.style.display = 'none';
        // 隐藏缩略图
        elements.thumbnailContainer.style.display = 'none';
        // 隐藏示例数据标识
        elements.sampleIndicator.style.display = 'none';
        elements.sampleNote.style.display = 'none';
        // 关闭预览模态框（如果开着）
        closeImagePreview();
    }
}
// 切换主题
function toggleTheme() {
    AppState.isDarkTheme = !AppState.isDarkTheme;
    document.body.classList.toggle('dark-theme', AppState.isDarkTheme);
    // 保存主题偏好
    localStorage.setItem('theme', AppState.isDarkTheme ? 'dark' : 'light');
    updateThemeButton();
}
// 更新主题按钮图标
function updateThemeButton() {
    const themeBtn = document.querySelector('[onclick="toggleTheme()"]');
    if (themeBtn) {
        const icon = themeBtn.querySelector('i');
        if (icon) {
            icon.className = AppState.isDarkTheme ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}
// 导出JSON
function exportJSON() {
    if (!AppState.currentData) {
        alert('没有可导出的数据');
        return;
    }
    const exportData = {
        ...AppState.currentData,
        is_sample_data: AppState.isSampleData,
        export_timestamp: new Date().toISOString()
    };
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const exportFileDefaultName = `image_analysis_${timestamp}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}
// 打印结果
function printResults() {
    window.print();
}
// 页面卸载时清理定时器
window.addEventListener('beforeunload', () => {
    stopConnectionMonitoring();
});
// 全局导出函数
window.showImagePreview = showImagePreview;
window.closeImagePreview = closeImagePreview;
