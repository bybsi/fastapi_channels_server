from typing import Literal, List, TypeVar, Generic
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc

T = TypeVar('T')
class DBQueryResult(BaseModel, Generic[T]):
    num_rows: int
    rows: List[T]


class DBQueryParams(BaseModel):
    limit: int = Field(25, gt=0, le=1000)
    page: int = Field(1, ge=1)
    sort_order: Literal['asc', 'desc', 'ASC', 'DESC'] = 'DESC'
    order_by: str
    search_key: List[str] | None = None
    search_val: List[str] | None = None


#search_types = {
#    '':'lte'
#}
def build_filter(tbl, query_params):
    keys = query_params.search_key
    if keys is None or len(keys) == 0:
        return []

    vals = query_params.search_val
    if vals is None or len(vals) != len(keys):
        return []

    filters = []
    for idx, key in enumerate(keys):
        filters.append(tbl.__table__.c[key] == vals[idx])

    return filters

def build_sort(tbl, query_params):
    f = tbl.__table__.c[query_params.order_by]
    return asc(f) if query_params.sort_order.lower() == 'asc' else desc(f)
