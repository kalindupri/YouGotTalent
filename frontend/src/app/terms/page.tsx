import { eyebrowClass } from "@/lib/ui";

export const metadata = { title: "Terms of Service — YouGotTalent" };

export default function TermsPage() {
  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-14">
      <span className={eyebrowClass}>Legal</span>
      <h1 className="mt-2 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        Terms of Service &amp; Disclaimer
      </h1>
      <p className="mt-2 text-sm text-zinc-500">Last updated: 15 August 2026</p>

      <div className="prose prose-zinc mt-8 max-w-none dark:prose-invert prose-headings:font-heading prose-headings:uppercase prose-headings:tracking-tight prose-a:text-rose-600">
        <p className="rounded-lg border-2 border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          <strong>Draft notice:</strong> these terms have not yet been reviewed by a lawyer and
          contain placeholder fields marked <code>[PLACEHOLDER]</code>. Fill those in and have
          them reviewed before relying on them.
        </p>

        <h2>1. Who these terms apply to</h2>
        <p>
          These terms govern use of the YouGotTalent platform (yougottalent.lk), operated by
          [PLACEHOLDER — registered company name]. By creating an account, you agree to these
          terms and to our <a href="/privacy">Privacy Policy</a>.
        </p>

        <h2>2. What YouGotTalent is — and isn&apos;t</h2>
        <p>
          YouGotTalent is a marketplace that connects talent (actors, singers, dancers, and other
          creative professionals) with recruiters (casting directors, agencies, and organizations
          looking to hire). <strong>We are a platform, not a party to any engagement, casting
          decision, or payment arrangement between a talent and a recruiter.</strong> We don&apos;t
          employ talent, we don&apos;t guarantee bookings, and we don&apos;t vet the legitimacy,
          professionalism, or intentions of every user.
        </p>

        <h2>3. Disclaimer of warranties</h2>
        <p>
          The platform is provided &ldquo;as is&rdquo; and &ldquo;as available&rdquo;, without
          warranties of any kind, express or implied. We do not warrant that:
        </p>
        <ul>
          <li>Any casting call, offer, or booking posted or made through the platform is genuine, accurately described, or will result in payment or work;</li>
          <li>Any talent profile accurately represents the individual&apos;s skills, availability, age, or identity;</li>
          <li>The service will be uninterrupted, error-free, or completely secure.</li>
        </ul>
        <p>
          You are responsible for exercising your own judgment before entering any agreement,
          attending any audition or shoot, or making any payment connected to a use of this
          platform. We strongly recommend verifying the other party&apos;s identity and the
          legitimacy of any opportunity before proceeding, especially for in-person meetings.
        </p>

        <h2>4. Limitation of liability</h2>
        <p>
          To the fullest extent permitted by law, YouGotTalent and its operators are not liable
          for any indirect, incidental, or consequential damages arising from your use of the
          platform, including but not limited to disputes between talent and recruiters, lost
          opportunities, or harm arising from an in-person meeting or engagement arranged through
          the platform. Our total liability for any claim arising from use of the platform is
          limited to the amount you paid us (if any) in the 12 months before the claim.
        </p>

        <h2>5. Accounts &amp; eligibility</h2>
        <ul>
          <li>You must be 18 or older to create an account.</li>
          <li>You&apos;re responsible for keeping your login credentials confidential and for all activity under your account.</li>
          <li>You must provide accurate information and keep your profile up to date.</li>
          <li>We may suspend or terminate accounts that violate these terms, submit fraudulent content, or are used to harass or defraud other users.</li>
        </ul>

        <h2>6. Content you post</h2>
        <p>
          You retain ownership of the content you upload (photos, videos, audio, bio, messages,
          community posts). By posting it, you grant YouGotTalent a license to display it on the
          platform as needed to operate the service (e.g. showing your portfolio to recruiters
          who browse). You&apos;re responsible for making sure you have the rights to anything
          you upload, and for not posting content that&apos;s illegal, infringing, or abusive.
        </p>

        <h2>7. Payments &amp; subscriptions</h2>
        <p>
          Premium subscriptions are billed through our payment processor, Stripe, on the cycle
          you select at checkout. Subscriptions renew automatically until cancelled. Pricing in
          effect at the time you subscribe is honored for the life of your subscription
          (&ldquo;grandfathering&rdquo;) unless you cancel and re-subscribe later. See the{" "}
          <a href="/pricing">pricing page</a> for current plans.
        </p>

        <h2>8. Reporting &amp; moderation</h2>
        <p>
          If you encounter a fake profile, scam, harassment, or other abuse, please use the
          report feature or contact us. We review reports and may remove content or suspend
          accounts at our discretion, but we don&apos;t proactively review every piece of content
          before it&apos;s posted.
        </p>

        <h2>9. Changes to these terms</h2>
        <p>
          We may update these terms from time to time. Continued use of the platform after an
          update means you accept the revised terms.
        </p>

        <h2>10. Governing law</h2>
        <p>These terms are governed by the laws of [PLACEHOLDER — jurisdiction, e.g. Sri Lanka].</p>

        <h2>11. Contact</h2>
        <p>Questions about these terms: [PLACEHOLDER — email address].</p>
      </div>
    </main>
  );
}
