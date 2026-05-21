import type React from "react";
import { VocabCard } from "../types";

interface Props {
  card: VocabCard;
  actions?: React.ReactNode;
}

export default function VocabCardComponent({ card, actions }: Props) {
  return (
    <div className="card">
      {/* Primary: compact study line */}
      <div className="card-study-line">{card.studyLine}</div>

      {/* Secondary: metadata below */}
      <div className="card-meta-inline">
        <span className="badge badge-pos">{card.pos}</span>
        {card.level && card.level !== "unknown" && (
          <span className="badge badge-level">{card.level}</span>
        )}
        <span className="badge badge-difficulty">D{Math.round(card.difficultyScore)}</span>
      </div>

      {card.reason && <div className="card-reason">{card.reason}</div>}
      {actions && <div className="card-actions">{actions}</div>}
    </div>
  );
}
