from typing import List

from pydantic import BaseModel, Field, RootModel


class Product(BaseModel):
    """Pet food store product."""

    product_name: str = Field(max_length=255)
    product_description: str
    quantity: int = Field(
        description="Number of available units in the store. Cannot be negative.", ge=0
    )
    price: float = Field(
        description="Price for a single unit in the store. Cannot be negative.", gt=0
    )
    active: bool = Field(description="Whether product can be sold.")


class ProductWithId(Product):
    """Pet food store product, but with ID."""

    product_id: int


class ProductWithIdList(RootModel):
    """List of products with ID."""

    root: List[ProductWithId]


class NotFoundProduct(BaseModel):
    """Model for Swagger UI."""

    detail: str = Field(example="Product with id=1123 is not found.")
