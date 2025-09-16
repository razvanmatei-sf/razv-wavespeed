import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient


class BytedanceSeedreamV4Edit:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Description of the image editing you want to apply"
                }),
                "image_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of input image (connect from Upload Image node)",
                    "forceInput": True
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results. -1 for random seed"
                }),
                "size": (["2227*3183", "1024*1024", "1536*1536", "2048*2048"], {
                    "default": "2227*3183",
                    "tooltip": "Output image size"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Wait for generation to complete before returning"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, prompt, image_url, seed, size, enable_sync_mode):
        real_client = WaveSpeedClient(api_key=client["api_key"])
        
        payload = {
            "enable_base64_output": False,
            "enable_sync_mode": enable_sync_mode,
            "images": [image_url],
            "prompt": prompt,
            "size": size
        }
        
        if seed != -1:
            payload["seed"] = seed

        endpoint = "/api/v3/bytedance/seedream-v4/edit"
        
        try:
            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)
            
            if enable_sync_mode:
                if "outputs" in response and response["outputs"]:
                    image_urls = response["outputs"]
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception(f"No output received from sync API. Response: {response}")
            else:
                task_id = response["id"]
                print(f"Task submitted successfully. Request ID: {task_id}")
                
                try:
                    result = real_client.wait_for_task(task_id, polling_interval=1, timeout=300)
                    
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
    "WaveSpeedAI Bytedance Seedream V4 Edit": BytedanceSeedreamV4Edit
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI Bytedance Seedream V4 Edit": "WaveSpeedAI Bytedance Seedream V4 Edit"
}