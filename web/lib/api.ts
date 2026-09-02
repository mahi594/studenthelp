import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Attach auth token to every request if present
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export async function listCompanies() {
  const res = await api.get("/companies/");
  return res.data;
}

export async function generatePrepPlan(targetCompanyId: string, daysTotal: number) {
  const res = await api.post("/prep-plan/generate", {
    target_company_id: targetCompanyId,
    days_total: daysTotal,
  });
  return res.data;
}

export type PrepPlanTask = { day: number; topic: string; task: string; source_title?: string | null; source_url?: string | null; reason?: string | null; completed?: boolean; status?: string };
export type PrepPlan = {
  id: string;
  target_company_id: string | null;
  days_total: number;
  tasks: PrepPlanTask[];
  progress_percent: number;
  created_at: string;
};

export type AuditLogItem = {
  id: string;
  institution_id: string;
  actor_user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  timestamp: string;
  metadata_json: Record<string, any> | null;
};

export async function updatePrepPlanTaskStatus(planId: string, taskIndex: number, completed: boolean): Promise<PrepPlan> {
  const res = await api.patch(`/prep-plan/${planId}/tasks/${taskIndex}`, { completed });
  return res.data;
}

export async function customizePrepPlan(planId: string, message: string, conversationHistory: { role: string; content: string }[] = []) {
  const res = await api.post(`/prep-plan/${planId}/customize`, {
    message,
    conversation_history: conversationHistory,
  });
  return res.data;
}

export async function customizeRoadmap(roadmapId: string, message: string, conversationHistory: { role: string; content: string }[] = []) {
  const res = await api.post(`/roadmap/${roadmapId}/customize`, {
    message,
    conversation_history: conversationHistory,
  });
  return res.data;
}

export async function verifyCompany(companyId: string, payload: { verified_by: string; confidence?: string; source_type?: string }) {
  const res = await api.post(`/companies/${companyId}/verify`, payload);
  return res.data;
}

export async function listAuditLogs(params?: { action?: string; limit?: number; offset?: number }): Promise<AuditLogItem[]> {
  const res = await api.get("/audit-logs/", { params });
  return res.data;
}

export async function getLatestPrepPlan(): Promise<PrepPlan | null> {
  try {
    const res = await api.get("/prep-plan/latest");
    return res.data;
  } catch (e: any) {
    if (e?.response?.status === 404) return null;
    throw e;
  }
}


export async function submitQuizResult(subject: string, scorePercent: number) {
  const res = await api.post("/quiz/submit", { subject, score_percent: scorePercent });
  return res.data;
}

export async function getQuizQuestions(subject: string, companyId?: string, limit: number = 10) {
  const res = await api.get("/quiz/questions", {
    params: { subject, company_id: companyId || undefined, limit },
  });
  return res.data;
}

export async function submitQuizAnswers(subject: string, answers: { question_id: string; selected_option_index: number }[]) {
  const res = await api.post("/quiz/submit-answers", { subject, answers });
  return res.data;
}

export async function getLatestReadiness() {
  const res = await api.get("/readiness/latest");
  return res.data;
}

export async function getReadinessHistory() {
  const res = await api.get("/readiness/history");
  return res.data;
}

export async function computeReadiness() {
  const res = await api.post("/readiness/compute");
  return res.data;
}

export async function markApplication(companyId: string, status: string = "applied") {
  const res = await api.post("/applications/mark", { company_id: companyId, status });
  return res.data;
}

export async function listMyApplications() {
  const res = await api.get("/applications/");
  return res.data;
}

// ---------- Auth ----------
export async function login(email: string, password: string): Promise<{ access_token: string; token_type: string; must_change_password: boolean }> {
  const form = new URLSearchParams();
  form.append("grant_type", "password");
  form.append("username", email);
  form.append("password", password);

  const res = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  if (typeof window !== "undefined") {
    // Stored even when it's a restricted must_change_password token - the
    // request interceptor attaches whatever's here, and /auth/change-password
    // accepts that restricted token (see get_current_user_for_password_change
    // on the backend). It gets overwritten with a full token once changed.
    localStorage.setItem("access_token", res.data.access_token);
  }
  return res.data;
}

export async function changePassword(newPassword: string): Promise<{ access_token: string; token_type: string; message: string }> {
  const res = await api.post("/auth/change-password", { new_password: newPassword });
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", res.data.access_token);
  }
  return res.data;
}

export async function register(payload: {
  name: string;
  email: string;
  password: string;
  branch?: string;
  grad_year?: number;
}) {
  const res = await api.post("/auth/register", payload);
  return res.data;
}

export function logout() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
  }
}

export async function forgotPassword(email: string): Promise<{ message: string; dev_reset_token?: string }> {
  const res = await api.post("/auth/forgot-password", { email });
  return res.data;
}

export async function resetPassword(token: string, newPassword: string) {
  const res = await api.post("/auth/reset-password", { token, new_password: newPassword });
  return res.data;
}

export function isLoggedIn(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

export type CurrentUser = {
  id: string;
  name: string;
  email: string;
  role: "student" | "admin" | "tpo_admin" | string;
  branch?: string | null;
  grad_year?: number | null;
  cgpa?: string | null;
  college_name?: string | null;
  email_verified?: boolean;
  target_company_ids: string[];
  leetcode_username?: string | null;
  leetcode_daily_goal?: number;
  leetcode_total_solved?: number;
  leetcode_easy_solved?: number;
  leetcode_medium_solved?: number;
  leetcode_hard_solved?: number;
  leetcode_streak?: number;
  leetcode_last_solved_date?: string | null;
  must_change_password?: boolean;
};

export async function getCurrentUser(): Promise<CurrentUser> {
  const res = await api.get("/auth/me");
  return res.data;
}

export async function updateProfile(payload: {
  name?: string;
  branch?: string;
  grad_year?: number;
  cgpa?: string;
  college_name?: string;
  leetcode_username?: string;
  leetcode_daily_goal?: number;
}): Promise<CurrentUser> {
  const res = await api.patch("/users/me", payload);
  return res.data;
}


// ---------- Admin ----------
export async function createCompany(payload: any) {
  const res = await api.post("/companies/", payload);
  return res.data;
}

export async function addRound(companyId: string, payload: {
  order_index: number;
  round_type: string;
  subjects_tested: string[];
  difficulty?: string;
  notes?: string;
}) {
  const res = await api.post(`/companies/${companyId}/rounds`, payload);
  return res.data;
}

export async function deleteRound(companyId: string, roundId: string) {
  const res = await api.delete(`/companies/${companyId}/rounds/${roundId}`);
  return res.data;
}

export async function generateQuizQuestions(payload: {
  subject: string;
  num_questions: number;
  company_id?: string;
}) {
  const res = await api.post("/admin/quiz/generate", payload);
  return res.data;
}

export async function listPendingQuizQuestions(params?: { subject?: string; company_id?: string }) {
  const res = await api.get("/admin/quiz/pending", { params });
  return res.data;
}

export async function approveQuizQuestion(questionId: string) {
  const res = await api.post(`/admin/quiz/${questionId}/approve`);
  return res.data;
}

export async function rejectQuizQuestion(questionId: string) {
  const res = await api.post(`/admin/quiz/${questionId}/reject`);
  return res.data;
}

export async function getTpoDashboard(params?: {
  branch?: string;
  grad_year?: number;
  cgpa_min?: number;
  cgpa_max?: number;
  readiness_min?: number;
  readiness_max?: number;
  risk_category?: string;
  assessment_status?: string;
  interview_status?: string;
  target_company_id?: string;
  skill_topic?: string;
  page?: number;
  page_size?: number;
}) {
  const res = await api.get("/tpo/dashboard", { params });
  return res.data;
}

export async function getTpoStudentDetail(studentId: string) {
  const res = await api.get(`/tpo/students/${studentId}`);
  return res.data;
}

export async function createAdmin(payload: {
  name: string;
  email: string;
  role: "admin" | "tpo_admin";
  college_name?: string;
}): Promise<{ id: string; name: string; email: string; role: string; temp_password: string; email_sent: boolean }> {
  const res = await api.post("/admin/create-admin", payload);
  return res.data;
}

// ---------- Weekly quiz cadence ----------
export type QuizWeeklySubjectStatus = {
  subject: string;
  last_taken_at: string | null;
  last_score_percent: number | null;
  next_eligible_at: string | null;
  is_due: boolean;
};

export async function getQuizWeeklyStatus(): Promise<QuizWeeklySubjectStatus[]> {
  const res = await api.get("/quiz/weekly-status");
  return res.data;
}

export async function getMyLeetcodeRecommendations() {
  const res = await api.get("/leetcode/recommendations/for-me");
  return res.data;
}

// ---------- Chat ----------
export type ChatMessage = { role: "user" | "assistant"; content: string };

export async function askChat(message: string, companyId?: string): Promise<{ answer: string; history: ChatMessage[] }> {
  const res = await api.post("/chat/ask", { message, company_id: companyId || undefined });
  return res.data;
}

export async function getChatHistory(): Promise<ChatMessage[]> {
  const res = await api.get("/chat/history");
  return res.data;
}

// ---------- Roadmap ----------
export type RoadmapPhase = {
  phase: string;
  focus_subjects: string[];
  milestones: string[];
  reason: string;
};

export type RoadmapResponse = {
  id: string;
  horizon_months: number;
  phases: RoadmapPhase[];
  target_company_ids?: string[];
  target_company_names?: string[];
  created_at: string;
};

export async function getLatestRoadmap(): Promise<RoadmapResponse | null> {
  try {
    const res = await api.get("/roadmap/user/latest");
    return res.data;
  } catch (e: any) {
    if (e?.response?.status === 404) return null;
    throw e;
  }
}


export async function generateRoadmap(horizonMonths: number, targetCompanyIds: string[] = []) {
  const res = await api.post("/roadmap/generate", {
    horizon_months: horizonMonths,
    target_company_ids: targetCompanyIds,
  });
  return res.data;
}

// ---------- Mock Interview ----------
export type MockInterviewTurn = { role: "interviewer" | "candidate"; content: string };
export type MockInterviewSession = {
  id: string;
  company_id: string | null;
  role_or_subject: string;
  transcript: MockInterviewTurn[];
  status: "in_progress" | "completed";
  overall_score: number | null;
  feedback: {
    technical_knowledge?: number;
    problem_solving?: number;
    communication_score?: number;
    answer_structure?: number;
    technical_depth?: number;
    strengths?: string[];
    improvements?: string[];
  } | null;
  created_at: string;
};


export async function startMockInterview(roleOrSubject: string, companyId?: string): Promise<MockInterviewSession> {
  const res = await api.post("/mock-interview/start", { role_or_subject: roleOrSubject, company_id: companyId || undefined });
  return res.data;
}

export async function respondMockInterview(sessionId: string, answer: string): Promise<MockInterviewSession> {
  const res = await api.post(`/mock-interview/${sessionId}/respond`, { answer });
  return res.data;
}

export async function finishMockInterview(sessionId: string): Promise<MockInterviewSession> {
  const res = await api.post(`/mock-interview/${sessionId}/finish`);
  return res.data;
}

// ---------- Resume ----------
export async function uploadAndMatchResume(targetCompanyId: string, file: File) {
  const formData = new FormData();
  formData.append("target_company_id", targetCompanyId);
  formData.append("file", file);
  const res = await api.post("/resume/upload-and-match", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function getResumeHistory(targetCompanyId?: string) {
  const res = await api.get("/resume/history", {
    params: { target_company_id: targetCompanyId || undefined },
  });
  return res.data;
}

// ---------- Email verification ----------
export async function resendVerification(): Promise<{ message: string; dev_verify_token?: string }> {
  const res = await api.post("/auth/resend-verification");
  return res.data;
}

export async function verifyEmail(token: string) {
  const res = await api.post("/auth/verify-email", { token });
  return res.data;
}

// ---------- Notifications ----------
export type AppNotification = {
  id: string;
  type: string;
  title: string;
  body: string | null;
  link: string | null;
  is_read: boolean;
  created_at: string;
};

export async function listNotifications(): Promise<AppNotification[]> {
  const res = await api.get("/notifications/");
  return res.data;
}

export async function getUnreadNotificationCount(): Promise<number> {
  const res = await api.get("/notifications/unread-count");
  return res.data.count;
}

export async function markNotificationRead(id: string) {
  const res = await api.post(`/notifications/${id}/read`);
  return res.data;
}

export async function markAllNotificationsRead() {
  const res = await api.post("/notifications/read-all");
  return res.data;
}

// ---------- Community Q&A ----------
export type QAAnswerItem = {
  id: string;
  author_id: string;
  author_name: string;
  body: string;
  upvotes: number;
  created_at: string;
};

export type QAQuestionListItem = {
  id: string;
  author_id: string;
  author_name: string;
  title: string;
  body: string;
  company_id: string | null;
  tags: string[];
  answer_count: number;
  created_at: string;
};

export type QAQuestionDetail = Omit<QAQuestionListItem, "answer_count"> & {
  answers: QAAnswerItem[];
};

export async function listQuestions(params?: { company_id?: string; tag?: string }): Promise<QAQuestionListItem[]> {
  const res = await api.get("/qa/questions", { params });
  return res.data;
}

export async function getQuestion(id: string): Promise<QAQuestionDetail> {
  const res = await api.get(`/qa/questions/${id}`);
  return res.data;
}

export async function createQuestion(payload: { title: string; body: string; company_id?: string; tags?: string[] }): Promise<QAQuestionDetail> {
  const res = await api.post("/qa/questions", payload);
  return res.data;
}

export async function answerQuestion(questionId: string, body: string): Promise<QAAnswerItem> {
  const res = await api.post(`/qa/questions/${questionId}/answers`, { body });
  return res.data;
}

export async function upvoteAnswer(answerId: string): Promise<QAAnswerItem> {
  const res = await api.post(`/qa/answers/${answerId}/upvote`);
  return res.data;
}

// ---------- Job listings ----------
export type JobListingItem = {
  id: string;
  company_name: string;
  role_title: string;
  location: string | null;
  apply_url: string;
  posted_at: string;
  [key: string]: any;
};

export async function browseJobListings(params?: { company_name?: string; role?: string; location?: string }): Promise<JobListingItem[]> {
  const res = await api.get("/job-listings/", { params });
  return res.data;
}

export async function searchJobListings(params: { keywords: string; location?: string; results_per_page?: number }): Promise<JobListingItem[]> {
  const res = await api.get("/job-listings/search", { params });
  return res.data;
}

export async function refreshJobListings(payload: { keywords: string; location?: string; results_per_page?: number }) {
  const res = await api.post("/job-listings/refresh", payload);
  return res.data;
}

// ---------- LeetCode ----------
export type LeetCodeLogItem = {
  id: string;
  problem_title: string;
  problem_slug: string | null;
  difficulty: string;
  topic: string | null;
  notes: string | null;
  solved_at: string;
};

export type LeetCodeProfile = {
  username: string | null;
  daily_goal: number;
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  streak: number;
  last_solved_date: string | null;
  solved_today: boolean;
  recent_logs: LeetCodeLogItem[];
};

export type LeetCodeRecommendation = {
  id: string;
  title: string;
  slug: string;
  difficulty: "Easy" | "Medium" | "Hard" | string;
  topic: string;
  level: "Beginner" | "Intermediate" | "Advanced" | string;
  description: string;
  leetcode_url: string;
  tags: string[];
};

export type LeetCodeStudentSummary = {
  user_id: string;
  name: string;
  email: string;
  leetcode_username: string | null;
  total_solved: number;
  streak: number;
  solved_today: boolean;
  last_solved_date: string | null;
  latest_problem: string | null;
};

export async function getLeetCodeProfile(): Promise<LeetCodeProfile> {
  const res = await api.get("/leetcode/profile");
  return res.data;
}

export async function syncLeetCodeProfile(payload: { leetcode_username?: string; leetcode_daily_goal?: number }) {
  const res = await api.post("/leetcode/sync", payload);
  return res.data;
}

export async function logLeetCodeProblem(payload: {
  problem_title: string;
  problem_slug?: string;
  difficulty: string;
  topic?: string;
  notes?: string;
}): Promise<LeetCodeLogItem> {
  const res = await api.post("/leetcode/log", payload);
  return res.data;
}

export async function getLeetCodeRecommendations(params?: { level?: string; topic?: string }): Promise<LeetCodeRecommendation[]> {
  const res = await api.get("/leetcode/recommendations", { params });
  return res.data;
}

export async function getAdminLeetCodeTrack(): Promise<LeetCodeStudentSummary[]> {
  const res = await api.get("/leetcode/admin/students");
  return res.data;
}

