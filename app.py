import base64
import os
import uuid

from flask import Flask, abort, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import LargeBinary

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://postit:postit@mysql:3306/postit",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    images = db.relationship(
        "Image",
        backref="post",
        cascade="all, delete-orphan",
        order_by="Image.position",
    )


class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.String(36), primary_key=True)
    post_id = db.Column(db.String(36), db.ForeignKey("posts.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    data_base64 = db.Column(db.Text(length=4_294_967_295), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/post", methods=["POST"])
def create_post():
    uploads = request.files.getlist("images")

    valid = []
    for upload in uploads:
        if not upload or not upload.filename:
            continue

        mime_type = upload.mimetype or "application/octet-stream"
        if not mime_type.startswith("image/"):
            continue

        raw = upload.read()
        if not raw:
            continue

        valid.append((upload.filename, mime_type, raw))

    if not valid:
        return render_template(
            "index.html",
            error="Please select or paste at least one image.",
        ), 400

    post = Post(id=str(uuid.uuid4()))
    db.session.add(post)

    for position, (filename, mime_type, raw) in enumerate(valid):
        encoded = base64.b64encode(raw).decode("ascii")
        db.session.add(
            Image(
                id=str(uuid.uuid4()),
                post_id=post.id,
                filename=filename,
                mime_type=mime_type,
                data_base64=encoded,
                position=position,
            )
        )

    db.session.commit()
    return redirect(url_for("view_post", post_id=post.id))


@app.route("/posts/<post_id>", methods=["GET"])
def view_post(post_id):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    return render_template("post.html", post=post)


@app.route("/posts/<post_id>/images/<image_id>", methods=["GET"])
def serve_image(post_id, image_id):
    image = db.session.get(Image, image_id)
    if image is None or image.post_id != post_id:
        abort(404)

    try:
        raw = base64.b64decode(image.data_base64)
    except Exception:
        abort(500)

    return raw, 200, {
        "Content-Type": image.mime_type,
        "Content-Length": str(len(raw)),
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    }


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
