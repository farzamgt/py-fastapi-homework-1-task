from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas.movies import MovieDetailResponseSchema, MovieListResponseSchema


router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(2, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> MovieListResponseSchema:
    total_items = (await db.execute(select(MovieModel))).scalars().all()
    total_count = len(total_items)

    if total_count == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_count + per_page - 1) // per_page
    offset = (page - 1) * per_page

    result = await db.execute(select(MovieModel).offset(offset).limit(per_page))
    movies_raw = result.scalars().all()

    if not movies_raw:
        raise HTTPException(status_code=404, detail="No movies found.")

    movies = []
    for m in movies_raw:
        movies.append(
            MovieDetailResponseSchema(
                id=m.id,
                name=m.name,
                date=m.date,
                score=m.score,
                genre=m.genre,
                overview=(
                    (m.overview[:120] + "...") if len(m.overview) > 120 else m.overview
                ),
                crew=", ".join(m.crew.split(",")[:2]),
                orig_title=m.orig_title,
                status=m.status.strip(),
                orig_lang=m.orig_lang.strip(),
                budget=int(m.budget),
                revenue=int(m.revenue),
                country=m.country,
            )
        )

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1
        else f"/theater/movies/?page=1&per_page={per_page}"
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else f"/theater/movies/?page={total_pages}&per_page={per_page}"
    )

    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_count,
    )


@router.get("/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(
    movie_id: int, db: AsyncSession = Depends(get_db)
) -> MovieDetailResponseSchema:
    result = await db.execute(select(MovieModel).filter(MovieModel.id == movie_id))
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404, detail="Movie with the given ID was not found."
        )
    return MovieDetailResponseSchema(
        id=movie.id,
        name=movie.name,
        date=movie.date,
        score=movie.score,
        genre=movie.genre,
        overview=movie.overview,
        crew=", ".join(movie.crew.split(",")[:2]),
        orig_title=movie.orig_title,
        status=movie.status.strip(),
        orig_lang=movie.orig_lang.strip(),
        budget=int(movie.budget),
        revenue=int(movie.revenue),
        country=movie.country,
    )
