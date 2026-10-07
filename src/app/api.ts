const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '');

export const CAREER_ROLE_OPTIONS = [
  'Data Analyst',
  'Data Engineer',
  'Business Analyst',
  'Project Manager',
  'Product Manager',
  'QA Automation Engineer',
  'System Administrator',
] as const;

export type CareerRole = (typeof CAREER_ROLE_OPTIONS)[number];
export type ProgressStatus = 'not_started' | 'in_progress' | 'completed';
export type EvidenceSource = 'resume' | 'education' | 'syllabus' | 'project' | 'certification' | 'internship' | 'self_declared' | 'github';

export interface StudentEvidenceInput {
  skill: string;
  source: EvidenceSource;
  evidence: string;
  proficiency?: 'exposure' | 'beginner' | 'intermediate' | 'advanced' | 'expert' | 'unknown';
  confidence: 'low' | 'medium' | 'high';
}

export interface ResumeSkillEvidence extends StudentEvidenceInput {
  source: 'resume';
  proficiency: 'unknown';
}

export interface ProcessedResumeResponse {
  status: 'processed';
  filename: string;
  text_character_count: number;
  extracted_skills: string[];
  skill_evidence: ResumeSkillEvidence[];
}

export interface RolePrediction {
  role: string;
  confidence: number;
}

export interface ResumeEnhancementResponse {
  filename: string;
  summary: string;
  strengths: string[];
  section_completeness: {
    present: string[];
    missing_sections: string[];
    applicability_note: string;
  };
  skill_coverage: {
    resume_skills: string[];
    skills_needing_stronger_evidence: string[];
  };
  target_role_coverage: null | {
    target_role: string;
    represented_skills: Array<{ skill: string; priority: string | null; role_frequency_percentage: number }>;
    not_represented_skills: Array<{ skill: string; priority: string | null; role_frequency_percentage: number }>;
    skills_needing_stronger_evidence: string[];
    note: string;
  };
  content_checks: Record<string, number>;
  suggestions: Array<{ priority: string; topic: string; suggestion: string }>;
  improvement_priorities: string[];
}

export interface StudentSkillRecord {
  skill: string;
  category: string;
  sources: EvidenceSource[];
  evidence: Array<{
    source: EvidenceSource;
    evidence: string;
    proficiency: string;
    proficiency_basis: string;
    confidence: string;
  }>;
}

export interface SkillGapItem {
  skill: string;
  category?: string;
  priority?: string;
  gap_type?: 'matched' | 'partial' | 'missing';
  [field: string]: unknown;
}

export interface SkillGapResponse {
  target_role: string;
  matched_skills: SkillGapItem[];
  partial_skills: SkillGapItem[];
  missing_skills: SkillGapItem[];
  matched_count: number;
  partial_count: number;
  missing_count: number;
}

export interface PrioritizedGap {
  skill: string;
  category?: string | null;
  gap_type: 'missing' | 'partial';
  industry_priority: string;
  priority_score: number;
  reason: string;
}

export interface CareerAlignmentResponse extends SkillGapResponse {
  prioritized_gaps: PrioritizedGap[];
  career_readiness: {
    target_role: string;
    career_readiness_score: number | null;
    score_available: boolean;
    score_status: string;
    matched_count: number;
    partial_count: number;
    missing_count: number;
    interpretation: string;
  };
}

export interface RoadmapStep {
  step: number;
  skill: string;
  skill_category: string;
  gap_type: 'missing' | 'partial';
  priority: string;
  priority_score: number;
  reason: string;
  prerequisites: string[];
  status: ProgressStatus;
  [field: string]: unknown;
}

export interface LearningRoadmapResponse {
  target_role: string;
  steps: RoadmapStep[];
  total_steps: number;
  optional_step_count: number;
}

export interface LearningResourceRecommendation {
  skill: string;
  resource_id: string;
  title: string;
  resource_type: string;
  level: string;
  provider: string;
  description: string;
  url: string;
  reason: string;
}

export interface YouTubeLearningVideo {
  video_id: string;
  title: string;
  description: string;
  thumbnail_url: string;
  channel_title: string;
  published_at: string;
  topic: string;
  youtube_url: string;
}

export interface YouTubeLearningVideosResponse {
  target_role: string;
  topics: string[];
  videos: YouTubeLearningVideo[];
  total_videos: number;
  message: string | null;
}

export interface ProjectRecommendation {
  project_id: string;
  title: string;
  description: string;
  difficulty: string;
  project_type: string;
  addressed_missing_skills: string[];
  addressed_partial_skills: string[];
  score: number;
  reason: string;
}

export interface JobRecordInput {
  job_id: string;
  title: string;
  skills: string[];
  career_role?: string;
  company?: string;
}

export interface JobMatch {
  job_id: string;
  title: string;
  career_role?: string;
  company?: string;
  score: number;
  matched_skills: string[];
  partial_skills: string[];
  missing_skills: string[];
  matched_count: number;
  partial_count: number;
  missing_count: number;
  total_skill_count: number;
  explanation: string;
}

export interface ProgressRecord {
  skill: string;
  status: ProgressStatus;
  updated_revision: number;
  notes: string | null;
  step_id?: string;
  completed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ProgressSummary {
  total_skills: number;
  not_started_count: number;
  in_progress_count: number;
  completed_count: number;
  completion_percentage: number;
}

export interface CompletionEvent {
  event_type: string;
  skill: string;
  status: 'completed';
  updated_revision: number;
  statement: string;
  proficiency: null;
  confidence: null;
}

export class ApiRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
  }
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 503) return error.message || 'A required backend model or dataset is unavailable.';
    return error.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return 'Could not complete the request. Check that the backend is running and that this preview origin is allowed by its CORS settings.';
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
  } catch {
    throw new ApiRequestError('Could not complete the request. Check that the backend is running and that this preview origin is allowed by its CORS settings.', 0);
  }

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const envelope = body && typeof body === 'object' ? body as { detail?: unknown; error?: unknown } : undefined;
    const detail = envelope?.detail;
    const nested = detail && typeof detail === 'object' ? detail as { error?: unknown; message?: unknown } : undefined;
    const message = typeof detail === 'string'
      ? detail
      : (typeof nested?.error === 'string' ? nested.error : typeof nested?.message === 'string' ? nested.message : typeof envelope?.error === 'string' ? envelope.error : `Request failed (${response.status}).`);
    throw new ApiRequestError(message, response.status);
  }
  return body as T;
}

const postJson = <T>(path: string, body: unknown): Promise<T> => requestJson<T>(path, {
  method: 'POST',
  body: JSON.stringify(body),
});

export const getHealth = () => requestJson<{ status: string }>('/api/health');
export const getRoles = () => requestJson<{ roles: string[] }>('/api/roles');
export const listCareerRoles = async (): Promise<string[]> => {
  try {
    return (await getRoles()).roles;
  } catch (error) {
    // The classifier artifact used by the legacy role-list endpoint may be
    // absent while the approved roles remain available to the twin APIs.
    if (error instanceof ApiRequestError && error.status === 503) return [...CAREER_ROLE_OPTIONS];
    throw error;
  }
};
export const predictRole = (jobDescription: string) =>
  postJson<RolePrediction[]>('/api/predict-role', { job_description: jobDescription });

export const extractSkills = (text: string) => postJson<{ extracted_skills: string[] }>('/api/skills/extract', { text });
export const createStudentSkillTwin = (records: StudentEvidenceInput[]) => postJson<StudentSkillRecord[]>('/api/student-skill-twin', { records });

export const processResume = async (file: File): Promise<ProcessedResumeResponse> => {
  const form = new FormData();
  form.append('file', file);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/resume/process`, { method: 'POST', body: form });
  } catch {
    throw new ApiRequestError('Could not upload the resume. Check that the backend is running and allowed by CORS.', 0);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const envelope = body && typeof body === 'object' ? body as { detail?: unknown } : undefined;
    const message = typeof envelope?.detail === 'string' ? envelope.detail : `Resume processing failed (${response.status}).`;
    throw new ApiRequestError(message, response.status);
  }
  return body as ProcessedResumeResponse;
};

export const enhanceResume = async (file: File, targetRole?: string): Promise<ResumeEnhancementResponse> => {
  const form = new FormData();
  form.append('file', file);
  if (targetRole?.trim()) form.append('target_role', targetRole.trim());
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/resume/enhance`, { method: 'POST', body: form });
  } catch {
    throw new ApiRequestError('Could not analyze the resume. Check that the backend is running and allowed by CORS.', 0);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const envelope = body && typeof body === 'object' ? body as { detail?: unknown } : undefined;
    const message = typeof envelope?.detail === 'string' ? envelope.detail : `Resume enhancement failed (${response.status}).`;
    throw new ApiRequestError(message, response.status);
  }
  return body as ResumeEnhancementResponse;
};

export const makeSelfDeclaredEvidence = (skills: string[]): StudentEvidenceInput[] => {
  const unique = [...new Set(skills.map((skill) => skill.trim()).filter(Boolean))];
  return unique.map((skill) => ({
    skill,
    source: 'self_declared',
    evidence: `User-provided skill: ${skill}`,
    confidence: 'low',
  }));
};

export const analyzeSkillGap = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<SkillGapResponse>('/api/skill-gap', { records, target_role: targetRole });

export const getCareerAlignment = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<CareerAlignmentResponse>('/api/career-alignment', { records, target_role: targetRole });

export const getLearningRoadmap = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<LearningRoadmapResponse>('/api/learning-roadmap', { records, target_role: targetRole });

export const getLearningResources = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<{ target_role: string; recommendations: LearningResourceRecommendation[]; total_recommendations: number }>(
    '/api/learning-resources', { records, target_role: targetRole },
  );

export const getYouTubeLearningVideos = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<YouTubeLearningVideosResponse>(
    '/api/youtube-learning-videos', { records, target_role: targetRole },
  );

export const getProjectRecommendations = (records: StudentEvidenceInput[], targetRole: string) =>
  postJson<{ target_role: string; recommendations: ProjectRecommendation[]; total_recommendations: number }>(
    '/api/project-recommendations', { records, target_role: targetRole },
  );

export const matchJobs = (studentRecords: StudentEvidenceInput[], jobs: JobRecordInput[]) =>
  postJson<{ matches: JobMatch[]; total_jobs: number; score_interpretation: string }>(
    '/api/job-matching', { student_records: studentRecords, jobs },
  );

const progressQuery = (studentId: string, roadmapId: string) =>
  `?${new URLSearchParams({ student_id: studentId, roadmap_id: roadmapId }).toString()}`;

export const initializeProgress = (roadmap: LearningRoadmapResponse, studentId: string) =>
  postJson<{ progress: ProgressRecord[]; summary: ProgressSummary; roadmap_id: string; target_role: string }>(
    '/api/progress/initialize', { roadmap, student_id: studentId },
  );

export const updateSkillProgress = (skill: string, status: ProgressStatus, studentId: string, roadmapId: string, notes?: string) =>
  requestJson<{ progress: ProgressRecord; newly_completed_skills: CompletionEvent[] }>('/api/progress/update', {
    method: 'PUT',
    body: JSON.stringify({ skill, status, student_id: studentId, roadmap_id: roadmapId, ...(notes === undefined ? {} : { notes }) }),
  });

export const getProgress = (studentId: string, roadmapId: string) =>
  requestJson<{ progress: ProgressRecord[]; total_skills: number; roadmap_id: string }>(`/api/progress${progressQuery(studentId, roadmapId)}`);
export const getProgressSummary = (studentId: string, roadmapId: string) =>
  requestJson<ProgressSummary>(`/api/progress/summary${progressQuery(studentId, roadmapId)}`);
export const getCompletedSkillEvents = (studentId: string, roadmapId: string) =>
  requestJson<{ newly_completed_skills: CompletionEvent[]; total_events: number }>(`/api/progress/completed-events${progressQuery(studentId, roadmapId)}`);
export const getSkillProgress = (skill: string, studentId: string, roadmapId: string) =>
  requestJson<ProgressRecord>(`/api/progress/skill/${encodeURIComponent(skill)}${progressQuery(studentId, roadmapId)}`);

export interface JobSearchRequest {
  skills: string[];
  syllabus_data_url?: string | null;
  location?: string | null;
  limit?: number;
}

export interface SearchedJob {
  job_id?: string;
  title: string;
  company: string;
  description?: string;
  career_role?: string;
  skills?: string[];
  location?: string;
  url?: string;
  job_type?: string;
  source?: string;
  days_ago?: number;
  criteria?: { min_cgpa?: number; min_10th?: number; min_12th?: number };
  tags?: string[];
  match_score?: number;
  matched_skills?: string[];
}

export const searchJobs = (payload: JobSearchRequest) => postJson<{
  jobs: SearchedJob[];
  total_found: number;
  jobs_with_skill_match: number;
  average_match_score: number;
  unique_companies: number;
  sources: string[];
  skills_searched: string[];
  location_filter: string | null;
  is_demo_fallback: boolean;
  source: 'demo_fallback' | 'live_results';
}>('/api/jobs/search', payload);

export const analyzeGitHubProfile = (username: string) => postJson<{
  username: string;
  skills: string[];
  projects: Array<{ name: string; description: string; skills: string[]; url: string; stars: number }>;
}>('/api/github/analyze', { username });
