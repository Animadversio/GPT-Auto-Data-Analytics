from openai import OpenAI
import time
from auto_analytics.utils.format_utils import Markdown, display
from auto_analytics.utils.vision_utils import encode_image
client = OpenAI()

def vision_qa_response(prompt, base64_image, 
                       img_fmt='image/png', max_tokens=1024,
                       model_name="gpt-4-vision-preview", display_output=True):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": prompt, 
                },
                {
                "type": "image_url",
                "image_url": {
                    # "url": f"data:image/jpeg;base64,{base64_image}"
                    "url": f"data:{img_fmt};base64,{base64_image}"
                }
                }
            ]
            }
        ],
        max_tokens=max_tokens,
    )
    # print(response.choices[0])
    # print(response.choices[0].message.content)
    if display_output:
        display(Markdown(response.choices[0].message.content))
    return response.choices[0].message

