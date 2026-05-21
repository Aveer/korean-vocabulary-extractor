import { VocabCard } from "../types";

interface Props {
  text: string;
  cards: VocabCard[];
}

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export default function ReadingHighlights({ text, cards }: Props) {
  const trimmed = text.trim();
  if (!trimmed || cards.length === 0) return null;

  const terms = Array.from(
    new Set(
      cards
        .flatMap((card) => [
          card.display,
          card.lemma,
          card.sourceFragment && card.sourceFragment.length <= 18 ? card.sourceFragment : null,
        ])
        .filter((term): term is string => Boolean(term && term.trim().length >= 2))
        .sort((a, b) => b.length - a.length)
    )
  ).slice(0, 40);

  if (terms.length === 0) return null;

  const pattern = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "g");
  const parts = trimmed.split(pattern).filter(Boolean);

  return (
    <section className="reading-highlights" aria-label="Highlighted reading passage">
      <div className="section-kicker">Reading map</div>
      <h2>Quest words in context</h2>
      <p className="reading-note">Best-effort highlights for this extraction only. Your full passage is not saved.</p>
      <div className="reading-text">
        {parts.map((part, index) =>
          terms.includes(part) ? (
            <mark key={`${part}-${index}`}>{part}</mark>
          ) : (
            <span key={`${part}-${index}`}>{part}</span>
          )
        )}
      </div>
    </section>
  );
}
