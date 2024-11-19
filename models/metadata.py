

class Author:
    def __init__(self, name : str, url: str, id: str):
        self.name = name
        self.id = id
        self.url = url

    @staticmethod
    def empty():
        return Author("","","")

    def __str__(self):
        return ', '.join(f"{key}={value}" for key, value in self.__dict__.items())


class Genre:
    def __init__(self, name: str, url: str, id: int):
        self.name = name
        self.id = id
        self.url = url

    @staticmethod
    def empty():
        return Genre("", "", -1)

    def __str__(self):
        return ', '.join(f"{key}={value}" for key, value in self.__dict__.items())