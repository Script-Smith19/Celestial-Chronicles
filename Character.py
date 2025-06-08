from pathlib import Path
import yaml
from typing import Optional

character_registry = {}

class Character:
	def __init__(self, data: str, mode: Optional[str] = 'FILE'):
		CharacterFiles = Path('.GameData') / Path('Characters')
		CharacterFiles.mkdir(exist_ok=True)

		if mode not in ['FILE', 'NAME']:
			raise ValueError("Mode must be either 'FILE' or 'NAME'.")

		if mode == 'NAME':
			self._file_path = CharacterFiles / Path(data.replace(' ', '_') + '.yaml')
			name = data
		else:
			self._file_path = CharacterFiles / Path(data)
			name = self._file_path.stem.replace('_', ' ')

		self._file_path.touch(exist_ok=True)

		with self._file_path.open('r+') as f:
			yaml_data = yaml.safe_load(f) or {}

		if 'Name' not in yaml_data:
			yaml_data['Name'] = name

		for key, value in yaml_data.items():
			setattr(self, key, value)

		character_registry[self.Name] = self

	def to_dict(self):
		return {
			key: value
			for key, value in self.__dict__.items()
			if not key.startswith('_')
		}
	
	def save(self):
		with self._file_path.open('w') as file:
			yaml.dump(self.to_dict(), file, allow_unicode=True)
			
character_registry = {}