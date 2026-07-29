"use client";

import { useEffect, useState } from "react";
import { Heart } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { btnSecondary, btnSmallPrimary } from "@/lib/ui";

export default function FollowRecruiterButton({ recruiterId }: { recruiterId: string }) {
  const { token } = useAuth();
  const [following, setFollowing] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!token) return;
    api
      .listMyFollowing(token)
      .then((list) => setFollowing(list.some((f) => f.recruiter_id === recruiterId)))
      .finally(() => setLoaded(true));
  }, [token, recruiterId]);

  async function toggleFollow() {
    if (!token) return;
    setSubmitting(true);
    try {
      if (following) {
        await api.unfollowRecruiter(recruiterId, token);
        setFollowing(false);
      } else {
        await api.followRecruiter(recruiterId, token);
        setFollowing(true);
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!loaded) return null;

  return (
    <button onClick={toggleFollow} disabled={submitting} className={following ? btnSmallPrimary : btnSecondary}>
      <Heart className="h-3.5 w-3.5" fill={following ? "currentColor" : "none"} />
      {following ? "Following" : "Follow"}
    </button>
  );
}
