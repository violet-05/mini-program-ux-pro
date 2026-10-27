const queue = [
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
    track: queue[0],
    queue,
    isPlaying: false,
    isFavorite: false,
    showLyrics: true,
    showQueue: false,
    progress: 42,
    currentTime: '1:33',
    duration: '3:42',
    statusBarHeight: 20,
    navContentHeight: 44,
    capsuleReserve: 0
  },

  onLoad(options) {
    const trackId = options && options.track
    const track = queue.find((item) => item.id === trackId) || queue[0]

    let windowInfo = { statusBarHeight: 20, windowWidth: 375 }
    try {
      windowInfo = wx.getWindowInfo()
    } catch (error) {
      // Older base libraries may not provide getWindowInfo; conservative fallbacks keep the nav usable.
    }

    let menu = null
    try {
      menu = wx.getMenuButtonBoundingClientRect()
    } catch (error) {
      menu = null
    }

    const statusBarHeight = windowInfo.statusBarHeight || 20
    const menuTop = menu && menu.top ? menu.top : statusBarHeight + 4
    const menuHeight = menu && menu.height ? menu.height : 32
    const navContentHeight = Math.max(44, menuHeight + Math.max(0, menuTop - statusBarHeight) * 2)
    const capsuleReserve = menu && menu.left
      ? Math.max(8, windowInfo.windowWidth - menu.left + 8)
      : 96

    this.setData({
      track,
      statusBarHeight,
      navContentHeight,
      capsuleReserve
    })
  },

  back() {
    const pages = getCurrentPages()
    if (pages.length > 1) {
      wx.navigateBack()
      return
    }
    wx.reLaunch({ url: '/pages/home/index' })
  },

  togglePlay() {
    this.setData({ isPlaying: !this.data.isPlaying })
  },

  toggleFavorite() {
    this.setData({ isFavorite: !this.data.isFavorite })
  },

  toggleLyrics() {
    this.setData({ showLyrics: !this.data.showLyrics })
  },

  openQueue() {
    this.setData({ showQueue: true })
  },

  closeQueue() {
    this.setData({ showQueue: false })
  },

  noop() {},

  onShareAppMessage() {
    return {
      title: `${this.data.track.title} · 夜航`,
      path: `/pages/player/index?track=${encodeURIComponent(this.data.track.id)}`
    }
  }
})