import { create } from "zustand";
import type {
  PdfImageInfo,
  UploadResponse,
  WikimediaImage,
} from "../api/types";

export interface AppState {
  // Access / session
  sessionId: string | null;
  activeProject: string;
  model: string;
  maxAllowableTokens: number;

  // Uploaded document
  upload: UploadResponse | null;
  reduceContent: boolean;

  // Word-doc fields
  title: string;
  subtitle: string;
  science: string;
  impact: string;
  summary: string;
  citation: string;
  funding: string;
  imageCaption: string;
  pointOfContact: string;
  suggestedSearchStrings: string;

  // Wikimedia
  wikimediaResults: WikimediaImage[] | null;
  selectedImage: WikimediaImage | null;

  // PowerPoint fields
  objective: string;
  approachPoints: string[];
  pptImpactPoints: string[];
  figures: Record<string, string> | null;
  selectedFigureId: string | null;
  figureCaption: string;
  pdfImages: PdfImageInfo[] | null;
  selectedFigureImageIndex: number | null;

  // POC directory
  projects: Record<string, string>;

  // actions
  setAuth: (v: {
    sessionId: string;
    activeProject: string;
    model: string;
    maxAllowableTokens: number;
  }) => void;
  logout: () => void;
  set: <K extends keyof AppState>(key: K, value: AppState[K]) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  activeProject: "Other",
  model: "",
  maxAllowableTokens: 150000,

  upload: null,
  reduceContent: false,

  title: "",
  subtitle: "",
  science: "",
  impact: "",
  summary: "",
  citation: "",
  funding: "",
  imageCaption: "",
  pointOfContact: "",
  suggestedSearchStrings: "",

  wikimediaResults: null,
  selectedImage: null,

  objective: "",
  approachPoints: [],
  pptImpactPoints: [],
  figures: null,
  selectedFigureId: null,
  figureCaption: "",
  pdfImages: null,
  selectedFigureImageIndex: null,

  projects: {},

  setAuth: (v) =>
    set({
      sessionId: v.sessionId,
      activeProject: v.activeProject,
      model: v.model,
      maxAllowableTokens: v.maxAllowableTokens,
    }),

  logout: () =>
    set({
      sessionId: null,
      upload: null,
      title: "",
      subtitle: "",
      science: "",
      impact: "",
      summary: "",
      citation: "",
      funding: "",
      imageCaption: "",
      objective: "",
      approachPoints: [],
      pptImpactPoints: [],
      figures: null,
      selectedFigureId: null,
      figureCaption: "",
      pdfImages: null,
      selectedFigureImageIndex: null,
      wikimediaResults: null,
      selectedImage: null,
      suggestedSearchStrings: "",
    }),

  set: (key, value) => set({ [key]: value } as Partial<AppState>),
}));
