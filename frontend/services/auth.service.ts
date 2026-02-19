import api from "./api";

const PREFIX = "/v1/auth/";

// Login user endpoint
export const loginUser = async (username: string, password: string) => {
  const response = await api.post(PREFIX + "login", {
    username: username,
    password: password,
  });
  return response.data;
};

// Register user endpoint
export const registerUser = async (
  email: string,
  username: string,
  password: string,
) => {
  const response = await api.post(PREFIX + "register", {
    email: email,
    username: username,
    password: password,
  });
  return response.data;
};
