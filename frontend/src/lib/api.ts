const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type UserRole = "talent" | "recruiter" | "admin";
export type TalentCategory =
  | "acting"
  | "singing"
  | "dancing"
  | "painting"
  | "script_writing"
  | "photography"
  | "music"
  | "choreography"
  | "comedy"
  | "voice_over"
  | "direction"
  | "modeling"
  | "design"
  | "other";
export type ApplicationStatus = "pending" | "shortlisted" | "rejected" | "accepted";
export type CastingCallStatus = "open" | "closed";
export type MediaType = "photo" | "video" | "audio" | "document";

export const TALENT_CATEGORIES: TalentCategory[] = [
  "acting",
  "singing",
  "dancing",
  "painting",
  "script_writing",
  "photography",
  "music",
  "choreography",
  "comedy",
  "voice_over",
  "direction",
  "modeling",
  "design",
  "other",
];

export interface User {
  id: string;
  email: string;
  phone: string | null;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export interface Media {
  id: string;
  url: string;
  media_type: MediaType;
  title: string | null;
  is_cover: boolean;
}

export type CreditProjectType =
  | "film"
  | "television"
  | "commercial"
  | "theatre"
  | "voice"
  | "music"
  | "event"
  | "online"
  | "other";

export interface Credit {
  id: string;
  talent_profile_id: string;
  project_type: CreditProjectType;
  title: string;
  role: string | null;
  company_or_director: string | null;
  location: string | null;
  date_label: string | null;
  reference_url: string | null;
  created_at: string;
}

export interface CreditInput {
  project_type: CreditProjectType;
  title: string;
  role?: string;
  company_or_director?: string;
  location?: string;
  date_label?: string;
  reference_url?: string;
}

export interface TalentProfile {
  id: string;
  user_id: string;
  display_name: string;
  category: TalentCategory;
  bio: string | null;
  city: string | null;
  date_of_birth: string | null;
  experience_years: number | null;
  skills: string[] | null;
  tier: "free" | "premium";
  is_verified: boolean;
  verification_requested_at: string | null;
  instagram_url: string | null;
  facebook_url: string | null;
  tiktok_url: string | null;
  twitter_url: string | null;
  youtube_url: string | null;
  website_url: string | null;
  intro_video_url: string | null;
  attributes: Record<string, string> | null;
  job_alert_emails: boolean;
  created_at: string;
  media: Media[];
  credits: Credit[];
}

export interface TalentProfileInput {
  display_name: string;
  category: TalentCategory;
  bio?: string | null;
  city?: string | null;
  date_of_birth?: string | null;
  experience_years?: number | null;
  skills?: string[] | null;
  instagram_url?: string | null;
  facebook_url?: string | null;
  tiktok_url?: string | null;
  twitter_url?: string | null;
  youtube_url?: string | null;
  website_url?: string | null;
  intro_video_url?: string | null;
  attributes?: Record<string, string> | null;
  job_alert_emails?: boolean;
}

export interface RecruiterProfile {
  id: string;
  user_id: string;
  company_name: string;
  industry: string | null;
  is_verified: boolean;
  verification_requested_at: string | null;
  tier: "free" | "premium";
  created_at: string;
}

export interface SavedSearch {
  id: string;
  recruiter_id: string;
  name: string;
  category: TalentCategory | null;
  city: string | null;
  q: string | null;
  experience_min: number | null;
  experience_max: number | null;
  verified_only: boolean;
  created_at: string;
}

export interface CastingCallRole {
  id: string;
  casting_call_id: string;
  title: string;
  criteria: string | null;
  category: string | null;
  compensation: string | null;
}

export interface CastingCallRoleInput {
  title: string;
  criteria?: string;
  category?: TalentCategory;
  compensation?: string;
}

export interface CastingCall {
  id: string;
  recruiter_id: string;
  title: string;
  description: string;
  category: TalentCategory;
  location: string | null;
  compensation: string | null;
  application_deadline: string | null;
  status: CastingCallStatus;
  audition_brief: string | null;
  audition_reference_url: string | null;
  tags: string[] | null;
  shoot_details: string | null;
  is_featured: boolean;
  view_count: number;
  created_at: string;
  roles: CastingCallRole[];
}

export interface Application {
  id: string;
  casting_call_id: string;
  role_id: string;
  talent_id: string;
  message: string | null;
  submission_url: string | null;
  status: ApplicationStatus;
  applied_at: string;
}

export type InvitationStatus = "pending" | "accepted" | "declined";

export interface Invitation {
  id: string;
  casting_call_id: string;
  talent_id: string;
  recruiter_id: string;
  message: string | null;
  status: InvitationStatus;
  created_at: string;
  casting_call: CastingCall;
}

export interface AvailabilityWindow {
  id: string;
  talent_id: string;
  day_of_week: number; // 0=Monday .. 6=Sunday
  start_time: string; // "HH:MM:SS"
  end_time: string;
  created_at: string;
}

export type BookingStatus = "pending" | "accepted" | "declined" | "cancelled";
export type AgreementStatus = "not_required" | "pending" | "signed";

export interface Booking {
  id: string;
  talent_id: string;
  recruiter_id: string;
  casting_call_id: string | null;
  start_at: string;
  end_at: string;
  message: string | null;
  status: BookingStatus;
  agreement_status: AgreementStatus;
  agreement_document_url: string | null;
  created_at: string;
  talent_display_name: string;
  recruiter_company_name: string;
  casting_call_title: string | null;
}

export interface Follow {
  id: string;
  talent_id: string;
  recruiter_id: string;
  created_at: string;
  recruiter_company_name: string;
}

export interface Review {
  id: string;
  booking_id: string;
  talent_id: string;
  recruiter_id: string;
  reviewer_role: "talent" | "recruiter";
  rating: number;
  comment: string | null;
  created_at: string;
  reviewer_name: string;
}

export interface TalentReviewSummary {
  average_rating: number | null;
  review_count: number;
  reviews: Review[];
}

export interface CastingCallAnalytics {
  id: string;
  title: string;
  status: CastingCallStatus;
  view_count: number;
  application_count: number;
  pending_count: number;
  shortlisted_count: number;
  accepted_count: number;
  rejected_count: number;
}

export interface RecruiterAnalytics {
  total_views: number;
  total_applications: number;
  response_rate: number;
  casting_calls: CastingCallAnalytics[];
}

export interface AdminStats {
  total_users: number;
  total_talents: number;
  total_recruiters: number;
  verified_talents: number;
  verified_recruiters: number;
  open_casting_calls: number;
  closed_casting_calls: number;
  total_applications: number;
  total_invitations: number;
}

export interface AdminCastingCall extends CastingCall {
  recruiter_company_name: string;
  application_count: number;
  invitation_count: number;
}

export interface FinancialOverview {
  currency: string;
  free_talents: number;
  premium_talents: number;
  free_recruiters: number;
  premium_recruiters: number;
  price_per_premium_talent: number;
  price_per_premium_recruiter: number;
  estimated_monthly_revenue: number;
}

export interface AdminUserDetail extends User {
  talent_profile: TalentProfile | null;
  recruiter_profile: RecruiterProfile | null;
}

export interface ConversationSummary {
  id: string;
  talent_id: string;
  recruiter_id: string;
  casting_call_id: string | null;
  created_at: string;
  other_party_name: string;
  last_message: string | null;
  last_message_at: string | null;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_user_id: string;
  body: string;
  read_at: string | null;
  created_at: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface RegisterInput {
  email: string;
  password: string;
  full_name: string;
  role: "talent" | "recruiter";
  phone?: string;
  consent_given: boolean;
}

export const api = {
  register: (data: RegisterInput) => request<User>("/auth/register", { method: "POST", body: JSON.stringify(data) }),

  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        if (typeof body.detail === "string") detail = body.detail;
      } catch {
        // ignore
      }
      throw new ApiError(res.status, detail);
    }
    return res.json() as Promise<{ access_token: string; token_type: string }>;
  },

  me: (token: string) => request<User>("/auth/me", {}, token),

  verifyEmail: (email: string, code: string) =>
    request<{ access_token: string; token_type: string }>(
      "/auth/verify-email",
      { method: "POST", body: JSON.stringify({ email, code }) }
    ),
  resendVerification: (email: string) =>
    request<void>("/auth/resend-verification", { method: "POST", body: JSON.stringify({ email }) }),

  forgotPassword: (email: string) =>
    request<void>("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) }),
  resetPassword: (email: string, code: string, new_password: string) =>
    request<{ access_token: string; token_type: string }>(
      "/auth/reset-password",
      { method: "POST", body: JSON.stringify({ email, code, new_password }) }
    ),

  listTalents: (
    params: {
      category?: TalentCategory;
      city?: string;
      q?: string;
      experience_min?: number;
      experience_max?: number;
      verified_only?: boolean;
    } = {}
  ) => {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    if (params.city) qs.set("city", params.city);
    if (params.q) qs.set("q", params.q);
    if (params.experience_min !== undefined) qs.set("experience_min", String(params.experience_min));
    if (params.experience_max !== undefined) qs.set("experience_max", String(params.experience_max));
    if (params.verified_only) qs.set("verified_only", "true");
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<TalentProfile[]>(`/talents${suffix}`);
  },
  getTalent: (id: string) => request<TalentProfile>(`/talents/${id}`),
  getMyTalentProfile: (token: string) => request<TalentProfile>("/talents/me", {}, token),
  createMyTalentProfile: (data: TalentProfileInput, token: string) =>
    request<TalentProfile>("/talents/me", { method: "POST", body: JSON.stringify(data) }, token),
  updateMyTalentProfile: (data: Partial<TalentProfileInput>, token: string) =>
    request<TalentProfile>("/talents/me", { method: "PATCH", body: JSON.stringify(data) }, token),
  addMyMedia: (data: { url: string; media_type: MediaType; title?: string; is_cover?: boolean }, token: string) =>
    request<Media>("/talents/me/media", { method: "POST", body: JSON.stringify(data) }, token),
  uploadMyMedia: async (
    data: { file: File; media_type: "video" | "audio"; title?: string },
    token: string
  ): Promise<Media> => {
    const form = new FormData();
    form.set("media_type", data.media_type);
    if (data.title) form.set("title", data.title);
    form.set("file", data.file);

    const res = await fetch(`${API_URL}/talents/me/media/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        if (typeof body.detail === "string") detail = body.detail;
      } catch {
        // ignore non-JSON error bodies
      }
      throw new ApiError(res.status, detail);
    }
    return res.json();
  },
  saveTalent: (talentId: string, token: string) =>
    request<void>(`/talents/${talentId}/save`, { method: "POST" }, token),
  unsaveTalent: (talentId: string, token: string) =>
    request<void>(`/talents/${talentId}/save`, { method: "DELETE" }, token),
  listSavedTalents: (token: string) => request<TalentProfile[]>("/recruiters/me/saved-talents", {}, token),
  requestTalentVerification: (token: string) =>
    request<TalentProfile>("/talents/me/request-verification", { method: "POST" }, token),
  upgradeTalentTier: (token: string) => request<TalentProfile>("/talents/me/upgrade", { method: "POST" }, token),
  addMyCredit: (data: CreditInput, token: string) =>
    request<Credit>("/talents/me/credits", { method: "POST", body: JSON.stringify(data) }, token),
  deleteMyCredit: (creditId: string, token: string) =>
    request<void>(`/talents/me/credits/${creditId}`, { method: "DELETE" }, token),

  createMyRecruiterProfile: (data: { company_name: string; industry?: string }, token: string) =>
    request<RecruiterProfile>("/recruiters/me", { method: "POST", body: JSON.stringify(data) }, token),
  getMyRecruiterProfile: (token: string) => request<RecruiterProfile>("/recruiters/me", {}, token),
  requestRecruiterVerification: (token: string) =>
    request<RecruiterProfile>("/recruiters/me/request-verification", { method: "POST" }, token),
  upgradeRecruiterTier: (token: string) => request<RecruiterProfile>("/recruiters/me/upgrade", { method: "POST" }, token),

  listSavedSearches: (token: string) => request<SavedSearch[]>("/recruiters/me/saved-searches", {}, token),
  createSavedSearch: (
    data: {
      name: string;
      category?: TalentCategory;
      city?: string;
      q?: string;
      experience_min?: number;
      experience_max?: number;
      verified_only?: boolean;
    },
    token: string
  ) => request<SavedSearch>("/recruiters/me/saved-searches", { method: "POST", body: JSON.stringify(data) }, token),
  deleteSavedSearch: (savedSearchId: string, token: string) =>
    request<void>(`/recruiters/me/saved-searches/${savedSearchId}`, { method: "DELETE" }, token),

  listCastingCalls: (params: { category?: TalentCategory } = {}) => {
    const qs = new URLSearchParams();
    if (params.category) qs.set("category", params.category);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<CastingCall[]>(`/casting-calls${suffix}`);
  },
  getCastingCall: (id: string) => request<CastingCall>(`/casting-calls/${id}`),
  createCastingCall: (
    data: {
      title: string;
      description: string;
      category: TalentCategory;
      location?: string;
      compensation?: string;
      application_deadline?: string;
      audition_brief?: string;
      audition_reference_url?: string;
      tags?: string[];
      shoot_details?: string;
      roles: CastingCallRoleInput[];
    },
    token: string
  ) => request<CastingCall>("/casting-calls", { method: "POST", body: JSON.stringify(data) }, token),

  applyToCastingCall: (
    castingCallId: string,
    data: { role_id: string; message?: string; submission_url?: string },
    token: string
  ) =>
    request<Application>(
      `/casting-calls/${castingCallId}/applications`,
      { method: "POST", body: JSON.stringify(data) },
      token
    ),
  listApplicationsForCastingCall: (castingCallId: string, token: string) =>
    request<Application[]>(`/casting-calls/${castingCallId}/applications`, {}, token),
  listMyApplications: (token: string) => request<Application[]>("/talents/me/applications", {}, token),
  updateApplicationStatus: (applicationId: string, status: ApplicationStatus, token: string) =>
    request<Application>(
      `/applications/${applicationId}`,
      { method: "PATCH", body: JSON.stringify({ status }) },
      token
    ),

  inviteTalentToCastingCall: (
    castingCallId: string,
    data: { talent_id: string; message?: string },
    token: string
  ) => request<Invitation>(`/casting-calls/${castingCallId}/invitations`, { method: "POST", body: JSON.stringify(data) }, token),
  listInvitationsForCastingCall: (castingCallId: string, token: string) =>
    request<Invitation[]>(`/casting-calls/${castingCallId}/invitations`, {}, token),
  listMyInvitations: (token: string) => request<Invitation[]>("/talents/me/invitations", {}, token),
  respondToInvitation: (invitationId: string, invitationStatus: "accepted" | "declined", token: string) =>
    request<Invitation>(
      `/invitations/${invitationId}`,
      { method: "PATCH", body: JSON.stringify({ status: invitationStatus }) },
      token
    ),

  listMyAvailability: (token: string) => request<AvailabilityWindow[]>("/talents/me/availability", {}, token),
  addMyAvailability: (data: { day_of_week: number; start_time: string; end_time: string }, token: string) =>
    request<AvailabilityWindow>("/talents/me/availability", { method: "POST", body: JSON.stringify(data) }, token),
  deleteMyAvailability: (windowId: string, token: string) =>
    request<void>(`/talents/me/availability/${windowId}`, { method: "DELETE" }, token),
  listTalentAvailability: (talentId: string) => request<AvailabilityWindow[]>(`/talents/${talentId}/availability`),

  requestBooking: (
    talentId: string,
    data: { start_at: string; end_at: string; message?: string; casting_call_id?: string },
    token: string
  ) => request<Booking>(`/talents/${talentId}/bookings`, { method: "POST", body: JSON.stringify(data) }, token),
  listMyBookingsAsTalent: (token: string) => request<Booking[]>("/talents/me/bookings", {}, token),
  listMyBookingsAsRecruiter: (token: string) => request<Booking[]>("/recruiters/me/bookings", {}, token),
  respondToBooking: (bookingId: string, bookingStatus: "accepted" | "declined", token: string) =>
    request<Booking>(
      `/bookings/${bookingId}/respond`,
      { method: "PATCH", body: JSON.stringify({ status: bookingStatus }) },
      token
    ),
  cancelBooking: (bookingId: string, token: string) =>
    request<Booking>(`/bookings/${bookingId}/cancel`, { method: "PATCH" }, token),
  signBookingAgreement: (bookingId: string, documentUrl: string | undefined, token: string) =>
    request<Booking>(
      `/bookings/${bookingId}/agreement`,
      { method: "PATCH", body: JSON.stringify({ agreement_document_url: documentUrl || null }) },
      token
    ),

  followRecruiter: (recruiterId: string, token: string) =>
    request<Follow>(`/recruiters/${recruiterId}/follow`, { method: "POST" }, token),
  unfollowRecruiter: (recruiterId: string, token: string) =>
    request<void>(`/recruiters/${recruiterId}/follow`, { method: "DELETE" }, token),
  listMyFollowing: (token: string) => request<Follow[]>("/talents/me/following", {}, token),

  trackCastingCallView: (castingCallId: string) =>
    request<void>(`/casting-calls/${castingCallId}/view`, { method: "POST" }),
  getMyAnalytics: (token: string) => request<RecruiterAnalytics>("/recruiters/me/analytics", {}, token),

  leaveReview: (bookingId: string, data: { rating: number; comment?: string }, token: string) =>
    request<Review>(`/bookings/${bookingId}/reviews`, { method: "POST", body: JSON.stringify(data) }, token),
  getTalentReviews: (talentId: string) => request<TalentReviewSummary>(`/talents/${talentId}/reviews`),
  listMyReviews: (token: string) => request<Review[]>("/recruiters/me/reviews", {}, token),

  startConversation: (talentId: string, castingCallId: string | undefined, token: string) =>
    request<ConversationSummary>(
      "/conversations",
      { method: "POST", body: JSON.stringify({ talent_id: talentId, casting_call_id: castingCallId }) },
      token
    ),
  listConversations: (token: string) => request<ConversationSummary[]>("/conversations", {}, token),
  listMessages: (conversationId: string, token: string) =>
    request<Message[]>(`/conversations/${conversationId}/messages`, {}, token),
  sendMessage: (conversationId: string, body: string, token: string) =>
    request<Message>(
      `/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify({ body }) },
      token
    ),

  adminGetStats: (token: string) => request<AdminStats>("/admin/stats", {}, token),
  adminGetFinancialOverview: (token: string) => request<FinancialOverview>("/admin/financial-overview", {}, token),
  adminListUsers: (params: { role?: UserRole; q?: string } = {}, token: string) => {
    const qs = new URLSearchParams();
    if (params.role) qs.set("role", params.role);
    if (params.q) qs.set("q", params.q);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<User[]>(`/admin/users${suffix}`, {}, token);
  },
  adminSetUserActive: (userId: string, isActive: boolean, token: string) =>
    request<User>(
      `/admin/users/${userId}/status`,
      { method: "PATCH", body: JSON.stringify({ is_active: isActive }) },
      token
    ),
  adminGetUserDetail: (userId: string, token: string) =>
    request<AdminUserDetail>(`/admin/users/${userId}`, {}, token),
  adminListPendingTalentVerifications: (token: string) =>
    request<TalentProfile[]>("/admin/verification-requests/talents", {}, token),
  adminApproveTalentVerification: (talentId: string, token: string) =>
    request<TalentProfile>(`/admin/verification-requests/talents/${talentId}/approve`, { method: "POST" }, token),
  adminRejectTalentVerification: (talentId: string, token: string) =>
    request<TalentProfile>(`/admin/verification-requests/talents/${talentId}/reject`, { method: "POST" }, token),
  adminListPendingRecruiterVerifications: (token: string) =>
    request<RecruiterProfile[]>("/admin/verification-requests/recruiters", {}, token),
  adminApproveRecruiterVerification: (recruiterId: string, token: string) =>
    request<RecruiterProfile>(`/admin/verification-requests/recruiters/${recruiterId}/approve`, { method: "POST" }, token),
  adminRejectRecruiterVerification: (recruiterId: string, token: string) =>
    request<RecruiterProfile>(`/admin/verification-requests/recruiters/${recruiterId}/reject`, { method: "POST" }, token),
  adminListCastingCalls: (params: { status?: CastingCallStatus } = {}, token: string) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set("status_filter", params.status);
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<AdminCastingCall[]>(`/admin/casting-calls${suffix}`, {}, token);
  },
  adminSetCastingCallStatus: (castingCallId: string, callStatus: CastingCallStatus, token: string) =>
    request<AdminCastingCall>(
      `/admin/casting-calls/${castingCallId}/status`,
      { method: "PATCH", body: JSON.stringify({ status: callStatus }) },
      token
    ),
};
