from datetime import datetime
from typing import Annotated, List
from pydantic import BaseModel, Field, parse_obj_as
#from pydantic import ValidationError

from fastapi import APIRouter, HTTPException, Query
from core.logger import Logger
import settings

from sqlalchemy import asc, desc
from sqlalchemy.orm.exc import NoResultFound
from core.db import DB
from core.db.decrypt import DBCrypt

from api.routes.query_model import (
    DBQueryResult, DBQueryParams,
    build_filter, build_sort
)

logger = Logger('music')

db = DB(
    engine=DBCrypt().decrypt(settings.DB_ENGINE),
    logger=logger
)
# This file gets included twice in dev mode!
# Make sure to use run mode for production!
# Or just run using uvicorn!
#logger.info("Here1")

class MusicRecord(BaseModel):
    id: int
    title: str
    watch_id: str
    length_seconds: int
    plays: int
    audio_file: str
    created_at: datetime

router = APIRouter(prefix="/music", tags=["music"])

@router.get("/")
def index(db_query: Annotated[DBQueryParams, Query()]):
    try:
        num_rows = db_query.limit
        start_row = (db_query.page - 1) * num_rows
        total_rows = db.tbl_music\
            .filter(*build_filter(db.tbl_music, db_query))\
            .count()
        results = []
        for result in db.tbl_music\
            .filter(*build_filter(db.tbl_music, db_query))\
            .order_by(build_sort(db.tbl_music, db_query))\
            .limit(num_rows)\
            .offset(start_row)\
            .all():
            results.append(MusicRecord.model_validate(result, from_attributes=True))
    except Exception as exc:
        logger.error(f"Error fetching music data: {exc}")
        raise HTTPException(
            status_code=500, detail=f"Could not get music data, see logs")
    else:
        return DBQueryResult(num_rows=total_rows, rows=results)

