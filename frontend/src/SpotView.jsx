import { useEffect, useRef, useState } from "react";
import { X } from "@phosphor-icons/react";
import { loadAMap } from "./amap";

function SpotMiniMap({ position }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let disposed = false;

    loadAMap()
      .then((AMap) => {
        if (disposed || !containerRef.current) return;
        const map = new AMap.Map(containerRef.current, {
          zoom: 14,
          center: position,
          zooms: [14, 14],
          dragEnable: false,
          scrollWheel: false,
          doubleClickZoom: false,
          keyboardEnable: false,
          touchZoom: false,
          mapStyle: "amap://styles/whitesmoke",
        });
        mapRef.current = map;

        const marker = new AMap.Marker({
          position,
          content: '<div class="spot-pin"><span class="spot-pin-dot"></span></div>',
          offset: new AMap.Pixel(-9, -9),
        });
        marker.setMap(map);
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
  }, [position]);

  if (error) {
    return <div className="spot-map spot-map-error">{error}</div>;
  }

  return <div ref={containerRef} className="spot-map" />;
}

function SpotImage({ src, alt }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <div className="spot-image placeholder">{alt}</div>;
  }
  return (
    <img
      className="spot-image"
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

function SpotPhotos({ spot }) {
  if (!spot.images?.length) {
    return <div className="spot-photos-empty">实景图待补充</div>;
  }
  return (
    <div className="spot-photos">
      {spot.images.map((src, index) => (
        <SpotImage key={src} src={src} alt={`${spot.name}实景 ${index + 1}`} />
      ))}
    </div>
  );
}

export function SpotPanel({ spot, onClose }) {
  return (
    <aside className="spot-panel surface">
      <div className="spot-panel-head">
        <div>
          <span className="spot-kicker">当前景点</span>
          <h3>{spot.name}</h3>
          <p>{spot.city} · {spot.address}</p>
        </div>
        <button className="spot-close" type="button" onClick={onClose} aria-label="关闭景点信息">
          <X weight="regular" aria-hidden="true" />
        </button>
      </div>
      <SpotMiniMap position={spot.position} />
      <p className="spot-desc">{spot.description}</p>
      <SpotPhotos spot={spot} />
    </aside>
  );
}

export function SpotModal({ spot, onClose }) {
  return (
    <div className="spot-modal-backdrop" onClick={onClose} role="presentation">
      <section
        className="spot-modal"
        role="dialog"
        aria-modal="true"
        aria-label={`${spot.name}实景`}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="spot-modal-head">
          <div>
            <span className="spot-kicker">查看实景</span>
            <h3>{spot.name}</h3>
            <p>{spot.city} · {spot.address}</p>
          </div>
          <button className="spot-close" type="button" onClick={onClose} aria-label="关闭">
            <X weight="regular" aria-hidden="true" />
          </button>
        </header>
        <SpotMiniMap position={spot.position} />
        <p className="spot-desc">{spot.description}</p>
        <SpotPhotos spot={spot} />
      </section>
    </div>
  );
}
