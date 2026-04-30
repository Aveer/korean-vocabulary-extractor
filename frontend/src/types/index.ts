export type TargetLevel = "ANY" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6";

export type Pos = "noun" | "verb" | "adjective" | "adverb" | "phrase" | "unknown";

export type VocabLevel = "TOPIK_I_1" | "TOPIK_I_2" | "TOPIK_II_3" | "TOPIK_II_4" | "TOPIK_II_5" | "TOPIK_II_6" | "unknown";

export interface ExtractVocabRequest {
  text: string;
  targetLevel: TargetLevel;
  wordCount: number;
  includeSentenceTranslation: boolean;
}

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
}

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
