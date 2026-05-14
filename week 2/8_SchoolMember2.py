
class SchoolMember:
    def __init__(self):
        self.name = '경기과학고'
        super().__init__()

    def introduce(self):
        print("안녕하세요!")

class ClubMember:
    def __init__(self):
        self.club = 'AI 동아리'
        super().__init__()

    def club_info(self):
        print("저는", self.club, "소속입니다.")

class Student(SchoolMember, ClubMember):   # 다중상속
    def __init__(self):
        # SchoolMember 클래스에 정의된 __init__ 메서드를 현재 객체(self)에 대해 실행해라
        #SchoolMember.__init__(self)   # SchoolMember의 __init__ 호출.
        #ClubMember.__init__(self)     # ClubMember의 __init__ 호출
        super().__init__()
        self.ID = '2600000'

    def introduce(self):
        super().introduce()
        print("반갑습니다!")
        print("이름:", self.name)
        print("학번:", self.ID)
        print("동아리:", self.club)

s = Student()
s.introduce()
s.club_info()