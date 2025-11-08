import './GeneratePage.css';

const promptCards = [
  { title: 'Top Prompt', body: '“Describe the best relaxing ambience for sleepy commuters.”' },
  { title: 'Customized', body: '“Tailor a whisper script for rainy-night listeners.”' },
];

export default function GeneratePage() {
  return (
    <div className="generate-page">
      <header className="top-bar">
        <div className="brand">
          <span className="brand-icon">◎</span>
          <span className="brand-name">A1 ASMR</span>
        </div>
        <nav className="menu">
          <button className="menu-item">Reels ▾</button>
          <button className="menu-item active">Generate ▾</button>
        </nav>
        <button className="profile-pill">Me</button>
      </header>

      <main className="workspace">
        <aside className="prompt-panel">
          <h2>Suggestions</h2>
          <p className="panel-subtitle">Top prompts</p>
          <div className="prompt-list">
            {promptCards.map((card) => (
              <article key={card.title} className="prompt-card">
                <header>{card.title}</header>
                <p>{card.body}</p>
                <button className="ghost-btn">Copy</button>
              </article>
            ))}
          </div>
          <div className="prompt-input">
            <input placeholder="Write your own prompt…" />
            <button>Send</button>
          </div>
        </aside>

        <section className="video-panel">
          <div className="video-frame">
            <button className="play-button">▶</button>
          </div>
        </section>
      </main>

      <section className="actions">
        <button className="action-btn primary">🙂 Generate 1 min</button>
        <button className="action-btn">🙁 Regenerate</button>
        <button className="action-btn">✈ Post</button>
        <button className="action-btn">⬇ Download</button>
      </section>
    </div>
  );
}
