import { Activity, Radio, SearchCode, Award, FileCheck2, Camera, Sun, HelpCircle } from "lucide-react";

export function RailNav({ activeTab, setActiveTab, projectorMode, setProjectorMode, onOpenHelp }) {
  const navItems = [
    { id: "overview", label: "Overview", icon: Activity, desc: "Landing & Pitch" },
    { id: "stream", label: "Stream Viewer", icon: Radio, desc: "Causal Replay Chart" },
    { id: "evidence", label: "Evidence", icon: SearchCode, desc: "Flag Anatomy & Proof" },
    { id: "comparison", label: "Comparison", icon: Award, desc: "Leaderboard & Radar" },
    { id: "manifest", label: "Manifest", icon: FileCheck2, desc: "SHA-256 Integrity" },
    { id: "figures", label: "Figures", icon: Camera, desc: "Slide Capture Shelf" }
  ];

  return (
    <nav
      style={{
        width: "72px",
        minWidth: "72px",
        height: "100vh",
        background: "rgba(8, 12, 18, 0.95)",
        borderRight: "1px solid var(--panel-border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "16px 0",
        zIndex: 50,
        position: "sticky",
        top: 0
      }}
    >
      {/* Brand Icon */}
      <div
        style={{
          width: "42px",
          height: "42px",
          borderRadius: "8px",
          background: "linear-gradient(135deg, rgba(61,242,224,0.15), rgba(8,12,18,0.8))",
          border: "1px solid var(--cyan-signal)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--cyan-signal)",
          marginBottom: "28px",
          boxShadow: "0 0 12px var(--cyan-glow)",
          cursor: "pointer"
        }}
        onClick={() => setActiveTab("overview")}
        title="Sentinel Pulse"
      >
        <span style={{ fontFamily: "Space Grotesk", fontWeight: 700, fontSize: "1.1rem" }}>SP</span>
      </div>

      {/* Nav List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%", alignItems: "center", flex: 1 }}>
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                width: "52px",
                height: "52px",
                borderRadius: "var(--radius-sm)",
                background: isActive ? "rgba(61, 242, 224, 0.12)" : "transparent",
                border: isActive ? "1px solid var(--cyan-signal)" : "1px solid transparent",
                color: isActive ? "var(--cyan-signal)" : "var(--text-muted)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "4px",
                cursor: "pointer",
                transition: "all var(--transition-fast)",
                position: "relative"
              }}
              title={`${item.label} (${item.desc})`}
            >
              <Icon size={19} />
              <span style={{ fontSize: "0.6rem", fontFamily: "var(--font-ui)", fontWeight: 500 }}>
                {item.label.split(" ")[0]}
              </span>
              {isActive && (
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    width: "3px",
                    height: "24px",
                    background: "var(--cyan-signal)",
                    borderRadius: "0 2px 2px 0",
                    boxShadow: "0 0 8px var(--cyan-signal)"
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Controls */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px", alignItems: "center" }}>
        {/* Projector Mode Toggle */}
        <button
          onClick={() => setProjectorMode(!projectorMode)}
          style={{
            width: "38px",
            height: "38px",
            borderRadius: "var(--radius-sm)",
            background: projectorMode ? "var(--amber-translucent)" : "transparent",
            border: projectorMode ? "1px solid var(--amber-threshold)" : "1px solid var(--panel-border)",
            color: projectorMode ? "var(--amber-threshold)" : "var(--text-dim)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "all var(--transition-fast)"
          }}
          title={projectorMode ? "Projector Mode: ON (High Contrast)" : "Projector Mode: OFF"}
        >
          <Sun size={17} />
        </button>

        {/* Shortcuts / Help */}
        <button
          onClick={onOpenHelp}
          style={{
            width: "38px",
            height: "38px",
            borderRadius: "var(--radius-sm)",
            background: "transparent",
            border: "1px solid var(--panel-border)",
            color: "var(--text-dim)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer"
          }}
          title="Keyboard Shortcuts ([Space], Arrows, [, ], E)"
        >
          <HelpCircle size={17} />
        </button>
      </div>
    </nav>
  );
}