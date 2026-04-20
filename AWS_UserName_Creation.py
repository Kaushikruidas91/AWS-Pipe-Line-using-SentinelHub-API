### User Name creation in ASW IAM
import boto3

def create_user(username):
    iam = boto3.client('iam')
    response = iam.create_user(UserName=username)
    print(response)
    
create_user('testuser')

### Update User Name in IAM ######

def update_user(old_user, new_user):
    iam  = boto3.client('iam')
    responce = iam.update_user(
        UserName=old_user,
        NewUserName=new_user
        )
    
    print(responce)
    
update_user('testuser', 'testupdateuser')


#### create s3 bucket using python #######

bucket = boto3.resource('s3')

response = bucket.create_bucket(
    Bucket = 'Bappa',
    ACL = 'private',
    
    CreateBucketConfiguration= {
        'LocationConstrait': 'ap-south-1'}
)

print(response)