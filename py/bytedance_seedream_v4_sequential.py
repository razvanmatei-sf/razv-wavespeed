import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class ByteDanceSeedDreamV4Sequential:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Generate a set of 4 consecutive illustrations, capturing a high-octane giant robot battle in a classic mecha anime style, from two massive mechs charging at each other in a ruined cityscape, to a dynamic clash of energy swords creating a shower of sparks, a close-up on a pilot's determined face inside the cockpit, and the final explosive shot of the victorious mech standing over its defeated foe.",
                    "tooltip": "Text description specifying the number and content of sequential images to generate. Must clearly specify the number of images in the prompt."
                }),
                "max_images": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 15,
                    "tooltip": "Maximum number of images to generate. Must align with number specified in prompt."
                }),
                "size": (["1024*1024", "1024*2048", "2048*1024", "2048*2048"], {
                    "default": "2048*2048",
                    "tooltip": "Size of the generated images"
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

    def execute(self, client, prompt, max_images, size, enable_sync_mode, seed=-1, enable_base64_output=False):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Build payload
        payload = {
            "prompt": prompt,
            "max_images": max_images,
            "size": size,
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": enable_base64_output,
        }

        # Add seed if not random
        if seed != -1:
            payload["seed"] = seed

        # API endpoint for sequential generation
        endpoint = "/api/v3/bytedance/seedream-v4/sequential"

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
                    # Wait for task to complete
                    result = real_client.wait_for_task(task_id, polling_interval=0.5, timeout=600)

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
    "WaveSpeedAI ByteDance Seedream V4 Sequential": ByteDanceSeedDreamV4Sequential
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI ByteDance Seedream V4 Sequential": "WaveSpeedAI ByteDance Seedream V4 Sequential"
}