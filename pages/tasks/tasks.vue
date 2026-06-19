<template>
  <view class="container">
    <!-- 头部 -->
    <view class="header">
      <text class="title">转录任务</text>
    </view>

    <!-- 刷新按钮 -->
    <view class="refresh-bar">
      <text class="refresh-text">共 {{ tasks.length }} 个任务</text>
      <view class="refresh-btn" @click="loadTasks">
        <text>🔄 刷新</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty-state" v-if="tasks.length === 0">
      <text class="empty-icon">📋</text>
      <text class="empty-text">暂无转录任务</text>
      <text class="empty-hint">去首页创建新任务吧</text>
    </view>

    <!-- 任务列表 -->
    <view class="task-list" v-else>
      <view 
        class="task-item" 
        v-for="task in tasks" 
        :key="task.id"
        @click="showTaskDetail(task)"
      >
        <!-- 任务头部 -->
        <view class="task-header">
          <text class="task-id">#{{ task.id.slice(0, 8) }}</text>
          <text class="task-status" :class="'status-' + task.status">
            {{ statusText(task.status) }}
          </text>
        </view>

        <!-- 进度条 -->
        <view class="progress-bar">
          <view class="progress-fill" :style="{width: task.progress + '%'}"></view>
        </view>

        <!-- 进度文字 -->
        <view class="progress-text">
          <text>进度: {{ task.progress }}%</text>
          <text>{{ task.created_at || '' }}</text>
        </view>

        <!-- 错误信息 -->
        <view class="error-msg" v-if="task.error_msg">
          <text>⚠️ {{ task.error_msg }}</text>
        </view>

        <!-- 完成结果 -->
        <view class="result-actions" v-if="task.status === 'completed'">
          <button class="btn-action" @click.stop="viewTranscript(task.id)">
            📄 查看转录
          </button>
          <button class="btn-action" @click.stop="viewSummary(task)" v-if="task.summary">
            📝 AI总结
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      tasks: [],
      loading: false,
      polling: false,
      API_BASE: 'https://ai4u.site/api'
    }
  },
  onLoad() {
    // 从本地存储读取 API 配置
    const savedApi = uni.getStorageSync('api_base');
    if (savedApi) {
      this.API_BASE = savedApi;
    }
    this.loadTasks();
  },
  onShow() {
    // 每次显示页面时刷新任务
    this.loadTasks();
    // 启动轮询
    if (!this.polling) {
      this.startPolling();
    }
  },
  onHide() {
    // 页面隐藏时停止轮询
    this.stopPolling();
  },
  onUnload() {
    this.stopPolling();
  },
  methods: {
    async loadTasks() {
      try {
        const response = await uni.request({
          url: `${this.API_BASE}/tasks`,
          method: 'GET'
        });

        if (response.data.tasks) {
          this.tasks = response.data.tasks.reverse();
        }
      } catch (e) {
        console.error('加载任务失败:', e);
        // 可以显示提示但不影响用户体验
      }
    },

    startPolling() {
      this.polling = true;
      this.pollTimer = setInterval(() => {
        this.loadTasks();
        
        // 检查是否有正在运行的任务
        const hasRunning = this.tasks.some(t => 
          ['pending', 'downloading', 'transcribing', 'correcting'].includes(t.status)
        );
        
        if (!hasRunning) {
          // 没有运行中的任务，可以减少轮询频率
          // 这里暂时继续轮询，用户可能同时开多个任务
        }
      }, 3000);
    },

    stopPolling() {
      this.polling = false;
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    },

    statusText(status) {
      const map = {
        'pending': '等待中',
        'downloading': '下载中',
        'transcribing': '转录中',
        'correcting': 'AI处理中',
        'completed': '已完成',
        'error': '失败',
      };
      return map[status] || status;
    },

    showTaskDetail(task) {
      uni.showModal({
        title: '任务详情',
        content: `任务ID: ${task.id}\n状态: ${this.statusText(task.status)}\n进度: ${task.progress}%\n${task.error_msg ? '错误: ' + task.error_msg : ''}`,
        showCancel: false
      });
    },

    viewTranscript(taskId) {
      // 打开转录结果
      const url = `${this.API_BASE.replace('/api', '')}/outputs/${taskId}.txt`;
      uni.navigateTo({
        url: `/pages/webview/webview?url=${encodeURIComponent(url)}`
      });
    },

    viewSummary(task) {
      // 显示 AI 总结
      uni.showModal({
        title: '📝 AI 总结',
        content: task.summary || '暂无总结',
        showCancel: false
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

.refresh-text {
  font-size: 26rpx;
  color: #666666;
}

.refresh-btn {
  padding: 12rpx 24rpx;
  background: #f0f0f0;
  border-radius: 8rpx;
}

.refresh-btn text {
  font-size: 26rpx;
  color: #667eea;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 30rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333333;
  margin-bottom: 16rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #999999;
}

.task-list {
  padding: 0 30rpx;
}

.task-item {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.task-id {
  font-size: 28rpx;
  font-weight: 600;
  color: #667eea;
}

.task-status {
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
  font-weight: 500;
}

.status-pending { background: #fff3cd; color: #856404; }
.status-downloading { background: #cce5ff; color: #004085; }
.status-transcribing { background: #cce5ff; color: #004085; }
.status-correcting { background: #cce5ff; color: #004085; }
.status-completed { background: #d4edda; color: #155724; }
.status-error { background: #f8d7da; color: #721c24; }

.progress-bar {
  width: 100%;
  height: 8rpx;
  background: #e0e0e0;
  border-radius: 4rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
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
  color: #999999;
}

.error-msg {
  margin-top: 16rpx;
  padding: 16rpx;
  background: #fff0f0;
  border-radius: 8rpx;
}

.error-msg text {
  font-size: 24rpx;
  color: #dc3545;
}

.result-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 20rpx;
}

.btn-action {
  flex: 1;
  padding: 20rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border: none;
  border-radius: 8rpx;
  font-size: 26rpx;
  text-align: center;
}
</style>