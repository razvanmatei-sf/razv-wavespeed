import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class ByteDanceSeeDreamV4:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Describe the image to generate. Only one image can be generated per request."
                }),
            },
            "optional": {
                "size": ("STRING", {
                    "default": "2048*2048",
                    "tooltip": "Output image dimensions (1024-4096 pixels per dimension). Format: width*height"
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
    RETURN_NAMES = ("output_image",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, prompt, size="2048*2048", enable_base64_output=False, enable_sync_mode=True, seed=-1):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Build payload
        payload = {
            "prompt": prompt,
            "size": size,
            "enable_base64_output": enable_base64_output,
            "enable_sync_mode": enable_sync_mode
        }

        # Add seed if specified (not -1)
        if seed != -1:
            payload["seed"] = seed

        # API endpoint
        endpoint = "/api/v3/bytedance/seedream-v4"

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
                print(f"ByteDance SeeDream V4 task submitted. Request ID: {task_id}")

                try:
                    result = real_client.wait_for_task(task_id, polling_interval=2, timeout=300)

                    if "outputs" in result and result["outputs"]:
                        image_urls = result["outputs"]
                        return (imageurl2tensor(image_urls),)
                    else:
                        raise Exception("Task completed but no output received")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in ByteDance SeeDream V4: {str(e)}")
            raise e


# Node registration
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI ByteDance SeeDream V4": ByteDanceSeeDreamV4
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI ByteDance SeeDream V4": "WaveSpeedAI ByteDance SeeDream V4"
}