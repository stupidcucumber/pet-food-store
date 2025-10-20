import json

from google import genai
from src.data.models import Recommendation, RecommendationPetDescription
from src.data.queries import select_active_nonzero_products
from src.llm.basellm import BaseLLMRecommender
from typing_extensions import override


class GeminiRecommender(BaseLLMRecommender):
    """Recommender class with Gemini.

    Parameters
    ----------
    api_key : str
        Token to access Gemini API. Can be obtained in the Google AI Studio.
    """

    def __init__(self, api_key: str, **kwargs) -> None:

        super(GeminiRecommender, self).__init__(**kwargs)

        self.api_key = api_key

        self.client = genai.Client(api_key=self.api_key)

        self.aio_client = self.client.aio

    @override
    async def recommend(
        self, description: RecommendationPetDescription
    ) -> Recommendation:

        active_products_list = await select_active_nonzero_products(self.connection)

        system_instructions = [
            "You are an expert **Product Recommendation Engine** for a database of retail products.",
            "Your task is to recommend the single best-suited product based on a given product catalog structure and a user's description.",
        ]

        query = f"""
        ---

        ### **INPUT DATA STRUCTURES**

        1.  **Product Table Schema:**
            * **Table Name:** `products`
            * **Fields:** `product_id` (integer, Primary Key), `product_name` (varchar[255], Not Null), `product_description` (text, Not Null), `quantity` (integer), `price` (decimal[10,2]), `active` (bool)

        2.  **Product Catalog Data:**
            ```json
            {active_products_list.model_dump_json(indent=4)}
            ```

        3.  **User Description:**
            ```json
            {description.model_dump_json(indent=4)}
            ```

        ---

        ### **INSTRUCTIONS & CONSTRAINTS**

        1.  **Recommendation Logic:** Analyze the `product_description` field from the Product Catalog to find the item that best matches the characteristics in the User Description (`"An active dog, 10 years old."`).
        2.  **Selection Rule:** You **must** return exactly **one** product.
        3.  **Mandatory Field Mapping:** The value for the output `"name"` field must be taken from the input's `"product_name"` field. The value for the output `"product_id"` must be taken from the input's `"product_id"` field.

        ---

        ### **OUTPUT FORMAT**

        Generate a JSON object that strictly adheres to the following structure. **Do not include any other text, explanation, or markdown outside of the final JSON block. DO NOT WRAP RESPONSE IN ```json...```**
            {{
                "product_id": (integer corresponding to the recommended product),
                "name": (string of the recommended product's name),
                "reason": (a brief, single sentence justifying the recommendation based on the product description and user's description)
            }}
        """

        response = await self.aio_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instructions
            ),
        )

        response_dict = json.loads(response.text)

        return Recommendation(**response_dict)
