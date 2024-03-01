from flask import Flask, render_template, request


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        dropdown_value = request.form['dropdown']
        search_text = request.form['search_text']
        # Perform search or any other action here
        print(f"Dropdown Value: {dropdown_value}, Search Text: {search_text}")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)