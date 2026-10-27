const tracks = [
  {
    id: 'night-flight',
    title: '夜航',
    artist: '林屿',
    album: '潮汐之后',
    duration: '3:42'
  },
  {
    id: 'slow-tide',
    title: '慢潮',
    artist: '周野',
    album: '低空飞行',
    duration: '4:08'
  },
  {
    id: 'window-light',
    title: '窗边灯',
    artist: '未命名乐队',
    album: '小房间现场',
    duration: '3:16'
  }
]

Page({
  data: {
    loading: true,
    demoState: 'normal',
    tracks
  },

  onLoad(options) {
    const requestedState = options && (options.demo === 'error' || options.demo === 'empty')
      ? options.demo
      : 'normal'

    if (requestedState !== 'normal') {
      this.setData({ loading: false, demoState: requestedState })
      return
    }

    this._loadTimer = setTimeout(() => {
      this.setData({ loading: false })
    }, 420)
  },

  onUnload() {
    if (this._loadTimer) {
      clearTimeout(this._loadTimer)
      this._loadTimer = null
    }
  },

  retry() {
    this.setData({ loading: true, demoState: 'normal' })
    this._loadTimer = setTimeout(() => {
      this.setData({ loading: false })
    }, 520)
  },

  resetState() {
    this.setData({ demoState: 'normal', loading: false })
  },

  openPlayer() {
    wx.navigateTo({ url: '/pages/player/index?track=night-flight' })
  },

  openTrack(event) {
    const id = event.currentTarget.dataset.id || 'night-flight'
    wx.navigateTo({ url: `/pages/player/index?track=${encodeURIComponent(id)}` })
  },

  onShareAppMessage() {
    return {
      title: '夜航 · 今晚听见自己的节奏',
      path: '/pages/home/index'
    }
  }
})