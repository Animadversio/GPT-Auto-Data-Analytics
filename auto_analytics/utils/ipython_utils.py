import base64
from PIL import Image
import numpy as np
from io import BytesIO
import IPython
from IPython.utils.capture import RichOutput
from IPython.core.interactiveshell import InteractiveShell

def richoutput_to_image(output):
    try:
        assert isinstance(output, RichOutput)
        # assert output.data['image/png']
        if "image/png" in output.data:
            image_data = output.data['image/png']
            image_data = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_data))
            return image
        elif "text/html" in output.data:
            html = output.data['text/html']
            return html
        elif "text/plain" in output.data:
            # note mostly text/plain and text/html co exist. not one or the other. 
            text = output.data['text/plain']
            return text
    except AssertionError and KeyError:
        return None
    
    
def ipyshell_code_exec(shell, code, verbose=False):
    with IPython.utils.io.capture_output() as captured:
        # Execute the code
        out = shell.run_cell(code)
    if verbose:
        print("Result of the code execution: ", type(out.result), "\n", out.result)
        print("Standard Output:", captured.stdout)
        print("Standard Error:", captured.stderr)
        print("Captured Outputs:", captured.outputs)
    disp_images = []
    if captured.outputs:
        for display_output in captured.outputs:
            # Process each display output as needed
            disp_images.append(richoutput_to_image(display_output))
    # note stdout returns a string
    # out.result returns real objects like tensors! important!
    return out, captured, disp_images


def ipyshell_get_var(shell, var_name):
    return shell.user_ns[var_name]