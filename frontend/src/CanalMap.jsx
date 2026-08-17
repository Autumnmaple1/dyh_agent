import { useEffect, useMemo, useRef, useState } from "react";
import { loadAMap } from "./amap";
import { CANAL_ROUTE, MAP_CHARACTERS, MAP_PALETTE } from "./mapData";

function markerContent(character, meta, selected) {
  return `<span class="canal-marker${selected ? " is-selected" : ""}">
    <span class="marker-portrait"><img src="${meta.portrait}" alt="" /></span>
    <span class="marker-copy"><b>${character.name}</b><small>${character.city}</small></span>
  </span>`;
}

function useIsCompactMap() {
  const [isCompact, setIsCompact] = useState(() => window.matchMedia("(max-width: 760px)").matches);

  useEffect(() => {
    const query = window.matchMedia("(max-width: 760px)");
    const handler = (event) => setIsCompact(event.matches);
    query.addEventListener("change", handler);
    return () => query.removeEventListener("change", handler);
  }, []);

  return isCompact;
}

export default function CanalMap({ characters, selectedId, onSelect }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerMapRef = useRef(new Map());
  const lineRef = useRef([]);
  const hasFitRef = useRef(false);
  const fitSignatureRef = useRef("");
  const onSelectRef = useRef(onSelect);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);
  const isCompact = useIsCompactMap();

  const items = useMemo(
    () =>
      characters
        .map((character) => ({ character, meta: MAP_CHARACTERS[character.id] }))
        .filter((item) => item.meta),
    [characters],
  );

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    let disposed = false;

    loadAMap()
      .then((AMap) => {
        if (disposed || !containerRef.current) return;
        const map = new AMap.Map(containerRef.current, {
          zoom: 5,
          center: [117.5, 32.3],
          zooms: [5, 13],
          mapStyle: "amap://styles/whitesmoke",
        });
        mapRef.current = map;
        setReady(true);
      })
      .catch((reason) => {
        if (!disposed) setError(reason.message || "高德地图加载失败。");
      });

    return () => {
      disposed = true;
      if (mapRef.current) {
        mapRef.current.destroy();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const AMap = window.AMap;
    if (!map || !AMap || !ready) return undefined;

    for (const marker of markerMapRef.current.values()) marker.setMap(null);
    markerMapRef.current.clear();
    for (const line of lineRef.current) line.setMap(null);
    lineRef.current = [];

    const overlays = [];
    for (const { character, meta } of items) {
      const selected = character.id === selectedId;
      const marker = new AMap.Marker({
        position: meta.position,
        content: markerContent(character, meta, selected),
        offset: new AMap.Pixel(-29, -29),
        zIndex: selected ? 800 : 100,
        title: `${character.name}：${meta.siteName}`,
      });
      marker.on("click", () => onSelectRef.current?.(character.id));
      marker.setMap(map);
      markerMapRef.current.set(character.id, marker);
      overlays.push(marker);
    }

    if (CANAL_ROUTE.length) {
      const outline = new AMap.Polyline({
        path: CANAL_ROUTE,
        strokeColor: MAP_PALETTE.routeOutline,
        strokeWeight: 18,
        strokeOpacity: 0.96,
        lineJoin: "round",
        lineCap: "round",
      });
      const main = new AMap.Polyline({
        path: CANAL_ROUTE,
        strokeColor: MAP_PALETTE.routeMain,
        strokeWeight: 5,
        strokeOpacity: 0.92,
        lineJoin: "round",
        lineCap: "round",
      });
      const flow = new AMap.Polyline({
        path: CANAL_ROUTE,
        strokeColor: MAP_PALETTE.routeFlow,
        strokeWeight: 1.5,
        strokeOpacity: 0.35,
        strokeStyle: "dashed",
        lineJoin: "round",
        lineCap: "round",
      });
      [outline, main, flow].forEach((line) => {
        line.setMap(map);
        lineRef.current.push(line);
      });
    }

    const bottomInset = isCompact
      ? Math.ceil(12 + (document.querySelector(".character-inspector")?.getBoundingClientRect().height || 192) + 18)
      : 50;
    const avoid = isCompact ? [24, bottomInset, 16, 16] : [50, 50, 50, 50];
    const fitSignature = `${items.length}-${isCompact ? "compact" : "wide"}`;
    const fitChanged = fitSignature !== fitSignatureRef.current;
    fitSignatureRef.current = fitSignature;

    if (fitChanged || !hasFitRef.current) {
      if (overlays.length) {
        map.setFitView(overlays, false, avoid, 13);
      }
      hasFitRef.current = true;
    } else {
      const selected = MAP_CHARACTERS[selectedId];
      if (selected) map.setZoomAndCenter(7, selected.position, false, 400);
    }

    return undefined;
  }, [ready, items, selectedId, isCompact]);

  function zoom(delta) {
    const map = mapRef.current;
    if (!map) return;
    if (delta > 0) map.zoomIn();
    else map.zoomOut();
  }

  return (
    <div className="map-stage" aria-label="大运河人物地点地图">
      <div ref={containerRef} className="amap-map" />
      <div className="map-zoom" aria-hidden="true">
        <button type="button" onClick={() => zoom(1)} aria-label="放大地图">+</button>
        <button type="button" onClick={() => zoom(-1)} aria-label="缩小地图">−</button>
      </div>
      <div className="map-wash" aria-hidden="true" />
      {error ? (
        <div className="map-error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => window.location.reload()}>重试</button>
        </div>
      ) : null}
    </div>
  );
}
