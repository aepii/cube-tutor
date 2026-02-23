import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { getAlgorithms } from "@/services/alg.service";
import { View, FlatList, Text, TouchableOpacity } from "react-native";
import { globalStyles as styles } from "@/styles/globalStyles";
import { AlgorithmCase, AlgorithmSolution } from "@/types";
import CaseGroup from "@/components/learn/CaseGroup";

export default function AlgorithmScreen() {
  const [algs, setAlgs] = useState<AlgorithmCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token } = useAuth();

  useEffect(() => {
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
    loadAlgorithms();
  }, []);

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
