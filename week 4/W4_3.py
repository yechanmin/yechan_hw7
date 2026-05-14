class Player:
    def __init__(self):
        self.__hp = 100      # name mangling 적용

    @property                  #메서드를 속성처럼 사용할 수 있게 해주는 장치
    def hp(self):
        return self.__hp

    @hp.setter                 #setter 메서드
    def hp(self, value):
        if value < 0:
            self.__hp = 0
        else:
            self.__hp = value

p = Player()
print(p.hp)      # 변수처럼쓰지만 실제로는 메서드가 실행됨!
p.hp = -50       # 변수처럼쓰지만 실제로는 메서드가 실행됨! 내부에서 검증 후 처리됨
print(p.hp)