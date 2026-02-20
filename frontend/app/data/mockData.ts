// Shared UI-only type definitions used by visualization components.
// All runtime data now comes from the backend API.

export interface ConceptNode {
  id: string;
  name: string;
  readiness: number;
  depth: number;
  prerequisites: string[];
  x?: number;
  y?: number;
}

export interface Student {
  id: string;
  name: string;
  conceptReadiness: Record<string, number>;
}

export interface Alert {
  id: string;
  conceptId: string;
  conceptName: string;
  severity: 'high' | 'medium' | 'low';
  impact: number;
  studentsAffected: number;
  message: string;
}

export interface WaterfallItem {
  label: string;
  value: number;
  type: 'positive' | 'negative' | 'total';
}
