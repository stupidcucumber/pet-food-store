from typing import List, Optional

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


class ProductUpdate(BaseModel):
    """Product, but with all fields non-required."""

    product_name: Optional[str] = Field(None, max_length=255)
    product_description: Optional[str] = Field(None)
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[float] = Field(None, gt=0)
    active: Optional[bool] = Field(None)


class ProductWithId(Product):
    """Pet food store product, but with ID."""

    product_id: int = Field(ge=0, description="Id of the product.")


class RequestedSellingQuantity(BaseModel):
    """Selling quantity of the product."""

    quantity: int = Field(gt=0, description="Quantity of the product you want to sell.")


class ProductWithIdList(RootModel):
    """List of products with ID."""

    root: List[ProductWithId]


class NotFoundProduct(BaseModel):
    """Model for Swagger UI."""

    detail: str = Field(example="Product with id=1123 is not found.")
