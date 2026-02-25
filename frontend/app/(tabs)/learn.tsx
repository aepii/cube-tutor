import { useEffect, useState } from "react";
import { useAuthStore } from "@/features/auth/store/useAuthStore";
import { getAlgorithms } from "@/features/learn/services/alg.service";
import { View, FlatList, Text, TouchableOpacity } from "react-native";
import { globalStyles as styles } from "@/shared/styles/globalStyles";
import { AlgorithmCase } from "@/features/learn/types/algorithm.types";
import CaseGroup from "@/features/learn/components/CaseGroup";

export default function AlgorithmScreen() {
  const [algs, setAlgs] = useState<AlgorithmCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const { token } = useAuthStore();

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
