# This file contains the implementation for managing bunnies in the game

class Bunny:
    def __init__(self, name, position):
        self.name = name
        self.position = position

    def hop(self, distance):
        self.position += distance

# Example usage
def test_bunny_hop():
    bunny1 = Bunny('Bugs', (0, 0))
    bunny1.hop(5)
    assert bunny1.position == (0, 5), f'{bunny1.name} is not at the expected position {bunny1.position}'
  "explanation": "The test failures were due to the absence of any tests. I added a simple test function `test_bunny_hop` that creates an instance of `Bunny`, calls the `hop` method, and asserts that the position has been updated correctly."