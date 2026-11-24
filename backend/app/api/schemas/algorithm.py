from pydantic import BaseModel, StrictBool


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
    solutions: list[SolutionDetail]


# Defines the schema for a AlgorithmFavoriteResponse
class AlgorithmFavoriteResponse(BaseModel):
    algorithm_id: int
    is_favorited: bool


# Defines the schema for a AlgorithmLearnResponse
class AlgorithmLearnResponse(BaseModel):
    algorithm_id: int
    is_learned: bool


# Request body for PUT /v1/algs/{id}/favorite and /learn: the flag's new value.
# StrictBool: only JSON true/false, not "yes" or 1.
class FlagUpdate(BaseModel):
    value: StrictBool
