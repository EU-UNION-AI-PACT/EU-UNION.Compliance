import React from "react";

/**
 * 3D isometric layered stack — CSS-only, GPU-transform based.
 * Photorealistic tech look for the 5-layer public-goods architecture.
 * Props: layers = [{ level, title }, ...] (max 5)
 */
export default function Iso3DStack({ layers = [], height = 380 }) {
  const items = layers.slice(0, 5);
  return (
    <div
      className="pnia-iso-scene relative w-full"
      style={{ height: `${height}px` }}
      aria-hidden="true"
      data-testid="iso3d-stack"
    >
      <div
        className="pnia-iso-stack absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        style={{ width: "82%", height: "62%" }}
      >
        {items.map((l, i) => (
          <div
            key={l.level || i}
            className={`pnia-iso-layer l${i + 1}`}
          >
            <span className="lbl">{l.level || `Ebene ${i + 1}`}</span>
            <span className="desc">{l.title?.slice(0, 34) || "layer"}</span>
            {/* pulsing node on top-most layer */}
            {i === items.length - 1 && (
              <>
                <span
                  className="pnia-iso-node"
                  style={{ top: "22%", left: "18%" }}
                />
                <span
                  className="pnia-iso-node"
                  style={{ top: "62%", left: "58%", animationDelay: "0.6s" }}
                />
                <span
                  className="pnia-iso-node"
                  style={{ top: "36%", left: "76%", animationDelay: "1.2s" }}
                />
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
