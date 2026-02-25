import api from "@/shared/api/client";

const PREFIX = "/v1/algs/";

// Algorithm retrieval endpoint
export const getAlgorithms = async () => {
  const response = await api.get(PREFIX);
  return response.data;
};

// Favorite an algorithm
export const favoriteAlgorithm = async (alg_id: number) => {
  const response = await api.post(PREFIX + alg_id + "/favorite");
  return response.data;
};

// Learn an algorithm
export const learnAlgorithm = async (alg_id: number) => {
  const response = await api.post(PREFIX + alg_id + "/learn");
  return response.data;
};
