import time
import json
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient

class QwenImageTextToImageLoraNode:
    """
    Qwen Image Text-to-Image with LoRA Node

    Advanced version of Qwen-Image text-to-image that supports LoRA (Low-Rank Adaptation) models
    for fine-tuned generation with specific styles and characteristics.
    """

    # Resolution presets with aspect ratios
    RESOLUTION_MAP = {
        "1:1 (Square)": (1024, 1024),
        "16:9 (Widescreen Landscape)": (1664, 928),
        "9:16 (Widescreen Portrait)": (928, 1664),
        "4:3 (Standard Landscape)": (1472, 1104),
        "3:4 (Standard Portrait)": (1104, 1472),
        "3:2 (Classic Landscape)": (1584, 1056),
        "2:3 (Classic Portrait)": (1056, 1584)
    }

    SIZES = list(RESOLUTION_MAP.keys())

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text prompt for image generation (e.g., 'Realism, a female inventor with auburn hair...')"
                }),
                "size": (s.SIZES, {
                    "default": "1:1 (Square)",
                    "tooltip": "The aspect ratio and resolution of the generated image"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results. -1 for random seed"
                }),
                "output_format": (["jpeg", "png", "webp"], {
                    "default": "jpeg",
                    "tooltip": "The format of the output image"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Wait for image generation to complete before returning"
                }),
            },
            "optional": {
                "loras": ("STRING", {
                    "multiline": True,
                    "default": '[]',
                    "tooltip": 'JSON array of LoRA models. Example: [{"path": "flymy-ai/qwen-image-realism-lora", "scale": 1}]'
                }),
                "custom_size": ("STRING", {
                    "default": "",
                    "tooltip": "Custom size as 'width*height' (e.g. '1920*1080'). Overrides size dropdown if provided."
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)

    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, prompt, size="1:1 (Square)", seed=-1,
                output_format="jpeg", enable_sync_mode=True, loras='[]', custom_size=""):
        """
        Execute the Qwen Image Text-to-Image with LoRA model

        Args:
            client: WaveSpeed API client
            prompt: Text prompt for image generation
            size: Image size from dropdown (aspect ratio preset)
            seed: Random seed (-1 for random)
            output_format: Output format (jpeg, png, or webp)
            enable_sync_mode: Whether to wait for completion
            loras: JSON string of LoRA configurations
            custom_size: Optional custom size override

        Returns:
            Generated image tensor
        """

        # Parse LoRA configuration
        try:
            if loras and loras.strip() and loras.strip() != '[]':
                lora_list = json.loads(loras)
                # Validate LoRA structure
                for lora in lora_list:
                    if not isinstance(lora, dict):
                        raise ValueError(f"Each LoRA must be a dictionary with 'path' and 'scale' keys")
                    if 'path' not in lora:
                        raise ValueError(f"LoRA missing 'path' key: {lora}")
                    if 'scale' not in lora:
                        lora['scale'] = 1.0  # Default scale if not provided
            else:
                lora_list = []
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid LoRA JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Error processing LoRA configuration: {e}")

        # Use custom size if provided, otherwise convert dropdown selection to width*height
        if custom_size.strip():
            final_size = custom_size.strip()
            # Validate custom size format
            if '*' not in final_size:
                raise ValueError(f"Invalid custom size format: {final_size}. Must be 'width*height' (e.g., '1024*1024')")
        else:
            # Get resolution from map
            if size in self.RESOLUTION_MAP:
                width, height = self.RESOLUTION_MAP[size]
                final_size = f"{width}*{height}"
            else:
                raise ValueError(f"Invalid size selection: {size}")

        # Prepare the request payload
        payload = {
            "prompt": prompt,
            "size": final_size,
            "seed": seed,
            "output_format": output_format,
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": False,
            "loras": lora_list
        }

        # API endpoint for Qwen Image Text-to-Image with LoRA
        endpoint = "/api/v3/wavespeed-ai/qwen-image/text-to-image-lora"

        try:
            # Create the actual client object from the client dict
            real_client = WaveSpeedClient(api_key=client["api_key"])

            # Make the API request
            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)

            # Handle sync mode response
            if enable_sync_mode:
                # WaveSpeedClient already extracts the 'data' field
                if "outputs" in response and response["outputs"]:
                    image_urls = response["outputs"]
                    print(f"Sync mode completed. Generated {len(image_urls)} image(s)")
                    # Pass the full URLs array
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception(f"No output received from sync API. Response: {response}")

            # Handle async mode response
            else:
                # Extract task ID from response
                if "id" not in response:
                    raise Exception(f"No task ID received from API. Response: {response}")

                task_id = response["id"]
                print(f"Task submitted successfully. Request ID: {task_id}")

                # Use the client's wait_for_task method for polling
                try:
                    result = real_client.wait_for_task(task_id, polling_interval=1, timeout=300)

                    if "outputs" in result and result["outputs"]:
                        image_urls = result["outputs"]
                        print(f"Task completed. Generated {len(image_urls)} image(s)")
                        # Pass the full URLs array
                        return (imageurl2tensor(image_urls),)
                    else:
                        raise Exception("Task completed but no output received")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in Qwen Image Text-to-Image LoRA: {str(e)}")
            raise e


# Node registration
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI Qwen Image Text to Image LoRA": QwenImageTextToImageLoraNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI Qwen Image Text to Image LoRA": "WaveSpeedAI Qwen Image Text-to-Image LoRA"
}