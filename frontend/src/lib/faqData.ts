export interface FaqEntry {
  id: string;
  question: string;
  keywords: string[];
  answer: string;
  category: string;
}

// A rule-based (no-LLM) knowledge base for the help chat widget — every answer here is a
// canned, human-written response, matched by keyword overlap in faqMatch.ts. Keep answers
// short (2-4 sentences) and grounded in what the app actually does today.
export const FAQ_ENTRIES: FaqEntry[] = [
  // Getting started
  {
    id: "register",
    question: "How do I create an account?",
    keywords: ["register", "sign up", "create account", "join", "signup", "make an account", "new account"],
    answer:
      "Click Register in the top navigation, choose whether you're a Talent or a Talent Hunt (recruiter), fill in your name, email, and password, and agree to the terms. We'll email you a verification code to confirm your address before you can log in.",
    category: "Getting started",
  },
  {
    id: "verify-email",
    question: "I didn't get my verification code",
    keywords: ["verify", "verification code", "email code", "confirm email", "resend code", "resend"],
    answer:
      "Check your spam folder first. If it's not there, the verification screen has a \"Resend code\" option — click it to get a new code sent to your email.",
    category: "Getting started",
  },
  {
    id: "talent-vs-recruiter",
    question: "What's the difference between a Talent and a Talent Hunt account?",
    keywords: ["talent vs recruiter", "difference between", "account type", "talent hunt account", "recruiter account", "what is a talent hunt"],
    answer:
      "A Talent account is for performers, artists, and creatives who want to build a profile and apply to opportunities. A Talent Hunt (recruiter) account is for companies, agencies, or individuals posting casting calls and searching for talent. You choose one when you register.",
    category: "Getting started",
  },
  {
    id: "forgot-password",
    question: "I forgot my password",
    keywords: ["forgot password", "reset password", "cant log in", "cannot log in", "password reset"],
    answer:
      "On the login page, click \"Forgot password?\", enter your email, and we'll send you a reset link.",
    category: "Getting started",
  },

  // Talent — profile
  {
    id: "create-profile",
    question: "How do I create my talent profile?",
    keywords: ["create profile", "set up profile", "talent profile", "build profile", "make profile"],
    answer:
      "Once you register as Talent and verify your email, your Dashboard shows a short form to set your display name, categories, city, and bio — that creates your profile.",
    category: "Talent profile",
  },
  {
    id: "multi-category",
    question: "Can I list more than one talent category?",
    keywords: ["multiple categories", "multi category", "singer and actor", "more than one category", "categories", "two categories"],
    answer:
      "Yes — your profile supports multiple categories at once (e.g. Acting + Singing + Modeling). Pick all that apply when you create your profile, or update them anytime from Dashboard → Profile.",
    category: "Talent profile",
  },
  {
    id: "edit-profile",
    question: "How do I edit my profile?",
    keywords: ["edit profile", "update profile", "change bio", "update categories", "change profile"],
    answer: "Go to Dashboard → Profile and click \"Edit\" on your profile card to update your bio, city, skills, and categories.",
    category: "Talent profile",
  },
  {
    id: "upload-photo-video",
    question: "How do I upload photos or videos?",
    keywords: ["upload photo", "upload video", "add media", "upload audition", "portfolio upload", "add photo"],
    answer:
      "In Dashboard → Portfolio, use \"Add an audition\" to upload a photo, video, audio clip, or document. Videos are limited to 30 seconds and are automatically compressed after upload — no need to compress them yourself.",
    category: "Talent profile",
  },
  {
    id: "video-length-limit",
    question: "How long can my audition video be?",
    keywords: ["video length", "how long video", "30 seconds", "video duration", "max video length", "video limit", "video too long"],
    answer:
      "Manually uploaded videos (auditions, intro video, work library, application submissions) are capped at 30 seconds. If your file is longer, trim it before uploading — the site will reject it and tell you the exact length it detected.",
    category: "Talent profile",
  },
  {
    id: "intro-video",
    question: "What is the intro video?",
    keywords: ["intro video", "pitch video", "introduce myself", "introduction video"],
    answer:
      "The intro video is a short pitch clip shown at the top of your public profile — your chance to introduce yourself directly. You can upload a file (30s max) or paste a link (e.g. YouTube) instead.",
    category: "Talent profile",
  },
  {
    id: "portfolio-limit",
    question: "How many portfolio items can I add?",
    keywords: ["portfolio limit", "free tier limit", "how many photos", "media limit", "how many videos"],
    answer:
      "Free accounts can add up to 3 portfolio items total, with at most 1 video. Premium accounts get unlimited portfolio items and up to 5 videos.",
    category: "Talent profile",
  },
  {
    id: "credits",
    question: "What are credits?",
    keywords: ["credits", "experience", "past projects", "resume", "cv"],
    answer: "Credits are past-project entries — like a résumé — shown on your public profile. Add them from Dashboard → Portfolio → Credits & experience.",
    category: "Talent profile",
  },
  {
    id: "social-links",
    question: "Can I add my social media links?",
    keywords: ["social links", "instagram", "youtube link", "spotify link", "social media", "tiktok"],
    answer:
      "Yes — Dashboard → Profile → Social links lets you add links to Instagram, YouTube, Spotify, and other platforms so talent hunts can find you elsewhere too.",
    category: "Talent profile",
  },

  // Talent — bookings/availability
  {
    id: "availability",
    question: "How do I set my availability?",
    keywords: ["set availability", "availability window", "when am i free", "booking availability", "my schedule"],
    answer:
      "In Dashboard → Bookings, add recurring weekly windows (day + start/end time) under Availability. Talent hunts can then request to book a session with you during those windows.",
    category: "Bookings",
  },
  {
    id: "work-calendar",
    question: "What is the work calendar?",
    keywords: ["work calendar", "calendar", "busy dates"],
    answer:
      "The Work calendar (Dashboard → Bookings) shows your confirmed bookings and any gigs you add yourself, all in one place — click a day to add your own entry.",
    category: "Bookings",
  },
  {
    id: "booking-request",
    question: "How do bookings work?",
    keywords: ["booking request", "how booking works", "accept booking", "decline booking", "book a talent", "book someone", "hire someone for a session"],
    answer:
      "A talent hunt can request a time slot within your declared availability. You'll see the request in Dashboard → Bookings, where you can Accept or Decline it.",
    category: "Bookings",
  },

  // Talent — applications
  {
    id: "apply-role",
    question: "How do I apply to a casting call?",
    keywords: ["apply", "apply to role", "apply to casting call", "submit application", "audition for a role"],
    answer:
      "Open a talent hunt, pick the role you want (if there are multiple), and click Apply. You can attach a message, a link to your audition, or upload a video/audio file directly (30s max for uploads).",
    category: "Applications",
  },
  {
    id: "application-status",
    question: "How do I check my application status?",
    keywords: ["application status", "did they see my application", "track application", "application seen"],
    answer:
      "Dashboard → Activity → My applications lists every application you've submitted along with its status (pending, shortlisted, accepted, rejected) and whether the recruiter has seen it yet.",
    category: "Applications",
  },
  {
    id: "invitations",
    question: "What are invitations?",
    keywords: ["invitation", "invited", "direct invite", "invitations"],
    answer:
      "Invitations are direct requests from a talent hunt inviting you to a specific role, without you having to apply first. Find them in Dashboard → Activity → Invitations, where you can Accept or Decline.",
    category: "Applications",
  },
  {
    id: "offer-contract",
    question: "What happens after I get accepted?",
    keywords: ["offer", "contract", "accepted", "sign agreement", "how do i get accepted", "hired"],
    answer:
      "Being accepted isn't automatic — a recruiter first sends you a contract offer (visible in Dashboard → Bookings) with drafted terms. Once you review and sign it, and the recruiter signs too, only then does your application become Accepted.",
    category: "Applications",
  },

  // Talent — messaging & following
  {
    id: "messaging",
    question: "How does messaging work?",
    keywords: ["messaging", "message a recruiter", "chat", "read receipt", "seen", "saw my message", "did they see my message"],
    answer:
      "Messages between you and a talent hunt live under Messages in the top nav. Each message shows a timestamp, and you'll see \"Seen\" once the other person has opened the conversation.",
    category: "Messaging",
  },
  {
    id: "following",
    question: "How do I follow a talent hunt?",
    keywords: ["follow", "following", "unfollow"],
    answer: "Click Follow on any talent hunt's casting call page to get notified about their new postings. Manage who you follow from Dashboard → Activity → Following.",
    category: "Messaging",
  },

  // Talent — premium
  {
    id: "talent-premium",
    question: "What do I get with Premium?",
    keywords: ["premium", "upgrade", "talent premium benefits", "subscription benefits", "premium features", "upgrade my account", "upgrade to premium", "go premium"],
    answer:
      "Talent Premium unlocks unlimited portfolio items, up to 5 audition videos, boosted placement in search, a dedicated work library/reel, who-viewed-your-profile visibility, and exact read-receipt times on messages.",
    category: "Billing",
  },

  // Recruiter — posting & board
  {
    id: "post-casting-call",
    question: "How do I post a talent hunt?",
    keywords: ["post talent hunt", "post job", "create casting call", "new posting", "post a role", "post a casting call", "create a casting call"],
    answer:
      "From Dashboard → Talent hunts, fill in the \"Post a talent hunt\" form: title, category, description, and at least one role. Premium recruiters can add multiple roles to a single posting.",
    category: "Recruiter",
  },
  {
    id: "applicant-board",
    question: "How do I review applicants?",
    keywords: ["review applicants", "applicant board", "manage applications", "shortlist", "who applied", "see who applied", "view applicants"],
    answer:
      "Click Manage on any of your talent hunts to open the applicant board — search by name, sort by date or match score, and move applicants between Pending, Shortlisted, Accepted, and Rejected columns.",
    category: "Recruiter",
  },
  {
    id: "message-applicant",
    question: "Can I message an applicant directly?",
    keywords: ["message applicant", "contact talent", "message talent"],
    answer: "Yes — click the Message button right on an applicant's card in the board to start a conversation, without needing to open their full profile first.",
    category: "Recruiter",
  },
  {
    id: "send-offer",
    question: "How do I hire someone / send an offer?",
    keywords: ["send offer", "hire", "contract offer", "how to accept applicant", "make an offer"],
    answer:
      "From the applicant board, click Send Offer on an applicant's card to draft a branded contract (no date/time needed). Once the talent signs and you sign too, their application automatically becomes Accepted.",
    category: "Recruiter",
  },

  // Recruiter — discovery
  {
    id: "saved-talent",
    question: "How do I save a talent profile?",
    keywords: ["save talent", "saved talent", "shortlist talent", "bookmark talent"],
    answer: "Click Save talent on any talent's public profile. Saved profiles appear in Dashboard → Discover talent → Saved talent.",
    category: "Recruiter",
  },
  {
    id: "talent-lists",
    question: "What are talent lists?",
    keywords: ["talent lists", "pipeline", "crm", "organize candidates"],
    answer:
      "Talent lists are a Premium feature for organizing saved talent into named lists per project (e.g. \"Monsoon Diaries — Lead\"). Manage them from Dashboard → Discover talent → Talent lists.",
    category: "Recruiter",
  },
  {
    id: "saved-search",
    question: "Can I save my search filters?",
    keywords: ["saved search", "save filters", "save my search"],
    answer:
      "Yes, saved searches are a Premium feature — set your filters on the Browse talent page and save them from Dashboard → Discover talent → Saved searches to reapply them anytime.",
    category: "Recruiter",
  },
  {
    id: "recruiter-premium",
    question: "What do I get with Recruiter Premium?",
    keywords: ["recruiter premium", "premium benefits recruiter", "upgrade recruiter"],
    answer:
      "Recruiter Premium unlocks unlimited postings, AI match scoring on applicants, talent CRM lists, bulk invite, early access to new talent sign-ups, and exclusive premium-only talent hunts.",
    category: "Recruiter",
  },

  // Billing
  {
    id: "pricing",
    question: "How much does Premium cost?",
    keywords: ["price", "pricing", "how much", "cost", "subscription price"],
    answer:
      "Current pricing is shown on the Pricing page, with separate plans for Talent and Talent Hunt accounts. Prices are locked in at the rate you signed up for even if they change later.",
    category: "Billing",
  },
  {
    id: "free-trial",
    question: "Is there a free trial?",
    keywords: ["free trial", "trial period"],
    answer: "Yes — starting Premium begins with a free trial before any charge. Start it from your Dashboard's Membership tab or the Pricing page.",
    category: "Billing",
  },
  {
    id: "cancel-subscription",
    question: "How do I cancel my subscription?",
    keywords: ["cancel subscription", "cancel premium", "stop paying", "cancel plan"],
    answer:
      "Go to Dashboard → Membership and click Cancel subscription. You'll keep Premium until the end of your current billing period, and you can reactivate anytime before then.",
    category: "Billing",
  },
  {
    id: "payment-history",
    question: "Where can I see my payment history?",
    keywords: ["payment history", "billing history", "past payments", "invoices"],
    answer: "Your payment history is listed on the Membership tab of your Dashboard, below your subscription status.",
    category: "Billing",
  },

  // Community & general
  {
    id: "community",
    question: "What is the Community section?",
    keywords: ["community", "titles", "discussions", "discussion board"],
    answer: "Community is a public hub with a Titles catalog (rate and review films/shows/songs) and Discussion boards, open to any logged-in talent or recruiter.",
    category: "Community",
  },
  {
    id: "report-content",
    question: "How do I report something?",
    keywords: ["report", "flag content", "inappropriate", "abuse", "report a problem"],
    answer: "Most profiles, posts, and messages have a Report button — click it to flag content for our team to review.",
    category: "Community",
  },
  {
    id: "notifications",
    question: "How do notifications work?",
    keywords: ["notifications", "notification bell", "alerts", "bell icon"],
    answer:
      "The bell icon in the top nav shows a badge when something happens — a new application, message, or booking update. Click it to see recent notifications and jump straight to what changed.",
    category: "General",
  },
  {
    id: "contact-support",
    question: "How do I contact support?",
    keywords: ["contact support", "help", "support", "talk to someone", "contact us", "delete my account", "close my account", "deactivate account"],
    answer: "Use the \"Report a problem\" link in the footer, or the Report button on the relevant page, to reach our team directly — including for account deletion requests, which our team handles manually.",
    category: "General",
  },
  {
    id: "get-verified",
    question: "How do I get a verified badge on my profile?",
    keywords: ["get verified", "verification badge", "verify my profile", "blue check", "request verification", "how to get verified"],
    answer:
      "From Dashboard → Profile, click \"Request verification.\" Our team reviews requests manually (it isn't instant) — once approved, a verified badge appears on your public profile.",
    category: "Talent profile",
  },
  {
    id: "boost-visibility",
    question: "How do I get more views or show up higher in search?",
    keywords: ["more visibility", "get discovered", "boost my profile", "featured placement", "show up in search", "more views", "get noticed"],
    answer:
      "Premium talent get boosted placement in search results and a rotating spot in Featured Talent, on top of the profile-views insights that show who's been checking you out. A complete, verified profile with recent portfolio items also ranks higher organically.",
    category: "Talent profile",
  },
];
