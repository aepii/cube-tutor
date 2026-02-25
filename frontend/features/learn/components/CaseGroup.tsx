import { useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from "react-native";
import { AlgorithmCase } from "@/features/learn/types/algorithm.types";
import { globalStyles as styles } from "@/shared/styles/globalStyles";
import SolutionDetail from "./SolutionDetail";
import { colors } from "@/shared/theme/colors";

function orientationToString(orientation: number): string {
  const map: Record<number, string> = {
    0: "Front Right",
    1: "Front Left",
    2: "Back Left",
    3: "Back Right",
  };
  return map[orientation];
}

export default function CaseGroup({ item }: { item: AlgorithmCase }) {
  const isOriented = item.subset === "F2L";
  const [activeOrientation, setActiveOrientation] = useState<number>(0);
  const displayedSolutions = isOriented
    ? item.solutions.filter((sol) => sol.orientation === activeOrientation)
    : item.solutions;
  const orientations = [0, 1, 2, 3];
  return (
    <View style={styles.container}>
      <Text style={styles.header}>{item.case_name}</Text>
      <Text>
        {item.subset} - {item.subgroup}
      </Text>
      <Text>Setup: {item.setup}</Text>

      {isOriented && (
        <View style={localStyles.tabContainer}>
          {orientations.map((orientation) => (
            <TouchableOpacity
              key={orientation}
              onPress={() => setActiveOrientation(orientation)}
              style={localStyles.tab}
            >
              <Text>{orientationToString(orientation)}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <FlatList
        data={displayedSolutions}
        renderItem={({ item }) => <SolutionDetail key={item.solution_id} item={item} />}
      ></FlatList>
    </View>
  );
}

const localStyles = StyleSheet.create({
  tabContainer: {
    flex: 1,
    flexDirection: "row",
  },
  tab: {
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderTopEndRadius: 10,
    borderTopStartRadius: 10,
    backgroundColor: colors.primary,
  },
});
