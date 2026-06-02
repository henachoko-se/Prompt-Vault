/* QUARTET MUSIC — sections A: Nav, Hero, Now Playing, Featured */
const { useState: useStateA, useEffect: useEffectA } = React;

function Nav() {
  const [scrolled, setScrolled] = useStateA(false);
  useEffectA(() => {
    const on = () => setScrolled(window.scrollY > 30);
    on(); window.addEventListener("scroll", on);
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <nav className={"nav" + (scrolled ? " scrolled" : "")}>
      <div className="wrap nav-inner">
        <div className="logo"><QLogoMark /> QUARTET</div>
        <div className="nav-links">
          <a href="#songs">Songs</a>
          <a href="#playlists">Playlists</a>
          <a href="#members">Members</a>
          <a href="#ranking">Ranking</a>
          <a href="https://ornate-cocada-830f5d.netlify.app/" target="_blank" rel="noopener">Official Site</a>
          <a href="#cta" className="btn btn-ghost nav-cta">最新曲をチェック</a>
        </div>
      </div>
    </nav>
  );
}

function Hero({ current, playing, onToggle }) {
  const m = QMEMBERS;
  return (
    <header className="hero">
      <div className="wrap hero-grid">
        <div>
          <span className="eyebrow">QUARTET Official Music</span>
          <h1>QUARTET<br /><span className="grad">MUSIC</span></h1>
          <p className="sub">4人の声が、君の心のど真ん中へ響く。</p>
          <p className="lead">
            2026年春、日本武道館デビュー。王道ポップスからエモーショナルなバラードまで、
            QUARTETの楽曲をまとめて楽しめるスペシャルミュージックページ。
          </p>
          <div className="hero-cta">
            <a href="#songs" className="btn btn-primary"><IcPlay s={17} /> 楽曲を聴く</a>
            <a href="#playlists" className="btn btn-ghost">プレイリストを見る</a>
          </div>
          <div className="hero-meta">
            <div className="m"><div className="n">40+</div><div className="l">Songs</div></div>
            <div className="m"><div className="n">4</div><div className="l">Members</div></div>
            <div className="m"><div className="n">2026</div><div className="l">Budokan Debut</div></div>
          </div>
        </div>

        <div className="jacket-stack">
          <div className="jacket main">
            <Jacket img={IMG.budokan} alt="QUARTET 武道館、決定。" pos="center top">
              <div className="jacket-body" style={{ justifyContent: "flex-start" }}>
                <div className="jacket-top">
                  <span className="lbl">1st Single · 2026</span>
                  <div className="jacket-colors">
                    <span className="dot" style={{ color: m.nagi.color, background: m.nagi.color }} />
                    <span className="dot" style={{ color: m.natsu.color, background: m.natsu.color }} />
                    <span className="dot" style={{ color: m.ruka.color, background: m.ruka.color }} />
                    <span className="dot" style={{ color: m.hena.color, background: m.hena.color }} />
                  </div>
                </div>
              </div>
            </Jacket>
            <div className="jacket-mini">
              <PlayBtn playing={playing} onClick={onToggle} size={40} />
              <div className="t"><b>{current.title}</b><span>QUARTET</span></div>
              <Eq playing={playing} />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function NowPlaying({ current, playing, progress, onToggle, onSeek, onPrev, onNext, vol, onVol }) {
  const mem = QMEMBERS[current.member] || null;
  const frac = Math.min(1, progress / current.dur);
  const seek = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    onSeek((e.clientX - r.left) / r.width);
  };
  const setVolFromEvent = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    onVol && onVol(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)));
  };
  return (
    <section className="section-pad" id="player">
      <div className="wrap">
        <div className="sec-head">
          <span className="eyebrow">Now Streaming</span>
          <h2 className="jp">いま、QUARTETが鳴っている。</h2>
        </div>
        <div className="np-card glass">
          <div className="np-art">
            <Jacket img={current.img} bg={current.bg} alt={current.title}>
              <span className="np-art-scrim" />
              <Wave playing={playing} />
            </Jacket>
          </div>
          <div className="np-body">
            <div className="np-row1">
              <span className="np-now"><span className="live" /> Now Playing</span>
              <Eq playing={playing} />
            </div>
            <div className="np-title">{current.title}</div>
            <div className="np-artist">
              QUARTET · {current.kw}{mem ? ` · ${mem.emoji} ${mem.name}` : ""}
            </div>
            <div className="np-controls">
              <button className="np-ic" onClick={onPrev} aria-label="前へ"><IcPrev /></button>
              <PlayBtn playing={playing} onClick={onToggle} size={54} />
              <button className="np-ic" onClick={onNext} aria-label="次へ"><IcNext /></button>
              <button className="np-ic" aria-label="シャッフル"><IcShuffle /></button>
              <button className="np-ic" aria-label="お気に入り"><IcHeart /></button>
            </div>
            <div className="np-seek">
              <span className="np-time">{fmt(progress)}</span>
              <div className="np-bar" onClick={seek}>
                <div className="np-fill" style={{ width: `${frac * 100}%` }} />
              </div>
              <span className="np-time">{fmt(current.dur)}</span>
            </div>
            <div className="np-seek" style={{ marginTop: 12 }}>
              <div className="np-vol">
                <IcVol />
                <div className="vbar" onClick={setVolFromEvent} style={{ cursor: "pointer" }}>
                  <div className="vfill" style={{ width: `${Math.round((vol ?? 0.85) * 100)}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SongCard({ song, idx, isCurrent, playing, onPlay }) {
  const mem = QMEMBERS[song.member];
  return (
    <div className={"song-card" + (isCurrent ? " active" : "")} onClick={() => onPlay(song.id)}>
      <div className="song-art">
        <Jacket img={song.img} bg={song.bg} alt={song.title} sweep={false}>
          <span className="song-art-scrim" />
          <span className="num">{String(idx + 1).padStart(2, "0")}</span>
        </Jacket>
        <div className="pl">
          <PlayBtn playing={isCurrent && playing} onClick={() => onPlay(song.id)} size={44} />
        </div>
      </div>
      <div className="song-name">{song.title}</div>
      <div className="song-sub">
        {mem ? <><Dot c={mem.color} glow /> {mem.emoji} {song.lead}</> : <><Dot c="#c4cbe0" /> {song.lead}</>}
        <span style={{ color: "var(--faint)" }}>· {fmt(song.dur)}</span>
      </div>
      <div className="song-foot">
        <span className="chip">{song.tag}</span>
        <span style={{ fontFamily: "var(--ff-en)", fontSize: 12, color: "var(--faint)" }}>{song.plays} plays</span>
      </div>
    </div>
  );
}

function Featured({ current, playing, onPlay }) {
  return (
    <section className="section-pad" id="songs">
      <div className="wrap">
        <div className="sec-head">
          <span className="eyebrow">Featured Songs</span>
          <h2>代表曲を、<span className="jp">まとめて。</span></h2>
          <p>王道アイドルポップスからJ-ROCK、シティ・ポップ、そして武道館へ続くバラードまで。QUARTETの幅広い音楽性をこの一覧で。</p>
        </div>
        <div className="song-grid">
          {QSONGS.map((s, i) => (
            <SongCard key={s.id} song={s} idx={i}
              isCurrent={current.id === s.id} playing={playing} onPlay={onPlay} />
          ))}
        </div>
      </div>
    </section>
  );
}

Object.assign(window, { Nav, Hero, NowPlaying, Featured });
