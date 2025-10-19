import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

import aiosqlite
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse

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
