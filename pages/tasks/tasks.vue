<template>
  <view class="container">
    <view class="header">
      <text class="title">转录任务</text>
    </view>

    <!-- 刷新栏 -->
    <view class="refresh-bar">
      <text class="refresh-text">共 {{ tasks.length }} 个任务</text>
      <view class="refresh-btn" @click="loadTasks">
        <text>🔄 刷新</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty-state" v-if="tasks.length === 0 && !loading">
      <text class="empty-icon">📋</text>
      <text class="empty-text">暂无转录任务</text>
      <text class="empty-hint">去首页创建新任务吧</text>
    </view>

    <!-- 加载中 -->
    <view class="loading-spinner-wrap" v-if="loading && tasks.length === 0">
      <view class="loading-spinner"></view>
      <text>加载中...</text>
    </view>

    <!-- 任务列表 -->
    <view class="task-list" v-else-if="tasks.length > 0">
      <view class="task-item" v-for="task in tasks" :key="task.task_id" @click="toggleDetail(task)">
        <!-- 任务头部 -->
        <view class="task-header">
          <text class="task-title" v-if="task.title">{{ truncate(task.title, 30) }}</text>
          <text class="task-id" v-else>#{{ task.task_id.slice(0, 8) }}</text>
          <text class="task-status" :class="'status-' + task.status">
            {{ statusText(task.status) }}
          </text>
        </view>

        <!-- 来源 -->
        <text class="task-source" v-if="task.url">{{ shortUrl(task.url) }}</text>

        <!-- 进度条 -->
        <view class="progress-bar">
          <view class="progress-fill" :style="{width: (task.progress || 0) + '%'}"></view>
        </view>
        <view class="progress-text">
          <text>{{ task.message || statusText(task.status) }}</text>
          <text>{{ task.progress || 0 }}%</text>
        </view>

        <!-- 错误 -->
        <view class="error-msg" v-if="task.status === 'failed' && task.error">
          <text>⚠️ {{ task.error }}</text>
        </view>

        <!-- ====== 展开详情 ====== -->
        <view class="detail-section" v-if="expandedId === task.task_id">
          <!-- 已完成：显示结果 -->
          <template v-if="task.status === 'completed' && task.result">
            <view class="detail-tabs">
              <view class="dt-tab" :class="{active: detailTab === 'segments'}" @click.stop="detailTab='segments'">📄 逐句</view>
              <view class="dt-tab" :class="{active: detailTab === 'corrected'}" @click.stop="detailTab='corrected'" v-if="task.result.corrected_text">✏️ 纠错</view>
              <view class="dt-tab" :class="{active: detailTab === 'summary'}" @click.stop="detailTab='summary'" v-if="task.result.summary">📝 总结</view>
            </view>

            <!-- 逐句文本 -->
            <view class="detail-content" v-if="detailTab === 'segments'">
              <view class="segment-row" v-for="(seg, i) in task.result.segments" :key="i">
                <text class="seg-time">{{ fmtTime(seg.start) }}</text>
                <text class="seg-text">{{ seg.text }}</text>
              </view>
              <view v-if="!task.result.segments || task.result.segments.length === 0">
                <text class="empty-detail">无转录内容</text>
              </view>
            </view>

            <!-- 纠错 -->
            <view class="detail-content" v-if="detailTab === 'corrected'">
              <text class="detail-text">{{ task.result.corrected_text }}</text>
            </view>

            <!-- 总结 -->
            <view class="detail-content" v-if="detailTab === 'summary'">
              <text class="detail-text" style="white-space:pre-line">{{ task.result.summary }}</text>
            </view>

            <!-- 导出按钮 -->
            <view class="export-bar">
              <button class="btn-export" @click.stop="exportTask(task.task_id, 'txt')">📄 TXT</button>
              <button class="btn-export" @click.stop="exportTask(task.task_id, 'srt')">📝 SRT</button>
              <button class="btn-export" @click.stop="exportTask(task.task_id, 'json')">📋 JSON</button>
            </view>
          </template>

          <!-- 运行中：显示详细状态 -->
          <view class="detail-loading" v-else-if="task.status !== 'failed'">
            <view class="loading-spinner"></view>
            <text>{{ task.message || statusText(task.status) }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
const API_BASE = 'https://ai4u.site/api';

export default {
  data() {
    return {
      tasks: [],
      loading: false,
      expandedId: null,
      detailTab: 'segments',
      pollTimers: {}
    }
  },
  onLoad() {
    this.loadTasks();
  },
  onShow() {
    this.loadTasks();
    // 启动全局轮询
    if (!this._globalPoll) {
      this._globalPoll = setInterval(() => this.loadTasks(), 3000);
    }
  },
  onHide() {
    if (this._globalPoll) {
      clearInterval(this._globalPoll);
      this._globalPoll = null;
    }
  },
  onUnload() {
    if (this._globalPoll) {
      clearInterval(this._globalPoll);
      this._globalPoll = null;
    }
    // 清除所有单个任务轮询
    Object.values(this.pollTimers).forEach(t => clearInterval(t));
    this.pollTimers = {};
  },
  methods: {
    async loadTasks() {
      try {
        const res = await uni.request({ url: `${API_BASE}/tasks?limit=50`, method: 'GET' });
        if (res.statusCode === 200 && Array.isArray(res.data)) {
          this.tasks = res.data;
          this.startRunningPoll();
        }
      } catch (e) {
        console.error('加载任务失败:', e);
      }
    },

    // 对运行中的任务发起单个轮询（实时更新进度和结果）
    startRunningPoll() {
      const runningTasks = this.tasks.filter(t =>
        ['queued', 'downloading', 'transcribing', 'processing'].includes(t.status)
      );
      const currentIds = new Set(runningTasks.map(t => t.task_id));
      // 清除已完成的轮询
      Object.keys(this.pollTimers).forEach(id => {
        if (!currentIds.has(id)) {
          clearInterval(this.pollTimers[id]);
          delete this.pollTimers[id];
        }
      });
      // 为新任务创建轮询
      runningTasks.forEach(t => {
        if (!this.pollTimers[t.task_id]) {
          this.pollTimers[t.task_id] = setInterval(() => this.pollTask(t.task_id), 3000);
        }
      });
    },

    async pollTask(taskId) {
      try {
        const res = await uni.request({ url: `${API_BASE}/task/${taskId}`, method: 'GET' });
        if (res.statusCode === 200 && res.data) {
          const idx = this.tasks.findIndex(t => t.task_id === taskId);
          if (idx !== -1) {
            this.$set(this.tasks, idx, res.data);
            // 完成后停止轮询
            if (['completed', 'failed'].includes(res.data.status)) {
              if (this.pollTimers[taskId]) {
                clearInterval(this.pollTimers[taskId]);
                delete this.pollTimers[taskId];
              }
            }
          }
        }
      } catch (e) {
        console.error('轮询任务失败:', taskId, e);
      }
    },

    toggleDetail(task) {
      if (this.expandedId === task.task_id) {
        this.expandedId = null;
      } else {
        this.expandedId = task.task_id;
        this.detailTab = 'segments';
        // 如果展开的是运行中的任务，确保在轮询
        if (['queued', 'downloading', 'transcribing', 'processing'].includes(task.status) && !this.pollTimers[task.task_id]) {
          this.pollTimers[task.task_id] = setInterval(() => this.pollTask(task.task_id), 3000);
        }
      }
    },

    statusText(status) {
      const map = {
        'queued': '排队中',
        'downloading': '下载中',
        'transcribing': '转录中',
        'processing': 'AI处理中',
        'completed': '已完成',
        'failed': '失败'
      };
      return map[status] || status;
    },

    shortUrl(url) {
      if (!url) return '';
      if (url.startsWith('upload://')) return url.replace('upload://', '📤 ');
      return url.length > 50 ? url.slice(0, 50) + '...' : url;
    },

    fmtTime(seconds) {
      const m = Math.floor(seconds / 60);
      const s = Math.floor(seconds % 60);
      return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    },

    truncate(text, len) {
      if (!text) return '';
      return text.length > len ? text.slice(0, len) + '...' : text;
    },

    exportTask(taskId, fmt) {
      const url = `${API_BASE.replace('/api', '')}/api/export/${taskId}?fmt=${fmt}`;
      uni.setClipboardData({
        data: url,
        success: () => uni.showToast({ title: '下载链接已复制到剪贴板', icon: 'success' }),
        fail: () => {
          // 回退：直接打开
          uni.navigateTo({ url: '/pages/webview/webview?url=' + encodeURIComponent(url) });
        }
      });
    }
  }
}
</script>

<style>
.container {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 120rpx;
}
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40rpx 0;
  text-align: center;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #ffffff;
}
.refresh-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 30rpx;
  background: #ffffff;
  margin-bottom: 20rpx;
}
.refresh-text { font-size: 26rpx; color: #666; }
.refresh-btn { padding: 12rpx 24rpx; background: #f0f0f0; border-radius: 8rpx; }
.refresh-btn text { font-size: 26rpx; color: #667eea; }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 120rpx 0; }
.empty-icon { font-size: 120rpx; margin-bottom: 30rpx; }
.empty-text { font-size: 32rpx; color: #333; margin-bottom: 16rpx; }
.empty-hint { font-size: 26rpx; color: #999; }
.loading-spinner-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
  gap: 20rpx;
  color: #999;
  font-size: 28rpx;
}
.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid #e0e0e0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.task-list { padding: 0 30rpx; }
.task-item {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
}
.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.task-title { font-size: 28rpx; font-weight: 600; color: #333; flex: 1; margin-right: 16rpx; overflow: hidden; }
.task-id { font-size: 26rpx; font-weight: 600; color: #667eea; }
.task-status {
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  font-weight: 500;
  white-space: nowrap;
}
.task-source { display: block; font-size: 22rpx; color: #999; margin-bottom: 16rpx; }
.status-queued { background: #fff3cd; color: #856404; }
.status-downloading { background: #cce5ff; color: #004085; }
.status-transcribing { background: #cce5ff; color: #004085; }
.status-processing { background: #d1ecf1; color: #0c5460; }
.status-completed { background: #d4edda; color: #155724; }
.status-failed { background: #f8d7da; color: #721c24; }
.progress-bar {
  width: 100%; height: 8rpx;
  background: #e0e0e0;
  border-radius: 4rpx;
  overflow: hidden;
  margin-bottom: 12rpx;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s;
}
.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
  color: #999;
}
.error-msg { margin-top: 12rpx; padding: 16rpx; background: #fff0f0; border-radius: 8rpx; }
.error-msg text { font-size: 24rpx; color: #dc3545; }

/* ====== 详情展开 ====== */
.detail-section {
  margin-top: 24rpx;
  border-top: 2rpx solid #eee;
  padding-top: 20rpx;
}
.detail-tabs {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
  flex-wrap: wrap;
}
.dt-tab {
  padding: 12rpx 24rpx;
  background: #f0f0f0;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: #666;
}
.dt-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
.detail-content {
  max-height: 600rpx;
  overflow-y: auto;
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 20rpx;
}
.segment-row {
  display: flex;
  gap: 16rpx;
  padding: 8rpx 0;
  border-bottom: 1rpx solid #eee;
}
.segment-row:last-child { border-bottom: none; }
.seg-time {
  font-size: 22rpx;
  color: #667eea;
  white-space: nowrap;
  font-family: monospace;
  min-width: 80rpx;
}
.seg-text { font-size: 26rpx; color: #333; flex: 1; }
.detail-text { font-size: 26rpx; color: #333; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.empty-detail { font-size: 26rpx; color: #999; text-align: center; padding: 40rpx; }

.detail-loading {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 30rpx;
  justify-content: center;
  color: #666;
  font-size: 26rpx;
}
.detail-loading .loading-spinner {
  width: 32rpx; height: 32rpx;
}

.export-bar {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
}
.btn-export {
  flex: 1;
  padding: 16rpx;
  background: #f0f0f0;
  border: 2rpx solid #e0e0e0;
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #667eea;
  text-align: center;
}
</style>
