import os
from typing import List
from shutil import rmtree
from pathlib import Path
import threading
import re
from PIL import Image
from io import BytesIO

import tantivy
from tqdm import tqdm
import numpy as np
import pandas as pd

from google_images_search import GoogleImagesSearch

def get_first_image(query) -> Image:
    with GoogleImagesSearch(os.environ["GCS_DEVELOPER_KEY"], os.environ["GCS_CX"]) as gis:
        gis.search(search_params=dict(q=query, num=1))
        img = Image.open(BytesIO(list(gis.results())[0].get_raw_data()))
        height = 500
        img = img.resize((round(img.size[0] / img.size[1] * height), height), Image.ANTIALIAS)
    return img

####################################################################################################

rules = [
    "^\| Not Rated",
    "^\| NR",
    "^\| R",
    "^\| PG-13",
    "^\| PG",
    "^\| TV-MA",
    "^\| TV-14",
    "^\| NC-17",
    "^\| Unrated",
    "^\| G",
    "^\| TV-PG",
    "^\| M",
    "^\| Approved",
    "^\| TV-G",
    "^\| Passed",
    "^\| X",
    "^\| Open",
    "^\| AO",
    "^\| TV-Y7-FV",
    "^\| TV-Y7",
]

def remove_rating(s: str):
    for rule in rules:
        s = re.sub(rule, "", s).strip()
    return s

def try_integer(x):
    try:
        return int(x)
    except:
        return -1

####################################################################################################

class SearchDB:
    def __init__(self, df: pd.DataFrame, index_path: Path):
        self.df = df
        self.index_path = Path(index_path)
        self.create_index()

    def create_index(self):
        schema_builder = tantivy.SchemaBuilder()
        for key in self.df.keys():
            schema_builder.add_text_field(key, stored=True)
        schema_builder.add_integer_field("index", stored=True)
        self.schema = schema_builder.build()
        if self.index_path.exists() and not self.index_path.is_dir():
            rmtree(str(self.index_path.absolute()))
        if not self.index_path.exists():
            self.index_path.mkdir(parents=True, exist_ok=True)
        self.index = tantivy.Index(self.schema, str(self.index_path))

    def build_index(self, rebuild: bool = False):
        if not self.index_path.is_dir() or (rebuild and self.index_path.exists() and len(os.listdir(self.index_path)) > 1):
            rmtree(str(self.index_path.absolute()), ignore_errors=True)
            self.create_index()

        self.index_path.mkdir(parents=True, exist_ok=True)
        if len(os.listdir(self.index_path)) > 3:
            return
        writer = self.index.writer()
        for i, row in tqdm(self.df.iterrows(), total=self.df.shape[0]):
            writer.add_document(
                tantivy.Document(**dict({k: v for (k, v) in row.items()}, index=i))
            )
        writer.commit()
        self.index.reload()

    def search(self, query: str, fields: List[str], num_hits: int = 20):
        searcher = self.index.searcher()
        query = self.index.parse_query(query, fields)
        hits = searcher.search(query, num_hits).hits
        idxs = [searcher.doc(hit[1])["index"][0] for hit in hits]
        return self.df.iloc[idxs]