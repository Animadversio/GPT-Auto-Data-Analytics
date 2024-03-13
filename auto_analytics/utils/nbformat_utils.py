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


def save_cells_to_nb(cells, nbpath, save_pdf=False, save_html=False):
    # Create a new notebook
    nb = new_notebook()
    for cell in cells:
        nb.cells.append(cell)
    # Write the notebook to a file
    with open(nbpath, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print(f"Notebook saved to {nbpath}")
    if save_html:
        try:
            convert_notebook_to_html(nb, nbpath.replace('.ipynb', '.html'))
        except Exception as e:
            print("Failed to convert to html")
            print(e)
    if save_pdf:
        try:
            convert_notebook_to_pdf(nb, nbpath.replace('.ipynb', '.pdf'))
        except Exception as e:
            print("Failed to convert to pdf")
            print(e)
    return nb

from nbconvert import HTMLExporter, PDFExporter
import nbformat

def convert_notebook_to_html(notebook_path, output_path=None):
    """
    Converts a Jupyter Notebook to an HTML file.

    Parameters:
    - notebook_path: Path to the input Jupyter Notebook (.ipynb).
    - output_path: Path for the output HTML file.
    """
    # Load the notebook
    if type(notebook_path) == str:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    elif type(notebook_path) == nbformat.notebooknode.NotebookNode:
        nb = notebook_path
    else:
        raise ValueError("notebook_path must be a string or a NotebookNode")
    
    # Initialize the HTML Exporter and convert
    html_exporter = HTMLExporter()
    html_body, _ = html_exporter.from_notebook_node(nb)
    if output_path is None and type(notebook_path) == str:
        output_path = notebook_path.replace('.ipynb', '.html')
    # Write the HTML output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_body)

    print(f"HTML report saved to {output_path}")


def convert_notebook_to_pdf(notebook_path, output_path=None):
    """
    Converts a Jupyter Notebook to a PDF file.

    Parameters:
    - notebook_path: Path to the input Jupyter Notebook (.ipynb).
    - output_path: Path for the output PDF file.
    """
    # Load the notebook
    if type(notebook_path) == str:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    elif type(notebook_path) == nbformat.notebooknode.NotebookNode:
        nb = notebook_path
    else:
        raise ValueError("notebook_path must be a string or a NotebookNode")
    # Initialize the PDF Exporter and convert
    pdf_exporter = PDFExporter()
    # pdf_exporter.template_file = 'article'
    pdf_body, _ = pdf_exporter.from_notebook_node(nb)
    if output_path is None and type(notebook_path) == str:
        output_path = notebook_path.replace('.ipynb', '.pdf')
    # Write the PDF output
    with open(output_path, 'wb') as f:
        f.write(pdf_body)

    print(f"PDF report saved to {output_path}")

