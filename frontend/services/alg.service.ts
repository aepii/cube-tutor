import api from "./api";

const PREFIX = "/v1/algs";

// Algorithm retrieval endpoint
export const getAlgorithms = async () => {
  const response = await api.get(PREFIX);
  return response.data;
};
