import { ActivityIndicator, Pressable, Text } from "react-native";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const variantStyles: Record<Variant, string> = {
  primary: "bg-primary",
  secondary: "bg-slate-200",
  ghost: "bg-transparent border border-slate-300",
  danger: "bg-danger",
};

const textStyles: Record<Variant, string> = {
  primary: "text-white",
  secondary: "text-ink",
  ghost: "text-ink",
  danger: "text-white",
};

const sizeStyles: Record<Size, string> = {
  sm: "px-3 py-2",
  md: "px-5 py-3",
  lg: "px-6 py-4",
};

const textSizes: Record<Size, string> = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
};

interface Props {
  label: string;
  onPress: () => void;
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
}

export function Button({
  label,
  onPress,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  className = "",
}: Props) {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      className={`rounded-xl items-center justify-center flex-row gap-2 ${variantStyles[variant]} ${sizeStyles[size]} ${isDisabled ? "opacity-50" : ""} ${className}`}
    >
      {loading && <ActivityIndicator size="small" color={variant === "primary" ? "#fff" : "#0F172A"} />}
      <Text className={`font-semibold ${textStyles[variant]} ${textSizes[size]}`}>{label}</Text>
    </Pressable>
  );
}
