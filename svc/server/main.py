import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import aiosqlite
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Path, Request, Response, status
from fastapi.responses import JSONResponse
from google.genai.errors import APIError
from src.data.exceptions import PetStoreException
from src.data.models import (
    NotFoundProduct,
    Product,
    ProductUpdate,
    ProductWithId,
    ProductWithIdList,
    Recommendation,
    RecommendationPetDescription,
    RequestedSellingQuantity,
)
from src.data.queries import (
    deactivate_product,
    insert_product,
    select_product,
    select_products,
    sell_product,
    update_product,
)
from src.llm.geminillm import GeminiRecommender
from src.logger import start_logging, stop_logging

load_dotenv()


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan_event(app: FastAPI) -> AsyncGenerator[None, None]:
    """Generate lifespan event on demand of API.

    Instantiates database connection object, and puts into the state of the
    application.

    Parameters
    ----------
    app : FastAPI
        Main application that will create lifespan event.

    Yields
    ------
    None
        Asynchronous generator of lifespan events.
    """
    start_logging()

    app.state.database = await aiosqlite.connect(
        os.environ.get("DATABASE_PATH", "default.sqlite")
    )

    app.state.gemini_recommender = GeminiRecommender(
        api_key=os.environ.get("GEMINI_API_KEY"), connection=app.state.database
    )

    async with app.state.database.cursor() as cursor:

        with open(os.environ.get("DATABASE_INIT_SCRIPT_PATH", "init_sql.sql")) as f:

            initial_script = f.read()

        await cursor.executescript(initial_script)

    await app.state.database.commit()

    logger.info("Database has been initialized.")

    try:

        yield

    finally:

        logger.info("Closing the connection to the database.")

        await app.state.database.close()

        logger.info("Logger is stopping.")

        stop_logging()


async def get_db_connection(request: Request) -> aiosqlite.Connection:
    """Get current database connection.

    Parameters
    ----------
    request : Request
        Received request from client.

    Returns
    -------
    aiosqlite.Connection
        Connection to the database.
    """
    return request.app.state.database


async def get_gemini_recommender(request: Request) -> GeminiRecommender:
    """Get current GeminiRecommender class.

    Parameters
    ----------
    request : Request
        Received request from client.

    Returns
    -------
    GeminiRecommender
        Recommender that uses GeminiAPI.
    """
    return request.app.state.gemini_recommender


app = FastAPI(lifespan=lifespan_event)


@app.exception_handler(aiosqlite.Error)
async def database_error_exception_handler(
    request: Request, exc: aiosqlite.Error
) -> JSONResponse:

    logger.error("Caught an database error.", exc_info=True)

    await request.app.state.database.rollback()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "database_error": exc.sqlite_errorname,
        },
    )


@app.exception_handler(APIError)
async def gemini_api_exception_handler(request: Request, exc: APIError) -> JSONResponse:

    logger.error("Caught an error while sending API request to Gemini.", exc_info=True)

    await request.app.state.database.rollback()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"gemini_error": exc}
    )


@app.exception_handler(PetStoreException)
async def pet_store_custom_exceptions_handler(
    request: Request, exc: PetStoreException
) -> JSONResponse:

    logger.error(
        "Caught an error while sending API request to the store itself.", exc_info=True
    )

    await request.app.state.database.rollback()

    return JSONResponse(
        status_code=exc.status_code, content={"store_error": exc.detail}
    )


@app.get("/api/status")
async def api_status(
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)]
) -> JSONResponse:
    """Get status of components of the API.

    Parameters
    ----------
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    JSONResponse
        In case of success returns status 200. Contains status for each integral
        component of the service.
    """
    database_alive = True

    if not connection:

        database_alive = False

    try:

        async with connection.cursor() as cursor:

            await cursor.execute("SELECT 1;")

    except Exception:

        database_alive = False

    return JSONResponse(
        content={"database_status": database_alive}, status_code=status.HTTP_200_OK
    )


@app.get("/api/products", response_model=ProductWithIdList, description="")
async def get_products(
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)]
) -> JSONResponse:
    """Get all products from a database.

    Parameters
    ----------
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    JSONResponse
        List of all products in the database.
    """
    products = await select_products(connection=connection)

    return JSONResponse(content=products.model_dump(), status_code=status.HTTP_200_OK)


@app.get(
    "/api/products/{id}",
    response_model=ProductWithId,
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundProduct}},
)
async def get_product(
    id: Annotated[
        int,
        Path(
            ge=0,
            title="Product ID",
            description="Id of the product to fetch from the database.",
        ),
    ],
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)],
) -> JSONResponse:
    """Get product by id.

    Parameters
    ----------
    id : Annotated
        ID of the product to get.
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    JSONResponse
        Product with the specified id if such exists.
    """
    product = await select_product(id, connection)

    return JSONResponse(content=product.model_dump(), status_code=status.HTTP_200_OK)


@app.post("/api/product", response_model=ProductWithId)
async def post_product(
    product: Product,
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)],
) -> JSONResponse:
    """Create a new product.

    Parameters
    ----------
    product : Product
        Product to create.
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    JSONResponse
        Newly created product along with its assigned id.
    """
    product_with_id = await insert_product(product, connection)

    return JSONResponse(
        content=product_with_id.model_dump(), status_code=status.HTTP_200_OK
    )


@app.put(
    "/api/product/{id}",
    response_model=ProductWithId,
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundProduct}},
)
async def put_product(
    id: Annotated[
        int,
        Path(
            ge=0,
            title="Product ID",
            description="Id of the product you want to update.",
        ),
    ],
    product: ProductUpdate,
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)],
) -> JSONResponse:
    """Set new values for specified product columns.

    Parameters
    ----------
    id : Annotated
        Id of the product you want to update.
    product : ProductUpdate
        Product fields along with values that needs to be updated.
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    JSONResponse
        Newly created product along with its assigned id.
    """
    product_with_id = await update_product(id, product, connection)

    return JSONResponse(
        content=product_with_id.model_dump(), status_code=status.HTTP_200_OK
    )


@app.delete(
    "/app/product/{id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundProduct}},
)
async def delete_product(
    id: Annotated[
        int,
        Path(
            ge=0,
            title="Product ID",
            description="Id of the product you want to delete.",
        ),
    ],
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)],
) -> Response:
    """Set "active" column to false, virtually deleting product from database.

    Parameters
    ----------
    id : Annotated
        Id of the product you want to delete.
    connection : Annotated[aiosqlite.Connection, Depends(get_db_connection)]
        Connection to the database that was saved in FastAPI state.

    Returns
    -------
    Response
        A response with status_code=204 if everything is right. No body is
        returned.
    """
    _ = await deactivate_product(id, connection)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/app/products/{id}/sell",
    response_model=ProductWithId,
    responses={status.HTTP_404_NOT_FOUND: {"model": NotFoundProduct}},
)
async def post_product_sell(
    id: Annotated[
        int,
        Path(
            gt=0, title="Product ID", description="Id of the product you want to sell."
        ),
    ],
    quantity: RequestedSellingQuantity,
    connection: Annotated[aiosqlite.Connection, Depends(get_db_connection)],
) -> JSONResponse:
    left_product = await sell_product(id, quantity, connection)

    return JSONResponse(
        content=left_product.model_dump(), status_code=status.HTTP_200_OK
    )


@app.post("/app/recommendation", response_model=Recommendation)
async def post_recommendation(
    description: RecommendationPetDescription,
    gemini_recommender: Annotated[GeminiRecommender, Depends(get_gemini_recommender)],
) -> JSONResponse:
    response = await gemini_recommender.recommend(description)

    return JSONResponse(content=response.model_dump(), status_code=status.HTTP_200_OK)
