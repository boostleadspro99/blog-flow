export interface ImageModel {
  id: string;
  label: string;
  provider: string;
  recommendedFor: string;
  pricing?: string;
}

export const IMAGE_MODELS: ImageModel[] = [
  {
    id: 'gemini-3-pro-image',
    label: 'Gemini 3 Pro Image',
    provider: 'Google (via Gemini-Free-API)',
    recommendedFor: 'High quality image generation with auto watermark removal',
    pricing: 'Free',
  },
];
