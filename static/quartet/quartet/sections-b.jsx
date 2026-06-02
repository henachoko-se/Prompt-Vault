/* QUARTET MUSIC — sections B: Playlist, Members, Ranking, Final CTA, Footer */

function Playlists() {
  return (
    <section className="section-pad" id="playlists">
      <div className="wrap">
        <div className="sec-head">
          <span className="eyebrow">Playlists</span>
          <h2>気分で選ぶ、<span className="jp">QUARTET。</span></h2>
          <p>その日の空気に合わせて。4人の楽曲を気分別にまとめたプレイリスト。</p>
        </div>
        <div className="pl-grid">
          {QPLAYLISTS.map((p) => (
            <div className="pl-card" key={p.id}>
              <div className="cover"><Jacket bg={p.bg} /></div>
              <PlayBtn size={50} label={p.title} />
              <div className="body">
                <div className="kw">{p.kw}</div>
                <h3>{p.title}</h3>
                <p>{p.desc}</p>
                <div className="meta">
                  <span style={{ fontFamily: "var(--ff-en)" }}>{p.count} tracks</span>
                  <span>·</span>
                  <span style={{ fontFamily: "var(--ff-en)" }}>{p.min} min</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function MemberCard({ data }) {
  const m = QMEMBERS[data.key];
  return (
    <div className="mem-card" style={{ "--mc": m.color }}>
      <span className="mem-accent" style={{ background: `linear-gradient(90deg, ${m.color}, transparent)` }} />
      <div className="mem-portrait">
        <Jacket img={m.img} alt={m.en} pos="center 18%" sweep={false}>
          <span className="mem-scrim" />
        </Jacket>
      </div>
      <div className="mem-body">
        <div className="mem-name">
          <b>{m.name}</b><span className="en">{m.en} {m.emoji}</span>
        </div>
        <div className="mem-color"><Dot c={m.color} glow /> Member Color — {m.colorName}</div>
        <p className="mem-catch">{data.catch}</p>
        <div className="mem-traits">
          <div><span>Voice</span><span style={{ color: "var(--muted)" }}>{data.voice}</span></div>
          <div><span>Genre</span><span style={{ color: "var(--muted)" }}>{data.genre}</span></div>
          <div><span>Position</span><span style={{ color: "var(--muted)" }}>{data.pos}</span></div>
        </div>
      </div>
    </div>
  );
}

function Members() {
  return (
    <section className="section-pad" id="members">
      <div className="wrap">
        <div className="sec-head">
          <span className="eyebrow">Member Voice</span>
          <h2>4つの声、<span className="jp">4つの色。</span></h2>
          <p>スカイブルー、ブルー、パープル、ブラック。重なり合うことで生まれる、QUARTETの音。</p>
        </div>
        <div className="mem-grid">
          {QMEMBER_CARDS.map((c) => <MemberCard key={c.key} data={c} />)}
        </div>
      </div>
    </section>
  );
}

function Ranking({ current, playing, onPlay }) {
  return (
    <section className="section-pad" id="ranking">
      <div className="wrap">
        <div className="sec-head">
          <span className="eyebrow">QUARTET Weekly Ranking</span>
          <h2>今週、<span className="jp">最も響いた歌。</span></h2>
          <p>ファンが選ぶ、今週のQUARTET人気曲ランキング。</p>
        </div>
        <div className="rank-list glass" style={{ padding: 14 }}>
          {QRANKING.map((r, i) => {
            const mem = QMEMBERS[r.member];
            const isCur = current.id === r.id;
            return (
              <div className="rank-row" key={r.id} onClick={() => onPlay(r.id)}>
                <div className={"rank-no" + (i === 0 ? " top" : "")}>{i + 1}</div>
                <div className="rank-art"><Jacket img={r.img} bg={r.bg} alt={r.title} sweep={false} /></div>
                <div className="rank-info">
                  <b>{r.title}</b>
                  <span>{mem ? <><Dot c={mem.color} glow /> {mem.emoji} {mem.name}</> : <><Dot c="#c4cbe0" /> QUARTET</>}</span>
                </div>
                <div className="rank-plays">{r.plays} plays</div>
                <PlayBtn playing={isCur && playing} onClick={() => onPlay(r.id)} size={36} />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="section-pad" id="cta">
      <div className="wrap">
        <div className="final">
          <div className="en">QUARTET — The Story Continues</div>
          <h2 style={{ marginTop: 18 }}>4つの声が重なった瞬間、<br />ただの歌じゃなく、君の物語になる。</h2>
          <div className="final-cta">
            <a href="#songs" className="btn btn-primary"><IcPlay s={17} /> QUARTETの世界へ</a>
            <a href="https://ornate-cocada-830f5d.netlify.app/" target="_blank" rel="noopener" className="btn btn-ghost">Official Site →</a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="wrap footer-inner">
        <div>
          <div className="logo"><QLogoMark /> QUARTET</div>
          <p>QUARTET Official Music Page。4人だから見えた景色を、君の心のど真ん中へ。<br />2026 Japan Budokan Debut.</p>
        </div>
        <div className="cols">
          <div className="col">
            <h5>Music</h5>
            <a href="#songs">Featured Songs</a>
            <a href="#playlists">Playlists</a>
            <a href="#ranking">Weekly Ranking</a>
          </div>
          <div className="col">
            <h5>Group</h5>
            <a href="#members">Members</a>
            <a href="#">Live · Budokan 2026</a>
            <a href="https://www.threads.com/@henachoko_pm" target="_blank" rel="noopener">Produced by へなP</a>
          </div>
          <div className="col">
            <h5>Follow</h5>
            <a href="https://ornate-cocada-830f5d.netlify.app/" target="_blank" rel="noopener">Official Site</a>
            <a href="#">Fan Club</a>
            <a href="#">News</a>
          </div>
        </div>
      </div>
      <div className="wrap fine">© 2026 QUARTET MUSIC — これは架空アイドルグループのデザインコンセプトページです。実在の配信サービス・アーティストとは関係ありません。</div>
    </footer>
  );
}

Object.assign(window, { Playlists, Members, Ranking, FinalCTA, Footer });
