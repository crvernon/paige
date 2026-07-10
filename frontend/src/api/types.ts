// Shared API types mirroring the FastAPI backend schemas.

export interface AuthResponse {
  session_id: string;
  active_project: string;
  model: string;
  max_allowable_tokens: number;
}

export interface UploadResponse {
  filename: string;
  n_pages: number;
  n_characters: number;
  n_words: number;
  n_tokens: number;
  max_allowable_tokens: number;
  exceeds_limit: boolean;
  has_pdf_images: boolean;
}

export interface GenerateResponse {
  text: string;
  word_count: number;
}

export interface StructuredResponse {
  points: string[];
}

export interface WikimediaImage {
  id: number | null;
  title: string;
  thumbnail_url: string | null;
  full_url: string | null;
  page_url: string | null;
  license: string;
  artist_html: string;
  artist_plain: string;
  license_url: string | null;
  mime: string;
}

export interface WikimediaSearchResponse {
  results: WikimediaImage[];
}

export interface PdfImageInfo {
  index: number;
  page: number;
  data_url: string;
  mime: string;
}

export interface PdfImagesResponse {
  images: PdfImageInfo[];
}

export interface FigureListResponse {
  figures: Record<string, string>;
}

export interface ProjectsResponse {
  projects: Record<string, string>;
}

export interface SelectedImage {
  full_url?: string | null;
  page_url?: string | null;
  artist_plain?: string | null;
  license?: string | null;
  license_url?: string | null;
}
