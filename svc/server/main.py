import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import aiosqlite
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from src.data.models import (
    NotFoundProduct,
    Product,
    ProductUpdate,
    ProductWithId,
    ProductWithIdList,
)
from src.data.queries import (
    insert_product,
    select_product,
    select_products,
    update_product,
)

load_dotenv()


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
    app.state.database = await aiosqlite.connect(
        os.environ.get("DATABASE_PATH", "default.sqlite")
    )

    async with app.state.database.cursor() as cursor:

        with open(os.environ.get("DATABASE_INIT_SCRIPT_PATH", "init_sql.sql")) as f:

            initial_script = f.read()

        await cursor.executescript(initial_script)

    await app.state.database.commit()

    try:

        yield

    finally:

        await app.state.database.close()


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


app = FastAPI(lifespan=lifespan_event)


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

    except aiosqlite.Error:

        database_alive = False

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

    Raises
    ------
    HTTPException
        In case server encounteres an unexpected error.
    """
    try:

        products = await select_products(connection=connection)

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception caught: {e}.",
        )

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

    Raises
    ------
    HTTPException
        In case server encounteres an unexpected error.
    """
    try:

        product = await select_product(id, connection)

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Exception caught: {e}.",
        )

    if not product:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id={id} is not found.",
        )

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

    Raises
    ------
    HTTPException
        In case server encounteres an unexpected error.
    """
    try:

        product_with_id = await insert_product(product, connection)

    except Exception as e:

        await connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not insert a product into the database: {e}",
        )

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

    Raises
    ------
    HTTPException
        In case server encounteres an unexpected error.
    """
    try:

        product_with_id = await update_product(id, product, connection)

    except Exception as e:

        await connection.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update product with id={id}: {e}",
        )

    return JSONResponse(
        content=product_with_id.model_dump(), status_code=status.HTTP_200_OK
    )
