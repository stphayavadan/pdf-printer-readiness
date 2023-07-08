from flask import Flask, render_template, request
import PyPDF2
import warnings
import re

app = Flask(__name__)

# define printable area for A4 size paper
printable_area = (0, 0, 595, 842)

# define minimum and maximum margins in points
min_margin = 24
max_margin = 72

# define minimum and maximum font sizes in points
min_font_size = 6
max_font_size = 14

# define minimum and maximum image resolution in dpi
min_resolution = 300
max_resolution = 600

# define bleed size in points
bleed_size = 24


# define function to check for printer readiness issues
def check_printer_readiness(pdf_file):
    # open PDF file and ignore PyPDF2 warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pdf = PyPDF2.PdfReader(pdf_file)

    issues = []

    # check for page orientation issues
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        media_box = page.mediabox
        if media_box.width > media_box.height:
            issues.append(f"Page {i + 1} has landscape orientation.")

    # check for margin issues
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        media_box = page.mediabox
        if (media_box.upper_right[0] - media_box.lower_left[0] > printable_area[2] + max_margin or
                media_box.upper_right[0] - media_box.lower_left[0] < printable_area[2] - min_margin or
                media_box.upper_right[1] - media_box.lower_left[1] > printable_area[3] + max_margin or
                media_box.upper_right[1] - media_box.lower_left[1] < printable_area[3] - min_margin):

            issues.append(f"Page {i + 1} has margin issues. Please adjust margins.")

    # check for font size issues
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        content = page.extract_text()
        font_sizes = re.findall(r"/F\d+ (\d+\.?\d*) Tf", content)
        for font_size in font_sizes:
            font_size = float(font_size)
            if font_size < min_font_size or font_size > max_font_size:
                issues.append(f"Page {i + 1} has font size issues. Please adjust font size.")

    # check for image resolution issues
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        x_objects = page['/Resources']['/XObject'].get_object()
        for obj in x_objects:
            if x_objects[obj]['/Subtype'] == '/Image':
                width = x_objects[obj]['/Width']
                height = x_objects[obj]['/Height']
                dpi = max(width / (media_box.width - bleed_size) * 72,
                          height / (media_box.height - bleed_size) * 72)
                if dpi < min_resolution:
                    issues.append(
                        f"Page {i + 1} has image resolution issues. Please use images with at least {min_resolution} dpi."
                    )

    # check for transparency issues
    for i in range(len(pdf.pages)):
        page = pdf.pages[i]
        x_objects = page['/Resources']['/XObject'].get_object()
        for obj in x_objects:
            if x_objects[obj]['/Subtype'] == '/Transparency':
                issues.append(f"Page {i + 1} has transparency issues. Please remove transparency.")

    return issues


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # check if a file is uploaded
        if "pdf_file" not in request.files:
            return "No file uploaded."

        pdf_file = request.files["pdf_file"]

        # check if a file is selected
        if pdf_file.filename == "":
            return "No file selected."

        # check if the file is a PDF
        if not pdf_file.filename.lower().endswith(".pdf"):
            return "Please upload a PDF file."

        # save the uploaded file
        pdf_path = f"uploads/{pdf_file.filename}"
        pdf_file.save(pdf_path)

        # check printer readiness issues
        issues = check_printer_readiness(pdf_path)

        # render the template with the results
        return render_template("result.html", filename=pdf_file.filename, issues=issues)

    # render the initial upload form
    return render_template("upload.html")


if __name__ == "__main__":
    app.run(debug=True)
