// Typed fetch wrapper for the PAIGE backend API.

import type {
  AuthResponse,
  FigureListResponse,
  GenerateResponse,
  PdfImagesResponse,
  ProjectsResponse,
  SelectedImage,
  StructuredResponse,
  UploadResponse,
  WikimediaSearchResponse,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore JSON parse failures
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export interface GenerateParams {
  sessionId: string;
  additionalContent?: string;
  contentOverride?: string;
  maxWordCount?: number;
  minWordCount?: number;
}

function generateBody(params: GenerateParams) {
  return JSON.stringify({
    session_id: params.sessionId,
    additional_content: params.additionalContent ?? null,
    content_override: params.contentOverride ?? null,
    max_word_count: params.maxWordCount ?? null,
    min_word_count: params.minWordCount ?? null,
  });
}

export const api = {
  auth(payload: {
    password?: string;
    apiKey?: string;
    baseUrl?: string;
    model?: string;
  }): Promise<AuthResponse> {
    return request<AuthResponse>("/auth", {
      method: "POST",
      body: JSON.stringify({
        password: payload.password ?? null,
        api_key: payload.apiKey ?? null,
        base_url: payload.baseUrl ?? null,
        model: payload.model ?? null,
      }),
    });
  },

  projects(): Promise<ProjectsResponse> {
    return request<ProjectsResponse>("/projects");
  },

  async upload(sessionId: string, file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("file", file);
    const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        detail = (await res.json()).detail || detail;
      } catch {
        // ignore
      }
      throw new Error(detail);
    }
    return (await res.json()) as UploadResponse;
  },

  generate(kind: string, params: GenerateParams): Promise<GenerateResponse> {
    return request<GenerateResponse>(`/generate/${kind}`, {
      method: "POST",
      body: generateBody(params),
    });
  },

  structured(kind: string, params: GenerateParams): Promise<StructuredResponse> {
    return request<StructuredResponse>(`/generate/${kind}`, {
      method: "POST",
      body: generateBody(params),
    });
  },

  figureList(params: GenerateParams): Promise<FigureListResponse> {
    return request<FigureListResponse>("/generate/figure-list", {
      method: "POST",
      body: generateBody(params),
    });
  },

  wikimedia(query: string, limit: number): Promise<WikimediaSearchResponse> {
    const qs = new URLSearchParams({ query, limit: String(limit) });
    return request<WikimediaSearchResponse>(`/images/wikimedia?${qs.toString()}`);
  },

  pdfExtract(sessionId: string): Promise<PdfImagesResponse> {
    const qs = new URLSearchParams({ session_id: sessionId });
    return request<PdfImagesResponse>(`/images/pdf-extract?${qs.toString()}`, {
      method: "POST",
    });
  },

  proxyImageUrl(url: string): string {
    return `${BASE}/images/proxy?url=${encodeURIComponent(url)}`;
  },

  async exportDocx(payload: {
    sessionId: string;
    title?: string;
    subtitle?: string;
    imageCaption?: string;
    science?: string;
    impact?: string;
    summary?: string;
    funding?: string;
    citation?: string;
    relatedLinks?: string;
    pointOfContact?: string;
    selectedImage?: SelectedImage | null;
  }): Promise<Blob> {
    const res = await fetch(`${BASE}/export/docx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: payload.sessionId,
        title: payload.title ?? "",
        subtitle: payload.subtitle ?? "",
        image_caption: payload.imageCaption ?? "",
        science: payload.science ?? "",
        impact: payload.impact ?? "",
        summary: payload.summary ?? "",
        funding: payload.funding ?? "",
        citation: payload.citation ?? "",
        related_links: payload.relatedLinks ?? "",
        point_of_contact: payload.pointOfContact ?? "",
        selected_image: payload.selectedImage ?? null,
      }),
    });
    if (!res.ok) throw new Error(await extractError(res));
    return res.blob();
  },

  async exportPptx(payload: {
    sessionId: string;
    title: string;
    objective: string;
    citation: string;
    figureCaption: string;
    approachPoints: string[];
    impactPoints: string[];
    figureImageIndex?: number | null;
  }): Promise<Blob> {
    const res = await fetch(`${BASE}/export/pptx`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: payload.sessionId,
        title: payload.title,
        objective: payload.objective,
        citation: payload.citation,
        figure_caption: payload.figureCaption,
        approach_points: payload.approachPoints,
        impact_points: payload.impactPoints,
        figure_image_index: payload.figureImageIndex ?? null,
      }),
    });
    if (!res.ok) throw new Error(await extractError(res));
    return res.blob();
  },
};

async function extractError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
