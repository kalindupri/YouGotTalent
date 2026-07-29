import { avatarGradient, initials } from "@/lib/ui";

export default function TalentAvatar({
  name,
  coverUrl,
  className = "h-full w-full",
}: {
  name: string;
  coverUrl?: string | null;
  className?: string;
}) {
  if (coverUrl) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={coverUrl} alt={name} className={`${className} object-cover`} />;
  }
  return (
    <div
      className={`${className} flex items-center justify-center bg-gradient-to-br ${avatarGradient(
        name
      )} font-semibold text-white`}
    >
      {initials(name)}
    </div>
  );
}
