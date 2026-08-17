export const MAP_PALETTE = {
  routeOutline: "#efe6d5",
  routeMain: "#2c5e5a",
  routeFlow: "#7fa8a3",
};

export const MAP_CHARACTERS = {
  "su-shi-xuzhou": {
    portrait: "/static/assets/su-shi.webp",
    siteName: "黄楼公园",
    address: "江苏省徐州市鼓楼区黄河南路",
    position: [117.1818754, 34.2728792],
  },
  "chen-xuan-huaian": {
    portrait: "/static/assets/chen-xuan.webp",
    siteName: "陈瑄二公祠",
    address: "江苏省淮安市清江浦区轮埠路里运河畔",
    position: [119.0363, 33.595],
  },
  "zhang-boxing-suzhou": {
    portrait: "/static/assets/zhang-boxing.webp",
    siteName: "江苏巡抚衙门旧址",
    address: "江苏省苏州市姑苏区书院巷20号",
    position: [120.6177386, 31.299801],
  },
};

export const CANAL_ROUTE = [
  MAP_CHARACTERS["su-shi-xuzhou"].position,
  [118.3, 34.0],
  MAP_CHARACTERS["chen-xuan-huaian"].position,
  [119.42, 32.4],
  [119.43, 32.19],
  [120.28, 31.58],
  MAP_CHARACTERS["zhang-boxing-suzhou"].position,
];

export const MAP_BOUNDS = [
  [116.55, 30.05],
  [121.05, 34.55],
];
