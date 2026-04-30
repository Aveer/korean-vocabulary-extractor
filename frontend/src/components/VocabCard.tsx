import { VocabCard } from "../types";

interface Props {
  card: VocabCard;
}

export default function VocabCardComponent({ card }: Props) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-lemma">{card.display}</span>
        <div className="card-meta">
          <span className="badge badge-pos">{card.pos}</span>
          {card.level && card.level !== "unknown" && (
            <span className="badge badge-level">{card.level}</span>
          )}
        </div>
      </div>

      {card.englishGlosses.length > 0 && (
        <div className="card-gloss">{card.englishGlosses.join(", ")}</div>
      )}

      <div className="card-source">{card.sourceSentence}</div>

      {card.sourceSentenceTranslation && (
        <div className="card-source-translation">{card.sourceSentenceTranslation}</div>
      )}

      {card.reason && <div className="card-reason">{card.reason}</div>}
    </div>
  );
}
