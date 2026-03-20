export type HashSide = 'left' | 'middle' | 'right';

export interface SituationEvent {
  down: 1 | 2 | 3 | 4;
  distance: number;
  yard_line: number;
  clock_seconds: number;
  offense_personnel: string;
  defense_shell: string;
  defense_front: string;
  hash: HashSide;
}

export interface PlayRecommendation {
  play_name: string;
  formation: string;
  concept: string;
  confidence: number;
  rationale: string;
}

export interface SuggestResponse {
  recommendations: PlayRecommendation[];
}
