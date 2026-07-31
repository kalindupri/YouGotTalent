import { avatarGradient, initials } from "@/lib/ui";

export default function AuthorAvatar({ name, className = "h-9 w-9 text-xs" }: { name: string; className?: string }) {
  return (
    <div
      className={`${className} flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${avatarGradient(
        name
      )} font-bold text-white`}
    >
      {initials(name)}
    </div>
  );
}
