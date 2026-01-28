from pydantic import BaseModel


# Defines the schema for a AlgorithResponse
class AlgorithmResponse(BaseModel):
    solution_id: int
    case_id: int
    case_name: str
    subset: str
    notation: str
    orientation: int


# Defines the schema for a AlgorithFavoriteResponse
class AlgorithmFavoriteResponse(BaseModel):
    algorithm_id: str
    is_favorited: bool


# Defines the schema for a AlgorithLearnResponse
class AlgorithmLearnResponse(BaseModel):
    algorithm_id: str
    is_learned: bool
