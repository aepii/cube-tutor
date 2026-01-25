from pydantic import BaseModel


# Defines the schema for a AlgorithmRead
class AlgorithmRead(BaseModel):
    solution_id: int
    case_id: int
    case_name: str
    subset: str
    notation: str
    orientation: int
