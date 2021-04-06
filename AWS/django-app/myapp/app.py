#!flask/bin/python
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from env import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_REGION, PHOTOGALLERY_S3_BUCKET_NAME, DYNAMODB_TABLE
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask import render_template, redirect
import time
import exifread
import json
import uuid
import boto3  
from boto3.dynamodb.conditions import Key, Attr
import pymysql.cursors
from datetime import datetime
import pytz

"""
    INSERT NEW LIBRARIES HERE (IF NEEDED)
"""
import uuid
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from botocore.exceptions import ClientError
from flask import session


"""
"""

app = Flask(__name__, static_url_path="")
app.secret_key = uuid.uuid4().hex

dynamodb = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION)

table = dynamodb.Table(DYNAMODB_TABLE)

UPLOAD_FOLDER = os.path.join(app.root_path,'static','media')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getExifData(path_name):
    f = open(path_name, 'rb')
    tags = exifread.process_file(f)
    ExifData={}
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            key="%s"%(tag)
            val="%s"%(tags[tag])
            ExifData[key]=val
    return ExifData

def s3uploading(filename, filenameWithPath, uploadType="photos"):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                       
    bucket = PHOTOGALLERY_S3_BUCKET_NAME
    path_filename = uploadType + "/" + filename

    s3.upload_file(filenameWithPath, bucket, path_filename)  
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=path_filename)
    return f'''http://{PHOTOGALLERY_S3_BUCKET_NAME}.s3.amazonaws.com/{path_filename}'''


"""
    INSERT YOUR NEW FUNCTION HERE (IF NEEDED)
"""

def check_login_session():
    if 'email' in session:
        try:
            serializer = URLSafeTimedSerializer('some_secret_key')
            decode = serializer.loads(
                session['email'],
                salt = 'some-secret-salt-for-confirmation',
                max_age = 300
            )
            return True
        except Exception as e:
            session.pop('email', None)
            print('Token Expired')
            return False
    else:
        return False


"""
"""

"""
    INSERT YOUR NEW ROUTE HERE (IF NEEDED)
"""

users_table = dynamodb.Table('PhotoGalleryUser')
@app.route('/signup', methods=['GET','POST'])
def signup():
    """ signup
    get:
        description: Endpoint to return signup form
        responses: Returns signup form

    post:
        description: Endpoint to send signup form
        responses: Returns users to login page
    """
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password1 = request.form['password1']
        existing_emails = users_table.scan(FilterExpression=Attr('email').eq(email))
        matching_emails = existing_emails['Items']
        if (len(matching_emails) == 0) and (password == password1):
            userID = uuid.uuid4()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users_table.put_item(
                Item={
                    "userID": str(userID),
                    "username": username,
                    "name": name,
                    "email": email,
                    "password": hashed_password,
                    "verified": "no"
                }
            )
            serializer = URLSafeTimedSerializer('some_secret_key')
            token = serializer.dumps(email, salt='some-secret-salt-for-confirmation')
            ses = boto3.client('ses', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            SENDER = 'vwang314@gatech.edu'
            RECEIVER = email
            try:
                #Provide the contents of the email.
                response = ses.send_email(
                    Destination={
                        'ToAddresses': [RECEIVER],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Data': 'Confirm your email at http://ec2-3-80-50-95.compute-1.amazonaws.com:5000/confirm/' + str(token),
                            },
                        },
                        'Subject': {
                            'Data': 'Photo Gallery Email Confirmation'
                        },
                    },
                    Source=SENDER
                )
            # Display an error if something goes wrong.
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                print("Email sent! Message ID:"),
                print(response['MessageId']),
                print(token),
            return render_template('confirmemail.html')
        return redirect('/login')
    else:
        return render_template('signup.html')

@app.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    """ confirm email
    post:
        description: Endpoint to confirm user email
        responses: Returns user to home page signed in
    """
    try:
        serializer = URLSafeTimedSerializer('some_secret_key')
        email = serializer.loads(
            str(token),
            salt = 'some-secret-salt-for-confirmation',
            max_age = 600
        )
        users_table.update_item(
            Key={
                'email': email
            },
            UpdateExpression = "set verified=:v",
            ExpressionAttributeValues={ 
                ':v': "yes" 
            }
        )
        return redirect('/login')
    except Exception as e:
        print('expired token')
        return redirect('/signup')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """ login
    get:
        description: Endpoint to return login site
        responses: Returns login site

    post:
        description: Endpoint to send login credentials
        responses: Returns user to home page signed in
    """
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            existing_email = users_table.scan(FilterExpression=Attr('email').eq(email))
            matching_email = existing_email['Items']
            if existing_email is None:
                return redirect('/')
            elif (bcrypt.hashpw(password.encode('utf-8'), matching_email[0]['password'].value) == matching_email[0]['password'].value) and matching_email[0]['verified'] == "yes":
                serializer = URLSafeTimedSerializer('some_secret_key')
                session['email'] = serializer.dumps(matching_email[0]['email'], salt="some-secret-salt-for-confirmation")
            return redirect('/')
        except Exception as e:
            print(e)
            return redirect('/')
    else:
        print('login failed')
        return render_template('login.html')

@app.route('/deleteaccount', methods = ['GET', 'POST'])
def delete_account():
    if check_login_session():
        if request.method == 'POST':
            serializer = URLSafeTimedSerializer('some_secret_key')
            email = serializer.loads(session['email'], salt="some-secret-salt-for-confirmation")
            albums = table.scan(FilterExpression=Attr('photoID').eq('thumbnail'))
            albums = albums['Items']
            for i in range(len(albums)):
                if albums[i]['author'] == email:
                    albumID = albums[i]['albumID']
                    photos = table.scan(FilterExpression=Attr('albumID').eq(albumID))
                    photos = photos['Items']
                    for i in range(len(photos)):
                        table.delete_item(
                            Key={
                                'albumID': albumID,
                                'photoID': photos[i]['photoID']
                            }
                        )
            users_table.delete_item(
                Key={
                    'email': email
                }
            )
            session.pop('email',None)

            return redirect('/')
        else:
            return render_template('deleteaccount.html')
    else:
        return redirect('/login')

@app.route('/album/<albumID>/photo/<photoID>/updatePhotoForm', methods = ['GET','POST'])
def updatePhoto(albumID, photoID):
    if check_login_session():
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            tags = request.form['tags']
            serializer = URLSafeTimedSerializer('some_secret_key')
            email = serializer.loads(session['email'], salt="some-secret-salt-for-confirmation")
            updatedAtlocalTime = datetime.now().astimezone()
            updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)
            table.update_item(
                Key={
                    'albumID': albumID,
                    'photoID': photoID
                },
                UpdateExpression = "set description=:d, tags=:a, title=:t, updatedAt=:u",
                ExpressionAttributeValues={ 
                    ':d': description, 
                    ':a': tags,
                    ':t': title,
                    ':u': updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            return redirect('/')
        else:
            return render_template('updatephoto.html', albumID=albumID, photoID=photoID)
    else:
        return redirect('/login')

"""
"""

@app.errorhandler(400)
def bad_request(error):
    """ 400 page route.

    get:
        description: Endpoint to return a bad request 400 page.
        responses: Returns 400 object.
    """
    return make_response(jsonify({'error': 'Bad request'}), 400)



@app.errorhandler(404)
def not_found(error):
    """ 404 page route.

    get:
        description: Endpoint to return a not found 404 page.
        responses: Returns 404 object.
    """
    return make_response(jsonify({'error': 'Not found'}), 404)



@app.route('/', methods=['GET'])
def home_page():
    """ Home page route.

    get:
        description: Endpoint to return home page.
        responses: Returns all the albums.
    """
    if check_login_session():
        response = table.scan(FilterExpression=Attr('photoID').eq("thumbnail"))
        results = response['Items']

        if len(results) > 0:
            for index, value in enumerate(results):
                createdAt = datetime.strptime(str(results[index]['createdAt']), "%Y-%m-%d %H:%M:%S")
                createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
                results[index]['createdAt'] = createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y")

        return render_template('index.html', albums=results)
    else:
        return redirect('/login')



@app.route('/createAlbum', methods=['GET', 'POST'])
def add_album():
    """ Create new album route.

    get:
        description: Endpoint to return form to create a new album.
        responses: Returns all the fields needed to store new album.

    post:
        description: Endpoint to send new album.
        responses: Returns user to home page.
    """
    if check_login_session():
        if request.method == 'POST':
            uploadedFileURL=''
            file = request.files['imagefile']
            name = request.form['name']
            description = request.form['description']

            if file and allowed_file(file.filename):
                albumID = uuid.uuid4()
                
                filename = file.filename
                filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filenameWithPath)
                
                uploadedFileURL = s3uploading(str(albumID), filenameWithPath, "thumbnails");

                createdAtlocalTime = datetime.now().astimezone()
                createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)

                serializer = URLSafeTimedSerializer('some_secret_key')
                email = serializer.loads(session['email'], salt="some-secret-salt-for-confirmation")

                table.put_item(
                    Item={
                        "albumID": str(albumID),
                        "photoID": "thumbnail",
                        "name": name,
                        "description": description,
                        "thumbnailURL": uploadedFileURL,
                        "author": email,
                        "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                    }
                )

            return redirect('/')
        else:
            return render_template('albumForm.html')
    else:
        return redirect('/login')



@app.route('/album/<string:albumID>', methods=['GET','POST'])
def view_photos(albumID):
    """ Album page route.

    get:
        description: Endpoint to return an album.
        responses: Returns all the photos of a particular album.
    """
    if check_login_session():
        if request.method == 'POST':
            response = table.scan(FilterExpression=Attr('albumID').eq(albumID))
            photos = response['Items']
            for i in range(len(photos)):
                table.delete_item(
                    Key={
                        'albumID': albumID,
                        'photoID': photos[i]['photoID']
                    }
                )
            return redirect('/')
        else:
            albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
            albumMeta = albumResponse['Items']

            response = table.scan(FilterExpression=Attr('albumID').eq(albumID) & Attr('photoID').ne('thumbnail'))
            items = response['Items']

            return render_template('viewphotos.html', photos=items, albumID=albumID, albumName=albumMeta[0]['name'])
    else:
        return redirect('/login')


@app.route('/album/<string:albumID>/addPhoto', methods=['GET', 'POST'])
def add_photo(albumID):
    """ Create new photo under album route.

    get:
        description: Endpoint to return form to create a new photo.
        responses: Returns all the fields needed to store a new photo.

    post:
        description: Endpoint to send new photo.
        responses: Returns user to album page.
    """
    if check_login_session():
        if request.method == 'POST':    
            uploadedFileURL=''
            file = request.files['imagefile']
            title = request.form['title']
            description = request.form['description']
            tags = request.form['tags']

            if file and allowed_file(file.filename):
                photoID = uuid.uuid4()
                filename = file.filename
                filenameWithPath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filenameWithPath)            
                
                uploadedFileURL = s3uploading(filename, filenameWithPath);
                
                ExifData=getExifData(filenameWithPath)
                ExifDataStr = json.dumps(ExifData)

                createdAtlocalTime = datetime.now().astimezone()
                updatedAtlocalTime = datetime.now().astimezone()

                createdAtUTCTime = createdAtlocalTime.astimezone(pytz.utc)
                updatedAtUTCTime = updatedAtlocalTime.astimezone(pytz.utc)

                table.put_item(
                    Item={
                        "albumID": str(albumID),
                        "photoID": str(photoID),
                        "title": title,
                        "description": description,
                        "tags": tags,
                        "photoURL": uploadedFileURL,
                        "EXIF": ExifDataStr,
                        "createdAt": createdAtUTCTime.strftime("%Y-%m-%d %H:%M:%S"),
                        "updatedAt": updatedAtUTCTime.strftime("%Y-%m-%d %H:%M:%S")
                    }
                )

            return redirect(f'''/album/{albumID}''')

        else:

            albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
            albumMeta = albumResponse['Items']

            return render_template('photoForm.html', albumID=albumID, albumName=albumMeta[0]['name'])
    else:
        return redirect('/login')


@app.route('/album/<string:albumID>/photo/<string:photoID>', methods=['GET', 'POST'])
def view_photo(albumID, photoID):
    """ photo page route.

    get:
        description: Endpoint to return a photo.
        responses: Returns a photo from a particular album.
    """ 
    if check_login_session():
        if request.method == 'POST':
            table.delete_item(
                Key={
                    'albumID': albumID,
                    'photoID': photoID
                }
            )
            return redirect('/')
        else: 
            albumResponse = table.query(KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq('thumbnail'))
            albumMeta = albumResponse['Items']

            response = table.query( KeyConditionExpression=Key('albumID').eq(albumID) & Key('photoID').eq(photoID))
            results = response['Items']

            if len(results) > 0:
                photo={}
                photo['photoID'] = results[0]['photoID']
                photo['title'] = results[0]['title']
                photo['description'] = results[0]['description']
                photo['tags'] = results[0]['tags']
                photo['photoURL'] = results[0]['photoURL']
                photo['EXIF']=json.loads(results[0]['EXIF'])

                createdAt = datetime.strptime(str(results[0]['createdAt']), "%Y-%m-%d %H:%M:%S")
                updatedAt = datetime.strptime(str(results[0]['updatedAt']), "%Y-%m-%d %H:%M:%S")

                createdAt_UTC = pytz.timezone("UTC").localize(createdAt)
                updatedAt_UTC = pytz.timezone("UTC").localize(updatedAt)

                photo['createdAt']=createdAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
                photo['updatedAt']=updatedAt_UTC.astimezone(pytz.timezone("US/Eastern")).strftime("%B %d, %Y at %-I:%M:%S %p")
                
                tags=photo['tags'].split(',')
                exifdata=photo['EXIF']
                
                return render_template('photodetail.html', photo=photo, tags=tags, exifdata=exifdata, albumID=albumID, albumName=albumMeta[0]['name'])
            else:
                return render_template('photodetail.html', photo={}, tags=[], exifdata={}, albumID=albumID, albumName="")
    else:
        return redirect('/login')


@app.route('/album/search', methods=['GET'])
def search_album_page():
    """ search album page route.

    get:
        description: Endpoint to return all the matching albums.
        responses: Returns all the albums based on a particular query.
    """ 
    if check_login_session():
        query = request.args.get('query', None)    

        response = table.scan(FilterExpression=Attr('name').contains(query) | Attr('description').contains(query))
        results = response['Items']

        items=[]
        for item in results:
            if item['photoID'] == 'thumbnail':
                album={}
                album['albumID'] = item['albumID']
                album['name'] = item['name']
                album['description'] = item['description']
                album['thumbnailURL'] = item['thumbnailURL']
                items.append(album)

        return render_template('searchAlbum.html', albums=items, searchquery=query)
    else:
        return redirect('/login')



@app.route('/album/<string:albumID>/search', methods=['GET'])
def search_photo_page(albumID):
    """ search photo page route.

    get:
        description: Endpoint to return all the matching photos.
        responses: Returns all the photos from an album based on a particular query.
    """ 
    if check_login_session():
        query = request.args.get('query', None)    

        response = table.scan(FilterExpression=Attr('title').contains(query) | Attr('description').contains(query) | Attr('tags').contains(query) | Attr('EXIF').contains(query))
        results = response['Items']

        items=[]
        for item in results:
            if item['photoID'] != 'thumbnail' and item['albumID'] == albumID:
                photo={}
                photo['photoID'] = item['photoID']
                photo['albumID'] = item['albumID']
                photo['title'] = item['title']
                photo['description'] = item['description']
                photo['photoURL'] = item['photoURL']
                items.append(photo)

        return render_template('searchPhoto.html', photos=items, searchquery=query, albumID=albumID)
    else:
        return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
