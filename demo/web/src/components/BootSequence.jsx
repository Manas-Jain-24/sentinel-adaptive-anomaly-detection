import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ShieldCheck, Cpu, Zap, Activity } from "lucide-react";

export function BootSequence({ onComplete }) {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setStage(1), 350);
    const t2 = setTimeout(() => setStage(2), 700);
    const t3 = setTimeout(() => setStage(3), 1100);
    const t4 = setTimeout(() => {
      setStage(4);
      if (onComplete) onComplete();
    }, 1600);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [onComplete]);

  if (stage >= 4) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        exit={{ opacity: 0, filter: "blur(8px)" }}
        transition={{ duration: 0.4 }}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 9999,
          background: "#05070a",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "24px"
        }}
      >
        {/* Animated oscilloscope line drawing across */}
        <div style={{ width: "320px", height: "2px", background: "rgba(255,255,255,0.1)", position: "relative", overflow: "hidden" }}>
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: "100%" }}
            transition={{ duration: 1.2, ease: "easeInOut" }}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              background: "linear-gradient(90deg, transparent, #3df2e0, #ffffff, transparent)",
              boxShadow: "0 0 16px #3df2e0"
            }}
          />
        </div>

        {/* Title */}
        <div style={{ textAlign: "center" }}>
          <h2 style={{ fontFamily: "Space Grotesk, sans-serif", fontSize: "1.4rem", letterSpacing: "0.2em", textTransform: "uppercase", color: "#f0f4f8" }}>
            SENTINEL PULSE
          </h2>
          <p style={{ fontFamily: "JetBrains Mono, monospace", fontSize: "0.75rem", color: "#94a3b8", marginTop: "4px" }}>
            MISSION CONTROL FOR TIME • UTKRISHTA 2026
          </p>
        </div>

        {/* Arming Status Chips */}
        <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
          <div className={`status-chip ${stage >= 1 ? "active" : ""}`}>
            <span className="dot" />
            <span>CAUSAL</span>
          </div>
          <div className={`status-chip ${stage >= 2 ? "active" : ""}`}>
            <span className="dot" />
            <span>STREAMING</span>
          </div>
          <div className={`status-chip ${stage >= 3 ? "active" : ""}`}>
            <span className="dot" />
            <span>INTERPRETABLE</span>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}