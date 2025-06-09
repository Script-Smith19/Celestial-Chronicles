from pathlib import Path
import yaml
from typing import Optional
from graph_utils import toposort, build_reverse_graph, get_all_descendants


GameData = Path('.GameData')

CharacterFiles = GameData / Path('Characters')
CharacterFiles.mkdir(exist_ok=True)

CharacterSchemas = GameData / Path('CharacterSchemas')
CharacterSchemas.mkdir(exist_ok=True)

CharacterSchemaRegistry = {}
CharacterRegistry = {}

class CharacterSchema:
	def __init__(self, name: str):
		self._file_path = CharacterSchemas / Path(name + '.yaml')

		setattr(self, 'Name', name)
		with self._file_path.open('r') as file:
			data = yaml.safe_load(file) or {}
			
			setattr(self, 'Extends', data.pop('Extends', []) or [])
			setattr(self, 'Mandatory', data.pop('Mandatory', []))
			setattr(self, 'Optional', data.pop('Optional', []))
			setattr(self, 'AnyOf', data.pop('AnyOf', []))

		CharacterSchemaRegistry[self.Name] = self

	@classmethod
	def loadAll(cls):
		for file in CharacterSchemas.glob('*.yaml'):
			name = file.stem
			if name not in CharacterSchemaRegistry:
				cls(name)

class Character:
	def __init__(self, name: str, mode: Optional[str] = 'load'):
		if mode.lower() not in ['load', 'create']:
			raise ValueError("Mode must be either 'load' or 'create'.")
		
		self._file_path = CharacterFiles / Path(name.replace(' ', '_') + '.yaml')
		
		if mode.lower() == 'create':
			self._file_path.touch()
			self.Name = name
		elif mode.lower() == 'load':
			self.load()

		CharacterRegistry[self.Name] = self

	def to_dict(self):
		return {
			key: value
			for key, value in self.__dict__.items()
			if not key.startswith('_')
		}
	
	def save(self):
		with self._file_path.open('w') as file:
			yaml.dump(self.to_dict(), file, allow_unicode=True)

	def load(self):
		with self._file_path.open('r') as file:
			data = yaml.safe_load(file) or {}
			for key, value in data.items():
				setattr(self, key, value)

	def ValidateSchema(self, schema: CharacterSchema):
		ValidatedFields = set()
		MissingFields = set()

		if not schema.Extends:
			IsCoreSchema = False
		else:
			IsCoreSchema = True
		
		for field in schema.Mandatory:
			if hasattr(self, field):
				ValidatedFields.add(field)
			else:
				MissingFields.add(field)
		
		for field in schema.Optional:
			if hasattr(self, field):
				ValidatedFields.add(field)
		
		for field in schema.AnyOf:
			if not any(hasattr(self, opt) for opt in field):
				MissingFields.add(field)
			elif hasattr(self, field):
				ValidatedFields.add(field)
			else:
				pass

		if IsCoreSchema and len(MissingFields) > 0:
			return 0, ValidatedFields, MissingFields
		if len(MissingFields) > 0 and len(ValidatedFields) == 0:
			return 1, ValidatedFields, MissingFields
		if len(MissingFields) > 0 and len(ValidatedFields) != 0:
			return 0, ValidatedFields, MissingFields
		if len(MissingFields) == 0:
			return 2, ValidatedFields, MissingFields
		
		# if 0 is returned, then the character is in a unacceptable state
		# if 1 is returned, then the schema is invalid but if we drop this schema and those that it extends then the character is in a acceptable state
		# if 2 is returned, then the schema is valid and the character is in a acceptable state

def Validate(self):
	Schemas = toposort({
		name: schema.Extends for name, schema in CharacterSchemaRegistry.items()
	})
	reverse_graph = build_reverse_graph({
		name: schema.Extends for name, schema in CharacterSchemaRegistry.items()
	})

	DroppedSchemas = set()
	ValidFields = set()

	for schema_name in Schemas:
		if schema_name in DroppedSchemas:
			continue

		ErrorCode, ValidatedFields, MissingFields = self.ValidateSchema(CharacterSchemaRegistry[schema_name])

		if ErrorCode == 2:
			ValidFields |= ValidatedFields
		elif ErrorCode == 1:
			DroppedSchemas |= get_all_descendants(schema_name, reverse_graph)
		elif ErrorCode == 0:
			raise ValueError(f"Character '{self.Name}' is in an unacceptable state due to missing fields: {MissingFields}")