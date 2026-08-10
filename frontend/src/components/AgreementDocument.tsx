import { Booking } from "@/lib/api";

export default function AgreementDocument({ booking }: { booking: Booking }) {
  return (
    <div className="mx-auto max-w-2xl rounded-lg border border-zinc-200 bg-white p-8 shadow-inner dark:border-zinc-700 dark:bg-zinc-950">
      <div className="mb-6 border-b-2 border-zinc-900 pb-4 text-center dark:border-zinc-100">
        <p className="font-heading text-lg font-black tracking-tight text-rose-600">YouGotTalent</p>
        <h3 className="mt-1 text-xl font-bold uppercase tracking-wide text-zinc-900 dark:text-zinc-50">
          Talent Engagement Agreement
        </h3>
        <p className="mt-1 text-xs text-zinc-500">
          {booking.recruiter_company_name} &amp; {booking.talent_display_name}
          {booking.application_role_title ? ` — ${booking.application_role_title}` : ""}
        </p>
      </div>
      <div
        className="font-serif text-sm leading-relaxed text-zinc-900 dark:text-zinc-100 [&_h3]:mt-3 [&_h3]:mb-1.5 [&_h3]:text-base [&_h3]:font-bold [&_p]:mb-2 [&_ul]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:mb-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_li]:mb-1"
        dangerouslySetInnerHTML={{ __html: booking.contract_content || "" }}
      />
    </div>
  );
}
