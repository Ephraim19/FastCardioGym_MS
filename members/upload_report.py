import firebase_admin
from firebase_admin import credentials, storage
import os 
from decouple import config
def initialize_firebase(credentials_path):
    try:
        # Check if Firebase app is already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': "care-call-2b79d.appspot.com"  
            })
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        raise


def upload_to_firebase_storage(local_file_path, file_prefix='FD_reports/'):
 
    try:
        # Get a reference to the storage service
        bucket = storage.bucket()
        
        # Generate a unique filename to prevent overwriting
        unique_filename = f"{file_prefix}_{os.path.basename(local_file_path)}"
        
        # Create a new blob and upload the file's content
        blob = bucket.blob(unique_filename)
        blob.upload_from_filename(local_file_path)
        
        # Optional: Make the file publicly accessible
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        print(f"Firebase storage upload error: {e}")
        return None
    

def uploads(
    filename:str,
    firebase_credentials_path = 'credentials.json',
):

    try:        
        # Initialize return object
        report_info = {
            'local_path': filename,
            'firebase_url': None
        }
        # Upload to Firebase if credentials are provided
        if firebase_credentials_path:
            # Initialize Firebase Admin SDK
            initialize_firebase(firebase_credentials_path)
            
            # Upload file and get download URL
            firebase_url = upload_to_firebase_storage(filename)
            
            if firebase_url:
                report_info['firebase_url'] = firebase_url
                # print(f"Report uploaded to Firebase. Download URL: {firebase_url}")
        
        return report_info
    
    except Exception as e:
        print(f"Error in creating and uploading report: {e}")
        return {'firebase_url': None}