from typing import Optional, Tuple

from aiosqlite import Connection
from src.data.models import Product, ProductUpdate, ProductWithId, ProductWithIdList


async def _tuple2productWithId(item: Tuple) -> ProductWithId:
    return ProductWithId(
        product_id=item[0],
        product_name=item[1],
        product_description=item[2],
        quantity=item[3],
        price=item[4],
        active=item[5],
    )


async def select_product(
    product_id: int, connection: Connection
) -> Optional[ProductWithId]:
    """Select a specific product by id.

    Parameters
    ----------
    product_id : int
        Product id to select.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    Optional[ProductWithId]
        If such product exists returns this product.
    """
    async with connection.cursor() as cursor:

        await cursor.execute("SELECT * FROM products WHERE product_id=?;", [product_id])

        item = await cursor.fetchone()

    if item is None:

        return None

    return await _tuple2productWithId(item)


async def select_products(connection: Connection) -> ProductWithIdList:
    """Select all products from table products.

    Parameters
    ----------
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithIdList
        List of all products in the database.
    """
    async with connection.cursor() as cursor:

        await cursor.execute("SELECT * FROM products;")

        items = await cursor.fetchall()

    result = []

    for item in items:
        product = await _tuple2productWithId(item)
        result.append(product)

    return ProductWithIdList(result)


async def insert_product(product: Product, connection: Connection) -> ProductWithId:
    """Insert product into the database.

    Parameters
    ----------
    product : Product
        Product parameters.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithId
        Newly created product.
    """
    async with connection.cursor() as cursor:

        await cursor.execute(
            "INSERT INTO products "
            "(product_name, product_description, quantity, price, active) "
            "VALUES (?, ?, ?, ?, ?) "
            "RETURNING "
            "product_id, product_name, product_description, quantity, price, active;",
            list(product.model_dump().values()),
        )

        result = await cursor.fetchone()

    await connection.commit()

    return await _tuple2productWithId(result)


async def update_product(
    product_id: int, product: ProductUpdate, connection: Connection
) -> ProductWithId:
    """Update product with new values.

    Parameters
    ----------
    product_id : int
        Id of the product you will need to update.
    product : ProductUpdate
        Values that needs to be updated.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithId
        Newly created product.
    """
    async with connection.cursor() as cursor:

        product_dict = product.model_dump(exclude_none=True)

        set_string = ", ".join([key + "=?" for key in product_dict.keys()])

        await cursor.execute(
            f"UPDATE products SET {set_string} WHERE product_id=? "
            "RETURNING "
            "product_id, product_name, product_description, quantity, price, active;",
            (*list(product_dict.values()), product_id),
        )

        result = await cursor.fetchone()

    await connection.commit()

    return await _tuple2productWithId(result)
