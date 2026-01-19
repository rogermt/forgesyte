/**
 * Radar/pitch view component for displaying player positions and tracking data.
 */

import React from "react";

export interface PlayerPosition {
  id: string;
  x: number;
  y: number;
  team?: "home" | "away";
  label?: string;
  confidence?: number;
}

export interface RadarViewProps {
  players: PlayerPosition[];
  ball?: { x: number; y: number };
  width?: number;
  height?: number;
  pitchMarkings?: boolean;
}

const TEAM_COLORS = {
  home: "#FF6B6B",
  away: "#4ECDC4",
  default: "#45B7D1",
};

export function RadarView({
  players,
  ball,
  width = 400,
  height = 300,
  pitchMarkings = true,
}: RadarViewProps): JSX.Element {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = "var(--bg-primary)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw pitch markings
    if (pitchMarkings) {
      ctx.strokeStyle = "var(--border-light)";
      ctx.lineWidth = 1;

      // Pitch boundary
      ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

      // Center line
      ctx.beginPath();
      ctx.moveTo(canvas.width / 2, 10);
      ctx.lineTo(canvas.width / 2, canvas.height - 10);
      ctx.stroke();

      // Center circle
      ctx.beginPath();
      ctx.arc(
        canvas.width / 2,
        canvas.height / 2,
        30,
        0,
        Math.PI * 2
      );
      ctx.stroke();
    }

    // Draw players
    players.forEach((player) => {
      const color =
        TEAM_COLORS[player.team || "default"] || TEAM_COLORS.default;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(player.x, player.y, 6, 0, Math.PI * 2);
      ctx.fill();

      // Player number/label
      if (player.label) {
        ctx.fillStyle = "#000";
        ctx.font = "10px monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(player.label, player.x, player.y);
      }
    });

    // Draw ball
    if (ball) {
      ctx.fillStyle = "#FFD700";
      ctx.beginPath();
      ctx.arc(ball.x, ball.y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#FFA500";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }, [players, ball, pitchMarkings]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          border: "1px solid var(--border-light)",
          borderRadius: "4px",
          backgroundColor: "var(--bg-primary)",
        }}
      />
      <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
        <div>🔴 Home Team</div>
        <div>🔵 Away Team</div>
        <div>🟡 Ball</div>
      </div>
    </div>
  );
}
