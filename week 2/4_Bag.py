class Bag:
    def __init__(self):          #메서드(초기화)
        self.data = []

    def add(self, x):             #메서드 => 클래스 내부에서 정의되며, 첫번째 매개변수로 self를 사용
        self.data.append(x)       #self를 이용해 instance variable 접근 가능

    def addtwice(self, x):    #메서드 => 클래스 내부에서 정의되며, 첫번째 매개변수로 self를 사용
        self.add(x)                     #self를 이용해 다른 메서드 호출 가능
        self.add(x)

b = Bag()
b.add(10)
b.addtwice(20)
print(b.data)
