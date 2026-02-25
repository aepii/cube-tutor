export interface AlgorithmSolution {
  solution_id: number;
  notation: string;
  orientation: number;
  is_favorited: boolean;
  is_learned: boolean;
}

export interface AlgorithmCase {
  case_id: number;
  case_name: string;
  subset: string;
  subgroup: string;
  setup: string;
  solutions: Array<AlgorithmSolution>;
}
