import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class ByteDanceSeeDreamV4Sequential:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Detailed description including number of images to generate. Example: 'Generate a series of 4 images of [subject]...'"
                }),
            },
            "optional": {
                "size": ("STRING", {
                    "default": "2048*2048",
                    "tooltip": "Output image dimensions (1024-4096 pixels per dimension). Format: width*height"
                }),
                "max_images": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 15,
                    "tooltip": "Maximum number of images to generate (1-15). Must align with prompt's image count."
                }),
                "enable_base64_output": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Return image as BASE64 encoded string instead of URL"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Wait for generation to complete before returning"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results. -1 for random seed"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_images",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, prompt, size="2048*2048", max_images=1, enable_base64_output=False, enable_sync_mode=True, seed=-1):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Build payload
        payload = {
            "prompt": prompt,
            "size": size,
            "max_images": max_images,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode
        }

        # Add seed if specified (not -1)
        if seed != -1:
            payload["seed"] = seed

        # API endpoint
        endpoint = "/api/v3/bytedance/seedream-v4/sequential"

        try:
            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)

            if enable_sync_mode:
                # Sync mode - response should contain outputs directly
                if "outputs" in response and response["outputs"]:
                    image_urls = response["outputs"]
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception(f"No output received from sync API. Response: {response}")
            else:
                # Async mode - need to poll for results
                task_id = response["id"]
                print(f"ByteDance SeeDream V4 Sequential task submitted. Request ID: {task_id}")
                print(f"Generating {max_images} image(s) - this may take longer than usual.")

                try:
                    # Sequential generation typically takes longer, so increase timeout
                    timeout = max(300, max_images * 60)  # At least 1 minute per image
                    result = real_client.wait_for_task(task_id, polling_interval=3, timeout=timeout)

                    if "outputs" in result and result["outputs"]:
                        image_urls = result["outputs"]
                        return (imageurl2tensor(image_urls),)
                    else:
                        raise Exception("Task completed but no output received")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in ByteDance SeeDream V4 Sequential: {str(e)}")
            raise e


# Node registration
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI ByteDance SeeDream V4 Sequential": ByteDanceSeeDreamV4Sequential
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI ByteDance SeeDream V4 Sequential": "WaveSpeedAI ByteDance SeeDream V4 Sequential"
}