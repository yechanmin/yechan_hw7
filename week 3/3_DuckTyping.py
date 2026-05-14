class Dog:
   def speak(self):
      print("멍멍!")
class Cat:
   def speak(self):
      print("야옹~")
class Robot:
   def speak(self):
      print("삐리삐리!")

obj = [Dog(), Cat(), Robot()]

for o in obj:
   o.speak()
