import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class ByteDanceSeedDreamV4:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True, 
                    "default": "American retro style: a girl wearing a polka-dot dress with sunglasses adorning her head.",
                    "tooltip": "Text description of the image to generate"
                }),
                "width": ("INT", {
                    "default": 2048,
                    "min": 512,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Width of the generated image"
                }),
                "height": ("INT", {
                    "default": 2048,
                    "min": 512,
                    "max": 4096,
                    "step": 8,
                    "tooltip": "Height of the generated image"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
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
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"
    
    def execute(self, client, prompt, width, height, enable_sync_mode, seed=-1):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])
        
        # Build payload
        payload = {
            "prompt": prompt,
            "size": f"{width}*{height}",
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": False,
        }
        
        # Add seed if not random
        if seed != -1:
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
    "WaveSpeedAI ByteDance SeedDream V4": ByteDanceSeedDreamV4
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI ByteDance SeedDream V4": "WaveSpeedAI ByteDance SeedDream V4"
}