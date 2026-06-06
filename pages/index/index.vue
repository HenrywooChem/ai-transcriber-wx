<template>
  <view class="container">
    <!-- 头部 -->
    <view class="header">
      <text class="title">AI Transcriber</text>
      <text class="subtitle">智能转录助手</text>
    </view>

    <!-- Tab 切换 -->
    <view class="tabs">
      <view 
        class="tab-item" 
        :class="{active: activeTab === 'url'}"
        @click="activeTab = 'url'"
      >
        链接转录
      </view>
      <view 
        class="tab-item" 
        :class="{active: activeTab === 'file'}"
        @click="activeTab = 'file'"
      >
        文件上传
      </view>
    </view>

    <!-- 链接输入 -->
    <view class="card" v-if="activeTab === 'url'">
      <view class="input-group">
        <text class="label">输入 B站 / YouTube 链接</text>
        <input 
          class="input" 
          v-model="videoUrl" 
          placeholder="https://www.bilibili.com/video/BV... 或 https://www.youtube.com/watch?v=..."
          @confirm="submitUrl"
        />
      </view>
      <button 
        class="btn-primary" 
        :disabled="!videoUrl || loading"
        @click="submitUrl"
      >
        {{ loading ? '提交中...' : '开始转录' }}
      </button>
    </view>

    <!-- 文件上传 -->
    <view class="card" v-if="activeTab === 'file'">
      <view class="upload-area" @click="chooseFile">
        <text class="upload-icon">🎵</text>
        <text class="upload-text">{{ selectedFile ? selectedFile.name : '点击选择音频/视频文件' }}</text>
        <text class="upload-hint">支持 mp3, wav, m4a, mp4 等格式</text>
      </view>
      <button 
        class="btn-primary" 
        :disabled="!selectedFile || loading"
        @click="submitFile"
      >
        {{ loading ? '上传中...' : '开始转录' }}
      </button>
    </view>

    <!-- 提示信息 -->
    <view class="tips" v-if="tips">
      <text class="tips-text">{{ tips }}</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      activeTab: 'url',
      videoUrl: '',
      selectedFile: null,
      loading: false,
      tips: '',
      // API 配置 - 请根据实际部署修改
      API_BASE: 'http://124.221.77.205:8001/api'
    }
  },
  onLoad() {
    // 从本地存储读取 API 配置
    const savedApi = uni.getStorageSync('api_base');
    if (savedApi) {
      this.API_BASE = savedApi;
    }
  },
  methods: {
    chooseFile() {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['mp3', 'wav', 'm4a', 'ogg', 'mp4', 'avi', 'mov'],
        success: (res) => {
          this.selectedFile = res.tempFiles[0];
          this.tips = '已选择: ' + res.tempFiles[0].name;
        },
        fail: (err) => {
          // 如果微信文件选择失败，尝试普通文件选择
          uni.chooseFile({
            count: 1,
            type: 'all',
            success: (res) => {
              this.selectedFile = res.tempFiles[0];
              this.tips = '已选择: ' + res.tempFiles[0].name;
            },
            fail: () => {
              this.tips = '请使用微信小程序内选择文件';
            }
          });
        }
      });
    },

    async submitUrl() {
      if (!this.videoUrl) return;
      
      // 简单的 URL 验证
      if (!this.videoUrl.includes('bilibili.com') && !this.videoUrl.includes('youtube.com')) {
        uni.showToast({ title: '请输入 B站 或 YouTube 链接', icon: 'none' });
        return;
      }

      this.loading = true;
      this.tips = '正在提交任务...';

      try {
        const response = await uni.request({
          url: `${this.API_BASE}/transcribe/url`,
          method: 'POST',
          data: { url: this.videoUrl },
          header: { 'Content-Type': 'application/json' }
        });

        if (response.data.task_id) {
          uni.showToast({ title: '任务创建成功！', icon: 'success' });
          this.videoUrl = '';
          // 跳转到任务列表
          setTimeout(() => {
            uni.switchTab({ url: '/pages/tasks/tasks' });
          }, 1000);
        } else {
          throw new Error(response.data.error || '提交失败');
        }
      } catch (e) {
        uni.showToast({ title: '提交失败: ' + (e.message || '网络错误'), icon: 'none' });
      } finally {
        this.loading = false;
      }
    },

    async submitFile() {
      if (!this.selectedFile) return;

      this.loading = true;
      this.tips = '正在上传文件...';

      try {
        // 小程序上传需要用 uploadFile
        const uploadResult = await new Promise((resolve, reject) => {
          const uploadTask = uni.uploadFile({
            url: `${this.API_BASE}/transcribe/upload`,
            filePath: this.selectedFile.path,
            name: 'file',
            success: (res) => {
              const data = JSON.parse(res.data);
              if (data.task_id) {
                resolve(data);
              } else {
                reject(new Error(data.error || '上传失败'));
              }
            },
            fail: reject
          });
        });

        uni.showToast({ title: '任务创建成功！', icon: 'success' });
        this.selectedFile = null;
        setTimeout(() => {
          uni.switchTab({ url: '/pages/tasks/tasks' });
        }, 1000);
      } catch (e) {
        uni.showToast({ title: '上传失败: ' + (e.message || '网络错误'), icon: 'none' });
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style>
.container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 60rpx 0 40rpx;
}

.title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 16rpx;
}

.subtitle {
  display: block;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
}

.tabs {
  display: flex;
  background: #ffffff;
  border-radius: 16rpx;
  margin: 0 20rpx 30rpx;
  padding: 8rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 24rpx 0;
  font-size: 28rpx;
  color: #666666;
  border-radius: 12rpx;
  transition: all 0.3s;
}

.tab-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  font-weight: 600;
}

.card {
  background: #ffffff;
  border-radius: 24rpx;
  margin: 0 20rpx 30rpx;
  padding: 40rpx;
  box-shadow: 0 8rpx 30rpx rgba(0, 0, 0, 0.1);
}

.input-group {
  margin-bottom: 30rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #333333;
  font-weight: 500;
  margin-bottom: 16rpx;
}

.input {
  width: 100%;
  padding: 24rpx;
  border: 2rpx solid #e0e0e0;
  border-radius: 12rpx;
  font-size: 28rpx;
  background: #f8f9fa;
}

.btn-primary {
  width: 100%;
  padding: 28rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border: none;
  border-radius: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
}

.btn-primary[disabled] {
  opacity: 0.5;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 30rpx;
  border: 2rpx dashed #e0e0e0;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
}

.upload-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.upload-text {
  font-size: 28rpx;
  color: #333333;
  margin-bottom: 12rpx;
}

.upload-hint {
  font-size: 24rpx;
  color: #999999;
}

.tips {
  text-align: center;
  padding: 20rpx;
}

.tips-text {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}
</style>