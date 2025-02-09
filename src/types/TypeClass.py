import logging

class TypeClass:
    def load_dict(self, data: dict | None):
        if data:
            for key, value in data.items():
                try:
                    getattr(self, key)
                except AttributeError:
                    logging.debug(f"{key} is not an existing key in {self.__class__.__name__}")
                    
                setattr(self, key, value)

    def __str__(self):
        return str(self.to_dict())
    
    def to_dict(self):
        result = {}
        for key, value in vars(self).items():
            if isinstance(value, TypeClass):
                result[key] = value.to_dict()
            else:
                result[key] = value
        
        return result