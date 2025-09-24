# In file: py/wavespeed_api/requests/wan_2_5_i2v.py

from typing import Optional, List
from pydantic import Field
from ..utils import BaseRequest

class Wan25I2V(BaseRequest):
    """
    Request model for the WAN 2.5 Image-to-Video API.

    Advanced image-to-video generation with enhanced motion modeling,
    optional prompt expansion capabilities, and audio-driven generation support.
    """
    image: str = Field(..., description="The image URL for generating the video output.")
    prompt: str = Field(..., description="Text prompt describing the desired motion and content.")
    resolution: str = Field("720p", description="Output video resolution.", enum=["720p", "1080p"])
    duration: int = Field(5, description="Duration of the generated video in seconds.", enum=[5, 10])
    audio: Optional[str] = Field("", description="Optional audio URL for audio-driven video generation.")
    enable_prompt_expansion: Optional[bool] = Field(False, description="Enable automatic prompt expansion for enhanced details.")
    seed: Optional[int] = Field(-1, ge=-1, le=2147483647, description="Random seed for reproducible results.")

    def build_payload(self) -> dict:
        """Builds the request payload dictionary."""
        payload = self.model_dump(exclude_none=True)
        return self._remove_empty_fields(payload)

    def get_api_path(self) -> str:
        """Gets the API path for the request."""
        return "/api/v3/wavespeed-ai/wan-2.5/i2v"

    def field_required(self) -> List[str]:
        """Returns a list of required field names."""
        return ["image", "prompt"]

    def field_order(self) -> List[str]:
        """Defines the order of fields."""
        return ["image", "prompt", "resolution", "duration", "audio", "enable_prompt_expansion", "seed"]