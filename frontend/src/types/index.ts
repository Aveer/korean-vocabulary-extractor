export type TargetLevel = "ANY" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6";

export type Pos = "noun" | "verb" | "adjective" | "adverb" | "phrase" | "unknown";

export type VocabLevel = "TOPIK_I_1" | "TOPIK_I_2" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6" | "unknown";

export interface ExtractVocabRequest {
  text: string;
  targetLevel: TargetLevel;
  wordCount: number;
  includeSentenceTranslation: boolean;
  excludeKnown?: boolean;
  excludeIgnored?: boolean;
}

export type StudyStatus = "new" | "known" | "ignored";

export interface VocabCard {
  lemma: string;
  display: string;
  pos: Pos;
  englishGlosses: string[];
  koreanDefinition?: string | null;
  sourceSentence: string;
  sourceSentenceTranslation?: string | null;
  // Shortest useful Korean fragment containing the target word
  sourceFragment: string;
  sourceFragmentTranslation?: string | null;
  // Pre-formatted compact study line for display and copy
  studyLine: string;
  // CSV export fields
  csvFront: string;
  csvBack: string;
  level?: VocabLevel;
  difficultyScore: number;
  frequencyInText: number;
  reason: string;
  studyStatus?: StudyStatus | null;
  savedCardId?: string | number | null;
}

export interface StudyStats {
  todayReviews: number;
  dueCount: number;
  totalCards: number;
  knownLemmas: number;
  ignoredLemmas: number;
  currentStreakDays: number;
  xp: number;
  level: number;
}

export interface SavedStudyCard extends VocabCard {
  id: string | number;
  dueAt?: string | null;
}

export interface StudyCardsResponse {
  cards: SavedStudyCard[];
  total: number;
}

export interface DueReviewCard extends SavedStudyCard {}

export interface DueReviewsResponse {
  cards: DueReviewCard[];
  dueCount: number;
}

export type ReviewRating = "again" | "hard" | "good" | "easy";

export interface ExtractMeta {
  inputLength: number;
  candidateCount: number;
  returnedCount: number;
  dictionaryProvider: string;
  selectedTargetLevel?: string;
  candidateCountBeforeFiltering?: number;
  levelDistribution?: Record<string, number>;
}

export interface ExtractVocabResponse {
  cards: VocabCard[];
  meta: ExtractMeta;
}

export type AppTheme = "light" | "dark";

export type DictionaryProvider = "bundled" | "nikl";

export interface DictionaryConfig {
  provider: DictionaryProvider;
  apiKeySet: boolean;
  bundledAvailable: boolean;
  bundledEntryCount: number;
  bundledSource: string;
}

export interface DictionaryConfigRequest {
  provider: DictionaryProvider;
  api_key?: string;
}
