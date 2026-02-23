import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import { AlgorithmSolution } from "@/types";

export default function SolutionDetail({ item }: { item: AlgorithmSolution }) {
  return (
    <View>
      <Text>{item.notation}</Text>
    </View>
  );
}
