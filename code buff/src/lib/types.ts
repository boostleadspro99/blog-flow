export interface UserResponse {
  id: string;
  email: string;
  username: string;
  created_at: string;
  has_cookies: boolean;
  cookies_valid: boolean;
}

export interface CookieResponse {
  has_cookies: boolean;
  is_valid: boolean;
  last_validated_at: string | null;
  error_message: string | null;
}
