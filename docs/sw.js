// 极简 service worker：只为满足「可安装」条件，不做缓存，避免看到旧课表。
self.addEventListener("install", function () {
  self.skipWaiting();
});
self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});
self.addEventListener("fetch", function () {
  // 全部走网络
});
