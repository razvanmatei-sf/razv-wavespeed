import time
from .wavespeed_api.client import WaveSpeedClient

class WaveSpeedAIWAN25I2V:
    """
    WaveSpeed AI WAN 2.5 Image-to-Video Node

    Advanced image-to-video generation model with enhanced capabilities.
    Creates high-quality videos from still images with improved motion modeling,
    temporal consistency, and support for prompt expansion features.
    Optional audio-driven generation for lip-sync and audio-visual alignment.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "client": ("WAVESPEED_AI_API_CLIENT",),
                "image_url": ("STRING", {
                    "default": "",
                    "tooltip": "URL of input image for video generation (connect from Upload Image node)",
                    "forceInput": True
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Text prompt describing the desired motion and content"
                }),
                "resolution": (["720p", "1080p"], {
                    "default": "720p",
                    "tooltip": "Output video resolution (720p or 1080p)"
                }),
                "duration": ([5, 10], {
                    "default": 5,
                    "tooltip": "Duration of the generated video in seconds (5 or 10)"
                }),
                "enable_sync_mode": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Wait for generation to complete before returning"
                }),
            },
            "optional": {
                "audio_url": ("STRING", {
                    "default": "",
                    "tooltip": "Optional audio URL for audio-driven video generation (connect from Upload Audio node)",
                    "forceInput": True
                }),
                "enable_prompt_expansion": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Enable automatic prompt expansion for enhanced details"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "control_after_generate": True,
                    "tooltip": "Random seed for reproducible results. -1 for random seed"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_url",)
    CATEGORY = "WaveSpeedAI"
    FUNCTION = "execute"

    def execute(self, client, image_url, prompt, resolution, duration, enable_sync_mode,
                audio_url="", enable_prompt_expansion=False, seed=-1):
        # Create the actual client object from the client dict
        real_client = WaveSpeedClient(api_key=client["api_key"])

        # Build payload
        payload = {
            "image": image_url,
            "prompt": prompt,
            "resolution": resolution,
            "duration": duration,
            "enable_prompt_expansion": enable_prompt_expansion,
            "seed": seed
        }

        # Add optional audio if provided
        if audio_url and audio_url.strip():
            payload["audio"] = audio_url.strip()
            print(f"Audio-driven mode enabled with audio URL: {audio_url[:50]}...")

        # API endpoint
        endpoint = "/api/v3/wavespeed-ai/wan-2.5/i2v"

        try:
            print(f"Submitting WAN 2.5 I2V task...")
            print(f"Resolution: {resolution}")
            print(f"Duration: {duration} seconds")
            print(f"Prompt expansion: {enable_prompt_expansion}")
            print(f"Seed: {seed}")
            if prompt:
                print(f"Prompt: {prompt[:100]}...")

            response = real_client.post(endpoint, payload, timeout=real_client.once_timeout)

            if enable_sync_mode:
                # In sync mode, wait for the result
                if "outputs" in response and response["outputs"]:
                    video_urls = response["outputs"]  # Already a list
                    print(f"Task completed successfully. Received {len(video_urls)} video(s)")
                    # Return the first video URL
                    video_url = video_urls[0]
                    return (video_url,)
                else:
                    raise Exception(f"No output received from sync API. Response: {response}")
            else:
                # In async mode, submit task and poll for results
                task_id = response["id"]
                print(f"Task submitted successfully. Request ID: {task_id}")

                try:
                    # Poll for task completion - longer timeout for video generation
                    result = real_client.wait_for_task(task_id, polling_interval=2, timeout=900)

                    if "outputs" in result and result["outputs"]:
                        video_urls = result["outputs"]  # Already a list
                        print(f"Task completed successfully. Received {len(video_urls)} video(s)")
                        # Return the first video URL
                        video_url = video_urls[0]
                        return (video_url,)
                    else:
                        raise Exception(f"Task completed but no output received. Response: {result}")

                except Exception as e:
                    raise Exception(f"Async task failed: {str(e)}")

        except Exception as e:
            print(f"Error in WAN 2.5 I2V: {str(e)}")
            raise e

# Node registration - REQUIRED
NODE_CLASS_MAPPINGS = {
    "WaveSpeedAI WAN 2.5 I2V": WaveSpeedAIWAN25I2V
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WaveSpeedAI WAN 2.5 I2V": "WaveSpeedAI WAN 2.5 I2V"
}