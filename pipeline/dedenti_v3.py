import easyocr
import cv2
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
import glob
import re
from pyspark.ml import PipelineModel
from pyspark.sql.functions import col
import boto3
import os
import shutil
from PIL import Image
from io import BytesIO
import urllib.request


reader = easyocr.Reader(['en'])
#executor메모리 바꿀생각도 하기 캐시 안하면 무리는 안가는듯
spark = SparkSession.builder.appName("dedenti").getOrCreate()

def predict(test):  # test가 받아올 데이터, train가 학습시킬 기존 데이터

  date_pattern = r'(\d{2})\d{2}-\d{1,2}-\d{1,2}'
  test['date'] = test['extract'].str.extract(date_pattern)
  test['year'] = test['date']

  test.loc[test['date'].isnull(), 'year'] = test.loc[test['date'].isnull(), 'extract']

  test['extract']=test['year']
  test=test.drop(['date','year'],axis=1)

  test_data_spark = spark.createDataFrame(test, ['feature'])
  
  saved_model = PipelineModel.load('/home/ubuntu/model_registry')
  prediction = saved_model.transform(test_data_spark)
  preds = prediction.filter(col("prediction") == 1).select("feature", "prediction")
  preds.show()
  #시간 환자번호 이름이 날아올거야
  preds = preds.toPandas()

  return preds

accessKey='AKIAWNF324FTPDEVUV6X'
secretKey='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'
s3=boto3.client('s3', aws_access_key_id=accessKey, aws_secret_access_key=secretKey)
bucket_name = 'beforeprocess'
response =s3.list_objects_v2(Bucket=bucket_name)
prefix='https://beforeprocess.s3.ap-northeast-2.amazonaws.com/'

chk1=0
chk2=0
chk3=0

def img_read(url):
  resp = urllib.request.urlopen(url)
  image = np.asarray(bytearray(resp.read()), dtype='uint8')
  image = cv2.imdecode(image ,cv2.IMREAD_GRAYSCALE)
  return image

for obj in response['Contents']:
  url=prefix+str(obj['Key'])
  img = img_read(url)
  s3.delete_object(Bucket=bucket_name,Key=str(obj['Key']))
  ret, dst = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
  result = reader.readtext(dst)

  #튜플 리스트로 만들어주기
  for i in range(len(result)):
    result[i] = list(result[i])
 
  #이름 따로 나오면 전처리
  if ' ' not in result[1][1]:
    result[1][1] = result[1][1] + ' ' + result[2][1]
    result[1][0][1] = result[2][0][1]
    result[1][0][2] = result[2][0][2] 
    del result[2]
  
  #나이 성별 붙어서 나오면 전처리
  if ' ' in result[2][1]:
    age, gender = result[2][1].split(' ')
    del result[3]
    result.insert(2, [[[4, 64], [42, 64], [42, 94], [4, 94]], age, 0.9999998314126101])
    result.insert(3, [[[48, 66], [72, 66], [72, 90], [48, 90]], gender, 0.9272444468417831])

  result = result[:8]

  extraction = []
  for i in result:
      extraction.append(i[1])

  print(extraction)
  
  extraction[4] = extraction[4].replace('_', '-')
  extraction[5] = extraction[5].replace('_', '-')
  if extraction[3]== 'm':
      extraction[3] = 'M'
  if extraction[4]== 'm':
      extraction[4] = 'M'
  extraction[5] = extraction[5].replace('.', ':')
  extraction[6] = extraction[6].replace('.', ':')

  extract = np.array(extraction)
  df = pd.DataFrame(extract, columns = ['extract'])
  extract = extract.tolist()

 #사진 이미지이름 지정 용 코드 -> 여기 수정
  patient_parts = ['Chest', 'Hand', 'Foot']
  for term in extract:
    if term == 'F':
      s = term
    if term == 'M':
      s = term
    #나이 a변수에 넣기
    if term.isdigit() and term >= '20' and term <= '50':
      a = int(term)
    if term in patient_parts:
      part = term

  prediction = predict(df)
  prediction = prediction.values.tolist()

  for pred in prediction:
    idx = extract.index(pred[0])
    if result[idx][2]<0.4:
      continue
    left_upper = result[idx][0][0]
    right_lower = result[idx][0][2]
    try:
      if extract[idx][1] == ':':
        left_upper[0] = left_upper[0]-15
    except:
      pass
    right_lower[1] = right_lower[1]-5
    try:
      roi = img[left_upper[1]:right_lower[1], left_upper[0]:right_lower[0]]
    except:
      left_upper[1] = int(left_upper[1])
      left_upper[0] = int(left_upper[0])
      right_lower[1] = int(right_lower[1])
      right_lower[0] = int(right_lower[0])
      roi = img[left_upper[1]:right_lower[1], left_upper[0]:right_lower[0]]

    blurred_roi = cv2.blur(roi, (20, 20))
    img[left_upper[1]:right_lower[1], left_upper[0]:right_lower[0]] = blurred_roi

  ##이미지저장##
  cv2.imwrite("{}/{}_{}_{}.jpeg".format(part,part, s, a), img)
  if part=='Chest':
    chk1=1
  elif part =='Hand':
    chk2=1
  elif part =='Foot':
    chk3=1

if chk1==1:
  shutil.make_archive("Chest",'zip',"/home/ubuntu/Chest")
  os.system("scp -i jang.pem Chest.zip ubuntu@ec2-52-79-176-133.ap-northeast-2.compute.amazonaws.com:/home/ubuntu/Chest.zip")
elif chk2==1:
  shutil.make_archive("Hand",'zip',"/home/ubuntu/Hand")
  os.system("scp -i jang.pem Hand.zip ubuntu@ec2-52-79-176-133.ap-northeast-2.compute.amazonaws.com:/home/ubuntu/Hand.zip")
elif chk3==1:
  shutil.make_archive("Foot",'zip',"/home/ubuntu/Foot")
  os.system("scp -i jang.pem Foot.zip ubuntu@ec2-52-79-176-133.ap-northeast-2.compute.amazonaws.com:/home/ubuntu/Foot.zip")
#스파크클러스터 종료  
spark.stop()


