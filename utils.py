"""Definition of helpers functions"""

import json


def jsonable_class(name:str, slots:iter, bases:iter=[], other_attributes={},
                   repr_as_str:bool=True):
    """Return a class of given name and slots and bases and other_attributes.

    This class will implement a json conversion, allowing the object
    to be serialized easily.

    name -- class name
    slots -- iterable or comma separated string of the slot names.
    bases -- base classes
    other_attributes -- mapping name: value for additional attributes
    repr_as_str -- define __repr__ to behave like __str__

    Note that another way to provides other attributes is to subclass
    the class returned by this function.

    """
    if isinstance(slots, str):
        # broke up into pieces
        slots = tuple(map(str.strip, slots.split(',')))

    def build(name, slots, other_attributes):
        slots = tuple(slots)
        fields = tuple(field.lstrip('_') for field in slots)
        json_id = '__weldon_{}__'.format(name)
        constructor_def = """def constructor(self, {}):{}""".format(
            ', '.join(fields),
            '\n '+'\n '.join('self.{} = {}'.format(slot, slot.lstrip('_'))
                          for slot in slots) + '\n',
        )
        exec(constructor_def)  # get the function
        # for obscur reason, constructor is in locals but just accessing
        #  the variable do not works. So here's a patch
        constructor_func = locals()['constructor']
        def to_json(self):
            return {json_id: {
                field: getattr(self, field)
                for field in self.fields
            }}
        @classmethod
        def from_json(cls, data):
            payload = data.get(json_id)
            if payload:
                return cls(**payload)
        def get_fields(self):
            return fields
        def get_slot_getter(slotname):
            # we have to use slot, because found the slot knowing the field
            #  is non-trivial:  ______________a is a valid slot.
            @property
            def getter(self):
                return getattr(self, slotname)
            return getter
        def to_string(self):
            return '<{} {}>'.format(name, ' '.join('{}={}'.format(field, getattr(self, field)) for field in self.fields))
        attributes = {
            '__init__': constructor_func,
            '__slots__': slots,
            '__str__': to_string,
            'to_json': to_json,
            'from_json': from_json,
            'fields': property(get_fields),
            # **{slot.lstrip('_'): get_slot_getter(slot) for slot in slots
               # if slot.startswith('_')}, # else: no need for a accessor, slots are here
            # **other_attributes,
        }
        attributes.update(other_attributes)  # py 3.4 compatibility
        for slot in slots:
            if slot.startswith('_'):
                attributes[slot.lstrip('_')] = get_slot_getter(slot)
        if repr_as_str:
            attributes['__repr__'] = to_string
        return type(name, tuple(bases), attributes)
    return build(name, slots, other_attributes or {})


def custom_json_encoder(cls:type or [type]) -> json.JSONEncoder:
    """Return a class ready to be used by json module to encode given
    class(es) of custom objects.

    Classes must provide a as_json() method returning json serializable data.

    See https://docs.python.org/3.6/library/json.html for more background.

    """
    class CustomObjectEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, cls):
                return obj.to_json()
            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)
    return CustomObjectEncoder

def custom_json_decoder(classes:[type]):
    def custom_object_decoder(dct):
        for cls in classes:
            interp = cls.from_json(dct)
            if interp:
                return interp
        # nothing found
        return dct
    return custom_object_decoder
