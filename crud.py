from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from utils.pagination import paginate


async def get_all(
        db: AsyncSession, 
        model, 
        join = None,  
        filter_query: tuple = None, 
        options: list = None, 
        group_by: tuple = None, 
        order_by: tuple = None,
        unique: bool = False,
        page: int = 1, 
        limit: int = 20
        ):
    offset = (page - 1) * limit

    # Count total rows
    count_query = select(func.count()).select_from(model)
    if filter_query is not None:
        count_query = count_query.where(filter_query)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get data
    query = select(model).limit(limit).offset(offset)
    if filter_query is not None:
        query = query.where(filter_query)
    if options is not None:
        query = query.options(*options)
    if join:
        query = query.join(*join)
    if group_by:
        query = query.group_by(*group_by)
    if order_by is not None:
        query = query.order_by(order_by)

    result = await db.execute(query)
    if unique:
        data = result.unique().scalars().all()
    else:
        data = result.scalars().all()

    return await paginate(data=data, total=total, page=page, limit=limit)

async def get_one(db: AsyncSession, model, filter_query, options = None, first: bool = False):
    query = select(model).where(filter_query)
    if options is not None:
        query = query.options(*options)
        
    result = await db.execute(query)
    
    if first:
        return result.unique().first()
    return result.unique().scalar_one_or_none()
    
async def create(db: AsyncSession, model, form: dict, id: bool = False, flush: bool = False):
    query = insert(model).values(form)
    query_execute = await db.execute(query)
    if id:
        await db.commit()
        return query_execute.inserted_primary_key[0]
    if flush:
        await db.flush()
        return query_execute.inserted_primary_key[0]
    
    await db.commit()

async def change(db: AsyncSession, model, filter_query, form: dict):
    query = update(model).where(filter_query).values(form)
    await db.execute(query)
    await db.commit()

async def remove(db: AsyncSession, model, filter_query):
    query = delete(model).where(filter_query)
    await db.execute(query)
    await db.commit()