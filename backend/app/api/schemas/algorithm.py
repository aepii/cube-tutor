from pydantic import BaseModel
from typing import List


# Defines the schema for a SolutionDetail
class SolutionDetail(BaseModel):
    solution_id: int
    notation: str
    orientation: int
    is_favorited: bool
    is_learned: bool


# Defines the schema for a CaseGroup
class CaseGroup(BaseModel):
    case_id: int
    case_name: str
    subset: str
    subgroup: str
    setup: str
    solutions: List[SolutionDetail]


# Defines the schema for a AlgorithmFavoriteResponse
class AlgorithmFavoriteResponse(BaseModel):
    algorithm_id: int
    is_favorited: bool


# Defines the schema for a AlgorithmLearnResponse
class AlgorithmLearnResponse(BaseModel):
    algorithm_id: int
    is_learned: bool
