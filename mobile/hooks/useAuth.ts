import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ensureDeviceId, getToken, setToken } from "@/lib/storage";
import type { User } from "@/lib/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const authenticate = async () => {
    try {
      const deviceId = ensureDeviceId();
      const { data } = await api.post("/auth/anonymous", { device_id: deviceId });
      setToken(data.access_token);
      setUser(data.user);
    } catch (e) {
      console.warn("auth error", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getToken();
    if (!token) {
      authenticate();
    } else {
      api
        .get("/me")
        .then(({ data }) => setUser(data))
        .catch(() => authenticate())
        .finally(() => setIsLoading(false));
    }
  }, []);

  return { user, isLoading, refresh: authenticate };
}
