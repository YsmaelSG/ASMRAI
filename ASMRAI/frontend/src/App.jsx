// src/App.jsx
import { useRef, useState } from "react";
import "./App.css";
import playbutton1 from "./assets/playbutton1.gif";
import happyface1 from "./assets/happyface1.png";
import sadface1 from "./assets/sadface1.png";
import post1 from "./assets/post1.png";
import download1 from "./assets/download1.png";
import logo from "./assets/logo.png";

export default function App() {
  const videoRef = useRef(null);
  const [videoSrc, setVideoSrc] = useState("");

  const handleGenerate = () => {
    // TODO: replace with your real generate logic
    alert("Pretend we generated a 3-minute clip 🙂");
  };

  const handleRegenerate = () => {
    // TODO: replace with your real regenerate logic
    alert("Regenerating…");
  };

  const handlePost = () => {
    // TODO: replace with your real post logic
    alert("Posted!");
  };

  const handleDownload = () => {
    if (!videoSrc) return alert("No video to download yet.");
    const a = document.createElement("a");
    a.href = videoSrc;
    a.download = "video.mp4";
    a.click();
  };

  const handlePickLocalVideo = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    setVideoSrc(url);
  };

  return (
    <div className="app">
      {/* TOP MENU BAR */}
      <header className="topbar">
        <div className="brand">
          <img src={logo} alt="Logo" className="logo" />
          <span className="title"> Relief AI</span>
        </div>

        <nav className="nav">
          <button className="navbtn">Reels ▾</button>
          <button className="navbtn">Generate ▾</button>
          <button className="navbtn profile">Me</button>
        </nav>
      </header>

      {/* LEFT DIALOG / PROMPTS */}
      <aside className="sidebar">
        <h3>Suggestions</h3>

        <div className="card">
          <p className="cardTitle">Top prompt</p>
          <p className="cardBody">
            “Create a 60-second relaxing ocean-waves ASMR with soft rain.”
          </p>
          <button
            className="small"
            onClick={() =>
              navigator.clipboard.writeText(
                "Create a 60-second relaxing ocean-waves ASMR with soft rain."
              )
            }
          >
            Copy
          </button>
        </div>

        <div className="card">
          <p className="cardTitle">Customized prompt</p>
          <textarea
            className="textarea"
            rows="5"
            placeholder="Write your own idea…"
          />
          <button className="small">Copy</button>
        </div>

        <div className="picker">
          <label className="pickLabel">
            Pick a local video (for testing)
            <input type="file" accept="video/*" onChange={handlePickLocalVideo} />
          </label>
        </div>
      </aside>

      {/* MAIN: VIDEO + ACTION BUTTONS */}
      <main className="stage">
        <div className="videoBox">
          {videoSrc ? (
            <video ref={videoRef} src={videoSrc} controls />
          ) : (
            <div className="videoPlaceholder">
              <span className="playIcon">
                <img src={playbutton1} alt="Play" className="playIcon" />
              </span>
              <p>Your video will appear here</p>
            </div>
          )}
        </div>

        <div className="actions">
          <button className="primary" onClick={handleGenerate}>
              <img src={happyface1} alt="Generate" className="btnIcon" />
              Generate 3 min
          </button>
          <button onClick={handleRegenerate}>
             <img src={sadface1} alt="Regenerate" className="btnIcon" /> 
             Regenerate
          </button>
          <button onClick={handlePost}>
            <img src={post1} alt="Post" className="btnIcon" />
             Post</button>
          <button onClick={handleDownload}>
            <img src={download1} alt="Download" className="btnIcon" />
            Download</button>
        </div>
      </main>
    </div>
  );
}
