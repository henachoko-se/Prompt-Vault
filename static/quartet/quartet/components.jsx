/* QUARTET MUSIC — shared UI components */
const { useState, useEffect, useRef } = React;

const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

// ---- icons (inline SVG, simple shapes only) ----
const IcPlay = ({ s = 16 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13a1 1 0 0 0 1.5.87l11-6.5a1 1 0 0 0 0-1.74l-11-6.5A1 1 0 0 0 8 5.5z"/></svg>
);
const IcPause = ({ s = 16 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1.3"/><rect x="14" y="5" width="4" height="14" rx="1.3"/></svg>
);
const IcPrev = ({ s = 20 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><path d="M7 6a1 1 0 0 1 2 0v4.3l8.4-5a1 1 0 0 1 1.5.87v11.6a1 1 0 0 1-1.5.87L9 14.7V19a1 1 0 0 1-2 0z"/></svg>
);
const IcNext = ({ s = 20 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><path d="M17 6a1 1 0 0 0-2 0v4.3L6.6 5.3A1 1 0 0 0 5 6.17v11.6a1 1 0 0 0 1.6.87L15 13.7V18a1 1 0 0 0 2 0z"/></svg>
);
const IcVol = ({ s = 18 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><path d="M4 9v6h3.5L12 19V5L7.5 9H4z"/><path d="M15.5 8.5a4 4 0 0 1 0 7" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/><path d="M17.8 6.2a7 7 0 0 1 0 11.6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/></svg>
);
const IcShuffle = ({ s = 18 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M3 5h4l10 14h4M3 19h4l3-4.2M21 5h-4l-3 4.2"/><path d="M18 2l3 3-3 3M18 22l3-3-3-3"/></svg>
);
const IcHeart = ({ s = 18 }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 20s-7-4.5-7-9.5A3.5 3.5 0 0 1 12 7a3.5 3.5 0 0 1 7 3.5C19 15.5 12 20 12 20z"/></svg>
);

// circular play / pause control used on cards
function PlayBtn({ playing, onClick, size = 44, label }) {
  return (
    <button className="playbtn" style={{ width: size, height: size }} aria-label={label || "再生"}
      onClick={(e) => { e.stopPropagation(); onClick && onClick(); }}>
      {playing ? <IcPause s={size * 0.4} /> : <IcPlay s={size * 0.42} />}
    </button>
  );
}

// small equalizer bars
function Eq({ playing }) {
  return (
    <div className={"eq" + (playing ? "" : " paused")} aria-hidden="true">
      {[0.1, 0.4, 0.2, 0.5, 0.3].map((d, i) => (
        <i key={i} style={{ animationDelay: `${d}s`, animationDuration: `${0.7 + (i % 3) * 0.25}s` }} />
      ))}
    </div>
  );
}

// big waveform with fixed pseudo-random heights so it reads like audio
const WAVE_SEED = Array.from({ length: 64 }, (_, i) =>
  0.3 + Math.abs(Math.sin(i * 1.7) * 0.5 + Math.sin(i * 0.5) * 0.3));
function Wave({ playing }) {
  return (
    <div className={"wave" + (playing ? "" : " paused")} aria-hidden="true">
      {WAVE_SEED.map((h, i) => (
        <i key={i} style={{
          animationDelay: `${(i % 12) * 0.07}s`,
          animationDuration: `${1.1 + (i % 5) * 0.18}s`,
          opacity: 0.55 + (h - 0.3) * 0.5,
        }} />
      ))}
    </div>
  );
}

// a gradient (or image) album jacket with sweep + grain
function Jacket({ bg, img, alt, children, sweep = true, pos }) {
  return (
    <div className="jkt" style={{ position: "absolute", inset: 0, background: bg || "#0a0d1e" }}>
      {img && <img className="jkt-img" src={img} alt={alt || ""} loading="lazy"
        style={pos ? { objectPosition: pos } : null} />}
      {!img && <span className="grain" style={{ position: "absolute", inset: 0, mixBlendMode: "overlay", opacity: 0.35,
        backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" }} />}
      {sweep && <span className="jkt-sweep" />}
      {children}
    </div>
  );
}

// color dot
const Dot = ({ c, glow }) => (
  <span className="dot" style={{ background: c, boxShadow: glow ? `0 0 8px ${c}` : "none" }} />
);

// QUARTET brand mark — four member-color arcs forming a "Q"
function QLogoMark({ size = 32 }) {
  return (
    <svg className="qmark" viewBox="0 0 40 40" width={size} height={size} fill="none" aria-label="QUARTET">
      <g strokeWidth="5.4" strokeLinecap="round">
        <circle cx="20" cy="20" r="13" stroke="#74d4ff" strokeDasharray="15.4 66.3" transform="rotate(-86 20 20)" />
        <circle cx="20" cy="20" r="13" stroke="#4f7bff" strokeDasharray="15.4 66.3" transform="rotate(4 20 20)" />
        <circle cx="20" cy="20" r="13" stroke="#b070ff" strokeDasharray="15.4 66.3" transform="rotate(94 20 20)" />
        <circle cx="20" cy="20" r="13" stroke="#d2d8ea" strokeDasharray="15.4 66.3" transform="rotate(184 20 20)" />
      </g>
      <line x1="26.5" y1="26.5" x2="36.5" y2="36.5" stroke="#0a0d1a" strokeWidth="7.4" strokeLinecap="round" />
      <line x1="27" y1="27" x2="36" y2="36" stroke="#ffffff" strokeWidth="4.6" strokeLinecap="round" />
    </svg>
  );
}

Object.assign(window, {
  fmt, IcPlay, IcPause, IcPrev, IcNext, IcVol, IcShuffle, IcHeart,
  PlayBtn, Eq, Wave, Jacket, Dot, QLogoMark,
});
