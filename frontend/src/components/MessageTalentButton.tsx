"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { MessageCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnSmall } from "@/lib/ui";

export default function MessageTalentButton({ talentId }: { talentId: string }) {
  const { token } = useAuth();
  const router = useRouter();
  const [starting, setStarting] = useState(false);

  async function handleClick() {
    if (!token) return;
    setStarting(true);
    try {
      const conversation = await api.startConversation(talentId, undefined, token);
      router.push(`/messages/${conversation.id}`);
    } finally {
      setStarting(false);
    }
  }

  return (
    <button onClick={handleClick} disabled={starting} className={btnSmall}>
      {starting ? (
        "Opening…"
      ) : (
        <>
          <MessageCircle className="h-3.5 w-3.5" /> Message
        </>
      )}
    </button>
  );
}
