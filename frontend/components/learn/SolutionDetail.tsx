import { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { AiOutlineStar, AiFillStar } from "react-icons/ai";
import { FaGraduationCap } from "react-icons/fa6"
import { AlgorithmSolution } from "@/types";
import { colors } from "@/theme/colors";
import { favoriteAlgorithm, learnAlgorithm } from "@/services/alg.service";

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
      <Text>{item.notation}</Text>
      <TouchableOpacity onPress={() => toggleLearn()}>
        {learn ? (
          <FaGraduationCap style={{ fill: colors.primary }}></FaGraduationCap>
        ) : (
          <FaGraduationCap style={{ fill: "gray" }}></FaGraduationCap>
        )}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => toggleFavorite()}>
        {favorite ? (
          <AiFillStar style={{ fill: "gold" }}></AiFillStar>
        ) : (
          <AiOutlineStar style={{ fill: "gold" }}></AiOutlineStar>
        )}
      </TouchableOpacity>
    </View>
  );
}

const localStyles = StyleSheet.create({
  solutionContainer: {
    flex: 1,
    flexDirection: "row",
    padding: 5,
  },
});
