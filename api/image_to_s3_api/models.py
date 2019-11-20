from image_to_s3_api import db, ma

class Image(db.Model):
    """Create table and schema"""
    __tablename__ = 'downloads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(200))
    s3_path = db.Column(db.String(200))
    timestamp = db.Column(db.String(220))

    def __init__(self, name, url, s3_path, timestamp):
        self.name = name
        self.url = url
        self.s3_path = s3_path
        self.timestamp = timestamp


# Image Schema
class ImageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'url', 's3_path', 'timestamp')