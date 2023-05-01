import math
import sys
from PIL import Image
from copy import copy
from pathlib import Path
from io import BytesIO
from sqlitedict import SqliteDict
from base64 import b64encode

from flask import Flask, request, jsonify, send_from_directory
import pandas as pd

####################################################################################################

ROOT_DIR = Path(__file__).absolute().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from lib import SearchDB, get_first_image, get_first_image_tmdb

####################################################################################################

app = Flask(__name__)

####################################################################################################

COMB_DB = None
POSTER_DB = None
PLACEHOLDER_IMG = None


def read_database():
    global COMB_DB, POSTER_DB
    if COMB_DB is not None and POSTER_DB is not None:
        return COMB_DB, POSTER_DB
    comb_path = ROOT_DIR / "data" / "combined.csv"
    df_comb = pd.read_csv(comb_path)
    comb_db = SearchDB(df_comb, ROOT_DIR / "data" / "index_comb")
    comb_db.build_index()
    COMB_DB = comb_db
    poster_db_path = ROOT_DIR / "data" / "poster_db.sqlite"
    POSTER_DB = SqliteDict(poster_db_path, autocommit=True, tablename="posters_bytes")
    return COMB_DB, POSTER_DB


def get_img(title, year):
    _, poster_db = read_database()
    key = f"\"{title}\" {year} movie poster"
    if key in poster_db:
        return b64encode(poster_db[key]).decode("utf-8")
    #img = get_first_image(key)
    img = get_first_image_tmdb(title, year)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    poster_db[key] = copy(buf.getvalue())
    return b64encode(buf.getvalue()).decode("utf-8")


def try_to_float(x, default=None):
    try:
        return float(x)
    except:
        return default


def get_placeholder_img():
    global PLACEHOLDER_IMG
    if PLACEHOLDER_IMG is None:
        img = Image.open(ROOT_DIR / "data" / "placeholder.jpg")
        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        PLACEHOLDER_IMG = b64encode(buf.getvalue()).decode("utf-8")
    return copy(PLACEHOLDER_IMG)


####################################################################################################


@app.route("/search")
def search():
    comb_db, _ = read_database()
    query = request.args.get("query")
    assert query is not None
    minYear = try_to_float(request.args.get("minYear"), -math.inf)
    maxYear = try_to_float(request.args.get("maxYear"), math.inf)
    minScore = try_to_float(request.args.get("minScore"), -math.inf)
    maxScore = try_to_float(request.args.get("maxScore"), math.inf)

    df = comb_db.search(query, ["title", "year", "genres", "abstract"], 2000)
    df = df.loc[
        (df["year"] >= minYear)
        & (df["year"] <= maxYear)
        & (df["score"] >= minScore)
        & (df["score"] <= maxScore)
    ]
    df = df.sort_values(by=["score"], ascending=False)
    df = df[:50]
    results = []
    for i, row in df.iterrows():
        results.append(
            {
                "title": row["title"],
                "score": int(row["score"]),
                "year": int(row["year"]),
                "genres": str(row["genres"]),
                "abstract": row["abstract"],
                "img_data": get_placeholder_img(),
            }
        )
    return jsonify(results)


@app.route("/image")
def image():
    title = request.args.get("title", "")
    year = request.args.get("year", "")
    return jsonify(dict(img_data=get_img(title, year)))


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if path == "":
        return send_from_directory(ROOT_DIR, "index.html")
    else:
        return send_from_directory(ROOT_DIR, path)


####################################################################################################

if __name__ == "__main__":
    read_database()
    app.run(host="0.0.0.0", debug=True)
