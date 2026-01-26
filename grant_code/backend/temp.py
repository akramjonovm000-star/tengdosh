from apps.user.models import User, Student
import csv

with open('students.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)  # Skip the header row
    for row in reader:
        user = User.objects.create(username=row[0])
        user.set_password(row[1]) 
        user.save()
        
        student = Student.objects.create(
            user=user,
            full_name=row[2],
            faculty=row[3],
            speciality=row[4],
            group=row[5],
            education_language=row[6],
            education_type=row[7],
            gpa=float(row[8]),
            level=1,
        )
        student.save()
        print(student)