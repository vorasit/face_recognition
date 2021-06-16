from pymysql import NULL
import face_recognition
import cv2
import os
import numpy as np
import sys
import time
import mysql.connector
import datetime
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="db_face"
)
print(mydb)
mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

for x in mycursor:
  print(x)

p=""

d = datetime.datetime.now()
print(d.day)

t = 7   #วันก่อน
a = 0
# เปิดการใช้ webcam
video_capture = cv2.VideoCapture(0)

sql1 = "SELECT img FROM person"
mycursor.execute(sql1)
myresult1 = mycursor.fetchall()
person1_image = []
person1_face_encoding = []
known_face_encodings = []

for img in myresult1:
    image_n = str(img)
    n = image_n.strip("(',)") #ตัดสัญญาลักษณ์ออกจากข้อความ
    print(n)
    image = 'img/'+ str(n.strip())
# โหลดภาพ Pin.jpg และให้ระบบจดจำใบหน้า
    person1_image.append(face_recognition.load_image_file(image))
    person1_face_encoding.append(face_recognition.face_encodings(person1_image[a])[0])


    # สร้าง arrays ของคนที่จดจำและกำหนดชื่อ ตามลำดับ
    known_face_encodings.append(person1_face_encoding[a])
        
    
    a+1
known_face_names =[]

sql3 = "SELECT p_id FROM person"
mycursor.execute(sql3)
myresult3 = mycursor.fetchall()
for name_know in myresult3:
    know = str(name_know)
    k_n = know.strip("(',)")
    known_face_names.append(k_n)




# ตัวแปรเริ่มต้น
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True
i=0
while True:
    # ดึงเฟรมภาพมาจากวีดีโอ
    ret, frame = video_capture.read()

    # ย่อขนาดเฟรมเหลือ 1/4 ทำให้ face recognition ทำงานได้เร็วขึ้น
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # แปลงสีภาพจาก BGR (ถูกใช้ใน OpenCV) เป็นสีแบบ RGB (ถูกใช้ใน face_recognition)
    rgb_small_frame = small_frame[:, :, ::-1]

    # ประมวลผลเฟรมเว้นเฟรมเพื่อประหยัดเวลา
    if process_this_frame:
        # ค้นหาใบหน้าที่มีทั้งหมดในภาพ จากนั้นทำการ encodings ใบหน้าเพื่อจะนำไปใช้เปรียบเทียบต่อ
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # ทำการเปรียบเทียบใบหน้าที่อยู่ในวีดีโอกับใบหน้าที่รู้จักในระบบ
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # ถ้า encoding แล้วใบหน้าตรงกันก็จะแสดงข้อมูล
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            face_names.append(name)

            sql2 = 'SELECT p_id FROM check_temp WHERE p_id = (%s) '
            mycursor.execute(sql2,[name])
            myresult = mycursor.fetchall()
            print(myresult)
            if name != "Unknown":
                if myresult == []:       
                    sql = "INSERT INTO check_temp (p_id,temp,check_in) VALUES (%s,%s,%s)"
                    val = (name,"36",d)
                    mycursor.execute(sql,val)
                    mydb.commit()
                    print(mycursor.rowcount, "was inserted.")
                                        
                else:
                    print("repeated register !!")
                    
            d = datetime.datetime.now()        
            if d.day != t:
                print("test time")
                os.system('python backup_db.py')
                t = d.day             


    process_this_frame = not process_this_frame

    # แสดงผลลัพธ์
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # ขยายเฟรมที่ลดลงเหลือ 1/4 ให้กลับไปอยู่ในขนาดเดิม 
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # วาดกล่องรอบใบหน้า
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # เขียนตัวหนังสือที่แสดงชื่อลงที่กรอบ
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # แสดงรูปภาพผลลัพธ์
    cv2.imshow('Video', frame)

    # กด 'q' เพื่อปิด!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
        
video_capture.release()
cv2.destroyAllWindows()