import time

from .wavespeed_api.client import WaveSpeedClient
from .wavespeed_api.utils import imageurl2tensor


class GoogleNanoBananaProEditUltra:
    """
    Google Nano Banana Pro Edit Ultra (Gemini 3.0 Pro Image)

    Ultra high-resolution AI-powered image editing with 4K/8K output support.
    Combines precision, flexibility, and semantic awareness for professional-grade editing.

    Features:
    - Native 4K/8K image generation with fine detail and clean edges
    - Natural-language, context-aware editing
    - Multilingual on-image text with auto translation
    - Camera-style controls (angle, focus, depth of field)
    - Consistent character and style rendering

    Pricing: $0.15/image (4k), $0.18/image (8k)
    """

    # Aspect ratio options
    ASPECT_RATIOS = [
        "1:1",
        "3:2",
        "2:3",
        "3:4",
        "4:3",
        "4:5",
        "5:4",
        "9:16",
        "16:9",
        "21:9",
    ]

    # Resolution options (Ultra = 4k/8k)
    RESOLUTIONS = ["4k", "8k"]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text description of the edit to perform (e.g., 'Replace the cloudy sky with a clear sunset')",
                    },
                ),
                "image_url": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "URL of input image for editing (connect from Upload Image node)",
                        "forceInput": True,
                    },
                ),
                "aspect_ratio": (
                    s.ASPECT_RATIOS,
                    {
                        "default": "1:1",
                        "tooltip": "Aspect ratio of the output image",
                    },
                ),
                "resolution": (
                    s.RESOLUTIONS,
                    {
                        "default": "4k",
                        "tooltip": "Output resolution: 4k ($0.15), 8k ($0.18)",
                    },
                ),
                "output_format": (
                    ["png", "jpeg"],
                    {
                        "default": "png",
                        "tooltip": "Output format - use PNG for transparency support",
                    },
                ),
                "enable_sync_mode": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Wait for generation to complete before returning",
                    },
                ),
            },
            "optional": {
                "additional_images": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Additional image URLs (one per line, max 13 additional for 14 total)",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "WaveSpeedAI/Google"
    FUNCTION = "execute"

    def execute(
        self,
        client,
        prompt,
        image_url,
        aspect_ratio,
        resolution,
        output_format,
        enable_sync_mode,
        additional_images="",
    ):
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Build images array
        images = [image_url]

        # Add additional images if provided
        if additional_images and additional_images.strip():
            additional_urls = [
                url.strip() for url in additional_images.split("\n") if url.strip()
            ]
            # Limit to 13 additional images (14 total max)
            images.extend(additional_urls[:13])

        payload = {
            "prompt": prompt,
            "images": images,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "output_format": output_format,
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": False,
        }

        endpoint = "/api/v3/google/nano-banana-pro/edit-ultra"

        try:
            response = real_client.post(
                endpoint, payload, timeout=real_client.once_timeout
            )

            if enable_sync_mode:
                if "outputs" in response and response["outputs"]:
                    image_urls = response["outputs"]
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception(
                        f"No output received from sync API. Response: {response}"
                    )
            else:
                task_id = response["id"]
                print(f"Task submitted successfully. Request ID: {task_id}")

                try:
                    result = real_client.wait_for_task(
                        task_id, polling_interval=1, timeout=300
                    )

                    if "outputs" in result and result["outputs"]:
                        image_urls = result["outputs"]
                        return (imageurl2tensor(image_urls),)
                    else:
                        raise Exception("Task completed but no output received")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in {self.__class__.__name__}: {str(e)}")
            raise e


NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI Google Nano Banana Pro Edit Ultra": GoogleNanoBananaProEditUltra
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI Google Nano Banana Pro Edit Ultra": "WaveSpeedAI Google Nano Banana Pro Edit Ultra"
}
