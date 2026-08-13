import { useEffect, useState } from "react";
import { checkHealth } from "../lib/api";

export function useHealth() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const tick = async () => {
      const ok = await checkHealth();
      if (!cancelled) setOnline(ok);
    };
    tick();
    const id = setInterval(tick, 15000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return online;
}
