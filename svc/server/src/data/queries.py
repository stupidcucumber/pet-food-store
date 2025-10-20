from typing import Optional, Tuple

from aiosqlite import Connection
from src.data.models import (
    Product,
    ProductUpdate,
    ProductWithId,
    ProductWithIdList,
    RequestedSellingQuantity,
)


async def _tuple2productWithId(item: Tuple) -> ProductWithId:
    return ProductWithId(
        product_id=item[0],
        product_name=item[1],
        product_description=item[2],
        quantity=item[3],
        price=item[4],
        active=item[5],
    )


async def select_product(product_id: int, connection: Connection) -> ProductWithId:
    """Select a specific product by id.

    Parameters
    ----------
    product_id : int
        Product id to select.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithId
        If such product exists returns this product.

    Raises
    ------
    RuntimeError
        In case selected product does not exist.
    """
    async with connection.cursor() as cursor:

        await cursor.execute("SELECT * FROM products WHERE product_id=?;", [product_id])

        item = await cursor.fetchone()

    if item is None:

        raise RuntimeError(f"There is no product with product_id={product_id}")

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

    Raises
    ------
    RuntimeError
        In case selected product does not exist.
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

    if result is None:

        raise RuntimeError(f"There is no product with product_id={product_id}")

    await connection.commit()

    return await _tuple2productWithId(result)


async def deactivate_product(
    product_id: int, connection: Connection
) -> Optional[ProductWithId]:
    """Deactivate product.

    Parameters
    ----------
    product_id : int
        Id of the product you want to delete.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    Optional[ProductWithId]
        Product with Id that you deleted, if such exists.

    Raises
    ------
    RuntimeError
        In case selected product does not exist.
    """
    async with connection.cursor() as cursor:

        await cursor.execute(
            "UPDATE products SET active=false WHERE product_id=? "
            "RETURNING "
            "product_id, product_name, product_description, quantity, price, active;",
            [product_id],
        )

        result = await cursor.fetchone()

    if result is None:

        raise RuntimeError(f"There is no product with product_id={product_id}")

    await connection.commit()

    return await _tuple2productWithId(result)


async def sell_product(
    product_id: int, quantity: RequestedSellingQuantity, connection: Connection
) -> ProductWithId:
    """Sell a specific amount of product.

    Parameters
    ----------
    product_id : int
        Id of the product you want to sell.
    quantity : RequestedSellingQuantity
        How much product you want to sell.
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithId
        Updated product.

    Raises
    ------
    RuntimeError
        In case selected product does not exist, is not active, or does not have
        enought quantity.
    """
    product = await select_product(product_id, connection)

    if not product.active:

        raise RuntimeError("Selectected product is not active.")

    if product.quantity < quantity.quantity:

        raise RuntimeError("Not enough product to sell!")

    async with connection.cursor() as cursor:

        new_quantity = product.quantity - quantity.quantity

        await cursor.execute(
            "UPDATE products SET quantity=? WHERE product_id=? "
            "RETURNING "
            "product_id, product_name, product_description, quantity, price, active;",
            [new_quantity, product_id],
        )

        left_product = await cursor.fetchone()

    if left_product is None:

        raise RuntimeError(f"There is no product with product_id={product_id}")

    await connection.commit()

    return await _tuple2productWithId(left_product)


async def select_active_nonzero_products(connection: Connection) -> ProductWithIdList:
    """Select active products that have at least some items left.

    Parameters
    ----------
    connection : Connection
        A connection to the database that contains products table.

    Returns
    -------
    ProductWithIdList
        List of all active products with quantities bigger than 0 in the database.
    """
    async with connection.cursor() as cursor:
        
        await cursor.execute("SELECT * FROM products WHERE active=true AND quantity>0;")
        
        items = await cursor.fetchall()
        
    if len(items) == 0:
        
        raise RuntimeError(f"There is no active in-stock products right now at the store!")
    
    result = [await _tuple2productWithId(item) for item in items]
        
    return ProductWithIdList(result)
