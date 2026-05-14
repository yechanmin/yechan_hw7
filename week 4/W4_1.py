class Player:
    def __init__(self, name):
        self.name = name
        self.hp = 100
        self.score = 0

class Enemy:
    def __init__(self, name, damage):
        self.name = name
        self.damage = damage

    def attack(self, player):
        print(f"{self.name} attacks {player.name}!")
        player.hp -= self.damage
        print(f"{player.name}'s HP: {player.hp}")

player = Player("Koi")
enemy = Enemy("Biko", 25)

enemy.attack(player)

player.hp = -999
print(f"Someone changed {player.name}'s HP incorrectly: {player.hp}")

enemy.attack(player)
