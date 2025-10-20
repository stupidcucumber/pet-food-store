from fastapi import HTTPException, status


class PetStoreException(HTTPException):
    """Base class for all custom exceptions of the class."""


class ProductIsNotActive(PetStoreException):

    def __init__(self, product_id: int) -> None:

        super(ProductIsNotActive, self).__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with product_id={product_id} is not active.",
        )


class ProductNoSufficientStock(PetStoreException):

    def __init__(self, product_id: int, quantity: int) -> None:

        super(ProductNoSufficientStock, self).__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with product_id={product_id} has only {quantity} left.",
        )


class ProductNotFound(PetStoreException):

    def __init__(self, product_id: int) -> None:

        super(ProductNotFound, self).__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with product_id={product_id} is not in the database.",
        )


class NoActiveProducts(PetStoreException):

    def __init__(self):

        super(NoActiveProducts, self).__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database currently holds no active products.",
        )
