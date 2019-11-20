from image_to_s3_api import app
# from config import app_config

app.run(host='0.0.0.0', port=80, debug=True)