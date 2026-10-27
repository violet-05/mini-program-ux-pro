Page({
  data: {
    items: [{ id: 1, name: '测试商品' }],
    userToken: ''
  },
  onLoad() {
    localStorage.setItem('token', 'demo');
    const info = wx.getSystemInfoSync();
    this.setData({ statusBarHeight: info.statusBarHeight });
    wx.getLocation({ type: 'wgs84', success: () => {} });
  },
  go() {
    const el = document.querySelector('.title');
    if (el) el.style.color = '#123456';
  }
});