import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class ByteDanceSeedDreamV4:
    # Recommended resolution presets for ByteDance Seedream V4
    RECOMMENDED_PRESETS_SEEDREAM_4 = [
        ("2048x2048 (1:1)", 2048, 2048),
        ("2304x1728 (4:3)", 2304, 1728),
        ("1728x2304 (3:4)", 1728, 2304),
        ("2560x1440 (16:9)", 2560, 1440),
        ("1440x2560 (9:16)", 1440, 2560),
        ("2496x1664 (3:2)", 2496, 1664),
        ("1664x2496 (2:3)", 1664, 2496),
        ("3024x1296 (21:9)", 3024, 1296),
        ("4096x4096 (1:1)", 4096, 4096),
        ("Custom", None, None),
    ]

    SIZE_PRESETS = [preset[0] for preset in RECOMMENDED_PRESETS_SEEDREAM_4]

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text description of the image to generate"
                }),
                "size_preset": (s.SIZE_PRESETS, {
                    "default": "2048x2048 (1:1)",
                    "tooltip": "Resolution preset for the generated image"
                }),
                "width": ("INT", {
                    "default": 2048,
                    "min": 512,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Width of the generated image (used when Custom is selected)"
                }),
                "height": ("INT", {
                    "default": 2048,
                    "min": 512,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Height of the generated image (used when Custom is selected)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Wait for generation to complete before returning"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"
    
    def execute(self, client, prompt, size_preset, width, height, seed, enable_sync_mode):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Determine final size based on preset selection
        if size_preset == "Custom":
            final_size = f"{width}*{height}"
        else:
            # Find the preset dimensions
            preset_data = next((preset for preset in self.RECOMMENDED_PRESETS_SEEDREAM_4 if preset[0] == size_preset), None)
            if preset_data:
                final_size = f"{preset_data[1]}*{preset_data[2]}"
            else:
                final_size = f"{width}*{height}"  # Fallback to custom values

        # Build payload
        payload = {
            "prompt": prompt,
            "size": final_size,
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": False,
        }

        # Add seed if not 0 (0 means random for this API)
        if seed != 0:
            payload["seed"] = seed
        
        # API endpoint
        endpoint = "/api/v3/bytedance/seedream-v4"
        
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
                    result = real_client.wait_for_task(task_id, polling_interval=0.5, timeout=300)
                    
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
    "WaveSpeedAI ByteDance Seedream V4": ByteDanceSeedDreamV4
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI ByteDance Seedream V4": "WaveSpeedAI ByteDance Seedream V4"
}