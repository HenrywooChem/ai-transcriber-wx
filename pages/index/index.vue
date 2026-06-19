<template>
  <view class="container">
    <!-- 头部 -->
    <view class="header">
      <text class="title">AI Transcriber</text>
      <text class="subtitle">智能转录助手</text>
    </view>

    <!-- ====== 未登录：显示登录/注册 ====== -->
    <view class="card" v-if="!isLoggedIn">
      <view class="auth-tabs">
        <view class="auth-tab" :class="{active: authMode === 'login'}" @click="authMode='login'">登录</view>
        <view class="auth-tab" :class="{active: authMode === 'register'}" @click="authMode='register'">注册</view>
      </view>

      <view class="input-group">
        <text class="label">用户名</text>
        <input class="input" v-model="authUser" placeholder="请输入用户名" @confirm="doAuth" />
      </view>
      <view class="input-group">
        <text class="label">密码</text>
        <input class="input" v-model="authPass" type="text" password placeholder="请输入密码" @confirm="doAuth" />
      </view>
      <view class="input-group" v-if="authMode === 'register'">
        <text class="label">确认密码</text>
        <input class="input" v-model="authConfirm" type="text" password placeholder="再次输入密码" @confirm="doAuth" />
      </view>
      <button class="btn-primary" :disabled="authLoading || !authUser || !authPass" @click="doAuth">
        {{ authLoading ? '处理中...' : (authMode === 'login' ? '登录' : '注册') }}
      </button>
      <view class="auth-error" v-if="authError">
        <text>⚠️ {{ authError }}</text>
      </view>
    </view>

    <!-- ====== 已登录：显示转录功能 ====== -->
    <template v-else>
      <!-- Tab 切换 -->
      <view class="tabs">
        <view class="tab-item" :class="{active: activeTab === 'url'}" @click="activeTab = 'url'">链接转录</view>
        <view class="tab-item" :class="{active: activeTab === 'file'}" @click="activeTab = 'file'">文件上传</view>
      </view>

      <!-- 链接输入 -->
      <view class="card" v-if="activeTab === 'url'">
        <view class="input-group">
          <text class="label">输入 B站 / YouTube 链接</text>
          <input class="input" v-model="videoUrl" placeholder="https://www.bilibili.com/video/BV...  或 https://youtu.be/..." @confirm="submitUrl" />
        </view>
        <button class="btn-primary" :disabled="!videoUrl || loading" @click="submitUrl">
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
        <button class="btn-primary" :disabled="!selectedFile || loading" @click="submitFile">
          {{ loading ? '上传中...' : '开始转录' }}
        </button>
      </view>

      <!-- 提示信息 -->
      <view class="tips" v-if="tips && !loading">
        <text class="tips-text">{{ tips }}</text>
      </view>

      <!-- 加载中动画 -->
      <view class="loading-bar" v-if="loading">
        <view class="loading-spinner"></view>
        <text class="loading-text">{{ loadingMsg }}</text>
      </view>
    </template>
  </view>
</template>

<script>
const STORAGE_KEY = 'wx_transcriber_token';
const USER_KEY = 'wx_transcriber_user';
const API_BASE = 'https://ai4u.site/api';

export default {
  data() {
    return {
      // 认证
      isLoggedIn: false,
      authToken: '',
      authMode: 'login',
      authUser: '',
      authPass: '',
      authConfirm: '',
      authLoading: false,
      authError: '',
      // 转录
      activeTab: 'url',
      videoUrl: '',
      selectedFile: null,
      loading: false,
      loadingMsg: '',
      tips: '',
    }
  },
  onLoad() {
    const token = uni.getStorageSync(STORAGE_KEY);
    if (token) {
      this.authToken = token;
      this.isLoggedIn = true;
    }
  },
  methods: {
    // ======== 认证 ========
    async doAuth() {
      if (!this.authUser || !this.authPass) return;
      if (this.authMode === 'register' && this.authPass !== this.authConfirm) {
        this.authError = '两次密码不一致';
        return;
      }
      if (this.authPass.length < 4) {
        this.authError = '密码至少4个字符';
        return;
      }
      this.authLoading = true;
      this.authError = '';
      try {
        const res = await uni.request({
          url: `${API_BASE}/auth/${this.authMode}`,
          method: 'POST',
          data: { username: this.authUser, password: this.authPass },
          header: { 'Content-Type': 'application/json' }
        });
        if (res.statusCode === 200 && res.data.token) {
          this.authToken = res.data.token;
          this.isLoggedIn = true;
          uni.setStorageSync(STORAGE_KEY, res.data.token);
          uni.setStorageSync(USER_KEY, res.data.username);
          uni.showToast({ title: this.authMode === 'login' ? '登录成功' : '注册成功', icon: 'success' });
        } else {
          this.authError = res.data.detail || (this.authMode === 'login' ? '登录失败' : '注册失败');
        }
      } catch (e) {
        this.authError = '网络错误，请检查服务器是否可用';
      } finally {
        this.authLoading = false;
      }
    },

    // ======== 文件选择 ========
    chooseFile() {
      uni.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['mp3', 'wav', 'm4a', 'ogg', 'mp4', 'avi', 'mov'],
        success: (res) => {
          this.selectedFile = res.tempFiles[0];
          this.tips = '已选择: ' + res.tempFiles[0].name;
        },
        fail: () => {
          // 回退到普通选择
          uni.chooseFile({
            count: 1,
            type: 'all',
            success: (res) => {
              this.selectedFile = res.tempFiles[0];
              this.tips = '已选择: ' + res.tempFiles[0].name;
            },
            fail: () => { this.tips = '请在微信内选择文件'; }
          });
        }
      });
    },

    // ======== URL转录 ========
    async submitUrl() {
      if (!this.videoUrl) return;
      // B站短链接检查
      const url = this.videoUrl.trim();
      if (!url.includes('bilibili.com') && !url.includes('b23.tv') && !url.includes('youtube.com') && !url.includes('youtu.be')) {
        uni.showToast({ title: '请输B站/YouTube链接', icon: 'none' });
        return;
      }

      this.loading = true;
      this.loadingMsg = '正在提交任务...';
      this.tips = '';

      try {
        const res = await uni.request({
          url: `${API_BASE}/transcribe/url`,
          method: 'POST',
          data: { url, use_llm: true },
          header: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + this.authToken }
        });

        if (res.statusCode === 200 && res.data.task_id) {
          uni.showToast({ title: '✅ 任务已提交', icon: 'success' });
          this.videoUrl = '';
          setTimeout(() => { uni.switchTab({ url: '/pages/tasks/tasks' }); }, 800);
        } else if (res.statusCode === 401) {
          this.handleAuthExpired();
        } else {
          throw new Error(res.data.detail || '提交失败');
        }
      } catch (e) {
        uni.showToast({ title: '失败: ' + (e.message || '网络错误'), icon: 'none' });
      } finally {
        this.loading = false;
      }
    },

    // ======== 文件上传转录 ========
    async submitFile() {
      if (!this.selectedFile) return;
      this.loading = true;
      this.loadingMsg = '正在上传文件...';
      this.tips = '';

      try {
        const uploadResult = await new Promise((resolve, reject) => {
          uni.uploadFile({
            url: `${API_BASE}/transcribe/upload`,
            filePath: this.selectedFile.path,
            name: 'file',
            formData: { use_llm: 'true' },
            header: { 'Authorization': 'Bearer ' + this.authToken },
            success: (res) => {
              const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
              if (data.task_id) resolve(data);
              else reject(new Error(data.detail || '上传失败'));
            },
            fail: reject
          });
        });

        uni.showToast({ title: '✅ 任务已提交', icon: 'success' });
        this.selectedFile = null;
        setTimeout(() => { uni.switchTab({ url: '/pages/tasks/tasks' }); }, 800);
      } catch (e) {
        if (e.message && e.message.includes('401')) {
          this.handleAuthExpired();
        } else {
          uni.showToast({ title: '上传失败: ' + (e.message || '网络错误'), icon: 'none' });
        }
      } finally {
        this.loading = false;
      }
    },

    handleAuthExpired() {
      this.isLoggedIn = false;
      this.authToken = '';
      this.authUser = '';
      uni.removeStorageSync(STORAGE_KEY);
      uni.removeStorageSync(USER_KEY);
      uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' });
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
  box-sizing: border-box;
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
.btn-primary[disabled] { opacity: 0.5; }
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 30rpx;
  border: 2rpx dashed #e0e0e0;
  border-radius: 12rpx;
  margin-bottom: 30rpx;
  background: #fafbfc;
}
.upload-icon { font-size: 80rpx; margin-bottom: 20rpx; }
.upload-text { font-size: 28rpx; color: #333333; margin-bottom: 12rpx; }
.upload-hint { font-size: 24rpx; color: #999999; }
.tips { text-align: center; padding: 20rpx; }
.tips-text { font-size: 26rpx; color: rgba(255, 255, 255, 0.9); }
.loading-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30rpx;
  gap: 16rpx;
}
.loading-spinner {
  width: 32rpx;
  height: 32rpx;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-size: 28rpx; color: #ffffff; }

/* 认证 */
.auth-tabs {
  display: flex;
  margin-bottom: 30rpx;
  border-bottom: 2rpx solid #e0e0e0;
}
.auth-tab {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  font-size: 30rpx;
  color: #999999;
  font-weight: 500;
}
.auth-tab.active {
  color: #667eea;
  border-bottom: 4rpx solid #667eea;
}
.auth-error {
  margin-top: 20rpx;
  padding: 16rpx;
  background: #fff0f0;
  border-radius: 8rpx;
  text-align: center;
}
.auth-error text { font-size: 26rpx; color: #dc3545; }
</style>
