declare module "react-native-math-view" {
  import { StyleProp, ViewStyle } from "react-native";
  interface MathViewProps {
    math: string;
    style?: StyleProp<ViewStyle>;
  }
  const MathView: React.FC<MathViewProps>;
  export default MathView;
}
