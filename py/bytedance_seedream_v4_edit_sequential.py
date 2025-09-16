import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class BytedanceSeedreamV4EditSequential:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Generate a series of 2 magazine photoshoots for these models.",
                    "tooltip": "Description of the image editing/generation task. Specify the number of images to generate and use phrases like 'a series of' or 'group of images' for consistency."
                }),
                "images": ("STRING", {
                    "default": "",
                    "tooltip": "Comma-separated URLs of input images (connect from Upload Image nodes). Maximum 10 images.",
                    "forceInput": True
                }),
                "max_images": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 15,
                    "tooltip": "Number of images to generate. Must align with prompt description."
                }),
                "size": (["2227*3183", "1024*1024", "1536*1536", "2048*2048"], {
                    "default": "2048*2048",
                    "tooltip": "Output image size"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Wait for generation to complete before returning"
                }),
            },
            "optional": {
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results. -1 for random seed"
                }),
                "enable_base64_output": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enable base64 output format"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, prompt, images, max_images, size, enable_sync_mode, seed=-1, enable_base64_output=False):
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Process images input - handle both single URLs and comma-separated URLs
        if isinstance(images, str):
            if "," in images:
                # Comma-separated URLs
                image_urls = [url.strip() for url in images.split(",") if url.strip()]
            else:
                # Single URL
                image_urls = [images.strip()] if images.strip() else []
        else:
            # Handle list input (in case it comes as a list)
            image_urls = images if isinstance(images, list) else [str(images)]

        # Validate max 10 images as per API documentation
        if len(image_urls) > 10:
            raise Exception("Maximum 10 input images allowed")

        if not image_urls:
            raise Exception("At least one input image is required")

        payload = {
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode,
            "images": image_urls,
            "max_images": max_images,
            "prompt": prompt,
            "size": size
        }

        # Add seed if not random
        if seed != -1:
            payload["seed"] = seed

        # API endpoint for edit sequential
        endpoint = "/api/v3/bytedance/seedream-v4/edit-sequential"

        try:
            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)

            if enable_sync_mode:
                # In sync mode, we get the results directly
                if "outputs" in response and response["outputs"]:
                    image_urls = response["outputs"]  # Already a list
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception(f"No output received from sync API. Response: {response}")
            else:
                # In async mode, we need to poll for results
                task_id = response["id"]
                print(f"Task submitted successfully. Request ID: {task_id}")

                try:
                    # Wait for task to complete - longer timeout for sequential editing
                    result = real_client.wait_for_task(task_id, polling_interval=1, timeout=600)

                    if "outputs" in result and result["outputs"]:
                        image_urls = result["outputs"]  # Already a list
                        return (imageurl2tensor(image_urls),)
                    else:
                        raise Exception("Task completed but no output received")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in {self.__class__.__name__}: {str(e)}")
            raise e


# Node registration - REQUIRED
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI Bytedance Seedream V4 Edit Sequential": BytedanceSeedreamV4EditSequential
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI Bytedance Seedream V4 Edit Sequential": "WaveSpeedAI Bytedance Seedream V4 Edit Sequential"
}