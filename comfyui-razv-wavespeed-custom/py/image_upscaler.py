import time
from .wavespeed_api.utils import imageurl2tensor
from .wavespeed_api.client import WaveSpeedClient

class ImageUpscalerNode:
    """
    WaveSpeed AI Image Upscaler Node
    
    The AI image upscaler is a powerful tool designed to enhance the resolution and quality of images. 
    Our model allows users to choose different levels of enhancement by adjusting the value of creativity.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "image_url": ("STRING", {
                    "default": "",
                    "tooltip": "The URL of the image to upscale",
                    "forceInput": True
                }),
                "target_resolution": (["2k", "4k", "8k"], {
                    "default": "4k",
                    "tooltip": "The target resolution for upscaling"
                }),
                "creativity": ("FLOAT", {
                    "default": 0.0,
                    "min": -2.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider",
                    "tooltip": "Controls how strongly the upscaler will try to improve the image quality (-2 to 2)"
                }),
                "output_format": (["jpeg", "png", "webp"], {
                    "default": "jpeg",
                    "tooltip": "The format of the output image"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Wait for image generation to complete before returning"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("upscaled_image",)
    
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"
    
    def execute(self, client, image_url, target_resolution="4k", creativity=0.0, 
                output_format="jpeg", enable_sync_mode=True):
        """
        Execute the Image Upscaler model
        
        Args:
            client: WaveSpeed API client
            image_url: URL of the image to upscale
            target_resolution: Target resolution (2k, 4k, or 8k)
            creativity: Enhancement level (-2 to 2)
            output_format: Output format (jpeg, png, or webp)
            enable_sync_mode: Whether to wait for completion
        
        Returns:
            Upscaled image tensor
        """
        
        # Validate creativity range
        if creativity < -2.0 or creativity > 2.0:
            raise ValueError(f"Creativity must be between -2 and 2, got {creativity}")
        
        # Prepare the request payload
        payload = {
            "image": image_url,
            "target_resolution": target_resolution,
            "creativity": creativity,
            "output_format": output_format,
            "enable_sync_mode": enable_sync_mode,
            "enable_base64_output": False
        }
        
        # API endpoint for Image Upscaler
        endpoint = "/api/v3/wavespeed-ai/image-upscaler"
        
        try:
            # Create the actual client object from the client dict
            real_client = WaveSpeedClient(api_key=client["api_key"])
            
            # Make the API request
            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)
            
            # Handle sync mode response
            if enable_sync_mode:
                # Check if we have outputs
                if "outputs" in response and response["outputs"]:
                    # Get all output URLs
                    image_urls = response["outputs"]
                    # Pass the full URLs array like original nodes do
                    return (imageurl2tensor(image_urls),)
                else:
                    raise Exception("No output received from API")
            
            # Handle async mode response
            else:
                # Poll for completion
                task_id = response.get("id")
                if not task_id:
                    raise Exception("No task ID received from API")
                
                # Poll endpoint
                poll_endpoint = f"/api/v3/tasks/{task_id}"
                max_attempts = 60  # Max 30 minutes with 30 second intervals
                
                for attempt in range(max_attempts):
                    time.sleep(30)  # Wait 30 seconds between polls
                    
                    poll_response = real_client.get(poll_endpoint)
                    status = poll_response.get("status")
                    
                    if status == "completed":
                        if "outputs" in poll_response and poll_response["outputs"]:
                            image_urls = poll_response["outputs"]
                            return (imageurl2tensor(image_urls),)
                        else:
                            raise Exception("Task completed but no output received")
                    
                    elif status == "failed":
                        error_msg = poll_response.get("error", "Task failed without error message")
                        raise Exception(f"Task failed: {error_msg}")
                
                raise Exception("Task timed out after 30 minutes")
        
        except Exception as e:
            print(f"Error in Image Upscaler: {str(e)}")
            raise e


# Node registration
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI Image Upscaler": ImageUpscalerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI Image Upscaler": "WaveSpeedAI Image Upscaler"
}