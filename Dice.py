import random
import time
from typing import Optional, Callable, List

class Dice:
	def __init__(self, sides: int, weights: Optional[List[float]] = None, seed: Optional[int] = None):
		if sides < 2:
			raise ValueError("Dice must have at least 2 sides.")

		self.sides = sides
		self.faces = list(range(1, sides + 1))

		if weights is not None:
			if min(weights) == max(weights):
				weights = None
			else:
				if len(weights) != sides:
					raise ValueError("Number of weights must match number of sides.")
				if any(w < 0 for w in weights):
					raise ValueError("Weights must be non-negative.")
				if sum(weights) <= 0:
					raise ValueError("Sum of weights must be greater than zero.")
		self.weights = weights

		self.seed = seed if seed is not None else int(time.time_ns())
		self.rng = random.Random(self.seed)


	def roll(self) -> int:
		return self.rng.choices(self.faces, weights=self.weights, k=1)[0]

	def roll_many(self, k: int) -> List[int]:
		self._validate_k(k)
		return [self.roll() for _ in range(k)]

	def reroll_until(self, condition: Callable[[List[int]], bool]) -> List[int]:
		results = []
		while True:
			result = self.roll()
			results.append(result)
			if not condition(results):
				break
		return results
	
	def reroll_on_min(self) -> List[int]:
		return self.reroll_until(lambda rolls: rolls[-1] == 1)
	
	def reroll_on_max(self) -> List[int]:
		return self.reroll_until(lambda rolls: rolls[-1] == self.sides)

	def _validate_k(self, k: int):
		if k < 1:
			raise ValueError("Must roll at least once.")
		
	def get_seed(self) -> int:
		return self.seed

	def reseed(self, new_seed: Optional[int] = None):
		self.seed = new_seed if new_seed is not None else int(time.time_ns())
		self.rng.seed(self.seed)

	def __repr__(self):
		if self.weights is not None:
			return f'Weighted D{self.sides} with Weights{self.weights} Seeded with {self.seed}'
		else:
			return f'Unbiased D{self.sides} Seeded with {self.seed}'

# Dice Registry
DiceRegistry = {}