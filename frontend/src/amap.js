const AMAP_KEY = import.meta.env.VITE_AMAP_KEY;
const AMAP_SECURITY_CODE = import.meta.env.VITE_AMAP_SECURITY_CODE;
const AMAP_VERSION = import.meta.env.VITE_AMAP_VERSION || "2.0";

let loaderPromise = null;

export function loadAMap() {
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }

  if (!AMAP_KEY) {
    return Promise.reject(new Error("未配置 VITE_AMAP_KEY，无法加载高德地图。"));
  }

  if (!loaderPromise) {
    loaderPromise = new Promise((resolve, reject) => {
      if (AMAP_SECURITY_CODE) {
        window._AMapSecurityConfig = {
          securityJsCode: AMAP_SECURITY_CODE,
        };
      }

      const script = document.createElement("script");
      script.async = true;
      script.src = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${AMAP_KEY}`;
      script.onload = () => {
        if (window.AMap) {
          resolve(window.AMap);
        } else {
          reject(new Error("高德地图加载失败。"));
        }
      };
      script.onerror = () => reject(new Error("高德地图加载失败。"));
      document.head.appendChild(script);
    });
  }

  return loaderPromise;
}
