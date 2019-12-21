#!/usr/bin/env python
import os
from json import dumps
from flask import Flask, g, Response, request

from neo4j.v1 import GraphDatabase, basic_auth

app = Flask(__name__, static_url_path='/static/')

password = 'b.2Ps3xgbiTaOs.L6qlamTzeNKAC2D9'

driver = GraphDatabase.driver('bolt://hobby-memigaoofoojgbkeoeohefdl.dbs.graphenedb.com:24787',auth=basic_auth("szy11mon", password))

def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()

@app.route("/")
def get_index():
    return app.send_static_file('index.html')

def serialize_anime(anime):
    return {
        'id': anime['id'],
        'title': anime['title'],
        'released': anime['released'],
        'duration': anime['duration'],
        'score': anime['score']
    }

def serialize_cast(cast):
    return {
        'name': cast[0],
        'job': cast[1],
        'role': cast[2]
    }


@app.route("/show")
def get_all():
    db = get_db()
    results = db.run("MATCH (anime:Anime) "
                 "RETURN anime"
    )
    return Response(dumps([serialize_anime(record['anime']) for record in results]),
                    mimetype="application/json")


@app.route("/search")
def get_search():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = get_db()
        results = db.run("MATCH (anime:Anime) "
                 "WHERE anime.title =~ {title} "
                 "RETURN anime", {"title": "(?i).*" + q + ".*"}
        )
        return Response(dumps([serialize_anime(record['anime']) for record in results]),
                        mimetype="application/json")


@app.route("/search_studio")
def get_search_studio():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = get_db()
        results = db.run("MATCH (anime:Anime) "
                 "WHERE anime.released = {released} "
                 "RETURN anime", {"released": int(q)}
        )
        return Response(dumps([serialize_anime(record['anime']) for record in results]),
                        mimetype="application/json")


@app.route("/search_score")
def get_search_score():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = get_db()
        results = db.run("MATCH (anime:Anime) "
                 "WHERE anime.score > {score} "
                 "RETURN anime", {"score": float(q)}
        )
        return Response(dumps([serialize_anime(record['anime']) for record in results]),
                        mimetype="application/json")


@app.route("/anime/<title>")
def get_anime(title):
    db = get_db()
    results = db.run("MATCH (anime:Anime {title:{title}}) "
             "OPTIONAL MATCH (anime)<-[r]-(person:Person) "
             "RETURN anime.title as title,"
             "collect([person.name, "
             "         head(split(lower(type(r)), '_')), r.roles]) as cast "
             "LIMIT 1", {"title": title})

    studio = db.run("MATCH (anime:Anime {title:{title}}) "
             "OPTIONAL MATCH (anime)<-[r]-(studio:Studio) "
             "RETURN anime.title as title,"
             "collect([studio.name]) as creators "
             "LIMIT 1", {"title": title})

    result = results.single();
    studio = studio.single()
    return Response(dumps({"title": result['title'],
    	                   "studio": studio['creators'],
                           "cast": [serialize_cast(member)
                                    for member in result['cast']]}),
                    mimetype="application/json")


if __name__ == '__main__':
    app.run()
