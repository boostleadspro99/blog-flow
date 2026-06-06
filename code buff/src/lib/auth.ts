import { authRequest } from './api';
import type { UserResponse } from './types';

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return authRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function register(
  email: string,
  username: string,
  password: string,
): Promise<TokenResponse> {
  return authRequest<TokenResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

export async function getMe(): Promise<UserResponse> {
  return authRequest<UserResponse>('/auth/me');
}
