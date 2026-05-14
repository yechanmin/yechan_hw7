class SchoolMember:
    def __init__(self):
        self.name = '경기과학고'

    def introduce(self):
        print("안녕하세요!")

class Teacher(SchoolMember):
    pass

class Student(SchoolMember):
    def __init__(self):             #오버라이딩
        super().__init__()       # 부모클래스의 메소드를 호출하려면 super() 사용.
        self.ID = '2600000'

    def introduce(self):           #오버라이딩
        super().introduce()
        print("반갑습니다!")
t = Teacher()
print(t.name)

s = Student()
print(s.name)                       #error
s.introduce()
