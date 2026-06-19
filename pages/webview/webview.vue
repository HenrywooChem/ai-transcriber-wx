<template>
  <view class="container">
    <web-view :src="webUrl"></web-view>
  </view>
</template>

<script>
export default {
  data() {
    return { webUrl: '' }
  },
  onLoad(options) {
    if (options.url) {
      this.webUrl = decodeURIComponent(options.url);
    }
  }
}
</script>
<style>
.container { min-height: 100vh; }
</style>
