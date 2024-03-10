import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_output

def create_code_cell_from_captured(code, out, captured):
    """
    Example script of creating a Jupyter notebook from captured outputs
    
    from nbformat.v4 import new_notebook, new_code_cell, new_output
    # Create a new notebook
    nb = new_notebook()
    # Add a code cell with the executed code
    code = "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})\ndf"
    out, captured, disp_images = python_code_exec(code)
    # code_cell = create_code_cell_from_captured(code, out, captured)
    nb.cells.append(create_code_cell_from_captured(code, out, captured))
    code = "print('welcome!');import matplotlib.pyplot as plt\nplt.plot([1,2],[1,2,3,4])\nplt.show()"
    out, captured, disp_images = python_code_exec(code)
    nb.cells.append(create_code_cell_from_captured(code, out, captured))
    code = "print('welcome!');import matplotlib.pyplot as plt\nplt.plot([1,2,3,4])\nplt.show()"
    out, captured, disp_images = python_code_exec(code)
    nb.cells.append(create_code_cell_from_captured(code, out, captured))

    # Write the notebook to a file
    filename = 'notebook_with_plot_all.ipynb'
    with open(filename, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    """
    # Add a code cell with the executed code
    code_cell = new_code_cell(source=code)
    # handle errors
    if not out.success:
        if out.error_before_exec:
            output_stderr = new_output(output_type="stream",
                    name="stderr", text=repr(out.error_before_exec) )
            code_cell.outputs.append(output_stderr)
        if out.error_in_exec:
            output_stderr = new_output(output_type="stream",
                    name="stderr", text=repr(out.error_in_exec) )
            code_cell.outputs.append(output_stderr)
    # handle stdout outputs
    output_stdout = new_output(output_type="stream",
                name="stdout", text=captured.stdout )
    code_cell.outputs.append(output_stdout)
    # handle stderror outputs
    output_stderr = new_output(output_type="stream",
                name="stderr", text=captured.stderr )
    code_cell.outputs.append(output_stderr)
    # Process captured outputs
    for output in captured.outputs:
        if hasattr(output, 'data'):
            # For rich outputs (e.g., plots), `data` attribute holds the MIME-typed representations
            output_cell = new_output(
                output_type='display_data',
                data=output.data,
                metadata=output.metadata
            )
        elif hasattr(output, 'text'):
            # For text outputs, `text` attribute holds the content
            output_cell = new_output(
                output_type='stream',
                name='stdout',  # or 'stderr' for error outputs
                text=output.text
            )
        else:
            continue  # Skip any unsupported output types

        # Append each output cell to the code cell
        code_cell.outputs.append(output_cell)
    return code_cell