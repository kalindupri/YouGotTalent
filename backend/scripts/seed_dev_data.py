"""Seed the dev database with sample talent profiles and casting calls for demo purposes.

Uses placeholder avatar images (pravatar.cc) rather than real people's photos. All accounts
are prefixed `seed_` so they're easy to find and remove later. Casting calls are detailed,
category-specific postings (synopsis, role breakdown, submission instructions, shoot
logistics) rather than one-line placeholders, so the demo data reads like real listings.

Usage:
    python scripts/seed_dev_data.py
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.casting_call import CastingCall, CastingCallStatus  # noqa: E402
from app.models.casting_call_role import CastingCallRole  # noqa: E402
from app.models.credit import Credit  # noqa: E402
from app.models.media import Media, MediaType  # noqa: E402
from app.models.recruiter_profile import RecruiterProfile  # noqa: E402
from app.models.talent_profile import TalentProfile  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

SEED_PASSWORD = "SeedPass123!"

FIRST_NAMES = [
    "Ishara", "Dilshan", "Kavindi", "Nadeesha", "Chamara", "Hasini", "Ruwan", "Tharushi",
    "Sanduni", "Kasun", "Nimali", "Lahiru", "Dinithi", "Chathura", "Yasodha", "Nuwan",
    "Piumi", "Tharindu", "Sachini", "Isuru", "Anjali", "Malith", "Poornima", "Gayan",
    "Sewwandi", "Roshan", "Dulani", "Chanaka", "Vindya", "Amila",
]
LAST_NAMES = [
    "Fernando", "Silva", "Perera", "Jayasuriya", "Bandara", "Rathnayake", "Wickramasinghe",
    "Gunawardena", "Dissanayake", "Weerasinghe", "Rajapaksa", "Karunaratne", "Senanayake",
    "Amarasinghe", "Herath", "Mendis", "Wijesinghe", "Kumara",
]
CITIES = ["Colombo", "Kandy", "Galle", "Jaffna", "Negombo", "Matara", "Kurunegala", "Anuradhapura", "Batticaloa", "Ratnapura"]

CATEGORY_SKILLS = {
    "acting": ["drama", "comedy", "thriller", "Sinhala theatre", "screen acting"],
    "singing": ["playback singing", "carnatic classical", "sinhala pop", "opera"],
    "dancing": ["Kandyan", "contemporary", "hip-hop", "Bharatanatyam"],
    "painting": ["oil", "watercolor", "digital", "abstract"],
    "script_writing": ["screenplay", "teleplay", "sinhala dialogue writing"],
    "photography": ["portrait", "wedding", "product", "wildlife"],
    "music": ["guitar", "tabla", "jazz", "classical"],
    "choreography": ["Kandyan", "contemporary", "Bollywood"],
    "comedy": ["stand-up", "sketch", "improv"],
    "voice_over": ["narration", "character voices", "dubbing"],
    "direction": ["drama", "documentary", "advertising"],
    "modeling": ["runway", "print", "commercial"],
    "design": ["graphic design", "fashion design", "set design"],
    "other": ["special skills", "stunt work", "puppetry"],
}
CATEGORIES = list(CATEGORY_SKILLS.keys())

BIO_TEMPLATES = [
    "Passionate {category} performer based in {city} with {years} years of experience across stage and "
    "screen. Always looking for the next project that pushes my range as a performer.",
    "{category_title} professional based in {city}, specializing in work for film, TV, and live events. "
    "{years} years in the industry and counting — comfortable on set, on stage, or in the studio.",
    "Award-nominated talent working in {category} for over {years} years. I trained formally and have "
    "since built a career mixing commercial work with passion projects close to my heart.",
    "Freelance {category} professional based in {city}, available for local and remote projects. I bring "
    "reliability, punctuality, and a collaborative attitude to every job I take on.",
    "{years}-year veteran of the {category} scene in {city}. I love working with new directors and "
    "producers and I'm always up for a challenge that takes me outside my comfort zone.",
]

COMPANIES = [
    "Lotus Films", "Ceylon Casting Co.", "Ruhunu Productions", "Serendib Studios",
    "Indigo Media House", "Cinnamon Reel Works", "Kandy Creative Collective", "Blue Elephant Films",
    "Pearl Isle Productions", "Monsoon Media Group",
]

BUILDS = ["athletic", "slim", "average", "muscular", "curvy"]
HAIR_COLORS = ["black", "dark brown", "brown", "auburn"]
EYE_COLORS = ["brown", "dark brown", "hazel", "black"]
ETHNICITIES = ["South Asian", "Sri Lankan Sinhala", "Sri Lankan Tamil", "South Asian / Burgher"]
VOCAL_RANGES = ["soprano", "mezzo-soprano", "alto", "tenor", "baritone", "bass"]
VOICE_TYPES = ["belt/pop", "classical", "legit musical theatre", "R&B/soul"]
INSTRUMENTS = ["guitar", "tabla", "violin", "sitar", "piano", "flute"]
MEDIUMS = ["oil on canvas", "watercolor", "acrylic", "digital illustration"]
LANGUAGE_SETS = ["Sinhala, English", "Sinhala, English, Tamil", "English, Tamil", "Sinhala, Tamil"]
CAMERA_GEAR = ["Sony A7IV, 24-70mm f/2.8", "Canon R6, 50mm f/1.8", "Nikon Z6 II, 24-105mm"]
PERFORMANCE_STYLES = ["observational", "improv", "sketch", "satire"]
ACCENT_SPECIALTIES = ["British RP", "American General", "Neutral Sri Lankan English"]
DIRECTION_GENRES = ["drama", "documentary", "advertising", "comedy"]
SOFTWARE_TOOLS = ["Figma, Adobe Illustrator", "Adobe Photoshop, Procreate", "Blender, Adobe XD"]

CREDIT_TYPES_BY_CATEGORY = {
    "acting": ["film", "television", "theatre"],
    "singing": ["music", "event", "online"],
    "dancing": ["event", "theatre", "online"],
    "painting": ["event", "online", "other"],
    "script_writing": ["television", "film", "theatre"],
    "photography": ["commercial", "online", "event"],
    "music": ["music", "event", "online"],
    "choreography": ["event", "theatre", "television"],
    "comedy": ["event", "online", "theatre"],
    "voice_over": ["voice", "commercial", "online"],
    "direction": ["film", "television", "other"],
    "modeling": ["commercial", "online", "event"],
    "design": ["theatre", "television", "other"],
    "other": ["other", "event", "online"],
}
CREDIT_ROLES = ["Lead role", "Supporting role", "Featured role", "Ensemble", "Freelance contributor", "Principal"]
PROJECT_ADJECTIVES = ["Monsoon", "Golden", "Silent", "Broken", "Crimson", "Midnight", "Coastal", "Hidden", "Last", "Endless"]
PROJECT_NOUNS = ["Diaries", "Skies", "Harbor", "Echoes", "Horizon", "Garden", "Tides", "Legacy", "Reverie", "Crossing"]


def random_height() -> str:
    feet, inches = 5, random.randint(0, 11)
    cm = 150 + random.randint(0, 45)
    return f"{feet}'{inches}\" / {cm}cm"


def random_project_title() -> str:
    return f"{random.choice(PROJECT_ADJECTIVES)} {random.choice(PROJECT_NOUNS)}"


def build_attributes(category: str) -> dict[str, str] | None:
    if category == "acting":
        return {
            "height": random_height(),
            "weight": f"{55 + random.randint(0, 30)}kg",
            "build": random.choice(BUILDS),
            "hair_color": random.choice(HAIR_COLORS),
            "eye_color": random.choice(EYE_COLORS),
            "playing_age": f"{20 + random.randint(0, 10)}-{35 + random.randint(0, 20)}",
            "ethnicity": random.choice(ETHNICITIES),
        }
    if category == "modeling":
        return {
            "height": random_height(),
            "weight": f"{48 + random.randint(0, 25)}kg",
            "bust_chest": f"{32 + random.randint(0, 8)}\" / {80 + random.randint(0, 20)}cm",
            "waist": f"{24 + random.randint(0, 8)}\" / {60 + random.randint(0, 20)}cm",
            "hips": f"{34 + random.randint(0, 8)}\" / {86 + random.randint(0, 20)}cm",
            "shoe_size": f"UK {random.randint(4, 11)}",
            "hair_color": random.choice(HAIR_COLORS),
            "eye_color": random.choice(EYE_COLORS),
        }
    if category in ("dancing", "choreography"):
        return {"height": random_height(), "build": random.choice(BUILDS)}
    if category == "singing":
        return {"vocal_range": random.choice(VOCAL_RANGES), "voice_type": random.choice(VOICE_TYPES)}
    if category == "music":
        return {"primary_instrument": random.choice(INSTRUMENTS)}
    if category == "painting":
        return {"primary_medium": random.choice(MEDIUMS)}
    if category == "script_writing":
        return {"primary_language": random.choice(["Sinhala", "English", "Tamil"])}
    if category == "photography":
        return {"camera_gear": random.choice(CAMERA_GEAR)}
    if category == "comedy":
        return {"performance_style": random.choice(PERFORMANCE_STYLES)}
    if category == "voice_over":
        return {"languages_spoken": random.choice(LANGUAGE_SETS), "accent_specialties": random.choice(ACCENT_SPECIALTIES)}
    if category == "direction":
        return {"primary_genre": random.choice(DIRECTION_GENRES)}
    if category == "design":
        return {"software_tools": random.choice(SOFTWARE_TOOLS)}
    return None


def build_credits(talent_profile_id, category: str) -> list[Credit]:
    project_types = CREDIT_TYPES_BY_CATEGORY.get(category, ["other"])
    credits = []
    for _ in range(random.randint(1, 3)):
        year = 2019 + random.randint(0, 6)
        credits.append(
            Credit(
                talent_profile_id=talent_profile_id,
                project_type=random.choice(project_types),
                title=random_project_title(),
                role=random.choice(CREDIT_ROLES),
                company_or_director=random.choice(COMPANIES),
                location=random.choice(CITIES),
                date_label=str(year),
            )
        )
    return credits


# One fully detailed, category-specific posting per talent category — modeled on the shape of
# a real casting listing (synopsis, role breakdown with eligibility criteria, what to submit,
# shoot/session logistics, pay, deadline) rather than a one-line placeholder.
CATEGORY_JOBS = {
    "acting": {
        "title": "Lead & Supporting Roles — Independent Feature Film \"Monsoon Diaries\"",
        "description": (
            "Ruhunu Productions is casting principal and supporting roles for Monsoon Diaries, an "
            "independent feature about three generations of a tea-estate family navigating change in "
            "the hill country. We're looking for grounded, naturalistic performers comfortable working "
            "in both Sinhala and English, with the range to carry emotionally driven, dialogue-heavy "
            "scenes.\n\nThis is a SAG-equivalent non-union indie shoot with a small, close-knit crew. "
            "Prior feature or teledrama credits are a plus but not required — we care most about "
            "chemistry read tapes and audition quality."
        ),
        "roles": [
            {"title": "Kumari (Lead)", "criteria": "Female, 28-38, fluent Sinhala/English, singing ability a plus", "compensation": "LKR 25,000/day"},
            {"title": "Siripala (Supporting)", "criteria": "Male, 55-70, native Sinhala speaker", "compensation": "LKR 15,000/day"},
            {"title": "Featured Estate Worker (Ensemble)", "criteria": "Any gender, 20-50, comfortable with physical outdoor work", "compensation": "LKR 8,000/day"},
        ],
        "audition_brief": (
            "Submit a 1-2 minute self-tape of a dramatic monologue of your choice (Sinhala or English), "
            "plus a slate stating your height, age range, and languages spoken. Shortlisted actors will "
            "be invited to an in-person chemistry read in Colombo."
        ),
        "tags": ["Feature Film", "Drama", "Non-union", "Sinhala/English"],
        "shoot_details": "Principal photography: 3 weeks across Colombo and the Nuwara Eliya hill country. Meals, local transport, and accommodation for out-of-town cast provided.",
        "compensation": "LKR 8,000–25,000/day depending on role",
        "location": "Colombo",
    },
    "singing": {
        "title": "Lead Vocalist — National Tea Brand TV Commercial Jingle",
        "description": (
            "Indigo Media House is producing a 30-second national TV commercial for a leading Ceylon "
            "tea brand and needs a lead vocalist to record an original jingle blending traditional "
            "Sinhala folk melody with a modern pop arrangement. The recording will be used across TV, "
            "radio, and digital for a 12-month campaign.\n\nWe're after a warm, distinctive voice that "
            "feels authentic and inviting rather than overly polished — think heritage brand, not "
            "generic jingle."
        ),
        "roles": [
            {"title": "Lead Vocalist", "criteria": "Any gender, 20-45, strong command of Sinhala folk phrasing", "compensation": "LKR 60,000 flat + usage buyout"},
            {"title": "Backing Vocalist (x2)", "criteria": "Any gender, harmony experience preferred", "compensation": "LKR 20,000 flat"},
        ],
        "audition_brief": (
            "Send an audio or video clip of yourself singing any Sinhala folk or pop song, unaccompanied "
            "or with simple guitar/harmonium backing. Studio session will include a short vocal warm-up "
            "and 2-3 takes with the composer present."
        ),
        "tags": ["TV Commercial", "Jingle", "Studio Recording", "Sinhala Folk/Pop"],
        "shoot_details": "One studio session, half-day, at a Colombo recording studio. Exact date to be confirmed with shortlisted vocalists.",
        "compensation": "LKR 20,000–60,000 depending on role, plus usage buyout",
        "location": "Colombo",
    },
    "dancing": {
        "title": "Contemporary/Kandyan Fusion Dancers — Cultural Showcase Tour",
        "description": (
            "Serendib Studios is assembling a touring dance company for a cultural showcase blending "
            "traditional Kandyan forms with contemporary movement, performing at hotels and cultural "
            "centres across the south coast over a six-week season. Choreography draws on classical "
            "technique but is built for a mixed-audience stage show, not a strictly traditional "
            "performance context.\n\nWe want dancers with strong technical grounding who can also take "
            "direction into more contemporary, expressive movement."
        ),
        "roles": [
            {"title": "Principal Dancer (x2)", "criteria": "Any gender, 18-30, formal Kandyan or Bharatanatyam training required", "compensation": "LKR 12,000/show"},
            {"title": "Ensemble Dancer (x6)", "criteria": "Any gender, 18-35, at least 2 years dance training", "compensation": "LKR 7,000/show"},
        ],
        "audition_brief": (
            "In-person audition: prepare a 90-second traditional piece of your choice, followed by a "
            "short contemporary combo taught on the day. Please arrive warmed up and in practice attire."
        ),
        "tags": ["Live Show", "Kandyan Fusion", "Contemporary", "Touring"],
        "shoot_details": "Rehearsals in Galle (2 weeks), touring venues across Galle, Matara, and Hikkaduwa (4 weeks). Transport and accommodation provided during the tour.",
        "compensation": "LKR 7,000–12,000/show",
        "location": "Galle",
    },
    "painting": {
        "title": "Mural Artist — Colombo Urban Art Festival Commission",
        "description": (
            "Cinnamon Reel Works is coordinating public art commissions for this year's Colombo Urban "
            "Art Festival and is seeking a muralist to design and paint a large-scale outdoor piece "
            "celebrating Sri Lankan biodiversity, on a wall facing a busy pedestrian promenade. The "
            "commission includes full creative direction over concept and palette within the festival's "
            "biodiversity theme."
        ),
        "roles": [
            {"title": "Lead Muralist", "criteria": "Portfolio of prior large-scale/outdoor work required", "compensation": "LKR 150,000 flat, materials included"},
            {"title": "Assistant Painter (x2)", "criteria": "Comfortable working at height on scaffolding", "compensation": "LKR 30,000 flat"},
        ],
        "audition_brief": (
            "Submit a portfolio (digital or physical) of at least 5 prior works, with at least one "
            "outdoor/mural-scale piece if available. Shortlisted artists will present a concept sketch "
            "for the biodiversity theme."
        ),
        "tags": ["Mural", "Public Art", "Festival Commission", "Outdoor"],
        "shoot_details": "Painting window: 10 days, weather permitting, at a site in Colombo Fort. Scaffolding and materials supplied by the festival.",
        "compensation": "LKR 30,000–150,000 depending on role",
        "location": "Colombo",
    },
    "script_writing": {
        "title": "Staff Writer — 26-Episode Sinhala Teledrama",
        "description": (
            "Blue Elephant Films is staffing the writers' room for a new 26-episode primetime teledrama "
            "centred on a multi-generational family business drama, and is looking for a staff writer to "
            "join two senior writers in breaking story and drafting episodes. Strong Sinhala dialogue "
            "instincts and comfort with a fast broadcast production schedule are essential."
        ),
        "roles": [
            {"title": "Staff Writer", "criteria": "Prior teledrama, radio drama, or long-form fiction writing credits preferred", "compensation": "LKR 40,000/episode"},
        ],
        "audition_brief": (
            "Submit a writing sample (any format: teledrama episode, short screenplay, or short story) "
            "plus a one-page pitch for a family-drama storyline you'd want to explore in the series."
        ),
        "tags": ["Teledrama", "Writers' Room", "Sinhala Dialogue", "Long-form"],
        "shoot_details": "Writers' room meets twice weekly in Colombo; remote drafting between sessions. Production targets one block of 6 episodes per writing cycle.",
        "compensation": "LKR 40,000/episode",
        "location": "Colombo",
    },
    "photography": {
        "title": "Lead Photographer — Destination Wedding Season Package",
        "description": (
            "Pearl Isle Productions is building a roster of photographers for the upcoming destination "
            "wedding season along the south coast and is looking for a lead shooter comfortable running "
            "a full-day wedding solo or with a second shooter, from getting-ready shots through to the "
            "reception. Editing style should be natural and warm rather than heavily filtered."
        ),
        "roles": [
            {"title": "Lead Wedding Photographer", "criteria": "Portfolio of at least 3 full weddings shot required, own equipment", "compensation": "LKR 45,000/event"},
            {"title": "Second Shooter", "criteria": "Comfortable with candid/documentary style", "compensation": "LKR 18,000/event"},
        ],
        "audition_brief": (
            "Send a link to an online portfolio or gallery showing at least 3 full wedding shoots, plus "
            "your typical turnaround time for edited galleries."
        ),
        "tags": ["Wedding", "Destination", "Full-day Coverage", "South Coast"],
        "shoot_details": "Bookings run through the December-March wedding season, primarily in Galle, Mirissa, and Bentota. Travel costs covered for events outside Colombo.",
        "compensation": "LKR 18,000–45,000/event",
        "location": "Galle",
    },
    "music": {
        "title": "Session Guitarist — Album Recording, Fusion/Jazz Project",
        "description": (
            "Kandy Creative Collective is recording a debut fusion-jazz album blending Sri Lankan folk "
            "melodic lines with jazz harmony, and is looking for a session guitarist comfortable reading "
            "chord charts on the fly and improvising within a jazz idiom. Sessions will be led by the "
            "album's composer/bandleader."
        ),
        "roles": [
            {"title": "Session Guitarist", "criteria": "Strong jazz comping and soloing ability, reads chord charts", "compensation": "LKR 15,000/session"},
            {"title": "Tabla Player", "criteria": "Classical training preferred, comfortable with fusion arrangements", "compensation": "LKR 12,000/session"},
        ],
        "audition_brief": (
            "Submit an audio or video clip demonstrating jazz comping and a short improvised solo over "
            "any backing track of your choice."
        ),
        "tags": ["Album Recording", "Fusion/Jazz", "Session Work", "Studio"],
        "shoot_details": "Recording sessions spread across 4 half-days at a Kandy studio over three weeks.",
        "compensation": "LKR 12,000–15,000/session",
        "location": "Kandy",
    },
    "choreography": {
        "title": "Choreographer — Corporate Awards Night Opening Number",
        "description": (
            "Monsoon Media Group is producing a corporate awards night for a major local brand and "
            "needs a choreographer to design and stage a 4-minute opening number for a cast of 10 "
            "dancers, blending contemporary and traditional Sri Lankan styles to open the evening with "
            "energy and spectacle."
        ),
        "roles": [
            {"title": "Choreographer", "criteria": "Prior experience staging corporate/event pieces preferred", "compensation": "LKR 80,000 flat"},
        ],
        "audition_brief": (
            "Share a portfolio or video reel of previously choreographed pieces, ideally including at "
            "least one corporate or large-stage production."
        ),
        "tags": ["Corporate Event", "Opening Number", "Contemporary/Traditional Fusion"],
        "shoot_details": "Two weeks of rehearsal in Colombo followed by a single live performance at the event venue.",
        "compensation": "LKR 80,000 flat",
        "location": "Colombo",
    },
    "comedy": {
        "title": "Stand-up Comedians — New Talent Night, Colombo Comedy Club",
        "description": (
            "Lotus Films is co-producing a recurring New Talent Night at a Colombo comedy club and is "
            "looking for stand-up comedians to perform short sets in front of a live audience, with the "
            "best sets considered for a filmed comedy special later in the year."
        ),
        "roles": [
            {"title": "Stand-up Comedian", "criteria": "5-7 minutes of original material, any language mix of Sinhala/English/Tamil", "compensation": "LKR 5,000/set + tips"},
        ],
        "audition_brief": (
            "Submit a video of a previous live set (any length) or, if you don't have one yet, a "
            "self-recorded 3-minute set performed to camera."
        ),
        "tags": ["Stand-up", "Live Show", "New Talent Night", "Comedy Special"],
        "shoot_details": "Monthly show at a Colombo comedy club; filmed special recorded later in the year for standout performers.",
        "compensation": "LKR 5,000/set + tips",
        "location": "Colombo",
    },
    "voice_over": {
        "title": "Voice Artist — E-Learning Platform Narration (Sinhala & English)",
        "description": (
            "Ceylon Casting Co. is producing narration for a national e-learning platform's secondary "
            "school curriculum modules and needs voice artists who can deliver clear, warm, "
            "instructional narration in both Sinhala and English, sustaining energy and clarity across "
            "long-form recording sessions."
        ),
        "roles": [
            {"title": "Sinhala Narrator", "criteria": "Native Sinhala speaker, clear diction, home studio a plus", "compensation": "LKR 3,500/finished hour"},
            {"title": "English Narrator", "criteria": "Neutral/international accent preferred", "compensation": "LKR 3,500/finished hour"},
        ],
        "audition_brief": (
            "Record a 60-second sample reading the attached sample script in a clear, instructional "
            "tone, in either Sinhala or English (or both)."
        ),
        "tags": ["E-Learning", "Narration", "Sinhala/English", "Long-form"],
        "shoot_details": "Remote recording accepted if audio quality meets spec; studio sessions also available in Colombo.",
        "compensation": "LKR 3,500/finished hour",
        "location": "Colombo",
    },
    "direction": {
        "title": "Assistant Director — Documentary Series on Sri Lankan Tea Estates",
        "description": (
            "Serendib Studios is producing a 4-part documentary series on the history and future of Sri "
            "Lankan tea estates and needs an assistant director to support the director across "
            "scheduling, location logistics, and on-set coordination during shoots across the hill "
            "country."
        ),
        "roles": [
            {"title": "Assistant Director", "criteria": "Prior AD or production management experience on documentary or broadcast work", "compensation": "LKR 10,000/day"},
        ],
        "audition_brief": (
            "Send a CV with relevant credits, plus a short note on your experience managing shoot-day "
            "logistics on location."
        ),
        "tags": ["Documentary", "Assistant Director", "Location Shoot", "Hill Country"],
        "shoot_details": "Four separate shoot blocks across Nuwara Eliya, Haputale, and Ella over two months.",
        "compensation": "LKR 10,000/day",
        "location": "Nuwara Eliya",
    },
    "modeling": {
        "title": "Runway & Print Models — Colombo Fashion Week",
        "description": (
            "Cinnamon Reel Works is casting runway and print models for a Colombo Fashion Week designer "
            "showcase, spanning both the live runway show and the accompanying print/social media "
            "lookbook campaign. Designers are looking for a range of heights, builds, and looks to "
            "reflect an inclusive casting brief."
        ),
        "roles": [
            {"title": "Runway Model", "criteria": "Female, 168cm+, walking experience preferred", "compensation": "LKR 20,000/show"},
            {"title": "Print/Lookbook Model", "criteria": "Any gender, any height, strong camera presence", "compensation": "LKR 15,000/session"},
        ],
        "audition_brief": (
            "Submit current polaroid-style photos (no heavy filters/makeup) with height, measurements, "
            "and shoe size, plus a short walking video for runway applicants."
        ),
        "tags": ["Fashion Week", "Runway", "Print Campaign", "Lookbook"],
        "shoot_details": "Runway show + rehearsals over 2 days in Colombo; print/lookbook shoot on a separate studio day.",
        "compensation": "LKR 15,000–20,000",
        "location": "Colombo",
    },
    "design": {
        "title": "Set & Costume Designer — Period Teledrama Production",
        "description": (
            "Indigo Media House is producing a period teledrama set in 1960s Ceylon and is looking for "
            "a set and costume designer to establish the visual world of the show, working closely with "
            "the director to source or build era-accurate costumes and dressing for a mix of studio and "
            "location sets."
        ),
        "roles": [
            {"title": "Set & Costume Designer", "criteria": "Prior period or theatrical design experience preferred", "compensation": "LKR 100,000/production block"},
            {"title": "Assistant Designer", "criteria": "Sourcing and tailoring experience a plus", "compensation": "LKR 35,000/production block"},
        ],
        "audition_brief": (
            "Share a portfolio of previous design work (period or contemporary), including any sketches, "
            "mood boards, or photos of completed costume/set builds."
        ),
        "tags": ["Period Drama", "Costume Design", "Set Design", "Teledrama"],
        "shoot_details": "Pre-production and build over 6 weeks in Colombo, followed by ongoing on-set support through the shoot schedule.",
        "compensation": "LKR 35,000–100,000 per production block",
        "location": "Colombo",
    },
    "other": {
        "title": "Stunt Performers & Specialty Act — Live Action Sequence, Feature Film",
        "description": (
            "Ruhunu Productions needs stunt performers and a specialty act (fire performance or "
            "acrobatics) for a live-action street chase and market sequence in an upcoming feature film. "
            "Safety training and prior stunt coordination sign-off are required for all physical stunt "
            "work."
        ),
        "roles": [
            {"title": "Stunt Performer", "criteria": "Prior stunt or professional physical performance training required, safety certification a plus", "compensation": "LKR 20,000/day"},
            {"title": "Specialty Act (Fire/Acrobatics)", "criteria": "Portfolio or reel of prior performances required", "compensation": "LKR 25,000/day"},
        ],
        "audition_brief": (
            "Submit a reel or video demonstrating relevant stunt or specialty skills, plus details of any "
            "safety certifications or stunt coordinator references."
        ),
        "tags": ["Feature Film", "Stunts", "Specialty Act", "Action Sequence"],
        "shoot_details": "Two shoot days on a closed set in Colombo, with a certified stunt coordinator on-site throughout.",
        "compensation": "LKR 20,000–25,000/day",
        "location": "Colombo",
    },
}


def seed_talents(db, count: int = 100) -> None:
    existing = {u.email for u in db.query(User.email).filter(User.email.like("seed_talent_%")).all()}
    created = 0
    i = 0
    while created < count:
        i += 1
        email = f"seed_talent_{i:03d}@example.com"
        if email in existing:
            continue
        category = CATEGORIES[created % len(CATEGORIES)]
        first, last = random.choice(FIRST_NAMES), random.choice(LAST_NAMES)
        display_name = f"{first} {last}"
        city = random.choice(CITIES)
        years = random.randint(1, 15)
        bio = random.choice(BIO_TEMPLATES).format(
            category=category.replace("_", " "), category_title=category.replace("_", " ").title(), city=city, years=years
        )
        skills = random.sample(CATEGORY_SKILLS[category], k=min(3, len(CATEGORY_SKILLS[category])))
        handle = f"{first.lower()}{last.lower()}{i}"

        user = User(
            email=email,
            hashed_password=hash_password(SEED_PASSWORD),
            full_name=display_name,
            role=UserRole.TALENT,
            email_verified=True,
        )
        db.add(user)
        db.flush()

        profile = TalentProfile(
            user_id=user.id,
            display_name=display_name,
            category=category,
            bio=bio,
            city=city,
            experience_years=years,
            skills=skills,
            tier="premium" if created % 5 == 0 else "free",
            is_verified=created % 4 == 0,
            attributes=build_attributes(category),
            # Placeholder profile links, not real third-party accounts — pointed at the
            # reserved example.com domain so they never resolve to an unrelated real profile.
            instagram_url=f"https://example.com/instagram/{handle}" if created % 2 == 0 else None,
            website_url=f"https://example.com/portfolio/{handle}" if created % 3 == 0 else None,
        )
        db.add(profile)
        db.flush()

        db.add(
            Media(
                talent_profile_id=profile.id,
                url=f"https://i.pravatar.cc/400?u=seed_talent_{i:03d}",
                media_type=MediaType.PHOTO,
                title="Profile photo",
                is_cover=True,
            )
        )
        for photo_index in range(random.randint(1, 3)):
            db.add(
                Media(
                    talent_profile_id=profile.id,
                    url=f"https://picsum.photos/seed/seed_talent_{i:03d}_{photo_index}/800/600",
                    media_type=MediaType.PHOTO,
                    title=f"Portfolio sample {photo_index + 1}",
                    is_cover=False,
                )
            )

        for credit in build_credits(profile.id, category):
            db.add(credit)

        created += 1

    db.commit()
    print(f"Seeded {created} talent profiles with attributes, credits, and portfolio media.")


def seed_recruiters(db) -> list[RecruiterProfile]:
    existing = {u.email for u in db.query(User.email).filter(User.email.like("seed_recruiter_%")).all()}
    recruiters = []
    for i in range(1, 11):
        email = f"seed_recruiter_{i:02d}@example.com"
        if email in existing:
            recruiter = db.query(RecruiterProfile).join(User).filter(User.email == email).first()
            if recruiter:
                recruiters.append(recruiter)
            continue
        user = User(
            email=email,
            hashed_password=hash_password(SEED_PASSWORD),
            full_name=f"{COMPANIES[i - 1]} Casting",
            role=UserRole.RECRUITER,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        profile = RecruiterProfile(user_id=user.id, company_name=COMPANIES[i - 1], industry="Media & Entertainment")
        db.add(profile)
        db.flush()
        recruiters.append(profile)
    db.commit()
    return recruiters


def reset_seed_casting_calls(db) -> None:
    """Remove any previously-seeded casting calls so re-running produces the current
    detailed templates instead of piling up duplicates from earlier, shallower seed runs."""
    seed_recruiter_ids = [
        r.id for r in db.query(RecruiterProfile).join(User).filter(User.email.like("seed_recruiter_%")).all()
    ]
    if not seed_recruiter_ids:
        return
    deleted = db.query(CastingCall).filter(CastingCall.recruiter_id.in_(seed_recruiter_ids)).delete(synchronize_session=False)
    db.commit()
    if deleted:
        print(f"Removed {deleted} previously-seeded casting call(s) before reseeding.")


def seed_casting_calls(db, recruiters: list[RecruiterProfile]) -> None:
    created = 0
    for index, (category, job) in enumerate(CATEGORY_JOBS.items()):
        recruiter = recruiters[index % len(recruiters)]
        deadline = date.today() + timedelta(days=random.randint(20, 60))
        call = CastingCall(
            recruiter_id=recruiter.id,
            title=job["title"],
            description=job["description"],
            category=category,
            location=job["location"],
            compensation=job["compensation"],
            application_deadline=deadline,
            audition_brief=job["audition_brief"],
            tags=job["tags"],
            shoot_details=job["shoot_details"],
            status=CastingCallStatus.OPEN,
        )
        db.add(call)
        db.flush()
        for role in job["roles"]:
            db.add(
                CastingCallRole(
                    casting_call_id=call.id,
                    title=role["title"],
                    criteria=role["criteria"],
                    category=category,
                    compensation=role["compensation"],
                )
            )
        created += 1

    db.commit()
    print(f"Seeded {created} detailed casting calls (one per category) across {len(recruiters)} recruiters.")


def reset_seed_talents(db) -> None:
    """Remove any previously-seeded talents so re-running produces fresh profiles with the
    current attributes/credits/portfolio content instead of leaving the older bare-bones ones
    in place (the create loop otherwise just skips emails that already exist)."""
    seed_users = db.query(User).filter(User.email.like("seed_talent_%")).all()
    if not seed_users:
        return
    count = len(seed_users)
    for user in seed_users:
        db.delete(user)
    db.commit()
    print(f"Removed {count} previously-seeded talent(s) before reseeding.")


def main() -> None:
    db = SessionLocal()
    try:
        reset_seed_talents(db)
        seed_talents(db, count=100)
        recruiters = seed_recruiters(db)
        reset_seed_casting_calls(db)
        seed_casting_calls(db, recruiters)
    finally:
        db.close()


if __name__ == "__main__":
    main()
