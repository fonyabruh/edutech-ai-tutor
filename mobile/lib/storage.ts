import { createMMKV } from "react-native-mmkv";
import "react-native-get-random-values";
import { v4 as uuidv4 } from "uuid";

export const storage = createMMKV();

export const getToken = () => storage.getString("auth_token") ?? null;
export const setToken = (token: string) => storage.set("auth_token", token);
export const clearToken = () => storage.remove("auth_token");

export const getDeviceId = () => storage.getString("device_id") ?? null;

export function ensureDeviceId(): string {
  const existing = getDeviceId();
  if (existing) return existing;
  const id = uuidv4();
  storage.set("device_id", id);
  return id;
}
