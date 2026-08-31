export type Severity = 'critical' | 'high' | 'medium' | 'low'

export interface ScoreItem { label: string; value: number; reason: string }
export interface Issue { severity: Severity; category: string; title: string; description: string; recommendation: string }
export interface Analysis {
  analysis_id: number; overall_score: number; label: string; scores: ScoreItem[]; issues: Issue[];
  recommendations: string[]; matched_keywords: string[]; missing_keywords: string[]; weak_keywords: string[];
  detected_sections: string[]; detected_skills: string[]; extracted_text: string; language: string; job_match_score: number
}
export interface HistoryItem { id: number; filename: string; overall_score: number; job_match_score: number; created_at: string; main_issue: string | null }

