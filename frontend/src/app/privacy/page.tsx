import { eyebrowClass } from "@/lib/ui";

export const metadata = { title: "Privacy Policy — YouGotTalent" };

export default function PrivacyPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
      <span className={eyebrowClass}>Legal</span>
      <h1 className="mt-2 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        Privacy Policy
      </h1>
      <p className="mt-2 text-sm text-zinc-500">Last updated: 15 August 2026</p>

      <div className="prose prose-zinc mt-8 max-w-none dark:prose-invert prose-headings:font-heading prose-headings:uppercase prose-headings:tracking-tight prose-a:text-rose-600">
        <p className="rounded-lg border-2 border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          <strong>Draft notice:</strong> this policy has not yet been reviewed by a lawyer and
          contains placeholder fields marked <code>[PLACEHOLDER]</code>. Fill those in and have
          it reviewed before relying on it — privacy and data-protection requirements vary by
          jurisdiction (Sri Lanka, and wherever else talent or recruiters sign up from).
        </p>

        <h2>1. Who we are</h2>
        <p>
          YouGotTalent (&ldquo;<strong>we</strong>&rdquo;, &ldquo;<strong>us</strong>&rdquo;) operates
          the talent marketplace at yougottalent.lk. We are the data controller for personal data
          collected through the platform.
        </p>
        <ul>
          <li>Legal entity: [PLACEHOLDER — registered company name]</li>
          <li>Registered address: [PLACEHOLDER]</li>
          <li>Contact for privacy questions or data requests: [PLACEHOLDER — email address]</li>
        </ul>

        <h2>2. What we collect</h2>
        <p>We collect the information you give us directly, and a small amount we collect automatically:</p>
        <ul>
          <li>
            <strong>Account information</strong>: name, email, phone (optional), password (stored
            as a one-way hash, never in plain text), account role (talent or recruiter).
          </li>
          <li>
            <strong>Talent profile</strong>: category/skills, bio, city, date of birth, gender,
            experience, portfolio media (photos, video, audio), social media links, and any
            category-specific details you choose to add (e.g. height, vocal range, TikTok
            follower count). Date of birth is required — it is how we know whether guardian
            consent is needed and whether someone is old enough for paid work — but it is never
            shown publicly. Other people only ever see an age.
          </li>
          <li>
            <strong>Guardian verification documents</strong>: for a profile belonging to someone
            under 18, the birth certificate or other proof of guardianship the guardian uploads,
            along with their name, relationship, and contact details. These are stored privately
            and are only seen by the staff who review them — see Section 7.
          </li>
          <li>
            <strong>Recruiter profile</strong>: company/organizer name, industry, and casting
            calls you post.
          </li>
          <li>
            <strong>Communications</strong>: messages sent through the platform&apos;s messaging
            system, applications, and booking/contract records.
          </li>
          <li>
            <strong>Payment information</strong>: if you subscribe to a Premium plan, payment is
            handled entirely by our payment processor (see Section 4) — we never see or store
            your full card number.
          </li>
          <li>
            <strong>Usage data</strong>: standard web request logs (IP address, browser type,
            pages visited) collected automatically for security and reliability.
          </li>
        </ul>

        <h2>3. How we use it</h2>
        <ul>
          <li>To create and operate your account and profile.</li>
          <li>To let recruiters find and contact talent, and talent find and apply to roles.</li>
          <li>To send account-related emails (verification, password reset, application updates, job alerts you&apos;ve opted into).</li>
          <li>To process Premium subscription payments and manage billing.</li>
          <li>To investigate reports of abuse, spam, or policy violations.</li>
          <li>To keep the platform secure and diagnose technical problems.</li>
        </ul>
        <p>We do not sell your personal data, and we do not use it for third-party advertising.</p>

        <h2>4. Who we share it with</h2>
        <p>We share personal data only where necessary to run the service:</p>
        <ul>
          <li>
            <strong>Microsoft Azure</strong> — our cloud hosting provider. Azure hosts our
            application servers, database, and stores uploaded media (photos/video/audio).
          </li>
          <li>
            <strong>Stripe</strong> — our payment processor for Premium subscriptions. Stripe
            receives your payment details directly; we only receive confirmation that a payment
            succeeded or failed, plus a reference ID.
          </li>
          <li>
            <strong>Other platform users</strong> — a talent&apos;s public profile is visible to
            recruiters (and, unless you restrict visibility, other visitors). Messages are visible
            only to the sender and recipient.
          </li>
        </ul>
        <p>We do not share your data with any other third party except where required by law.</p>

        <h2>5. How long we keep it</h2>
        <p>
          We keep your account and profile data for as long as your account is active. If you
          delete your account, we delete or anonymize your personal data within [PLACEHOLDER —
          e.g. "30 days"], except where we&apos;re legally required to keep records longer (e.g.
          payment records for tax purposes).
        </p>

        <h2>6. Your rights</h2>
        <p>
          Depending on where you live, you may have the right to access, correct, delete, or
          export your personal data, and to object to or restrict certain processing. Most of
          this you can already do yourself from your profile settings; for anything else, contact
          us at [PLACEHOLDER — email address].
        </p>
        <p>
          If you are in Sri Lanka, these rights are provided under the Personal Data Protection
          Act No. 9 of 2022.
        </p>

        <h2>7. Young people under 18</h2>
        <p>
          Young performers are welcome on YouGotTalent, but a profile for anyone under 18 must be
          created and controlled by their parent or legal guardian. The guardian is the account
          holder: they register in their own name, with their own email address, and manage all
          activity on the profile. The young person does not get their own login.
        </p>
        <p>
          Under the Personal Data Protection Act No. 9 of 2022, a child&apos;s personal data is a
          special category and consent must come from a parent or legal guardian. Before a profile
          belonging to someone under 18 is visible to talent hunts or reachable by anyone, we ask
          the guardian to:
        </p>
        <ul>
          <li>
            tell us their own legal name, their relationship to the young person, and the young
            person&apos;s legal name;
          </li>
          <li>
            upload proof of that relationship — a certified copy of the birth certificate, or
            another document proving legal guardianship;
          </li>
          <li>
            choose specifically what they are consenting to, rather than agreeing to everything at
            once: being listed publicly, showing photos and audition media, being contacted by
            talent hunts, and being considered for paid work.
          </li>
        </ul>
        <p>
          Until a member of our team has reviewed those documents and approved the consent, the
          profile does not appear in search or browse, is not included in job-alert emails, and
          cannot be messaged, invited, or booked. If we cannot approve it, we tell the guardian why
          so they can correct it.
        </p>
        <p>
          <strong>Verification documents are treated differently from everything else on the
          platform.</strong> They are stored separately from profile media, are never published on
          the profile, are not accessible by any public link, and can only be opened by the small
          number of staff who review them — through a link that expires within minutes. We delete
          them [PLACEHOLDER — number] days after the review is complete.
        </p>
        <p>
          <strong>We never show a date of birth publicly.</strong> Talent hunts see an age, not a
          birth date. This applies to every profile, not only those belonging to young people.
        </p>
        <p>
          <strong>Paid work.</strong> Sri Lanka&apos;s minimum age of employment is 16. Talent under
          16 can build a profile and showcase their work, but cannot be offered or booked for paid
          engagements through YouGotTalent. For 16 and 17 year olds, any contract must be signed by
          their registered guardian, not by the young person.
        </p>
        <p>
          A guardian can withdraw consent at any time from the profile&apos;s dashboard, or by
          contacting us at [PLACEHOLDER — email address]. Withdrawing consent hides the profile
          immediately. If you believe a profile for a young person has been created by someone who
          is not their parent or legal guardian, contact us and we will investigate and take it
          down.
        </p>

        <h2>8. Security</h2>
        <p>
          We use industry-standard measures to protect your data — encrypted connections
          (HTTPS) everywhere, hashed passwords, and access controls limiting who can see what.
          No system is 100% secure, and we can&apos;t guarantee absolute security of information
          transmitted over the internet.
        </p>

        <h2>9. Changes to this policy</h2>
        <p>
          We may update this policy from time to time. We&apos;ll post the updated version here
          with a new &ldquo;Last updated&rdquo; date; material changes will also be flagged on
          the site.
        </p>

        <h2>10. Contact</h2>
        <p>Questions about this policy or your data: [PLACEHOLDER — email address].</p>
      </div>
    </main>
  );
}
