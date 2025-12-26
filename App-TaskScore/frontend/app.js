// 全局状态管理
const AppState = {
    config: {},
    currentData: null,
    isDarkTheme: false,
    isConnected: false,
    currentPage: 1,
    totalPages: 4,
    radarChart: null,
    dimensionStats: null,
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
    carouselTrack: null,
    prevBtn: null,
    nextBtn: null,
    currentPageSpan: null,
    totalPagesSpan: null,
    carouselPages: null,
    pageTitles: null,
    scoreOverviewContent: null,
    analysisReportContent: null,
    dimensionsContent: null,
    radarChartContent: null,
    pageHint: null,
    loadSampleBtn: null
};
// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    initializeEventListeners();
    loadConfig();
    initializeCarousel();
    initializeKeyboardNavigation();
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
    elements.pageHint = document.getElementById('pageHint');
    elements.loadSampleBtn = document.getElementById('loadSampleBtn');
    // 轮播相关元素
    elements.carouselTrack = document.getElementById('carouselTrack');
    elements.prevBtn = document.getElementById('prevBtn');
    elements.nextBtn = document.getElementById('nextBtn');
    elements.currentPageSpan = document.getElementById('currentPage');
    elements.totalPagesSpan = document.getElementById('totalPages');
    elements.carouselPages = document.querySelectorAll('.carousel-page');
    // 页面标题元素
    elements.pageTitles = {
        1: document.getElementById('page1Title'),
        2: document.getElementById('page2Title'),
        3: document.getElementById('page3Title'),
        4: document.getElementById('page4Title')
    };
    // 内容容器
    elements.scoreOverviewContent = document.getElementById('scoreOverviewContent');
    elements.analysisReportContent = document.getElementById('analysisReportContent');
    elements.dimensionsContent = document.getElementById('dimensionsContent');
    elements.radarChartContent = document.getElementById('radarChartContent');
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
    // 初始主题检查
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        AppState.isDarkTheme = true;
        document.body.classList.add('dark-theme');
        updateThemeButton();
    }
    // 轮播按钮事件
    elements.prevBtn.addEventListener('click', () => navigateCarousel(-1));
    elements.nextBtn.addEventListener('click', () => navigateCarousel(1));
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
// 初始化轮播
function initializeCarousel() {
    elements.totalPagesSpan.textContent = AppState.totalPages;
    updateCarousel();
}
// 初始化键盘导航
function initializeKeyboardNavigation() {
    document.addEventListener('keydown', (event) => {
        if (AppState.currentData) {
            if (event.key === 'ArrowLeft') {
                navigateCarousel(-1);
            } else if (event.key === 'ArrowRight') {
                navigateCarousel(1);
            }
        }
    });
}
// 轮播导航
function navigateCarousel(direction) {
    const newPage = AppState.currentPage + direction;
    if (newPage >= 1 && newPage <= AppState.totalPages) {
        AppState.currentPage = newPage;
        updateCarousel();
    }
}
// 更新轮播显示
function updateCarousel() {
    // 更新页码显示
    elements.currentPageSpan.textContent = AppState.currentPage;
    // 更新页面显示
    elements.carouselPages.forEach((page, index) => {
        if (index === AppState.currentPage - 1) {
            page.classList.add('active');
        } else {
            page.classList.remove('active');
        }
    });
    // 更新按钮状态
    elements.prevBtn.disabled = AppState.currentPage === 1;
    elements.nextBtn.disabled = AppState.currentPage === AppState.totalPages;
    // 高亮当前页面标题
    Object.keys(elements.pageTitles).forEach(pageNum => {
        const titleElement = elements.pageTitles[pageNum];
        if (titleElement) {
            if (parseInt(pageNum) === AppState.currentPage) {
                titleElement.style.color = 'var(--primary-color)';
                titleElement.style.fontWeight = '700';
            } else {
                titleElement.style.color = 'var(--text-color)';
                titleElement.style.fontWeight = '400';
            }
        }
    });
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
        elements.pageTitle.innerHTML = `<i class="fas fa-chart-line"></i> ${AppState.config.frontend.title}`;
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
    uploadFile(file);
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
        // 计算维度统计数据
        calculateDimensionStats();
        // 渲染所有页面内容
        renderAllPages();
        // 重置到第一页
        AppState.currentPage = 1;
        updateCarousel();
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
        // 清空所有内容容器
        elements.scoreOverviewContent.innerHTML = '';
        elements.analysisReportContent.innerHTML = '';
        elements.dimensionsContent.innerHTML = '';
        elements.radarChartContent.innerHTML = '';
        // 移除示例数据标识
        removeSampleIndicators();
    } else {
        elements.uploadProgress.style.display = 'none';
        elements.loadingElement.style.display = 'none';
    }
}
// 移除示例数据标识
function removeSampleIndicators() {
    const indicator = document.getElementById('sampleIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}
// 添加示例数据标识到每个页面
function addSampleIndicators() {
    if (!AppState.isSampleData) {
        removeSampleIndicators();
        return;
    }
    const indicator = document.getElementById('sampleIndicator');
    if (indicator) {
        indicator.style.display = 'flex'; // 或者 'inline-flex'
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
        // 计算维度统计数据
        calculateDimensionStats();
        // 渲染所有页面内容
        renderAllPages();
        // 添加示例数据标识
        addSampleIndicators();
        // 重置到第一页
        AppState.currentPage = 1;
        updateCarousel();
    } catch (error) {
        console.error('加载示例数据失败:', error);
        alert(`加载示例数据失败: ${error.message}`);
    } finally {
        showLoading(false);
    }
}
// 计算维度统计数据
function calculateDimensionStats() {
    if (!AppState.currentData) return;
    const data = AppState.currentData;
    const dimensionStats = {};
    // 检查是否有dimensions数组
    if (!Array.isArray(data.dimensions) || data.dimensions.length === 0) {
        AppState.dimensionStats = null;
        return;
    }
    // 处理数组格式的dimensions数据
    data.dimensions.forEach((dim, index) => {
        const points = dim.points || [];
        if (points.length === 0) return;
        // 计算每个维度的实际得分（累加所有要点的对应得分）
        let selfTotalScore = 0;
        let peerTotalScore = 0;
        let teacherTotalScore = 0;
        let totalMaxScore = 0;
        points.forEach(point => {
            const maxScore = parseFloat(point.score) || 0;
            const selfScore = parseFloat(point.self) || 0;
            const peerScore = parseFloat(point.peer) || 0;
            const teacherScore = parseFloat(point.teacher) || 0;
            totalMaxScore += maxScore;
            selfTotalScore += selfScore;
            peerTotalScore += peerScore;
            teacherTotalScore += teacherScore;
        });
        // 计算平均得分率
        const selfAvgRate = totalMaxScore > 0 ? (selfTotalScore / totalMaxScore) : 0;
        const peerAvgRate = totalMaxScore > 0 ? (peerTotalScore / totalMaxScore) : 0;
        const teacherAvgRate = totalMaxScore > 0 ? (teacherTotalScore / totalMaxScore) : 0;
        dimensionStats[`dim-${index + 1}`] = {
            desc: dim.desc || `维度${index + 1}`,
            totalMaxScore,
            selfTotalScore,
            peerTotalScore,
            teacherTotalScore,
            selfAvgRate,
            peerAvgRate,
            teacherAvgRate,
            points: points.length,
            // 保存原始要点数据用于显示
            pointData: points.map(point => ({
                desc: point.desc || '',
                score: parseFloat(point.score) || 0,
                self: parseFloat(point.self) || 0,
                peer: parseFloat(point.peer) || 0,
                teacher: parseFloat(point.teacher) || 0
            }))
        };
    });
    AppState.dimensionStats = dimensionStats;
}
// 渲染所有页面内容
function renderAllPages() {
    if (!AppState.currentData) return;
    // 确保维度统计数据已计算
    if (!AppState.dimensionStats) {
        calculateDimensionStats();
    }
    renderScoreOverview();
    renderAnalysisReport();
    renderDimensionsDetail();
    renderRadarChart();
}
// 页面1: 渲染分数概览
function renderScoreOverview() {
    if (!AppState.currentData || !elements.scoreOverviewContent) return;
    const data = AppState.currentData;
    // 确保total_score是数组格式
    let scores = [0, 0, 0];
    if (Array.isArray(data.total_score)) {
        scores = data.total_score;
    } else if (data.total_score && typeof data.total_score === 'object') {
        // 如果是对象格式，转换为数组
        scores = [
            data.total_score.self || 0,
            data.total_score.peer || 0,
            data.total_score.teacher || 0
        ];
    }
    // 计算平均分
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    const html = `
        <div class="score-overview">
            <!-- 第一行：平均分和评价并排居中 -->
            <div class="score-top-row">
                <!-- 简化的平均分显示 -->
                <div class="average-score-compact">
                    <div class="score-value">${avgScore.toFixed(1)}</div>
                    <div class="score-label">平均分</div>
                </div>
                <!-- 简化的评价 -->
                <div class="simplified-evaluation">
                    <p><i class="fas fa-lightbulb" style="color: var(--warning-color); margin-right: 6px;"></i>
                    ${avgScore >= 85 ? '表现优秀' : avgScore >= 75 ? '表现良好' : avgScore >= 60 ? '表现一般' : '需要加强'}</p>
                </div>
            </div>
            <!-- 第二行：三个分数卡片并排排列 -->
            <div class="score-cards-grid">
                <div class="score-card-simple self">
                    <div class="score-icon"><i class="fas fa-user-check self-color"></i></div>
                    <div class="score-value">${scores[0]}</div>
                    <div class="score-label self-color">自评</div>
                </div>
                <div class="score-card-simple peer">
                    <div class="score-icon"><i class="fas fa-users peer-color"></i></div>
                    <div class="score-value">${scores[1]}</div>
                    <div class="score-label peer-color">互评</div>
                </div>
                <div class="score-card-simple teacher">
                    <div class="score-icon"><i class="fas fa-chalkboard-teacher teacher-color"></i></div>
                    <div class="score-value">${scores[2]}</div>
                    <div class="score-label teacher-color">师评</div>
                </div>
            </div>
        </div>
    `;
    elements.scoreOverviewContent.innerHTML = html;
}
// 页面2: 渲染分析报告
function renderAnalysisReport() {
    if (!AppState.currentData || !elements.analysisReportContent) return;
    const data = AppState.currentData;
    const html = `
        <div class="analysis-report">
            <div class="report-summary">
                <!-- <h3><i class="fas fa-file-medical-alt"></i> 分数说明</h3> -->
                <p>${data.report || '暂无报告内容'}</p>
            </div>
            <div class="strengths-improvements">
                <div class="strengths-box">
                    <h3><i class="fas fa-thumbs-up"></i> 学习优势</h3>
                    <div class="strengths-list">
                        ${(data.strengths && data.strengths.length > 0) 
                            ? data.strengths.map((strength, index) => `
                                <div class="strength-item">
                                    <i class="fas fa-check-circle"></i>
                                    <div class="strength-text">
                                        ${strength}
                                    </div>
                                </div>
                            `).join('')
                            : '<p style="color: var(--text-secondary); text-align: center; padding: 15px;">暂无优势记录</p>'
                        }
                    </div>
                </div>
                <div class="improvements-box">
                    <h3><i class="fas fa-tools"></i> 改进建议</h3>
                    <div class="improvements-list">
                        ${(data.improvements && data.improvements.length > 0) 
                            ? data.improvements.map((improvement, index) => `
                                <div class="improvement-item">
                                    <i class="fas fa-exclamation-circle"></i>
                                    <div class="improvement-text">
                                        ${improvement}
                                    </div>
                                </div>
                            `).join('')
                            : '<p style="color: var(--text-secondary); text-align: center; padding: 15px;">暂无改进建议</p>'
                        }
                    </div>
                </div>
            </div>
            <div class="overall-evaluation">
                <h3><i class="fas fa-star"></i> 总体评价</h3>
                <p>${data.overall || '暂无总体评价'}</p>
            </div>
        </div>
    `;
    elements.analysisReportContent.innerHTML = html;
}
// 页面3: 渲染维度详情
function renderDimensionsDetail() {
    if (!AppState.currentData || !elements.dimensionsContent) return;
    // 使用计算好的维度统计数据
    if (!AppState.dimensionStats || Object.keys(AppState.dimensionStats).length === 0) {
        elements.dimensionsContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle empty-icon"></i>
                <p>未找到维度评分信息</p>
            </div>
        `;
        return;
    }
    const dimensions = Object.keys(AppState.dimensionStats).map(key => ({
        key,
        stats: AppState.dimensionStats[key]
    }));
    if (dimensions.length === 0) {
        elements.dimensionsContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle empty-icon"></i>
                <p>未找到维度评分信息</p>
            </div>
        `;
        return;
    }
    let html = `
        <div class="dimensions-detail">
            <div class="dimension-summary">
                <h3><i class="fas fa-info-circle"></i> 维度统计</h3>
                <div class="dimension-stats">
                    <div class="dimension-stat">
                        <i class="fas fa-layer-group" style="color: var(--primary-color);"></i>
                        <span>总维度数: ${dimensions.length}</span>
                    </div>
                </div>
            </div>
    `;
    dimensions.forEach((dim, dimIndex) => {
        const stats = dim.stats;
        html += `
            <div class="dimension-section" style="margin-bottom: 20px;">
                <!-- 修改后的标题区域 -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 15px 0 10px 0; flex-wrap: wrap; gap: 8px;">
                    <!-- 左侧：维度名称和总分 -->
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h4 style="margin: 0; color: var(--primary-color); display: flex; align-items: center; gap: 6px;">
                            <i class="fas fa-cube"></i> ${stats.desc}
                        </h4>
                        <span style="font-size: 0.86rem; font-weight: bold; color: var(--text-secondary); background: rgba(0,0,0,0.05); padding: 3px 8px; border-radius: 12px;">
                            总分: ${stats.totalMaxScore}
                        </span>
                    </div>
                    <!-- 右侧：三个评分总分 -->
                    <div class="dimension-stats" style="display: flex; gap: 10px; margin: 0; flex-wrap: wrap;">
                        <div class="dimension-stat self-stat">
                            <i class="fas fa-user-check self-color"></i>
                            <span class="self-color" style="font-weight: 600;">${stats.selfTotalScore.toFixed(1)}</span>
                        </div>
                        <div class="dimension-stat peer-stat">
                            <i class="fas fa-users peer-color"></i>
                            <span class="peer-color" style="font-weight: 600;">${stats.peerTotalScore.toFixed(1)}</span>
                        </div>
                        <div class="dimension-stat teacher-stat">
                            <i class="fas fa-chalkboard-teacher teacher-color"></i>
                            <span class="teacher-color" style="font-weight: 600;">${stats.teacherTotalScore.toFixed(1)}</span>
                        </div>
                    </div>
                </div>
                <table class="dimension-table">
                    <thead>
                        <tr>
                            <th>评分项</th>
                            <th>满分</th>
                            <th>自评</th>
                            <th>互评</th>
                            <th>师评</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${stats.pointData.length > 0 
                            ? stats.pointData.map((point, index) => `
                                <tr class="${index % 2 === 0 ? 'even-row' : 'odd-row'}">
                                    <td>${point.desc}</td>
                                    <td class="score-cell max">${point.score}</td>
                                    <td class="score-cell self self-color">${point.self}</td>
                                    <td class="score-cell peer peer-color">${point.peer}</td>
                                    <td class="score-cell teacher teacher-color">${point.teacher}</td>
                                </tr>
                            `).join('')
                            : `<tr><td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 20px;">无详细评分项数据</td></tr>`
                        }
                    </tbody>
                </table>
            </div>
        `;
    });
    html += '</div>';
    elements.dimensionsContent.innerHTML = html;
}
// 页面4: 渲染雷达图
function renderRadarChart() {
    if (!AppState.currentData || !elements.radarChartContent) return;
    // 确保维度统计数据已计算
    if (!AppState.dimensionStats) {
        calculateDimensionStats();
    }
    // 使用计算好的维度统计数据
    if (!AppState.dimensionStats || Object.keys(AppState.dimensionStats).length === 0) {
        elements.radarChartContent.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-circle empty-icon"></i>
                <p>未找到足够维度信息绘制雷达图</p>
            </div>
        `;
        return;
    }
    // 准备雷达图数据
    const radarData = prepareRadarData(AppState.dimensionStats);
    // 渲染雷达图容器
    elements.radarChartContent.innerHTML = `
        <div class="radar-chart-container">
            <div class="chart-wrapper">
                <canvas id="radarChartCanvas"></canvas>
            </div>
        </div>
    `;
    // 创建雷达图
    createRadarChart(radarData);
}
// 准备雷达图数据
function prepareRadarData(dimensionStats) {
    const labels = [];
    const selfData = [];
    const peerData = [];
    const teacherData = [];
    Object.keys(dimensionStats).forEach(dimKey => {
        const stats = dimensionStats[dimKey];
        labels.push(stats.desc);
        // 使用实际的得分数据
        selfData.push(stats.selfTotalScore);
        peerData.push(stats.peerTotalScore);
        teacherData.push(stats.teacherTotalScore);
    });
    return {
        labels,
        selfData,
        peerData,
        teacherData
    };
}
// 创建雷达图
function createRadarChart(radarData) {
    const canvas = document.getElementById('radarChartCanvas');
    if (!canvas) return;
    // 如果已有图表实例，先销毁
    if (AppState.radarChart) {
        AppState.radarChart.destroy();
    }
    const ctx = canvas.getContext('2d');
    const rootStyle = getComputedStyle(document.documentElement);
    // 获取CSS变量定义的配色
    const selfColor = rootStyle.getPropertyValue('--self-color').trim();
    const peerColor = rootStyle.getPropertyValue('--peer-color').trim();
    const teacherColor = rootStyle.getPropertyValue('--teacher-color').trim();
    // 获取当前主题的文本颜色和背景颜色
    const isDarkTheme = AppState.isDarkTheme;
    const textColor = isDarkTheme ? 'rgba(255, 255, 255, 0.8)' : rootStyle.getPropertyValue('--text-color').trim();
    const tooltip_textColor = rootStyle.getPropertyValue('--text-color').trim();
    const borderColor = rootStyle.getPropertyValue('--border-color').trim();
    const cardBg = rootStyle.getPropertyValue('--card-bg').trim();
    // 为不同主题设置网格线颜色
    const gridLineColor = isDarkTheme ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)';
    const angleLineColor = isDarkTheme ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)';
    const tickColor = isDarkTheme ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)';
    // 计算每个维度的最大值（用于标准化到0-100%）
    const maxValues = radarData.labels.map((_, index) => {
        return Math.max(
            radarData.selfData[index] || 0,
            radarData.peerData[index] || 0,
            radarData.teacherData[index] || 0
        );
    });
    // 标准化数据到0-100%
    const normalizeData = (data) => {
        return data.map((value, index) => {
            const max = maxValues[index];
            return max > 0 ? (value / max) * 100 : 0;
        });
    };
    const normalizedSelf = normalizeData(radarData.selfData);
    const normalizedPeer = normalizeData(radarData.peerData);
    const normalizedTeacher = normalizeData(radarData.teacherData);
    // 创建图表
    AppState.radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: radarData.labels,
            datasets: [
                {
                    label: '自评',
                    data: normalizedSelf,
                    backgroundColor: hexToRgba(selfColor, 0.2),
                    borderColor: hexToRgba(selfColor, 0.8),
                    borderWidth: 2,
                    pointBackgroundColor: selfColor,
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.1 // 曲线平滑度
                },
                {
                    label: '互评',
                    data: normalizedPeer,
                    backgroundColor: hexToRgba(peerColor, 0.2),
                    borderColor: hexToRgba(peerColor, 0.8),
                    borderWidth: 2,
                    pointBackgroundColor: peerColor,
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.1
                },
                {
                    label: '师评',
                    data: normalizedTeacher,
                    backgroundColor: hexToRgba(teacherColor, 0.2),
                    borderColor: hexToRgba(teacherColor, 0.8),
                    borderWidth: 2,
                    pointBackgroundColor: teacherColor,
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    // 根据屏幕宽度设置图例位置
                    position: window.innerWidth < 768 ? 'top' : 'left',
                    labels: {
                        color: textColor,
                        font: {
                            family: 'Inter',
                            size: 14
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        // 工具提示显示原始分数和百分比
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const index = context.dataIndex;
                            // 获取原始数据值
                            let originalValue = 0;
                            if (context.datasetIndex === 0) {
                                originalValue = radarData.selfData[index];
                            } else if (context.datasetIndex === 1) {
                                originalValue = radarData.peerData[index];
                            } else if (context.datasetIndex === 2) {
                                originalValue = radarData.teacherData[index];
                            }
                            return `${label}: ${originalValue.toFixed(1)}分`;
                        },
                        // 标题显示维度名称
                        title: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            return radarData.labels[index];
                        }
                    },
                    backgroundColor: cardBg,
                    titleColor: tooltip_textColor,
                    bodyColor: tooltip_textColor,
                    borderColor: borderColor,
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 5
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    min: 0,
                    max: 100,
                    ticks: {
                        display: true,
                        stepSize: 20,
                        color: tickColor,
                        font: {
                            family: 'Inter',
                            size: 12
                        },
                        backdropColor: 'transparent',
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    pointLabels: {
                        color: textColor,
                        font: {
                            family: 'Inter',
                            size: 13,
                            weight: '500'
                        },
                        padding: 10
                    },
                    angleLines: {
                        color: angleLineColor,
                        lineWidth: 1
                    },
                    grid: {
                        color: gridLineColor,
                        circular: true
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            },
            // 调整布局
            layout: {
                padding: {
                    left: 10,
                    right: 10,
                    top: 10,
                    bottom: 10
                }
            }
        }
    });
}
// 辅助函数：将十六进制颜色转换为rgba
function hexToRgba(hex, alpha = 1) {
    // 如果已经是rgba格式，直接返回
    if (hex.startsWith('rgba')) return hex;
    if (hex.startsWith('rgb')) {
        const rgb = hex.match(/\d+/g);
        return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
    }
    // 处理十六进制
    let r = 0, g = 0, b = 0;
    // 3位十六进制
    if (hex.length === 4) {
        r = parseInt(hex[1] + hex[1], 16);
        g = parseInt(hex[2] + hex[2], 16);
        b = parseInt(hex[3] + hex[3], 16);
    }
    // 6位十六进制
    else if (hex.length === 7) {
        r = parseInt(hex[1] + hex[2], 16);
        g = parseInt(hex[3] + hex[4], 16);
        b = parseInt(hex[5] + hex[6], 16);
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
// 切换主题
function toggleTheme() {
    AppState.isDarkTheme = !AppState.isDarkTheme;
    document.body.classList.toggle('dark-theme', AppState.isDarkTheme);
    // 保存主题偏好
    localStorage.setItem('theme', AppState.isDarkTheme ? 'dark' : 'light');
    updateThemeButton();
    // 重新创建雷达图以适应新主题
    if (AppState.currentData && AppState.radarChart) {
        // 先销毁现有图表
        if (AppState.radarChart) {
            AppState.radarChart.destroy();
            AppState.radarChart = null;
        }
        // 等待主题切换完成，然后重新渲染
        setTimeout(() => {
            if (AppState.currentData && AppState.currentPage === 4) {
                renderRadarChart();
            }
        }, 200);
    }
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
    // 添加维度统计数据到导出数据
    const exportData = {
        ...AppState.currentData,
        // dimension_stats: AppState.dimensionStats,
        export_timestamp: new Date().toISOString()
    };
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    // 生成文件名
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const exportFileDefaultName = `analysis_${timestamp}.json`;
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}
// 打印结果
function printResults() {
    window.print();
}
// 清空分析结果
function clearResults() {
    if (confirm('确定要清空所有分析结果吗？')) {
        AppState.currentData = null;
        AppState.dimensionStats = null;
        AppState.isSampleData = false;
        AppState.currentPage = 1;
        // 清空所有内容容器
        elements.scoreOverviewContent.innerHTML = '';
        elements.analysisReportContent.innerHTML = '';
        elements.dimensionsContent.innerHTML = '';
        elements.radarChartContent.innerHTML = '';
        // 移除示例数据标识
        removeSampleIndicators();
        // 重置轮播
        updateCarousel();
        // 销毁雷达图
        if (AppState.radarChart) {
            AppState.radarChart.destroy();
            AppState.radarChart = null;
        }
    }
}
// 页面卸载时清理定时器
window.addEventListener('beforeunload', () => {
    stopConnectionMonitoring();
});
