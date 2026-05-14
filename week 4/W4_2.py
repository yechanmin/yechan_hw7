class Player:
    def __init__(self, name):
        self.name = name
        self._hp = 100
        self._score = 0

    def take_damage(self, amount):
        self._hp -= amount
        if self._hp < 0:
            self._hp = 0

    def add_score(self, value):
        if value > 0:
            self._score += value

    def get_hp(self):
        return self._hp

class Enemy:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

    def attack(self, player):
        print(f"{self.name} attacks {player.name}!")
        player.take_damage(self.damage)
        print(f"{player.name}'s HP: {player.get_hp()}")

player = Player("Koi")
enemy = Enemy("Biko", 30)
print(f"Initial HP: {player.get_hp()}")

enemy.attack(player)
player.add_score(100)
print("Score increased by 100")

enemy.attack(player)
enemy.attack(player)
enemy.attack(player)

print(f"Final HP: {player.get_hp()}")