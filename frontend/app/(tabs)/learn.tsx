import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { getAlgorithms } from "@/services/alg.service";
import { View, FlatList, Text } from "react-native";
import { globalStyles as styles } from "@/styles/globalStyles";
import { AlgorithmCase, AlgorithmSolution } from "@/types";
import { AiOutlineStar, AiFillStar } from "react-icons/ai";

function orientationToString(orientation: number): string {
  const map: Record<number, string> = {
    0: "Front Right",
    1: "Front Left",
    2: "Back Left",
    3: "Back Right",
  };
  return map[orientation];
}

export default function AlgorithmScreen() {
  const [algs, setAlgs] = useState<AlgorithmCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token } = useAuth();

  useEffect(() => {
    loadAlgorithms();
  }, []);

  const loadAlgorithms = async () => {
    try {
      const data = await getAlgorithms();
      setAlgs(data);
    } catch (err: any) {
      console.error("Failed to load algs", err);
      setError("Failed to load algs");
    } finally {
      setLoading(false);
    }
  };

  const SolutionDetail = ({
    item,
    isOriented,
  }: {
    item: AlgorithmSolution;
    isOriented: boolean;
  }) => {
    return (
      <View>
        <Text>
          {item.notation}{" "}
          {isOriented ? orientationToString(item.orientation) : null}
        </Text>
      </View>
    );
  };

  const CaseGroup = ({ item }: { item: AlgorithmCase }) => {
    const isOriented = item.subset === "F2L" ? true : false;
    return (
      <View style={styles.container}>
        <Text style={styles.header}>{item.case_name}</Text>
        <Text>
          {item.subset} - {item.subgroup}
        </Text>
        <Text>Setup: {item.setup}</Text>
        <FlatList
          data={item.solutions}
          renderItem={({ item }) => (
            <SolutionDetail item={item} isOriented={isOriented} />
          )}
        ></FlatList>
      </View>
    );
  };

  return (
    <View style={styles.container}>
       {error ? <Text style={styles.error}>{error}</Text> : null}
      <FlatList
        data={algs}
        renderItem={({ item }) => <CaseGroup item={item} />}
      ></FlatList>
    </View>
  );
}
