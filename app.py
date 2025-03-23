from flask import Flask, request, render_template, redirect, url_for
import os
import numpy as np
from csv_io.read_csv import read_csv
from classification.classify_shape import classify_shape
from regularization.regularize_contour import regularize_contour
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Configure upload folder and allowed file extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        paths_XYs = read_csv(filename)
        original_img, regularized_img = plot_and_save(paths_XYs)
        return render_template('plot.html', original_img=original_img, regularized_img=regularized_img)
    return redirect(request.url)

def plot_and_save(paths_XYs):
    """
    Plot the shapes and save the plots to images in memory.
    """
    # Create plots
    def create_plot(title, paths_XYs, regularize=False):
        fig, ax = plt.subplots(tight_layout=True, figsize=(16, 8))
        colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k']  # Define colors
        if regularize:
            for i, XYs in enumerate(paths_XYs):
                c = colours[i % len(colours)]  # Choose color based on index
                for XY in XYs:
                    contour = np.array(XY, dtype=np.int32).reshape((-1, 1, 2))
                    regularized_contour = regularize_contour(contour)
                    shape_type = classify_shape(regularized_contour)
                    
                    if shape_type == "Straight Line":
                        # Directly plot the line using the start and end points
                        x0, y0 = XY[0]
                        x1, y1 = XY[-1]
                        ax.plot([x0, x1], [y0, y1], c=c, linewidth=2)
                    elif shape_type == 'Unknown Shape' or shape_type == 'Not a Triangle':
                        ax.plot(XY[:, 0], XY[:, 1], c=c, linewidth=2)
                    else:
                        # Plot the regularized contour for other shapes
                        contour_points = regularized_contour.reshape(-1, 2)
                        if shape_type == "Straight Line":
                            x0, y0 = XY[0]
                            x1, y1 = XY[-1]
                            ax.plot([x0, x1], [y0, y1], c=c, linewidth=2)
                        else:
                            # Ensure the contour is closed
                            if not np.array_equal(contour_points[0], contour_points[-1]):
                                contour_points = np.vstack([contour_points, contour_points[0]])
                            ax.plot(contour_points[:, 0], contour_points[:, 1], c=c, linewidth=2)
        else:
            for i, XYs in enumerate(paths_XYs):
                c = colours[i % len(colours)]
                for XY in XYs:
                    ax.plot(XY[:, 0], XY[:, 1], c=c, linewidth=2)
            
        ax.invert_yaxis()  # Flip the y-axis
        ax.set_aspect('equal')  # Ensure aspect ratio is equal
        ax.set_title(title)
        ax.legend()

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        img_data = base64.b64encode(img.read()).decode('utf-8')
        plt.close(fig)
        return img_data

    # Generate and return both images
    original_img = create_plot('', paths_XYs, regularize=False)
    regularized_img = create_plot('', paths_XYs, regularize=True)
    
    return original_img, regularized_img

if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
