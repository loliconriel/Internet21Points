from flask import Flask, request, jsonify,render_template

app = Flask(__name__)

# 資料庫，用於存儲學生信息 (透過list的方式建置，Python重啟時即會將記憶體內儲存的資料移除)
@app.route("/")
def home():
    return render_template('home.html')


if __name__ == "__main__":
    app.run(debug=True)