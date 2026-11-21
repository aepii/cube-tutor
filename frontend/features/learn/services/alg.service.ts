import api from "@/shared/api/client";

const PREFIX = "/v1/algs/";

// Algorithm retrieval endpoint
export const getAlgorithms = async () => {
  const response = await api.get(PREFIX);
  return response.data;
};

// Set an algorithm's favorite flag. PUT with the desired value is idempotent:
// a retry or a repeated tap can't flip it back.
export const putFavorite = async (alg_id: number, value: boolean) => {
  const response = await api.put(PREFIX + alg_id + "/favorite", { value });
  return response.data;
};

// Set an algorithm's learned flag (idempotent, same as putFavorite)
export const putLearned = async (alg_id: number, value: boolean) => {
  const response = await api.put(PREFIX + alg_id + "/learn", { value });
  return response.data;
};
