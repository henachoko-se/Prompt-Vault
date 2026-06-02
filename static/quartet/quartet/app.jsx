/* QUARTET MUSIC — App root + shared player state */
const { useState: useS, useEffect: useE, useRef: useR } = React;

function Particles() {
  const dots = React.useMemo(() => {
    const colors = ["#74d4ff", "#4f7bff", "#b070ff", "#c4cbe0"];
    return Array.from({ length: 22 }, (_, i) => ({
      left: Math.random() * 100,
      size: 2 + Math.random() * 4,
      dur: 14 + Math.random() * 18,
      delay: -Math.random() * 30,
      color: colors[i % colors.length],
    }));
  }, []);
  return (
    <div className="particles" aria-hidden="true">
      {dots.map((d, i) => (
        <span key={i} className="particle" style={{
          left: `${d.left}%`, bottom: "-5vh",
          width: d.size, height: d.size, background: d.color,
          boxShadow: `0 0 ${d.size * 3}px ${d.color}`,
          animationDuration: `${d.dur}s`, animationDelay: `${d.delay}s`,
        }} />
      ))}
    </div>
  );
}

function App() {
  const songs = QSONGS;
  const audioRef = useR(null);
  const [idx, setIdx] = useS(0);             // index into songs
  const [playing, setPlaying] = useS(false);
  const [progress, setProgress] = useS(0);   // seconds elapsed
  const [durs, setDurs] = useS({});          // real durations once metadata loads
  const [vol, setVol] = useS(0.85);
  const current = songs[idx];
  // effective duration: real (from <audio>) if known, else the listed estimate
  const curDur = durs[current.id] || current.dur;
  // a song object whose dur reflects the real value, for child display
  const currentLive = { ...current, dur: curDur };

  // restore position
  useE(() => {
    try {
      const saved = JSON.parse(localStorage.getItem("quartet_player") || "{}");
      if (typeof saved.idx === "number" && songs[saved.idx]) setIdx(saved.idx);
      if (typeof saved.progress === "number") setProgress(saved.progress);
      if (typeof saved.vol === "number") setVol(saved.vol);
    } catch (e) {}
  }, []);
  useE(() => {
    try { localStorage.setItem("quartet_player", JSON.stringify({ idx, progress, vol })); } catch (e) {}
  }, [idx, progress, vol]);

  // keep <audio> volume in sync
  useE(() => { if (audioRef.current) audioRef.current.volume = vol; }, [vol]);

  // when the track changes, load it (and restore saved offset on first mount)
  const firstRef = useR(true);
  useE(() => {
    const a = audioRef.current;
    if (!a) return;
    a.src = current.src;
    a.load();
    const startAt = firstRef.current ? progress : 0;
    firstRef.current = false;
    const onMeta = () => {
      setDurs((d) => ({ ...d, [current.id]: a.duration }));
      if (startAt > 0 && startAt < a.duration) a.currentTime = startAt;
      if (playing) a.play().catch(() => {});
    };
    a.addEventListener("loadedmetadata", onMeta, { once: true });
    if (!playing) setProgress(startAt);
    return () => a.removeEventListener("loadedmetadata", onMeta);
  }, [idx]);

  // play / pause reflects state (only act when audio is ready; track-change
  // playback is started from the loadedmetadata handler instead)
  useE(() => {
    const a = audioRef.current;
    if (!a) return;
    if (playing) { if (a.readyState >= 2) a.play().catch(() => {}); }
    else a.pause();
  }, [playing]);

  const onTime = () => { const a = audioRef.current; if (a) setProgress(a.currentTime); };
  const onEnded = () => { setIdx((i) => (i + 1) % songs.length); setProgress(0); setPlaying(true); };

  const playId = (id) => {
    const i = songs.findIndex((s) => s.id === id);
    if (i < 0) return;
    if (i === idx) { setPlaying((p) => !p); }
    else { setIdx(i); setProgress(0); setPlaying(true); }
  };
  const toggle = () => setPlaying((p) => !p);
  const seek = (frac) => {
    const a = audioRef.current;
    const t = Math.max(0, Math.min(1, frac)) * curDur;
    setProgress(t);
    if (a && isFinite(t)) a.currentTime = t;
  };
  const prev = () => { setIdx((i) => (i - 1 + songs.length) % songs.length); setProgress(0); setPlaying(true); };
  const next = () => { setIdx((i) => (i + 1) % songs.length); setProgress(0); setPlaying(true); };

  return (
    <>
      <audio ref={audioRef} preload="metadata"
        onTimeUpdate={onTime} onEnded={onEnded} />
      <Particles />
      <Nav />
      <Hero current={currentLive} playing={playing} onToggle={toggle} />
      <NowPlaying current={currentLive} playing={playing} progress={progress}
        onToggle={toggle} onSeek={seek} onPrev={prev} onNext={next}
        vol={vol} onVol={setVol} />
      <Featured current={currentLive} playing={playing} onPlay={playId} />
      <Playlists />
      <Members />
      <Ranking current={currentLive} playing={playing} onPlay={playId} />
      <FinalCTA />
      <Footer />
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
