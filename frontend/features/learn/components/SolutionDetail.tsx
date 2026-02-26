import { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { FontAwesome, FontAwesome6 } from "@expo/vector-icons";
import { AlgorithmSolution } from "@/features/learn/types/algorithm.types";
import { colors } from "@/shared/theme/colors";
import {
  favoriteAlgorithm,
  learnAlgorithm,
} from "@/features/learn/services/alg.service";

export default function SolutionDetail({ item }: { item: AlgorithmSolution }) {
  const [favorite, setFavorite] = useState<boolean>(item.is_favorited);
  const [learn, setLearn] = useState<boolean>(item.is_learned);

  const toggleFavorite = async () => {
    const previousState = favorite;
    setFavorite(!previousState);

    try {
      await favoriteAlgorithm(item.solution_id);
    } catch (err: any) {
      console.error(err);
      setFavorite(previousState);
    }
  };

  const toggleLearn = async () => {
    const previousState = learn;
    setLearn(!previousState);

    try {
      await learnAlgorithm(item.solution_id);
    } catch (err: any) {
      console.error(err);
      setLearn(previousState);
    }
  };

  return (
    <View style={localStyles.solutionContainer}>
      <Text style={localStyles.notationText}>{item.notation}</Text>

      <View style={localStyles.actionsContainer}>
        <TouchableOpacity
          onPress={() => toggleLearn()}
          style={localStyles.iconButton}
        >
          <FontAwesome6
            name="graduation-cap"
            size={20}
            color={learn ? colors.primary : "gray"}
          />
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => toggleFavorite()}
          style={localStyles.iconButton}
        >
          <FontAwesome
            name={favorite ? "star" : "star-o"}
            size={24}
            color="gold"
          />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const localStyles = StyleSheet.create({
  solutionContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  notationText: {
    flex: 1,
    fontSize: 16,
    color: colors.text,
  },
  actionsContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
  },
  iconButton: {
    padding: 8,
  },
});
