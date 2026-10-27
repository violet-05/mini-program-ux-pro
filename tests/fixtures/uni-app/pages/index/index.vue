<template>
  <view class="page">
    <view v-if="loading" class="state">加载中</view>
    <view v-else-if="error" class="state">加载失败，点击重试</view>
    <view v-else-if="!items.length" class="state">暂无内容</view>
    <text v-else class="title">uni-app fixture</text>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const loading = ref(true)
const error = ref(false)
const items = ref([])

onLoad(() => {
  loading.value = false
})
</script>

<style>
.page {
  padding: 32rpx;
}
.title {
  font-size: 30rpx;
}
.state {
  min-height: 88rpx;
}
</style>