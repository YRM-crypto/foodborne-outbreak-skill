import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

// —— 案例 ——
export async function listEvents() {
  return (await api.get("/events")).data;
}
export async function getEvent(id: string) {
  return (await api.get(`/events/${id}`)).data;
}
export async function createEvent(payload: any) {
  return (await api.post("/events", payload)).data;
}
export async function seedDemo() {
  return (await api.post("/events/seed-demo")).data;
}
export async function updateEvent(id: string, payload: any) {
  return (await api.patch(`/events/${id}`, payload)).data;
}
export async function loadEvent(id: string) {
  return (await api.get(`/events/${id}/load`)).data;
}
export async function timeline(id: string) {
  return (await api.get(`/events/${id}/timeline`)).data;
}
export async function analyzeEvent(id: string) {
  return (await api.get(`/events/${id}/analyze`)).data;
}
export async function reportEvent(id: string, kind: string) {
  return (await api.get(`/events/${id}/report`, { params: { kind } })).data;
}
export async function setDefinition(id: string, payload: any) {
  return (await api.put(`/events/${id}/definition`, payload)).data;
}
export async function upsertPeople(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/people`, payload)).data;
}
export async function upsertExposures(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/exposures`, payload)).data;
}
export async function upsertSamples(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/samples`, payload)).data;
}
export async function upsertFoods(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/foods`, payload)).data;
}
export async function upsertHygiene(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/hygiene`, payload)).data;
}
export async function upsertControls(id: string, payload: any[]) {
  return (await api.put(`/events/${id}/controls`, payload)).data;
}
export async function addEvidence(id: string, payload: any) {
  return (await api.post(`/events/${id}/evidence`, payload)).data;
}
export async function setConclusion(id: string, payload: any) {
  return (await api.post(`/events/${id}/conclusions`, payload)).data;
}
export async function setStage(id: string, payload: any) {
  return (await api.post(`/events/${id}/stages`, payload)).data;
}

// —— 知识库 ——
export async function kbDocs(lib: string) {
  return (await api.get("/kb/docs", { params: { lib } })).data;
}
export async function kbDoc(id: string, lib: string) {
  return (await api.get(`/kb/docs/${encodeURIComponent(id)}`, { params: { lib } })).data;
}
export async function kbSearch(q: string, lib: string) {
  return (await api.get("/kb/search", { params: { q, lib } })).data;
}

// —— AI 助手 ——
export async function assistantChat(payload: {
  event_id: string | null;
  question: string;
  history: { role: string; content: string }[];
}) {
  return (await api.post("/assistant/chat", payload)).data;
}
