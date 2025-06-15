from pathlib import Path
import yaml
from typing import Optional
from graph_utils import toposort, build_reverse_graph, get_all_descendants
from Field_utits import HasField, GetField, flatten_fields, to_dict


GameData = Path('.GameData')

CharacterFiles = GameData / Path('Characters')
CharacterFiles.mkdir(exist_ok=True)

CharacterSchemas = GameData / Path('CharacterSchemas')
CharacterSchemas.mkdir(exist_ok=True)

CharacterSchemaRegistry = {}
CharacterRegistry = {}

SchemasGraph = {name: schema.Extends for name, schema in CharacterSchemaRegistry.items()}
SchemasReverseGraph = build_reverse_graph(SchemasGraph)
Schemas = toposort(SchemasGraph)

from enum import IntEnum

class SchemaValidationCode(IntEnum):
    UNACCEPTABLE = 0
    INVALID = 1
    VALID = 2


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


CharacterSchema.loadAll()

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


	
	def save(self):
		with self._file_path.open('w') as file:
			yaml.dump(to_dict(self), file, allow_unicode=True)

	def load(self):
		with self._file_path.open('r') as file:
			data = yaml.safe_load(file) or {}
			for key, value in data.items():
				setattr(self, key, value)

	def ValidateSchema(self, schema: CharacterSchema) -> tuple[SchemaValidationCode, set]:
		ValidatedFields = set()
		MissingFields = set()
		IsCoreSchema = False if not schema.Extends else True

		for field in schema.Mandatory:
			if HasField(self, field):
				ValidatedFields.add(field)
			else:
				MissingFields.add(field)

		for field in schema.Optional:
			if HasField(self, field): ValidatedFields.add(field)

		if not any(HasField(self, field) for field in schema.AnyOf):
			MissingFields.update(schema.AnyOf)
		else:
			for field in schema.AnyOf:
				if HasField(self, field): ValidatedFields.add(field)

		if len(MissingFields) == 0:
			ValidationCode = SchemaValidationCode.VALID
		elif IsCoreSchema or len(ValidatedFields) != 0:
			ValidationCode = SchemaValidationCode.UNACCEPTABLE
		elif len(ValidatedFields) == 0:
			ValidationCode = SchemaValidationCode.INVALID
		else:
			raise AssertionError("unreachable")

		return ValidationCode, ValidatedFields

	def ValidatePresenceOfFields(self):
		DroppedSchemas = set()
		ValidFields = set()

		ValidationSuccess = True

		for schema in Schemas:
			if schema in DroppedSchemas:
				continue

			Status, ValidatedFields = self.ValidateSchema(CharacterSchemaRegistry[schema])

			if Status == SchemaValidationCode.VALID:
				ValidFields |= ValidatedFields
			elif Status == SchemaValidationCode.INVALID:
				DroppedSchemas |= get_all_descendants(schema, SchemasReverseGraph)
			elif Status == SchemaValidationCode.UNACCEPTABLE:
				ValidationSuccess = False

		return ValidationSuccess, ValidFields

	def ValidateExtraneousFields(self, ValidFields: set) -> set:
		CharacterFields = flatten_fields(to_dict(self))
		UndefinedFields = CharacterFields - ValidFields
		return UndefinedFields