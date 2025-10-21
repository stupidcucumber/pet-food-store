from typing import List, Optional

from pydantic import BaseModel, Field, RootModel


class Product(BaseModel):
    """Pet food store product."""

    product_name: str = Field(
        title="Product name", example="Purine Dogs Max", max_length=255
    )
    product_description: str = Field(
        title="Product description",
        description="Description of the product, for what pets is most suitable etc.",
        example="Most suitable for chill dogs with sleepy personality.",
    )
    quantity: int = Field(
        title="Available product units",
        description="Number of available units in the store. Cannot be negative.",
        example=100,
        ge=0,
    )
    price: float = Field(
        description="Price for a single unit in the store. Cannot be negative.", gt=0
    )
    active: bool = Field(description="Whether product can be sold.")


class ProductUpdate(BaseModel):
    """Product, but with all fields non-required."""

    product_name: Optional[str] = Field(
        None, title="Product name", example="Purine Dogs Max", max_length=255
    )
    product_description: Optional[str] = Field(
        None,
        title="Product description",
        description="New description of the product, for what pets is most suitable.",
        example="Most suitable for chill dogs with sleepy personality.",
    )
    quantity: Optional[int] = Field(
        None,
        title="Available product units",
        description="New number of available units in the store. Cannot be negative.",
        example=100,
        ge=0,
    )
    price: Optional[float] = Field(
        None,
        description="New price for a single unit in the store. Cannot be negative.",
        gt=0,
    )
    active: Optional[bool] = Field(None, description="New whether product can be sold.")


class ProductWithId(Product):
    """Pet food store product, but with ID."""

    product_id: int = Field(ge=0, description="Id of the product.")


class RequestedSellingQuantity(BaseModel):
    """Selling quantity of the product."""

    quantity: int = Field(
        title="Units to sell",
        description="Number of units you want to sell. Cannot be negative.",
        example=100,
        ge=0,
    )


class RecommendationPetDescription(BaseModel):
    """Description for the pet."""

    description: str = Field(
        min_length=5,
        max_length=1500,
        title="Pet description",
        description="Detailed description of your pet: age, weight, breed etc.",
        example="A husky, 5 years old, weights 10 kg, very active and playful.",
    )


class Recommendation(BaseModel):
    """Recommended product and explanation for it."""

    product_id: int = Field(ge=0, description="Id of the recommended product.")
    name: str = Field(description="Name of the recommended product.")
    reason: str = Field(description="Explanation about why this product suits the pet.")


class ProductWithIdList(RootModel):
    """List of products with ID."""

    root: List[ProductWithId]


class DefaultErrorModel(BaseModel):
    """Model for Swagger UI."""

    detail: str = Field(example="Product with id=1123 is not found.")
