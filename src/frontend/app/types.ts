export type PrimaryNodeType = 'question' | 'hypothesis' | 'evidence' | 'perspective' | 'conflict' | 'judge' | 'conclusion';
export type GraphNodeType = PrimaryNodeType | 'satellite';

export interface EvidenceItem { claim?: string; source_title?: string; url?: string; quality?: string | number; }
export interface PerspectiveItem { analysis?: string; point?: string; position?: string; }
export interface HypothesisData { hypotheses?: Array<{ claim?: string }>; }
export interface EvidenceData { evidence?: EvidenceItem[]; }
export interface PerspectiveData { perspectives?: PerspectiveItem[]; }
export interface ConflictData { summary?: string; conflicts?: string[]; }
export interface JudgeData { synthesis?: string; }
export interface ConclusionData { conclusion?: string; }
export interface QuestionData { question: string; }

export interface BaseNode<T extends GraphNodeType, D> { id: string; type: T; round: number; data: D; }
export type QuestionNode = BaseNode<'question', QuestionData>;
export type HypothesisNode = BaseNode<'hypothesis', HypothesisData>;
export type EvidenceNode = BaseNode<'evidence', EvidenceData>;
export type PerspectiveNode = BaseNode<'perspective', PerspectiveData>;
export type ConflictNode = BaseNode<'conflict', ConflictData>;
export type JudgeNode = BaseNode<'judge', JudgeData>;
export type ConclusionNode = BaseNode<'conclusion', ConclusionData>;
export interface SatelliteNode extends BaseNode<'satellite', EvidenceItem | PerspectiveItem> { satellite: true; parentId: string; parentType: 'evidence' | 'perspective'; }
export type ReasoningNode = QuestionNode | HypothesisNode | EvidenceNode | PerspectiveNode | ConflictNode | JudgeNode | ConclusionNode | SatelliteNode;
export type PositionedNode = ReasoningNode & { x: number; y: number; vx?: number; vy?: number; fx?: number | null; fy?: number | null; index?: number; };
export type GraphEdgeKind = 'flow' | 'continuation' | 'thread' | 'satellite';
export interface GraphEdge { source: string | PositionedNode; target: string | PositionedNode; kind: GraphEdgeKind; }
export interface GraphData { nodes: ReasoningNode[]; edges: GraphEdge[]; rounds: number; layoutSeed: string; }
export interface ReasoningState { nodes?: Array<{ id: string; type: string; round: number; data: unknown }>; iteration?: number; status: string; current_stage?: string; evidence?: EvidenceData; confidence?: { score?: number }; errors?: string[]; }
export interface SessionPayload { session_id?: string; question: string; state: ReasoningState; }
export interface PopupState { selectedNodeId: string | null; }

export function assertNever(value: never): never { throw new Error(`Unhandled node type: ${JSON.stringify(value)}`); }
